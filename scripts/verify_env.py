"""Prüft .env: Pflichtfelder gesetzt, MongoDB erreichbar."""

from __future__ import annotations

import sys


def main() -> int:
    """Run the command workflow."""
    try:
        from config.settings import get_settings
        from repositories.mongo import ping
    except Exception as exc:  # noqa: BLE001
        print(f"Import fehlgeschlagen: {exc}")
        return 1

    try:
        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        print("Settings ungültig (fehlende oder leere Pflichtvariablen):")
        print(f"  {exc}")
        return 1

    masked = {
        "OPENAI_API_KEY": _mask(settings.openai_api_key),
        "MONGODB_URI": _mask_uri(settings.mongodb_uri),
        "MONGODB_DB_NAME": settings.mongodb_db_name,
        "LANGFUSE_PUBLIC_KEY": _mask(settings.langfuse_public_key),
        "LANGFUSE_SECRET_KEY": _mask(settings.langfuse_secret_key),
        "LANGFUSE_HOST": settings.langfuse_host,
        "APP_ENV": settings.app_env,
    }
    print("Geladene Settings (maskiert):")
    for key, value in masked.items():
        print(f"  {key}={value}")

    try:
        ping(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"MongoDB ping fehlgeschlagen: {exc}")
        return 1

    print("OK: Pflichtvariablen geladen, MongoDB ping erfolgreich.")
    return 0


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _mask_uri(uri: str) -> str:
    if "@" not in uri:
        return _mask(uri)
    prefix, rest = uri.split("@", 1)
    if "://" in prefix:
        scheme, _ = prefix.split("://", 1)
        return f"{scheme}://***@{rest}"
    return _mask(uri)


if __name__ == "__main__":
    sys.exit(main())
