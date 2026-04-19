#!/usr/bin/env python3
"""tree.yaml 을 기준으로 docs/ 하위 폴더·README 의 자동 관리 구간을 생성·갱신한다.

- 신규 L0/L1 폴더 자동 생성
- 각 README 에 마커 구간(description/tree/posts) 보장
- description, tree 구간을 tree.yaml 기준으로 덮어쓰기
- posts 구간은 L1 폴더의 실제 포스트 파일 목록으로 갱신
- 이미 존재하는 README 의 마커 바깥 내용은 보존한다
- tree.yaml 에 없는 기존 폴더가 있으면 경고만 출력 (삭제하지 않음)
"""
from __future__ import annotations

import sys
from pathlib import Path

from _common import (
    DOCS_DIR,
    MARKER_BLOCKS,
    REPO_ROOT,
    RESERVED_FILES,
    category_dir,
    child_dir,
    ensure_markers,
    iter_categories,
    iter_children,
    iter_sub,
    load_tree,
    relative_url,
    replace_block,
)


ROOT_README_TEMPLATE = """# 학습 키워드 트리

<!-- description:start -->
학습 키워드를 계층적으로 정리한 루트 인덱스. 키워드 추가·수정은 `docs/tree.yaml` 을 편집한 뒤 `make scaffold` 로 동기화한다.
<!-- description:end -->

<!-- tree:start -->

<!-- tree:end -->
"""

L0_README_TEMPLATE = """# {name}

<!-- description:start -->
{description}
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->

<!-- tree:end -->
"""

L1_README_TEMPLATE = """# {name}

<!-- description:start -->
{description}
<!-- description:end -->

## 하위 키워드

<!-- tree:start -->

<!-- tree:end -->

## 포스트

<!-- posts:start -->

<!-- posts:end -->
"""


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_if_changed(path: Path, content: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def build_root_tree_block(tree) -> str:
    lines = []
    for cat in iter_categories(tree):
        cat_link = relative_url([cat["name"], "README.md"])
        lines.append(f"- [{cat['name']}](./{cat_link}) — {cat['description']}")
        for l1 in iter_children(cat):
            l1_link = relative_url([cat["name"], l1["name"], "README.md"])
            lines.append(f"  - [{l1['name']}](./{l1_link}) — {l1['description']}")
    return "\n".join(lines) if lines else "(비어 있음)"


def build_l0_tree_block(cat) -> str:
    lines = []
    for l1 in iter_children(cat):
        l1_link = relative_url([l1["name"], "README.md"])
        lines.append(f"- [{l1['name']}](./{l1_link}) — {l1['description']}")
        for l2 in iter_sub(l1):
            lines.append(f"  - {l2}")
    return "\n".join(lines) if lines else "(비어 있음)"


def build_l1_tree_block(l1) -> str:
    subs = iter_sub(l1)
    if not subs:
        return "(하위 키워드 없음)"
    return "\n".join(f"- {s}" for s in subs)


def build_posts_block(l1_dir: Path) -> str:
    posts = sorted(
        p for p in l1_dir.glob("*.md")
        if p.name not in RESERVED_FILES
    )
    if not posts:
        return "(없음)"
    lines = []
    for p in posts:
        lines.append(f"- [{p.stem}](./{relative_url([p.name])})")
    return "\n".join(lines)


def update_readme(
    path: Path,
    template: str,
    *,
    description: str,
    tree_block: str,
    posts_block: str | None = None,
    template_vars: dict | None = None,
) -> bool:
    if not path.exists():
        content = template.format(**(template_vars or {}))
        path.write_text(content, encoding="utf-8")
    content = path.read_text(encoding="utf-8")
    kinds = ["description", "tree"]
    if posts_block is not None:
        kinds.append("posts")
    content = ensure_markers(content, kinds)
    content = replace_block(content, "description", description)
    content = replace_block(content, "tree", tree_block)
    if posts_block is not None:
        content = replace_block(content, "posts", posts_block)
    return write_if_changed(path, content)


def detect_orphan_folders(tree) -> list[Path]:
    declared_cats = {cat["name"] for cat in iter_categories(tree)}
    declared_l1 = {
        (cat["name"], l1["name"])
        for cat in iter_categories(tree)
        for l1 in iter_children(cat)
    }
    orphans: list[Path] = []
    for entry in DOCS_DIR.iterdir():
        if not entry.is_dir():
            continue
        if entry.name not in declared_cats:
            orphans.append(entry)
            continue
        for sub in entry.iterdir():
            if sub.is_dir() and (entry.name, sub.name) not in declared_l1:
                orphans.append(sub)
    return orphans


def main() -> int:
    tree = load_tree()
    changed_files: list[Path] = []

    # 루트 README
    root_readme = DOCS_DIR / "README.md"
    if update_readme(
        root_readme,
        ROOT_README_TEMPLATE,
        description="학습 키워드를 계층적으로 정리한 루트 인덱스. 키워드 추가·수정은 `docs/tree.yaml` 을 편집한 뒤 `make scaffold` 로 동기화한다.",
        tree_block=build_root_tree_block(tree),
    ):
        changed_files.append(root_readme)

    # L0/L1
    for cat in iter_categories(tree):
        cat_dir = category_dir(cat)
        ensure_dir(cat_dir)
        l0_readme = cat_dir / "README.md"
        if update_readme(
            l0_readme,
            L0_README_TEMPLATE,
            description=cat["description"],
            tree_block=build_l0_tree_block(cat),
            template_vars={"name": cat["name"], "description": cat["description"]},
        ):
            changed_files.append(l0_readme)

        for l1 in iter_children(cat):
            l1_dir = child_dir(cat, l1)
            ensure_dir(l1_dir)
            l1_readme = l1_dir / "README.md"
            if update_readme(
                l1_readme,
                L1_README_TEMPLATE,
                description=l1["description"],
                tree_block=build_l1_tree_block(l1),
                posts_block=build_posts_block(l1_dir),
                template_vars={"name": l1["name"], "description": l1["description"]},
            ):
                changed_files.append(l1_readme)

    # 고아 폴더 경고
    orphans = detect_orphan_folders(tree)
    for p in orphans:
        rel = p.relative_to(REPO_ROOT)
        print(f"[warn] tree.yaml 에 없는 폴더: {rel} (수동 확인 필요)", file=sys.stderr)

    if changed_files:
        print(f"[scaffold] 갱신된 파일 {len(changed_files)}개")
        for p in changed_files:
            print(f"  - {p.relative_to(REPO_ROOT)}")
    else:
        print("[scaffold] 변경 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
