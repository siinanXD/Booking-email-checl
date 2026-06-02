"""JWT-Blocklist: MongoDB in Produktion, In-Memory in Tests."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from repositories.revoked_token_repository import RevokedTokenRepository

_backend: BlocklistBackend | None = None


class BlocklistBackend(ABC):
    """Abstraktion für Token-Widerruf."""

    @abstractmethod
    def revoke(self, jti: str, *, expires_at: datetime | None = None) -> None:
        """Token widerrufen."""

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Prüft ob Token widerrufen wurde."""


class InMemoryBlocklistBackend(BlocklistBackend):
    """Prozess-lokale Blocklist (nur Tests / Single-Worker-Dev)."""

    def __init__(self) -> None:
        """Leere In-Memory-Menge."""
        self._revoked: set[str] = set()

    def revoke(self, jti: str, *, expires_at: datetime | None = None) -> None:
        """Token widerrufen (expires_at wird ignoriert)."""
        _ = expires_at
        self._revoked.add(jti)

    def is_revoked(self, jti: str) -> bool:
        """Prüft ob Token widerrufen wurde."""
        return jti in self._revoked

    def clear(self) -> None:
        """Leert Blocklist (nur Tests)."""
        self._revoked.clear()


class MongoBlocklistBackend(BlocklistBackend):
    """MongoDB-Blocklist für Gunicorn mit mehreren Workern."""

    def __init__(self, repo: RevokedTokenRepository) -> None:
        """Verdrahtet Repository."""
        self._repo = repo

    def revoke(self, jti: str, *, expires_at: datetime | None = None) -> None:
        """Token widerrufen."""
        self._repo.revoke(jti, expires_at=expires_at)

    def is_revoked(self, jti: str) -> bool:
        """Prüft ob Token widerrufen wurde."""
        return self._repo.is_revoked(jti)


def configure(backend: BlocklistBackend) -> None:
    """Setzt Backend (App-Start oder Test-Fixture)."""
    global _backend
    _backend = backend


def _require() -> BlocklistBackend:
    if _backend is None:
        msg = "JWT blocklist not configured; call configure() at app startup"
        raise RuntimeError(msg)
    return _backend


def revoke(jti: str, *, expires_at: datetime | None = None) -> None:
    """Token widerrufen."""
    _require().revoke(jti, expires_at=expires_at)


def is_revoked(jti: str) -> bool:
    """Prüft ob Token widerrufen wurde."""
    return _require().is_revoked(jti)


def clear_for_tests() -> None:
    """Leert Blocklist (nur Tests)."""
    backend = _backend
    if isinstance(backend, InMemoryBlocklistBackend):
        backend.clear()
    elif isinstance(backend, MongoBlocklistBackend):
        backend._repo.clear_all()


def _exp_from_payload(exp: object) -> datetime | None:
    """JWT `exp` Claim in UTC-datetime."""
    if isinstance(exp, int | float):
        return datetime.fromtimestamp(exp, tz=UTC)
    return None
