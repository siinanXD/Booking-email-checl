"""WhatsApp-Empfänger pro Unterkunft (Cleaner/Mitarbeiter)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pymongo.collection import Collection

from repositories.mongo import Db


class PropertyWhatsAppRecipients(BaseModel):
    """Telefonnummern (E.164) für eine Unterkunft."""

    property_name: str
    phones: list[str] = Field(default_factory=list)


class PropertyRecipientRepository:
    """Collection `property_whatsapp_recipients`."""

    COLLECTION = "property_whatsapp_recipients"

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._col: Collection[dict[str, Any]] = db[self.COLLECTION]

    @staticmethod
    def _doc_id(account_id: str, property_name: str) -> str:
        key = property_name.strip().lower()
        return f"{account_id}:{key}"

    def get_phones(
        self,
        property_name: str | None,
        *,
        account_id: str | None = None,
    ) -> list[str]:
        """Lädt Empfänger für eine Unterkunft (case-insensitive Match)."""
        if not property_name or not property_name.strip() or not account_id:
            return []
        doc_id = self._doc_id(account_id, property_name)
        doc = self._col.find_one({"_id": doc_id})
        if doc is None:
            key = property_name.strip().lower()
            doc = self._col.find_one(
                {"property_name_lower": key, "account_id": account_id}
            )
        if doc is None:
            return []
        record = PropertyWhatsAppRecipients.model_validate(doc)
        return list(record.phones)

    def upsert(
        self,
        account_id: str,
        property_name: str,
        phones: list[str],
    ) -> PropertyWhatsAppRecipients:
        """Legt oder aktualisiert Empfänger für eine Unterkunft."""
        key = property_name.strip().lower()
        record = PropertyWhatsAppRecipients(
            property_name=property_name.strip(), phones=phones
        )
        doc = record.model_dump(mode="json")
        doc["_id"] = self._doc_id(account_id, property_name)
        doc["account_id"] = account_id
        doc["property_name_lower"] = key
        self._col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        return record

    def list_all(self, account_id: str) -> list[PropertyWhatsAppRecipients]:
        """Alle Unterkunft → Telefon-Zuordnungen eines Accounts."""
        records: list[PropertyWhatsAppRecipients] = []
        cursor = self._col.find({"account_id": account_id}).sort("property_name", 1)
        for doc in cursor:
            payload = {
                k: v for k, v in doc.items() if k not in ("_id", "property_name_lower")
            }
            records.append(PropertyWhatsAppRecipients.model_validate(payload))
        return records

    def replace_all(
        self,
        account_id: str,
        items: list[tuple[str, list[str]]],
    ) -> None:
        """Ersetzt die gesamte Empfänger-Liste eines Accounts."""
        self._col.delete_many({"account_id": account_id})
        for property_name, phones in items:
            name = property_name.strip()
            if not name:
                continue
            self.upsert(account_id, name, [p.strip() for p in phones if p.strip()])
