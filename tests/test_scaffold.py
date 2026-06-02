"""Smoke-Tests für Projekt-Scaffold."""

from __future__ import annotations


def test_package_imports() -> None:
    """Verify backend package imports."""
    import backend  # noqa: F401
    import backend.ai.services  # noqa: F401
    import backend.core.config  # noqa: F401


def test_settings_module_loads() -> None:
    """Verify settings module loads."""
    from backend.core.config import settings

    assert hasattr(settings, "Settings")
