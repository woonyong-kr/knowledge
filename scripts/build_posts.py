#!/usr/bin/env python3
"""docs/ 하위의 포스트 파일을 post/ 로 평탄화 미러 빌드한다.

동작:
1. 레포 루트의 post/ 디렉터리 전체 삭제 (원본 삭제 미러 효과).
2. post/ 재생성.
3. docs/**/*.md 중 README.md·CONTRIBUTING.md 를 제외한 파일을 스캔.
4. 각 파일의 git 최초 add 커밋일(YYYY-MM-DD) 을 얻어 파일명 prefix 로 사용.
   - git 이력 없으면 오늘 날짜 사용 + 경고.
5. post/{YYYY-MM-DD}-{원본파일명}.md 로 복사. 중복 시 -2, -3 접미사 부여.
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

from _common import DOCS_DIR, POST_DIR, REPO_ROOT, RESERVED_FILES


def git_first_date(path: Path) -> str | None:
    try:
        out = subprocess.run(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--follow",
                "--format=%ad",
                "--date=short",
                "-1",
                "--",
                str(path.relative_to(REPO_ROOT)),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode != 0:
            return None
        line = out.stdout.strip()
        return line or None
    except FileNotFoundError:
        return None


def uniquify(target_dir: Path, base: str) -> Path:
    candidate = target_dir / f"{base}.md"
    if not candidate.exists():
        return candidate
    i = 2
    while True:
        candidate = target_dir / f"{base}-{i}.md"
        if not candidate.exists():
            return candidate
        i += 1


def main() -> int:
    if POST_DIR.exists():
        shutil.rmtree(POST_DIR)
    POST_DIR.mkdir(parents=True, exist_ok=True)

    today = dt.date.today().isoformat()
    copied = 0
    warned_nogit = 0

    for src in sorted(DOCS_DIR.rglob("*.md")):
        if src.name in RESERVED_FILES:
            continue
        if src.is_symlink():
            continue
        date = git_first_date(src)
        if date is None:
            warned_nogit += 1
            print(
                f"[warn] git 이력 없음: {src.relative_to(REPO_ROOT)} — 오늘 날짜({today}) 사용",
                file=sys.stderr,
            )
            date = today
        base = f"{date}-{src.stem}"
        target = uniquify(POST_DIR, base)
        shutil.copy2(src, target)
        copied += 1

    print(f"[build] post/ 재생성 완료 — {copied}개 포스트")
    if warned_nogit:
        print(f"[build] 경고: git 이력 없는 파일 {warned_nogit}개 (오늘 날짜로 prefix)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
