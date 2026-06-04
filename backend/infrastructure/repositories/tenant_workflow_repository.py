"""Mandanten-spezifische Workflow-Definitionen (Phase A: Sandbox)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db

WorkflowImportance = Literal["high", "medium", "low"]
WorkflowLlmProvider = Literal["openai", "gemini"]


class WorkflowMatchRules(BaseModel):
    """Einfache Routing-Hinweise (Phase B: Live-Routing)."""

    subject_keywords: list[str] = Field(default_factory=list)
    from_domains: list[str] = Field(default_factory=list)
    body_keywords: list[str] = Field(default_factory=list)


class WorkflowTestEmail(BaseModel):
    """Test-Mail für Preview und spätere Eval."""

    subject: str
    body: str
    expected_fields: dict[str, Any] | None = None


class WorkflowFewShotExample(BaseModel):
    """Few-Shot-Beispiel für Klassifikation/Extraktion."""

    subject: str
    body: str
    expected_json: dict[str, Any] = Field(default_factory=dict)


class TenantWorkflowRecord(BaseModel):
    """Ein mandantenspezifischer Workflow-Pack."""

    id: str
    account_id: str
    slug: str
    label: str
    description: str = ""
    enabled: bool = False
    sandbox_only: bool = True
    priority: int = 0
    search_hints: str = ""
    importance: WorkflowImportance = "medium"
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    extraction_schema: dict[str, Any] = Field(default_factory=dict)
    classify_prompt: str = ""
    extract_prompt: str = ""
    draft_prompt: str = ""
    few_shot_examples: list[WorkflowFewShotExample] = Field(default_factory=list)
    test_emails: list[WorkflowTestEmail] = Field(default_factory=list)
    match_rules: WorkflowMatchRules = Field(default_factory=WorkflowMatchRules)
    llm_provider: WorkflowLlmProvider = "openai"
    supports_multimodal: bool = False
    multimodal_prompt: str = ""
    last_test_passed_at: datetime | None = None
    last_test_passed_total: int = 0
    last_test_passed_count: int = 0
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


def slugify_label(label: str) -> str:
    """Erzeugt einen URL-/API-tauglichen Slug aus einem Label."""
    base = label.strip().lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    base = base.strip("_")
    return base or "workflow"


class TenantWorkflowRepository:
    """Collection `tenant_workflows` — partitioniert nach account_id."""

    COLLECTION = "tenant_workflows"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def create(
        self,
        record: TenantWorkflowRecord,
        *,
        created_by_user_id: str | None = None,
    ) -> TenantWorkflowRecord:
        if self.get_by_slug(record.account_id, record.slug):
            msg = f"Workflow slug already exists: {record.slug!r}"
            raise ValueError(msg)
        now = datetime.now(UTC)
        record.id = record.id or uuid4().hex
        record.created_at = now
        record.updated_at = now
        record.created_by_user_id = created_by_user_id
        record.updated_by_user_id = created_by_user_id
        doc = record.model_dump(mode="json")
        doc["_id"] = record.id
        self._col.insert_one(doc)
        return record

    def get(self, account_id: str, workflow_id: str) -> TenantWorkflowRecord | None:
        doc = self._col.find_one({"_id": workflow_id, "account_id": account_id})
        if doc is None:
            return None
        payload = {k: v for k, v in doc.items() if k != "_id"}
        return TenantWorkflowRecord.model_validate(payload)

    def get_by_slug(
        self,
        account_id: str,
        slug: str,
    ) -> TenantWorkflowRecord | None:
        doc = self._col.find_one({"account_id": account_id, "slug": slug})
        if doc is None:
            return None
        payload = {k: v for k, v in doc.items() if k != "_id"}
        payload["id"] = doc["_id"]
        return TenantWorkflowRecord.model_validate(payload)

    def list_for_account(
        self,
        account_id: str,
        *,
        enabled_only: bool = False,
    ) -> list[TenantWorkflowRecord]:
        query: dict[str, Any] = {"account_id": account_id}
        if enabled_only:
            query["enabled"] = True
        cursor = self._col.find(query).sort([("priority", -1), ("updated_at", -1)])
        records: list[TenantWorkflowRecord] = []
        for doc in cursor:
            payload = {k: v for k, v in doc.items() if k != "_id"}
            payload["id"] = doc["_id"]
            records.append(TenantWorkflowRecord.model_validate(payload))
        return records

    def list_live(self, account_id: str) -> list[TenantWorkflowRecord]:
        """Aktive Live-Workflows (enabled, nicht Sandbox) für Routing."""
        query: dict[str, Any] = {
            "account_id": account_id,
            "enabled": True,
            "sandbox_only": False,
        }
        cursor = self._col.find(query).sort([("priority", -1), ("updated_at", -1)])
        records: list[TenantWorkflowRecord] = []
        for doc in cursor:
            payload = {k: v for k, v in doc.items() if k != "_id"}
            payload["id"] = doc["_id"]
            records.append(TenantWorkflowRecord.model_validate(payload))
        return records

    def update(
        self,
        record: TenantWorkflowRecord,
        *,
        updated_by_user_id: str | None = None,
    ) -> TenantWorkflowRecord:
        existing = self.get(record.account_id, record.id)
        if existing is None:
            msg = f"Workflow not found: {record.id}"
            raise ValueError(msg)
        if existing.slug != record.slug:
            conflict = self.get_by_slug(record.account_id, record.slug)
            if conflict is not None and conflict.id != record.id:
                msg = f"Workflow slug already exists: {record.slug!r}"
                raise ValueError(msg)
        record.version = existing.version + 1
        record.created_at = existing.created_at
        record.created_by_user_id = existing.created_by_user_id
        record.updated_at = datetime.now(UTC)
        record.updated_by_user_id = updated_by_user_id
        doc = record.model_dump(mode="json")
        doc["_id"] = record.id
        self._col.replace_one(
            {"_id": record.id, "account_id": record.account_id},
            doc,
        )
        return record

    def delete(self, account_id: str, workflow_id: str) -> bool:
        result = self._col.delete_one({"_id": workflow_id, "account_id": account_id})
        return bool(result.deleted_count > 0)
