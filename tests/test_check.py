from __future__ import annotations

from pathlib import Path

import pytest

from shotbible.check import check_bible
from shotbible.models import Character, ParseError, Scene, Take, parse_duration
from shotbible.store import save

from conftest import SETTING, make_sample_bible, write_dummy_png


def _codes(issues: list[object]) -> set[str]:
    out: set[str] = set()
    for issue in issues:
        code = getattr(issue, "code", None)
        if code is None and isinstance(issue, dict):
            code = issue.get("code")
        if code is not None:
            out.add(str(code))
    return out


def _by_code(issues: list[object], code: str) -> object:
    for issue in issues:
        value = getattr(issue, "code", None)
        if value is None and isinstance(issue, dict):
            value = issue.get("code")
        if value == code:
            return issue
    raise AssertionError(f"{code} not in {_codes(issues)}")


def test_check_flags_unknown_character(tmp_path: Path) -> None:
    root = tmp_path / "unknown"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible()
    bible.scenes["s01"].cast.append("ghost")
    bible.takes.append(
        Take(
            id="t002",
            scene="s01",
            character="ghost",
            beat="someone who is not in the bible walks through",
        )
    )
    save(root, bible)

    issues = check_bible(root, bible)
    assert "UNKNOWN_CHARACTER" in _codes(issues)
    issue = _by_code(issues, "UNKNOWN_CHARACTER")
    message = getattr(issue, "message", None) or issue["message"]  # type: ignore[index]
    assert "ghost" in str(message)


def test_check_flags_missing_ref(tmp_path: Path) -> None:
    root = tmp_path / "missing-ref"
    root.mkdir()
    bible = make_sample_bible(with_ref=True)
    bible.characters["mei"].refs = ["refs/mei/front.png"]
    save(root, bible)
    assert not (root / "refs" / "mei" / "front.png").exists()

    issues = check_bible(root, bible)
    assert "MISSING_REF" in _codes(issues)
    issue = _by_code(issues, "MISSING_REF")
    message = getattr(issue, "message", None) or issue["message"]  # type: ignore[index]
    assert "front.png" in str(message)


def test_check_flags_scene_without_takes(tmp_path: Path) -> None:
    root = tmp_path / "no-takes"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible(with_take=True)
    bible.scenes["s02"] = Scene(
        id="s02",
        title="走廊",
        setting="long campus hallway after class",
        lighting="green-white tubes",
        camera="tracking side-on, 9:16",
        cast=["mei"],
    )
    save(root, bible)

    issues = check_bible(root, bible)
    assert "SCENE_WITHOUT_TAKES" in _codes(issues)
    issue = _by_code(issues, "SCENE_WITHOUT_TAKES")
    message = getattr(issue, "message", None) or issue["message"]  # type: ignore[index]
    assert "s02" in str(message)
    level = str(getattr(issue, "level", None) or issue["level"]).lower()  # type: ignore[index]
    assert level in {"warn", "warning"}


def test_check_flags_duplicate_setting(tmp_path: Path) -> None:
    root = tmp_path / "dup-set"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible(with_take=True)
    bible.scenes["s02"] = Scene(
        id="s02",
        title="同一教室",
        setting=SETTING,
        lighting="other light",
        camera="static",
        cast=["mei"],
    )
    save(root, bible)
    issues = check_bible(root, bible)
    assert "DUPLICATE_SETTING" in _codes(issues)


def test_check_clean_bible_skips_required_codes(tmp_path: Path) -> None:
    root = tmp_path / "clean"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible(with_ref=True, with_take=True)
    save(root, bible)

    codes = _codes(check_bible(root, bible))
    assert "UNKNOWN_CHARACTER" not in codes
    assert "MISSING_REF" not in codes
    assert "SCENE_WITHOUT_TAKES" not in codes


def test_non_lead_does_not_require_refs(tmp_path: Path) -> None:
    root = tmp_path / "extra"
    root.mkdir()
    bible = make_sample_bible(with_ref=True, with_take=True)
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible.characters["extra"] = Character(
        id="extra",
        name="路人",
        role="non-lead",
        look="blurred extra in the hallway",
    )
    save(root, bible)
    codes = _codes(check_bible(root, bible))
    assert "NO_REFS" not in codes
    assert "UNUSED_CHARACTER" in codes


def test_missing_take_file_is_error(tmp_path: Path) -> None:
    root = tmp_path / "clip"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible(with_ref=True, with_take=True)
    bible.takes[0].file = "takes/missing.mp4"
    save(root, bible)
    issues = check_bible(root, bible)
    assert "MISSING_TAKE_FILE" in _codes(issues)


def test_orphan_ref_is_warned(tmp_path: Path) -> None:
    root = tmp_path / "orphan"
    root.mkdir()
    write_dummy_png(root / "refs" / "mei" / "front.png")
    write_dummy_png(root / "refs" / "stray.png")
    bible = make_sample_bible(with_ref=True, with_take=True)
    save(root, bible)
    issues = check_bible(root, bible)
    assert "ORPHAN_REF" in _codes(issues)
    issue = _by_code(issues, "ORPHAN_REF")
    message = getattr(issue, "message", None) or issue["message"]  # type: ignore[index]
    assert "stray.png" in str(message)


def test_parse_duration_accepts_seconds_suffix() -> None:
    assert parse_duration("6s") == 6
    assert parse_duration(6) == 6
    assert parse_duration(6.0) == 6
    assert parse_duration(None) is None
    with pytest.raises(ParseError):
        parse_duration(0)
    with pytest.raises(ParseError):
        parse_duration(6.5)
    with pytest.raises(ParseError):
        parse_duration("nope")
