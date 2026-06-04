"""Historie gespeicherter LLM-Prompt-Overrides."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from backend.infrastructure.repositories.mongo import Db

LlmPromptType = Literal["classify", "extract", "draft"]
MAX_ENTRIES_PER_TYPE = 50


class PlatformLlmPromptHistoryEntry(BaseModel):
    """Ein gespeicherter Prompt-Snapshot."""

    id: str
    prompt_type: LlmPromptType
    prompt_text: str | None = None
    user_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlatformLlmPromptHistoryRepository:
    """Collection `platform_llm_prompt_history`."""

    COLLECTION = "platform_llm_prompt_history"

    def __init__(self, db: Db) -> None:
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    def append(
        self,
        prompt_type: LlmPromptType,
        prompt_text: str | None,
        *,
        user_id: str | None = None,
    ) -> PlatformLlmPromptHistoryEntry:
        entry_id = uuid4().hex
        entry = PlatformLlmPromptHistoryEntry(
            id=entry_id,
            prompt_type=prompt_type,
            prompt_text=prompt_text,
            user_id=user_id,
        )
        doc = entry.model_dump(mode="json")
        doc["_id"] = entry_id
        self._col.insert_one(doc)
        self._trim_old_entries(prompt_type)
        return entry

    def list_by_type(
        self,
        prompt_type: LlmPromptType,
        *,
        limit: int = 15,
    ) -> list[PlatformLlmPromptHistoryEntry]:
        cursor = (
            self._col.find({"prompt_type": prompt_type})
            .sort("created_at", -1)
            .limit(max(1, min(limit, MAX_ENTRIES_PER_TYPE)))
        )
        entries: list[PlatformLlmPromptHistoryEntry] = []
        for doc in cursor:
            payload = {k: v for k, v in doc.items() if k != "_id"}
            entries.append(PlatformLlmPromptHistoryEntry.model_validate(payload))
        return entries

    def _trim_old_entries(self, prompt_type: LlmPromptType) -> None:
        excess = (
            self._col.count_documents({"prompt_type": prompt_type})
            - MAX_ENTRIES_PER_TYPE
        )
        if excess <= 0:
            return
        oldest = (
            self._col.find({"prompt_type": prompt_type}, {"_id": 1})
            .sort("created_at", 1)
            .limit(excess)
        )
        ids = [doc["_id"] for doc in oldest]
        if ids:
            self._col.delete_many({"_id": {"$in": ids}})
