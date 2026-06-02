"""One-time backend restructure: git mv + import rewrite. Run from repo root."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MOVES: list[tuple[str, str]] = [
    ("config", "backend/core/config"),
    ("models", "backend/core/models"),
    ("utils", "backend/core/utils"),
    ("repositories", "backend/infrastructure/repositories"),
    ("observability", "backend/infrastructure/observability"),
    ("workflows", "backend/ai/workflows"),
    ("prompts", "backend/ai/prompts"),
    ("routers", "backend/application"),
    ("web", "backend/api"),
    ("services/triage.py", "backend/ai/services/triage.py"),
    ("services/classification.py", "backend/ai/services/classification.py"),
    ("services/extraction.py", "backend/ai/services/extraction.py"),
    ("services/validation.py", "backend/ai/services/validation.py"),
    ("services/retrieval.py", "backend/ai/services/retrieval.py"),
    ("services/similarity_search.py", "backend/ai/services/similarity_search.py"),
    ("services/response_generation.py", "backend/ai/services/response_generation.py"),
    ("services/grounding.py", "backend/ai/services/grounding.py"),
    ("services/indexing.py", "backend/ai/services/indexing.py"),
    ("services/ingestion.py", "backend/ai/services/ingestion.py"),
    ("services/prompt_loader.py", "backend/ai/services/prompt_loader.py"),
    ("services/openai_client.py", "backend/ai/services/openai_client.py"),
    ("services/mock_llm.py", "backend/ai/services/mock_llm.py"),
    ("services/llm_errors.py", "backend/ai/services/llm_errors.py"),
    ("services/llm_types.py", "backend/ai/services/llm_types.py"),
    (
        "services/mail_connection_service.py",
        "backend/features/mail/mail_connection_service.py",
    ),
    ("services/mail_poll_service.py", "backend/features/mail/mail_poll_service.py"),
    (
        "services/notification_service.py",
        "backend/features/notifications/notification_service.py",
    ),
    (
        "services/whatsapp_client.py",
        "backend/features/notifications/whatsapp_client.py",
    ),
    (
        "services/effective_settings.py",
        "backend/features/platform/effective_settings.py",
    ),
    (
        "services/data_wipe_service.py",
        "backend/features/platform/data_wipe_service.py",
    ),
    (
        "services/booking_relevance.py",
        "backend/ai/domain/booking/booking_relevance.py",
    ),
    ("schemas/booking/taxonomy.py", "backend/ai/domain/booking/taxonomy.py"),
    ("schemas/booking/triage.py", "backend/ai/domain/booking/triage.py"),
    ("schemas/booking/extraction.py", "backend/ai/domain/booking/extraction.py"),
    ("schemas/booking/__init__.py", "backend/ai/domain/booking/__init__.py"),
    (
        "adapters/mail_connector.py",
        "backend/infrastructure/adapters/mail/connector.py",
    ),
    (
        "adapters/mail_ingestion.py",
        "backend/infrastructure/adapters/mail/ingestion.py",
    ),
    ("adapters/mail_presets.py", "backend/features/mail/presets.py"),
    (
        "adapters/outlook_graph.py",
        "backend/infrastructure/adapters/outlook/graph.py",
    ),
    (
        "adapters/outlook_ingestion.py",
        "backend/infrastructure/adapters/outlook/ingestion.py",
    ),
]

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "from backend.infrastructure.adapters.mail.connector import",
        "from backend.infrastructure.adapters.mail.connector import",
    ),
    (
        "from backend.infrastructure.adapters.mail.ingestion import",
        "from backend.infrastructure.adapters.mail.ingestion import",
    ),
    (
        "from backend.features.mail.presets import",
        "from backend.features.mail.presets import",
    ),
    (
        "from backend.infrastructure.adapters.outlook.graph import",
        "from backend.infrastructure.adapters.outlook.graph import",
    ),
    (
        "from backend.infrastructure.adapters.outlook.ingestion import",
        "from backend.infrastructure.adapters.outlook.ingestion import",
    ),
    ("from backend.ai.domain.booking.", "from backend.ai.domain.booking."),
    (
        "from backend.ai.domain.booking.booking_relevance import",
        "from backend.ai.domain.booking.booking_relevance import",
    ),
    (
        "from backend.features.mail.mail_connection_service import",
        "from backend.features.mail.mail_connection_service import",
    ),
    (
        "from backend.features.mail.mail_poll_service import",
        "from backend.features.mail.mail_poll_service import",
    ),
    (
        "from backend.features.notifications.notification_service import",
        "from backend.features.notifications.notification_service import",
    ),
    (
        "from backend.features.notifications.whatsapp_client import",
        "from backend.features.notifications.whatsapp_client import",
    ),
    (
        "from backend.features.platform.effective_settings import",
        "from backend.features.platform.effective_settings import",
    ),
    (
        "from backend.features.platform.data_wipe_service import",
        "from backend.features.platform.data_wipe_service import",
    ),
    ("from backend.ai.services.", "from backend.ai.services."),
    (
        "from backend.infrastructure.repositories.",
        "from backend.infrastructure.repositories.",
    ),
    (
        "from backend.infrastructure.observability.",
        "from backend.infrastructure.observability.",
    ),
    ("from backend.ai.workflows.", "from backend.ai.workflows."),
    ("from backend.ai.prompts.", "from backend.ai.prompts."),
    ("from backend.application.", "from backend.application."),
    ("from backend.api.", "from backend.api."),
    ("from backend.core.config.", "from backend.core.config."),
    ("from backend.core.models.", "from backend.core.models."),
    ("from backend.core.utils.", "from backend.core.utils."),
    ("import backend.api.", "import backend.api."),
]

INIT_DIRS = [
    "backend",
    "backend/core",
    "backend/infrastructure",
    "backend/infrastructure/adapters",
    "backend/infrastructure/adapters/mail",
    "backend/infrastructure/adapters/outlook",
    "backend/ai",
    "backend/ai/services",
    "backend/ai/domain",
    "backend/ai/domain/booking",
    "backend/features",
    "backend/features/mail",
    "backend/features/notifications",
    "backend/features/platform",
    "backend/application",
]


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()


def run_git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        if dst.exists():
            return
        print(f"skip missing: {src}")
        return
    if dst.exists():
        _remove_path(dst)
    subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, check=True)


def ensure_inits() -> None:
    for rel in INIT_DIRS:
        init = ROOT / rel / "__init__.py"
        init.parent.mkdir(parents=True, exist_ok=True)
        if not init.exists():
            init.write_text('"""Package."""\n', encoding="utf-8")
    for pkg in [
        ROOT / "backend/infrastructure/adapters/mail/__init__.py",
        ROOT / "backend/infrastructure/adapters/outlook/__init__.py",
    ]:
        if not pkg.exists():
            pkg.write_text('"""Adapters."""\n', encoding="utf-8")
    root_init = ROOT / "backend/__init__.py"
    if not root_init.exists():
        root_init.write_text('"""Backend application package."""\n', encoding="utf-8")


def do_moves() -> None:
    ensure_inits()
    for src_rel, dst_rel in MOVES:
        run_git_mv(ROOT / src_rel, ROOT / dst_rel)


def rename_api_blueprints() -> None:
    api_dir = ROOT / "backend/api/api"
    blueprints = ROOT / "backend/api/blueprints"
    if not api_dir.is_dir():
        return
    blueprints.mkdir(parents=True, exist_ok=True)
    for path in list(api_dir.glob("*.py")):
        dst = blueprints / path.name
        if dst.exists():
            _remove_path(dst)
        subprocess.run(["git", "mv", str(path), str(dst)], cwd=ROOT, check=True)
    init = api_dir / "__init__.py"
    if init.exists():
        subprocess.run(
            ["git", "mv", str(init), str(blueprints / "__init__.py")],
            cwd=ROOT,
            check=True,
        )
    if api_dir.exists() and not any(api_dir.iterdir()):
        api_dir.rmdir()


def fix_blueprint_imports() -> None:
    init = ROOT / "backend/api/blueprints/__init__.py"
    if not init.exists():
        return
    text = init.read_text(encoding="utf-8")
    text = text.replace("from backend.api.api.", "from backend.api.blueprints.")
    text = text.replace("from backend.api.api.", "from backend.api.blueprints.")
    init.write_text(text, encoding="utf-8")
    app_py = ROOT / "backend/api/app.py"
    if app_py.exists():
        text = app_py.read_text(encoding="utf-8")
        text = text.replace(
            "from backend.api.api import", "from backend.api.blueprints import"
        )
        text = text.replace(
            "from backend.api.api import", "from backend.api.blueprints import"
        )
        app_py.write_text(text, encoding="utf-8")


def rewrite_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    original = text
    for old, new in IMPORT_REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def rewrite_imports() -> int:
    changed = 0
    skip = {
        ".venv",
        "node_modules",
        "__pycache__",
        ".git",
        "dist",
        "email_platform.egg-info",
    }
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".md", ".yml", ".yaml", ".toml", ".sh"}:
            continue
        if any(p in path.parts for p in skip):
            continue
        if rewrite_file(path):
            changed += 1
    return changed


def fix_settings_root() -> None:
    settings = ROOT / "backend/core/config/settings.py"
    if not settings.exists():
        return
    text = settings.read_text(encoding="utf-8")
    text = text.replace(
        "_PROJECT_ROOT = Path(__file__).resolve().parent.parent",
        "_PROJECT_ROOT = Path(__file__).resolve().parents[3]",
    )
    settings.write_text(text, encoding="utf-8")


def cleanup_empty_dirs() -> None:
    for name in [
        "services",
        "adapters",
        "schemas",
        "config",
        "models",
        "utils",
        "repositories",
        "observability",
        "workflows",
        "prompts",
        "routers",
        "web",
    ]:
        p = ROOT / name
        if p.exists() and p.is_dir() and not any(p.iterdir()):
            p.rmdir()


def main() -> int:
    if "--moves-only" in sys.argv:
        do_moves()
        rename_api_blueprints()
        return 0
    if "--imports-only" in sys.argv:
        n = rewrite_imports()
        print(f"rewrote {n} files")
        return 0
    do_moves()
    rename_api_blueprints()
    fix_blueprint_imports()
    n = rewrite_imports()
    fix_settings_root()
    cleanup_empty_dirs()
    print(f"done, rewrote {n} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
