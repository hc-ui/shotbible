from __future__ import annotations

from pathlib import Path

from shotbible.check import check_bible
from shotbible.models import Scene, Take
from shotbible.store import save

from conftest import make_sample_bible, write_dummy_png


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
