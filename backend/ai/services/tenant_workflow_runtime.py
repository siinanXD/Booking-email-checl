"""Live-Routing und Ausführung mandantenspezifischer Workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from backend.ai.services.classification import LLMClient
from backend.ai.services.gemini_client import GeminiClientProtocol
from backend.ai.services.llm_errors import LLM_PIPELINE_ERRORS
from backend.core.models.email import StoredEmail
from backend.infrastructure.repositories.tenant_workflow_repository import (
    TenantWorkflowRecord,
    TenantWorkflowRepository,
)


@dataclass(frozen=True)
class WorkflowRouteResult:
    """Ergebnis der Workflow-Auswahl."""

    workflow: TenantWorkflowRecord
    score: int


class WorkflowRouter:
    """Wählt aktive Live-Workflows anhand einfacher Match-Regeln."""

    def __init__(self, repo: TenantWorkflowRepository) -> None:
        self._repo = repo

    def match(
        self,
        account_id: str | None,
        email: StoredEmail,
    ) -> WorkflowRouteResult | None:
        if not account_id:
            return None
        candidates = self._repo.list_live(account_id)
        if not candidates:
            return None

        subject = email.subject.lower()
        body = email.body_text.lower()
        from_domain = (
            email.from_address.rsplit("@", 1)[-1].lower()
            if "@" in email.from_address
            else ""
        )

        best: WorkflowRouteResult | None = None
        for workflow in candidates:
            score = _score_workflow(workflow, subject, body, from_domain)
            if score <= 0:
                continue
            if (
                best is None
                or score > best.score
                or (score == best.score and workflow.priority > best.workflow.priority)
            ):
                best = WorkflowRouteResult(workflow=workflow, score=score)
        return best


def _score_workflow(
    workflow: TenantWorkflowRecord,
    subject: str,
    body: str,
    from_domain: str,
) -> int:
    rules = workflow.match_rules
    if (
        not rules.subject_keywords
        and not rules.body_keywords
        and not rules.from_domains
    ):
        return 0

    score = 0
    for keyword in rules.subject_keywords:
        if keyword.lower() in subject:
            score += 2
    for keyword in rules.body_keywords:
        if keyword.lower() in body:
            score += 1
    for domain in rules.from_domains:
        if from_domain == domain.lower() or from_domain.endswith(f".{domain.lower()}"):
            score += 3
    return score


class TenantWorkflowExecutor:
    """Klassifikation, Extraktion und Validierung für Custom-Workflows."""

    def __init__(
        self,
        llm: LLMClient,
        *,
        classify_model: str,
        extract_model: str,
        gemini: GeminiClientProtocol | None = None,
        gemini_extract_model: str = "gemini-2.0-flash",
    ) -> None:
        self._llm = llm
        self._classify_model = classify_model
        self._extract_model = extract_model
        self._gemini = gemini
        self._gemini_extract_model = gemini_extract_model

    def classify_match(
        self,
        workflow: TenantWorkflowRecord,
        email: StoredEmail,
    ) -> bool:
        if not workflow.classify_prompt.strip():
            return True
        prompt = _format_prompt(
            workflow.classify_prompt,
            subject=email.subject,
            body=email.body_text,
            from_address=email.from_address,
        )
        try:
            completion = self._llm.complete(
                prompt,
                self._classify_model,
                temperature=0.0,
            )
            slug = completion.text.strip().lower().replace(" ", "_")
            return slug in {"match", workflow.slug, "yes", "true"}
        except LLM_PIPELINE_ERRORS:
            return False

    def extract_fields(
        self,
        workflow: TenantWorkflowRecord,
        email: StoredEmail,
    ) -> dict[str, Any]:
        if workflow.llm_provider == "gemini":
            return self._extract_with_gemini(workflow, email)
        if not workflow.extract_prompt.strip():
            return {"confidence": 0.0}
        prompt = format_extract_prompt(workflow, email.subject, email.body_text)
        try:
            completion = self._llm.complete(
                prompt,
                self._extract_model,
                temperature=0.0,
            )
            return parse_json_object(completion.text)
        except LLM_PIPELINE_ERRORS:
            return {"confidence": 0.0}

    def _extract_with_gemini(
        self,
        workflow: TenantWorkflowRecord,
        email: StoredEmail,
    ) -> dict[str, Any]:
        if self._gemini is None:
            return {"confidence": 0.0, "error": "gemini_not_configured"}
        prompt = build_gemini_extract_prompt(
            workflow,
            email.subject,
            email.body_text,
        )
        if not prompt.strip():
            return {"confidence": 0.0}
        try:
            completion = self._gemini.complete_text(
                prompt,
                self._gemini_extract_model,
                temperature=0.0,
            )
            return parse_json_object(completion.text)
        except LLM_PIPELINE_ERRORS:
            return {"confidence": 0.0}

    def validate_fields(
        self,
        workflow: TenantWorkflowRecord,
        data: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        for field_name in workflow.required_fields:
            value = data.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"missing required field: {field_name}")
        return errors


def format_extract_prompt(
    workflow: TenantWorkflowRecord,
    subject: str,
    body: str,
) -> str:
    return _format_prompt(
        workflow.extract_prompt,
        subject=subject,
        body=body,
    )


def build_gemini_extract_prompt(
    workflow: TenantWorkflowRecord,
    subject: str,
    body: str,
) -> str:
    sections: list[str] = []
    if workflow.multimodal_prompt.strip():
        sections.append(workflow.multimodal_prompt.strip())
    if workflow.extract_prompt.strip() or subject or body:
        sections.append(format_extract_prompt(workflow, subject, body))
    return "\n\n".join(sections) if sections else ""


def _format_prompt(
    template: str,
    *,
    subject: str,
    body: str,
    from_address: str = "",
) -> str:
    safe_subject = subject.replace("{", "{{").replace("}", "}}")
    safe_body = body.replace("{", "{{").replace("}", "}}")
    safe_from = from_address.replace("{", "{{").replace("}", "}}")
    if "{subject}" in template or "{body}" in template or "{from_address}" in template:
        return template.format(
            subject=safe_subject,
            body=safe_body,
            from_address=safe_from,
        )
    return (
        f"{template.rstrip()}\n\n"
        f"--- BEGIN UNTRUSTED MAIL ---\n"
        f"Betreff: {safe_subject}\n"
        f"Absender: {safe_from}\n"
        f"Inhalt:\n{safe_body}\n"
        f"--- END UNTRUSTED MAIL ---"
    )


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        msg = "LLM-Antwort ist kein JSON-Objekt"
        raise ValueError(msg)
    return payload
