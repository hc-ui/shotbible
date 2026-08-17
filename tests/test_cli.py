from __future__ import annotations

import json
from pathlib import Path

import pytest

from shotbible import __version__
from shotbible.cli import main
from shotbible.models import Bible
from shotbible.store import init_project, load, save

from conftest import BEAT, NAME, TITLE, write_dummy_png


def test_cli_init(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    dest = tmp_path / "short"
    assert main(["init", str(dest)]) == 0
    assert (dest / "bible.yaml").is_file()
    assert (dest / "refs").is_dir()
    assert (dest / "takes").is_dir()


def test_cli_add_character_scene_take_and_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    dest = tmp_path / "short"
    assert main(["init", str(dest)]) == 0
    monkeypatch.chdir(dest)

    png = write_dummy_png(dest / "face.png")
    assert (
        main(
            [
                "character",
                "add",
                "mei",
                "--name",
                NAME,
                "--look",
                "short black hair, navy hoodie, backpack",
                "--ref",
                str(png),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "scene",
                "add",
                "s01",
                "--title",
                "夜教室",
                "--setting",
                "empty university classroom at night, rows of desks",
                "--cast",
                "mei",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "take",
                "add",
                "s01",
                "--beat",
                BEAT,
            ]
        )
        == 0
    )

    capsys.readouterr()
    assert (
        main(
            [
                "prompt",
                "s01",
                "--beat",
                BEAT,
                "--character",
                "mei",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "navy hoodie" in out
    assert "classroom" in out.lower() or "desks" in out
    assert "sits" in out or "laptop" in out
    assert NAME in out or "mei" in out


def test_cli_prompt_all_writes_each_scene(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["prompt", "--all"]) == 0
    path = root / "takes" / "s01.prompt.txt"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert NAME in text
    assert "classroom" in text.lower() or "desks" in text


def test_cli_check_exit_codes(
    sample_project: tuple[Path, Bible], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, bible = sample_project
    monkeypatch.chdir(root)
    assert main(["check"]) == 0

    bible.scenes["s01"].cast.append("ghost")
    save(root, bible)
    assert main(["check"]) != 0


def test_cli_export_md_contains_title_and_name(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["export", "--format", "md"]) == 0
    out = capsys.readouterr().out
    text = out
    if TITLE not in text:
        md_files = list(root.glob("*.md"))
        assert md_files, "export --format md printed nothing and wrote no markdown file"
        text = md_files[0].read_text(encoding="utf-8")
    assert TITLE in text
    assert NAME in text


def test_cli_prompt_take_prints_text(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, bible = sample_project
    monkeypatch.chdir(root)
    take_id = bible.takes[0].id
    capsys.readouterr()
    assert main(["prompt-take", take_id]) == 0
    out = capsys.readouterr().out
    assert out.strip()
    assert "navy hoodie" in out
    assert "sits" in out or "laptop" in out or BEAT in out


def test_cli_list(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert NAME in out or "mei" in out
    assert "s01" in out or "夜教室" in out
    assert "t001" in out or "takes" in out
    # bible still loadable after list (read-only)
    _, loaded = load(root)
    assert loaded.title == TITLE


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_cli_set_and_remove(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["set", "--title", "新标题", "--aspect", "9:16"]) == 0
    _, loaded = load(root)
    assert loaded.title == "新标题"
    assert loaded.aspect == "9:16"

    assert main(["take", "rm", "t001"]) == 0
    assert main(["scene", "rm", "s01"]) == 0
    assert main(["character", "rm", "mei"]) == 0
    _, loaded = load(root)
    assert loaded.takes == []
    assert loaded.scenes == {}
    assert loaded.characters == {}
    capsys.readouterr()


def test_cli_rejects_zero_duration(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["take", "add", "s01", "--beat", "x", "--duration", "0"]) == 2


def test_cli_prompt_writes_default_file(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["prompt", "s01", "-o"]) == 0
    dest = root / "takes" / "s01.prompt.txt"
    assert dest.is_file()
    text = dest.read_text(encoding="utf-8")
    assert "阿梅" in text or "navy hoodie" in text


def test_cli_check_json_and_strict(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, bible = sample_project
    monkeypatch.chdir(root)
    bible.characters["mei"].refs = []
    save(root, bible)
    assert main(["check", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert any(item["code"] == "NO_REFS" for item in payload["issues"])
    assert main(["check", "--strict"]) == 1


def test_cli_list_json(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == TITLE
    assert payload["characters"][0]["id"] == "mei"


def test_cli_show_character(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["character", "show", "mei"]) == 0
    out = capsys.readouterr().out
    assert "阿梅" in out
    assert "navy hoodie" in out


def test_cli_take_file_is_copied(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    clip = root / "raw.mp4"
    clip.write_bytes(b"clip")
    assert main(["take", "add", "s01", "--beat", "another beat", "--file", str(clip)]) == 0
    _, loaded = load(root)
    last = loaded.takes[-1]
    assert last.file.startswith("takes/")
    assert (root / last.file).read_bytes() == b"clip"


def test_cli_rejects_path_like_ids(
    sample_project: tuple[Path, Bible],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _bible = sample_project
    monkeypatch.chdir(root)
    assert main(["character", "add", "../mei"]) == 2


def test_cli_explicit_project_missing_does_not_walk_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = init_project(tmp_path / "parent")
    empty = parent / "nested"
    empty.mkdir()
    monkeypatch.chdir(empty)
    assert main(["-C", str(empty), "list"]) == 2
