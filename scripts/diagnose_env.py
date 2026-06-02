"""Zeigt, welche .env geladen wird (ohne Secrets auszugeben)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import _ENV_FILE, get_settings  # noqa: E402


def main() -> int:
    cwd = Path.cwd()
    env_cwd = cwd / ".env"
    print(f"Terminal-Verzeichnis (cwd): {cwd}")
    cwd_env = env_cwd.resolve() if env_cwd.is_file() else "(fehlt)"
    print(f".env im cwd:               {cwd_env}")
    proj_env = _ENV_FILE.resolve() if _ENV_FILE.is_file() else "(fehlt)"
    print(f".env vom Projekt (genutzt): {proj_env}")
    if env_cwd.is_file() and env_cwd.resolve() != _ENV_FILE.resolve():
        print("WARNUNG: cwd-.env und Projekt-.env sind unterschiedliche Dateien!")

    shell_llm = os.environ.get("LLM_MODE")
    if shell_llm:
        print(
            f"Shell ueberschreibt .env: LLM_MODE={shell_llm!r} (hat Vorrang vor Datei)"
        )

    try:
        s = get_settings()
    except Exception as exc:
        print(f"Settings-Fehler: {exc}")
        return 1

    print("\nGeladene Werte (keine Secrets):")
    print(f"  LLM_MODE={s.llm_mode}")
    print(f"  OPENAI_MODEL_CLASSIFY={s.openai_model_classify}")
    print(f"  OPENAI_MODEL_EXTRACT={s.openai_model_extract}")
    print(f"  OPENAI_MODEL_DRAFT={s.openai_model_draft}")
    print(f"  EMBEDDING_MODEL={s.embedding_model}")
    print(f"  APP_ENV={s.app_env}")
    lf_ok = bool(s.langfuse_public_key and s.langfuse_secret_key)
    print(f"  LANGFUSE_KEYS gesetzt: {lf_ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
