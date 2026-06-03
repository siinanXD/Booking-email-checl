"""CRUD für Gäste und Buchungen (mandantenscharf)."""

from __future__ import annotations

import re
from typing import Any

from pymongo.collection import Collection

from backend.core.models.entities import Guest, Reservation
from backend.infrastructure.repositories.domain_collections import BOOKINGS, GUESTS
from backend.infrastructure.repositories.mongo import Db
from backend.infrastructure.repositories.tenant_scope import with_account_filter


class EntityRepository:
    """Repository für Booking-Entitäten mit account_id-Scope."""

    GUESTS = GUESTS
    BOOKINGS = BOOKINGS

    def __init__(self, db: Db) -> None:
        """Initialize the instance with its dependencies."""
        self._guests: Collection[dict[str, Any]] = db[self.GUESTS]
        self._bookings: Collection[dict[str, Any]] = db[self.BOOKINGS]
        self._guests.create_index([("account_id", 1), ("email", 1)])
        self._bookings.create_index([("account_id", 1), ("booking_number", 1)])
        self._bookings.create_index([("account_id", 1), ("guest_id", 1)])
        self._bookings.create_index([("account_id", 1), ("correlation_id", 1)])

    def upsert_guest(
        self,
        guest: Guest,
        *,
        account_id: str | None = None,
    ) -> Guest:
        """Gast speichern oder aktualisieren."""
        doc = guest.to_mongo()
        resolved_account = account_id or guest.account_id
        if resolved_account:
            doc["account_id"] = resolved_account
        self._guests.update_one(
            {"_id": guest.guest_id},
            {"$set": doc},
            upsert=True,
        )
        return guest

    def get_guest_by_email(
        self,
        email: str,
        *,
        account_id: str | None = None,
    ) -> Guest | None:
        """Gast anhand E-Mail-Adresse."""
        query = with_account_filter({"email": email.strip().lower()}, account_id)
        doc = self._guests.find_one(query)
        if doc is None:
            return None
        return Guest.from_mongo(doc)

    def get_guest_by_id(
        self,
        guest_id: str,
        *,
        account_id: str | None = None,
    ) -> Guest | None:
        """Gast anhand guest_id."""
        query = with_account_filter({"_id": guest_id}, account_id)
        doc = self._guests.find_one(query)
        if doc is None:
            return None
        return Guest.from_mongo(doc)

    def find_guests_by_name_and_platform(
        self,
        name: str,
        platform: str,
        *,
        account_id: str | None = None,
    ) -> list[Guest]:
        """Gäste mit gleichem Namen (case-insensitive) und Plattform."""
        pattern = re.compile(f"^{re.escape(name.strip())}$", re.IGNORECASE)
        base: dict[str, Any] = {"platform": platform.strip().lower()}
        query = with_account_filter(base, account_id)
        cursor = self._guests.find(query)
        return [
            Guest.from_mongo(doc)
            for doc in cursor
            if doc.get("name") and pattern.match(str(doc["name"]).strip())
        ]

    def upsert_reservation(
        self,
        reservation: Reservation,
        *,
        account_id: str | None = None,
    ) -> Reservation:
        """Reservierung speichern oder aktualisieren."""
        doc = reservation.to_mongo()
        resolved_account = account_id or reservation.account_id
        if resolved_account:
            doc["account_id"] = resolved_account
        self._bookings.update_one(
            {"_id": reservation.reservation_id},
            {"$set": doc},
            upsert=True,
        )
        return reservation

    def find_reservations_by_guest_id(
        self,
        guest_id: str,
        *,
        account_id: str | None = None,
    ) -> list[Reservation]:
        """Reservierungen eines Gastes."""
        query = with_account_filter({"guest_id": guest_id}, account_id)
        cursor = self._bookings.find(query)
        return [Reservation.from_mongo(doc) for doc in cursor]

    def find_reservations_by_guest_email(
        self,
        email: str,
        *,
        account_id: str | None = None,
    ) -> list[Reservation]:
        """Reservierungen über Gast-E-Mail (über guest_id-Verknüpfung)."""
        guest = self.get_guest_by_email(email, account_id=account_id)
        if guest is None:
            return []
        return self.find_reservations_by_guest_id(
            guest.guest_id,
            account_id=account_id,
        )

    def find_reservation_by_booking_number(
        self,
        booking_number: str,
        *,
        account_id: str | None = None,
    ) -> Reservation | None:
        """Reservierung anhand Buchungsnummer."""
        query = with_account_filter({"booking_number": booking_number}, account_id)
        doc = self._bookings.find_one(query)
        if doc is None:
            return None
        return Reservation.from_mongo(doc)

    def find_reservations_by_correlation_id(
        self,
        correlation_id: str,
        *,
        account_id: str | None = None,
    ) -> list[Reservation]:
        """Reservierungen einer Mail-Korrelation."""
        query = with_account_filter({"correlation_id": correlation_id}, account_id)
        cursor = self._bookings.find(query)
        return [Reservation.from_mongo(doc) for doc in cursor]
