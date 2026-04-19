"""공용 유틸: tree.yaml 로딩, 경로 계산, 슬러그 생성, README 마커 처리."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write(
        "[ERROR] PyYAML 이 필요합니다. `pip install --break-system-packages pyyaml` 또는 "
        "`python3 -m pip install pyyaml` 으로 설치하세요.\n"
    )
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
POST_DIR = REPO_ROOT / "post"
TREE_YAML = DOCS_DIR / "tree.yaml"

MARKER_BLOCKS = {
    "description": ("<!-- description:start -->", "<!-- description:end -->"),
    "tree": ("<!-- tree:start -->", "<!-- tree:end -->"),
    "posts": ("<!-- posts:start -->", "<!-- posts:end -->"),
}

RESERVED_FILES = {"README.md", "CONTRIBUTING.md", "tree.yaml"}


def load_tree() -> Dict[str, Any]:
    if not TREE_YAML.exists():
        sys.stderr.write(f"[ERROR] {TREE_YAML} 가 존재하지 않습니다.\n")
        sys.exit(2)
    with TREE_YAML.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "categories" not in data or not isinstance(data["categories"], list):
        sys.stderr.write("[ERROR] tree.yaml 에 'categories' 리스트가 없습니다.\n")
        sys.exit(2)
    return data


def iter_categories(tree: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    return tree.get("categories", [])


def iter_children(cat: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    return cat.get("children") or []


def iter_sub(l1: Dict[str, Any]) -> List[str]:
    return list(l1.get("sub") or [])


def keyword_slug(name: str, override: Optional[str] = None) -> str:
    """L1 키워드명에서 포스트 파일명용 슬러그 생성. 한글 유지, 공백은 하이픈, 특수문자 제거."""
    if override:
        return override.strip()
    s = name.strip()
    # 영문자는 소문자화
    s = "".join(ch.lower() if ch.isascii() and ch.isalpha() else ch for ch in s)
    # 공백을 하이픈으로
    s = re.sub(r"\s+", "-", s)
    # 한글·영문·숫자·하이픈만 남기고 제거
    s = re.sub(r"[^0-9a-z\-\uAC00-\uD7A3\u3131-\u318E]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def url_encode_path_segment(seg: str) -> str:
    """마크다운 링크용 URL 인코딩 (공백→%20 등)."""
    from urllib.parse import quote
    return quote(seg, safe="")


def relative_url(parts: List[str]) -> str:
    return "/".join(url_encode_path_segment(p) for p in parts)


# ---- README 마커 처리 ----

def extract_block(content: str, kind: str) -> Optional[str]:
    start, end = MARKER_BLOCKS[kind]
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end), content, re.DOTALL)
    if not m:
        return None
    return m.group(1)


def replace_block(content: str, kind: str, new_inner: str) -> str:
    start, end = MARKER_BLOCKS[kind]
    pattern = re.escape(start) + r".*?" + re.escape(end)
    replacement = f"{start}\n{new_inner.strip()}\n{end}"
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    # 마커가 없으면 뒤에 덧붙임
    return content.rstrip() + "\n\n" + replacement + "\n"


def ensure_markers(content: str, kinds: List[str]) -> str:
    """주어진 마커 블록들이 없으면 추가."""
    for kind in kinds:
        start, end = MARKER_BLOCKS[kind]
        if start not in content:
            content = content.rstrip() + f"\n\n{start}\n\n{end}\n"
    return content


# ---- 경로 ----

def category_dir(cat: Dict[str, Any]) -> Path:
    return DOCS_DIR / cat["name"]


def child_dir(cat: Dict[str, Any], l1: Dict[str, Any]) -> Path:
    return category_dir(cat) / l1["name"]
