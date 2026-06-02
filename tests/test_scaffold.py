"""Smoke-Tests für Projekt-Scaffold."""

from __future__ import annotations


def test_package_imports() -> None:
    """Verify package imports."""
    import config  # noqa: F401
    import models  # noqa: F401
    import services  # noqa: F401


def test_settings_module_loads() -> None:
    """Verify settings module loads."""
    from config import settings

    assert hasattr(settings, "Settings")
