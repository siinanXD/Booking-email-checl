"""Tenant-Workflow API-Schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

WorkflowImportance = Literal["high", "medium", "low"]
WorkflowLlmProvider = Literal["openai", "gemini"]


class WorkflowMatchRulesSchema(BaseModel):
    subject_keywords: list[str] = Field(default_factory=list)
    from_domains: list[str] = Field(default_factory=list)
    body_keywords: list[str] = Field(default_factory=list)


class WorkflowTestEmailSchema(BaseModel):
    subject: str
    body: str
    expected_fields: dict[str, Any] | None = None


class WorkflowFewShotExampleSchema(BaseModel):
    subject: str
    body: str
    expected_json: dict[str, Any] = Field(default_factory=dict)


class TenantWorkflowSummary(BaseModel):
    id: str
    slug: str
    label: str
    description: str
    enabled: bool
    sandbox_only: bool
    importance: WorkflowImportance
    supports_multimodal: bool
    test_email_count: int
    tests_passed: bool = False
    updated_at: str


class TenantWorkflowListResponse(BaseModel):
    items: list[TenantWorkflowSummary]


class TenantWorkflowResponse(BaseModel):
    id: str
    account_id: str
    slug: str
    label: str
    description: str
    enabled: bool
    sandbox_only: bool
    priority: int
    search_hints: str
    importance: WorkflowImportance
    required_fields: list[str]
    optional_fields: list[str]
    extraction_schema: dict[str, Any]
    classify_prompt: str
    extract_prompt: str
    draft_prompt: str
    few_shot_examples: list[WorkflowFewShotExampleSchema]
    test_emails: list[WorkflowTestEmailSchema]
    match_rules: WorkflowMatchRulesSchema
    llm_provider: WorkflowLlmProvider
    supports_multimodal: bool
    multimodal_prompt: str
    last_test_passed_at: str | None = None
    last_test_passed_count: int = 0
    last_test_passed_total: int = 0
    created_by_user_id: str | None
    updated_by_user_id: str | None
    created_at: str
    updated_at: str
    version: int


class TenantWorkflowCreateRequest(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=80)
    description: str = ""
    search_hints: str = ""
    importance: WorkflowImportance = "medium"
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    extraction_schema: dict[str, Any] = Field(default_factory=dict)
    classify_prompt: str = ""
    extract_prompt: str = ""
    draft_prompt: str = ""
    few_shot_examples: list[WorkflowFewShotExampleSchema] = Field(default_factory=list)
    test_emails: list[WorkflowTestEmailSchema] = Field(default_factory=list)
    match_rules: WorkflowMatchRulesSchema = Field(
        default_factory=WorkflowMatchRulesSchema
    )
    llm_provider: WorkflowLlmProvider = "openai"
    supports_multimodal: bool = False
    multimodal_prompt: str = ""
    enabled: bool = False
    sandbox_only: bool = True
    priority: int = 0


class TenantWorkflowUpdateRequest(TenantWorkflowCreateRequest):
    """PUT-Body — gleiche Felder wie Create."""


class TenantWorkflowSuggestRequest(BaseModel):
    """Beschreibung für KI-Assistent."""

    description: str = Field(min_length=10, max_length=4000)
    label_hint: str | None = Field(default=None, max_length=120)


class TenantWorkflowSuggestResponse(BaseModel):
    """KI-Vorschlag — noch nicht gespeichert."""

    label: str
    slug: str
    description: str
    search_hints: str
    importance: WorkflowImportance
    required_fields: list[str]
    optional_fields: list[str]
    extraction_schema: dict[str, Any]
    classify_prompt: str
    extract_prompt: str
    match_rules: WorkflowMatchRulesSchema
    test_emails: list[WorkflowTestEmailSchema]
    llm_provider: WorkflowLlmProvider = "openai"
    supports_multimodal: bool = False


class TenantWorkflowPreviewRequest(BaseModel):
    subject: str = "Test-Betreff"
    body: str = "Test-Inhalt der E-Mail."


class TenantWorkflowPreviewResponse(BaseModel):
    success: bool
    result: str | None = None
    error: str | None = None
    model: str


class TenantWorkflowTestCaseResult(BaseModel):
    subject: str
    success: bool
    result: str | None = None
    error: str | None = None


class TenantWorkflowRunTestsResponse(BaseModel):
    workflow_id: str
    total: int
    passed: int
    results: list[TenantWorkflowTestCaseResult]
