"""Restructure frontend/src into features/, lib/, shared/, app/."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"

FILE_MOVES: list[tuple[str, str]] = [
    ("main.tsx", "app/main.tsx"),
    ("App.tsx", "app/App.tsx"),
    ("pages/LoginPage.tsx", "features/auth/LoginPage.tsx"),
    ("pages/RegisterPage.tsx", "features/auth/RegisterPage.tsx"),
    ("pages/OnboardingPage.tsx", "features/onboarding/OnboardingPage.tsx"),
    ("pages/SettingsPage.tsx", "features/settings/SettingsPage.tsx"),
    ("pages/AdminApprovalsPage.tsx", "features/admin/AdminApprovalsPage.tsx"),
    ("pages/ReviewQueuePage.tsx", "features/review/ReviewQueuePage.tsx"),
    ("pages/PropertiesPage.tsx", "features/properties/PropertiesPage.tsx"),
    ("pages/DashboardPage.tsx", "features/dashboard/DashboardPage.tsx"),
    ("pages/CostsPage.tsx", "features/dashboard/CostsPage.tsx"),
    ("pages/EmailListPage.tsx", "features/emails/EmailListPage.tsx"),
    ("pages/BookingsPage.tsx", "features/emails/BookingsPage.tsx"),
    ("pages/CancellationsPage.tsx", "features/emails/CancellationsPage.tsx"),
    ("pages/ChangesPage.tsx", "features/emails/ChangesPage.tsx"),
    ("pages/MessagesPage.tsx", "features/emails/MessagesPage.tsx"),
    ("stores/authStore.ts", "features/auth/authStore.ts"),
    ("stores/authStore.test.ts", "features/auth/authStore.test.ts"),
]

DIR_MOVES: list[tuple[str, str]] = [
    ("api", "lib/api"),
    ("types", "lib/types"),
    ("components/ui", "shared/ui"),
    ("components/shared", "shared/components"),
    ("components/layout", "shared/layout"),
]

IMPORT_REPLACEMENTS: list[tuple[str, str]] = [
    ('from "@/api/', 'from "@/lib/api/'),
    ('from "@/types/', 'from "@/lib/types/'),
    ('from "@/pages/', 'from "@/features/'),
    ('from "@/stores/authStore', 'from "@/features/auth/authStore'),
    ('from "@/components/ui/', 'from "@/shared/ui/'),
    ('from "@/components/shared/', 'from "@/shared/components/'),
    ('from "@/components/layout/', 'from "@/shared/layout/'),
]

FEATURE_PATHS: list[tuple[str, str]] = [
    ("@/features/LoginPage", "@/features/auth/LoginPage"),
    ("@/features/RegisterPage", "@/features/auth/RegisterPage"),
    ("@/features/OnboardingPage", "@/features/onboarding/OnboardingPage"),
    ("@/features/SettingsPage", "@/features/settings/SettingsPage"),
    ("@/features/AdminApprovalsPage", "@/features/admin/AdminApprovalsPage"),
    ("@/features/ReviewQueuePage", "@/features/review/ReviewQueuePage"),
    ("@/features/PropertiesPage", "@/features/properties/PropertiesPage"),
    ("@/features/DashboardPage", "@/features/dashboard/DashboardPage"),
    ("@/features/CostsPage", "@/features/dashboard/CostsPage"),
    ("@/features/EmailListPage", "@/features/emails/EmailListPage"),
    ("@/features/BookingsPage", "@/features/emails/BookingsPage"),
    ("@/features/CancellationsPage", "@/features/emails/CancellationsPage"),
    ("@/features/ChangesPage", "@/features/emails/ChangesPage"),
    ("@/features/MessagesPage", "@/features/emails/MessagesPage"),
]


def git_mv(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, check=True)


def move_dir_contents(src_rel: str, dst_rel: str) -> None:
    src = SRC / src_rel
    dst = SRC / dst_rel
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in list(src.iterdir()):
        git_mv(item, dst / item.name)
    if src.exists() and not any(src.iterdir()):
        src.rmdir()


def rewrite_imports() -> None:
    for path in SRC.rglob("*"):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in IMPORT_REPLACEMENTS:
            text = text.replace(old, new)
        for old, new in FEATURE_PATHS:
            text = text.replace(old, new)
        if path.name == "main.tsx":
            text = text.replace('from "./App"', 'from "@/app/App"')
        if text != original:
            path.write_text(text, encoding="utf-8")


def update_index_html() -> None:
    index_html = ROOT / "frontend" / "index.html"
    if index_html.exists():
        text = index_html.read_text(encoding="utf-8")
        if 'src="/src/main.tsx"' in text:
            index_html.write_text(
                text.replace('src="/src/main.tsx"', 'src="/src/app/main.tsx"'),
                encoding="utf-8",
            )


def main() -> int:
    for src_rel, dst_rel in FILE_MOVES:
        git_mv(SRC / src_rel, SRC / dst_rel)
    for src_rel, dst_rel in DIR_MOVES:
        move_dir_contents(src_rel, dst_rel)
    rewrite_imports()
    update_index_html()
    print("frontend restructure done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
