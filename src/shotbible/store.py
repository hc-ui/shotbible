from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from .models import Bible, Character, Scene, Take

BIBLE_NAME = "bible.yaml"


class StoreError(RuntimeError):
    pass


def project_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / BIBLE_NAME).is_file():
            return candidate
    raise StoreError(f"no {BIBLE_NAME} found from {cur}")


def load(root: Path | None = None) -> tuple[Path, Bible]:
    root = project_root(root) if root is None or not (root / BIBLE_NAME).is_file() else root.resolve()
    path = root / BIBLE_NAME
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise StoreError(f"{path} is not a YAML mapping")
    return root, Bible.from_dict(raw)


def save(root: Path, bible: Bible) -> None:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "refs").mkdir(exist_ok=True)
    (root / "takes").mkdir(exist_ok=True)
    text = yaml.safe_dump(
        bible.to_dict(),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    tmp = root / f".{BIBLE_NAME}.tmp"
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(root / BIBLE_NAME)


def init_project(dest: Path, title: str = "untitled", aspect: str = "16:9") -> Path:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    bible_path = dest / BIBLE_NAME
    if bible_path.exists():
        raise StoreError(f"already a shotbible project: {bible_path}")
    bible = Bible(title=title, aspect=aspect)
    save(dest, bible)
    return dest


def copy_ref(root: Path, src: Path, bucket: str) -> str:
    src = src.expanduser().resolve()
    if not src.is_file():
        raise StoreError(f"reference file not found: {src}")
    dest_dir = root / "refs" / _safe_id(bucket)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.resolve() != src:
        shutil.copy2(src, dest)
    rel = dest.relative_to(root).as_posix()
    return rel


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip())
    cleaned = cleaned.strip("-_") or "item"
    return cleaned


def upsert_character(bible: Bible, character: Character) -> None:
    bible.characters[character.id] = character


def upsert_scene(bible: Bible, scene: Scene) -> None:
    bible.scenes[scene.id] = scene


def add_take(bible: Bible, take: Take) -> Take:
    if not take.id:
        take.id = bible.next_take_id()
    bible.takes.append(take)
    return take


def require_character(bible: Bible, cid: str) -> Character:
    try:
        return bible.characters[cid]
    except KeyError as exc:
        raise StoreError(f"unknown character: {cid}") from exc


def require_scene(bible: Bible, sid: str) -> Scene:
    try:
        return bible.scenes[sid]
    except KeyError as exc:
        raise StoreError(f"unknown scene: {sid}") from exc


def as_plain(bible: Bible) -> dict[str, Any]:
    return bible.to_dict()
