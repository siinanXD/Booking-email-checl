"""Globale LLM-/Prompt-Konfiguration (Plattform-Admin)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db

GLOBAL_LLM_CONFIG_ID = "global"


class PlatformLlmConfigRecord(BaseModel):
    """Singleton-Konfiguration für LLM-Pipeline."""

    id: str = GLOBAL_LLM_CONFIG_ID
    classify_temperature: float = 0.0
    extract_temperature: float = 0.0
    draft_temperature: float = 0.0
    similarity_top_k: int = 3
    classify_prompt_override: str | None = None
    extract_prompt_override: str | None = None
    draft_prompt_override: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_by_user_id: str | None = None


class PlatformLlmConfigRepository:
    """Collection `platform_llm_config` — ein Dokument `_id: global`."""

    COLLECTION = "platform_llm_config"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def get(self) -> PlatformLlmConfigRecord | None:
        doc = self._col.find_one({"_id": GLOBAL_LLM_CONFIG_ID})
        if doc is None:
            return None
        payload = {k: v for k, v in doc.items() if k != "_id"}
        payload["id"] = GLOBAL_LLM_CONFIG_ID
        return PlatformLlmConfigRecord.model_validate(payload)

    def get_or_default(self) -> PlatformLlmConfigRecord:
        return self.get() or PlatformLlmConfigRecord()

    def save(
        self,
        record: PlatformLlmConfigRecord,
        *,
        updated_by_user_id: str | None = None,
    ) -> PlatformLlmConfigRecord:
        record.updated_at = datetime.now(UTC)
        record.updated_by_user_id = updated_by_user_id
        doc = record.model_dump(mode="json")
        doc["_id"] = GLOBAL_LLM_CONFIG_ID
        doc["id"] = GLOBAL_LLM_CONFIG_ID
        self._col.replace_one({"_id": GLOBAL_LLM_CONFIG_ID}, doc, upsert=True)
        return record
