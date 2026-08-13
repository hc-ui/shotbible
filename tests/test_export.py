from __future__ import annotations

import json
from pathlib import Path

from shotbible.export import export_json, export_markdown
from shotbible.models import Bible

from conftest import NAME, TITLE


def _as_text(result: object, dest: Path | None = None) -> str:
    if isinstance(result, str):
        return result
    if dest is not None and dest.is_file():
        return dest.read_text(encoding="utf-8")
    if isinstance(result, Path) and result.is_file():
        return result.read_text(encoding="utf-8")
    return str(result)


def test_export_markdown_contains_title_and_character_name(
    sample_project: tuple[Path, Bible],
) -> None:
    _root, bible = sample_project
    md = _as_text(export_markdown(bible))
    assert TITLE in md
    assert NAME in md


def test_export_json_contains_title_and_character_name(
    sample_project: tuple[Path, Bible],
) -> None:
    _root, bible = sample_project
    raw = _as_text(export_json(bible))
    data = json.loads(raw)
    assert data["title"] == TITLE
    characters = data["characters"]
    if isinstance(characters, dict):
        mei = characters["mei"]
        name = mei["name"] if isinstance(mei, dict) else mei
    else:
        name = next(c["name"] for c in characters if c.get("id") == "mei" or c.get("name") == NAME)
    assert name == NAME
