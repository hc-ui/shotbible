from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from .models import Bible, Character, ParseError, Scene, Take

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
    if root is None:
        root = project_root()
    else:
        root = Path(root).expanduser().resolve()
        if root.is_file():
            if root.name != BIBLE_NAME:
                raise StoreError(f"not a {BIBLE_NAME}: {root}")
            root = root.parent
        elif not (root / BIBLE_NAME).is_file():
            raise StoreError(f"no {BIBLE_NAME} in {root}")
    path = root / BIBLE_NAME
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise StoreError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise StoreError(f"{path} is not a YAML mapping")
    try:
        return root, Bible.from_dict(raw)
    except ParseError as exc:
        raise StoreError(f"{path}: {exc}") from exc


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


def init_project(dest: Path, title: str = "untitled", aspect: str = "9:16") -> Path:
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    bible_path = dest / BIBLE_NAME
    if bible_path.exists():
        raise StoreError(f"already a shotbible project: {bible_path}")
    bible = Bible(title=title, aspect=aspect)
    save(dest, bible)
    ignore = dest / ".gitignore"
    if not ignore.exists():
        ignore.write_text(
            "\n".join(
                [
                    "takes/",
                    "*.mp4",
                    "*.mov",
                    "*.webm",
                    ".bible.yaml.tmp",
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
    return dest


def copy_ref(root: Path, src: Path, bucket: str) -> str:
    return copy_asset(root, src, "refs", bucket)


def copy_take_file(root: Path, src: Path, take_id: str) -> str:
    return copy_asset(root, src, "takes", take_id)


def copy_asset(root: Path, src: Path, kind: str, bucket: str) -> str:
    src = src.expanduser().resolve()
    if not src.is_file():
        raise StoreError(f"file not found: {src}")
    dest_dir = root / kind / _safe_id(bucket)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, src.name, src)
    if dest.resolve() != src:
        shutil.copy2(src, dest)
    return dest.relative_to(root).as_posix()


def _safe_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip())
    cleaned = cleaned.strip("-") or "item"
    return cleaned


def _unique_dest(dest_dir: Path, name: str, src: Path) -> Path:
    dest = dest_dir / name
    if not dest.exists() or dest.resolve() == src:
        return dest
    stem = dest.stem
    suffix = dest.suffix
    n = 2
    while True:
        candidate = dest_dir / f"{stem}-{n}{suffix}"
        if not candidate.exists() or candidate.resolve() == src:
            return candidate
        n += 1


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


def remove_character(bible: Bible, cid: str) -> None:
    require_character(bible, cid)
    used_in = [sid for sid, scene in bible.scenes.items() if cid in scene.cast]
    used_in += [take.id for take in bible.takes if take.character == cid]
    if used_in:
        raise StoreError(f"character '{cid}' is still used by: {', '.join(used_in)}")
    del bible.characters[cid]


def remove_scene(bible: Bible, sid: str) -> None:
    require_scene(bible, sid)
    blocking = [take.id for take in bible.takes if take.scene == sid]
    if blocking:
        raise StoreError(f"scene '{sid}' still has takes: {', '.join(blocking)}")
    del bible.scenes[sid]


def remove_take(bible: Bible, tid: str) -> Take:
    for index, take in enumerate(bible.takes):
        if take.id == tid:
            return bible.takes.pop(index)
    raise StoreError(f"unknown take: {tid}")
