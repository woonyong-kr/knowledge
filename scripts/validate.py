#!/usr/bin/env python3
"""tree.yaml 과 docs/ 실제 구조의 정합성을 검사한다.

검사 항목:
- tree.yaml 에 정의된 L0/L1 폴더가 실제 존재하는가
- docs/ 의 폴더가 모두 tree.yaml 에 정의되어 있는가
- 각 폴더에 README.md 가 있는가
- README 에 필요한 마커 구간이 모두 존재하는가
- 포스트 파일명이 {l0_slug}-... 규칙을 따르는가
- 포스트 프론트매터의 keyword/category 가 실제 위치와 일치하는가
- L0 slug 는 예약 표에 정의된 값만 사용하는가 (tree.yaml 과 일치)

실패 시 종료 코드 1.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import (
    DOCS_DIR,
    MARKER_BLOCKS,
    REPO_ROOT,
    RESERVED_FILES,
    category_dir,
    child_dir,
    iter_categories,
    iter_children,
    load_tree,
)


ALLOWED_L0_SLUGS = {
    "CS 기초": "cs",
    "Algorithm 및 Data Structures": "algo",
    "Malloc lab": "malloc",
    "네트워크": "net",
    "OS": "os",
    "Pintos": "pintos",
    "AI": "ai",
    "DB": "db",
    "프로젝트 공통 지식": "proj",
}


def parse_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip()
    result: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def check_markers(readme: Path, required: list[str], errors: list[str]) -> None:
    content = readme.read_text(encoding="utf-8")
    for kind in required:
        start, end = MARKER_BLOCKS[kind]
        if content.count(start) != 1 or content.count(end) != 1:
            errors.append(f"[marker] {readme.relative_to(REPO_ROOT)}: '{kind}' 마커 누락 또는 중복")


def main() -> int:
    tree = load_tree()
    errors: list[str] = []

    # L0 slug 검사
    declared_slugs = {cat["name"]: cat.get("slug") for cat in iter_categories(tree)}
    for name, slug in declared_slugs.items():
        expected = ALLOWED_L0_SLUGS.get(name)
        if expected is None:
            errors.append(f"[slug] 알 수 없는 L0 '{name}'. ALLOWED_L0_SLUGS 에 추가 필요.")
        elif slug != expected:
            errors.append(f"[slug] L0 '{name}' 의 slug '{slug}' 가 예약값 '{expected}' 와 다름")

    # tree.yaml 정의된 폴더 존재 검사 + README 검사
    declared_pairs = set()
    for cat in iter_categories(tree):
        cat_dir = category_dir(cat)
        declared_pairs.add((cat["name"], None))
        if not cat_dir.is_dir():
            errors.append(f"[missing] L0 폴더 없음: {cat_dir.relative_to(REPO_ROOT)}")
            continue
        l0_readme = cat_dir / "README.md"
        if not l0_readme.exists():
            errors.append(f"[missing] L0 README 없음: {l0_readme.relative_to(REPO_ROOT)}")
        else:
            check_markers(l0_readme, ["description", "tree"], errors)

        for l1 in iter_children(cat):
            declared_pairs.add((cat["name"], l1["name"]))
            l1_dir = child_dir(cat, l1)
            if not l1_dir.is_dir():
                errors.append(f"[missing] L1 폴더 없음: {l1_dir.relative_to(REPO_ROOT)}")
                continue
            l1_readme = l1_dir / "README.md"
            if not l1_readme.exists():
                errors.append(f"[missing] L1 README 없음: {l1_readme.relative_to(REPO_ROOT)}")
            else:
                check_markers(l1_readme, ["description", "tree", "posts"], errors)

            # 포스트 검사
            for p in l1_dir.glob("*.md"):
                if p.name in RESERVED_FILES:
                    continue
                slug = ALLOWED_L0_SLUGS[cat["name"]]
                prefix = f"{slug}-"
                if not p.stem.startswith(prefix):
                    errors.append(
                        f"[filename] 포스트 '{p.relative_to(REPO_ROOT)}' 는 '{prefix}' 로 시작해야 함"
                    )
                text = p.read_text(encoding="utf-8")
                fm = parse_frontmatter(text)
                if fm is None:
                    errors.append(f"[frontmatter] 없음: {p.relative_to(REPO_ROOT)}")
                else:
                    if fm.get("category") != cat["name"]:
                        errors.append(
                            f"[frontmatter] {p.relative_to(REPO_ROOT)}: category '{fm.get('category')}' ≠ '{cat['name']}'"
                        )
                    if fm.get("keyword") != l1["name"]:
                        errors.append(
                            f"[frontmatter] {p.relative_to(REPO_ROOT)}: keyword '{fm.get('keyword')}' ≠ '{l1['name']}'"
                        )

    # 고아 폴더 검사
    for entry in DOCS_DIR.iterdir():
        if not entry.is_dir():
            continue
        if (entry.name, None) not in declared_pairs:
            errors.append(f"[orphan] tree.yaml 에 없는 L0 폴더: {entry.relative_to(REPO_ROOT)}")
            continue
        for sub in entry.iterdir():
            if not sub.is_dir():
                continue
            if (entry.name, sub.name) not in declared_pairs:
                errors.append(
                    f"[orphan] tree.yaml 에 없는 L1 폴더: {sub.relative_to(REPO_ROOT)}"
                )

    if errors:
        print("[validate] FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[validate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
