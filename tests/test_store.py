from __future__ import annotations

from pathlib import Path

import pytest

from shotbible.models import Character, Scene, Take
from shotbible.store import (
    StoreError,
    add_take,
    copy_ref,
    copy_take_file,
    init_project,
    load,
    save,
    upsert_character,
    upsert_scene,
)

from conftest import NAME, TITLE, write_dummy_png

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "campus-night"


def test_init_creates_layout_and_bible(tmp_path: Path) -> None:
    root = init_project(tmp_path / "film", title=TITLE, aspect="9:16")
    assert (root / "bible.yaml").is_file()
    assert (root / "refs").is_dir()
    assert (root / "takes").is_dir()
    assert (root / ".gitignore").is_file()
    loaded_root, bible = load(root)
    assert loaded_root == root.resolve()
    assert bible.title == TITLE
    assert bible.aspect == "9:16"


def test_save_load_roundtrip_chinese(tmp_path: Path) -> None:
    root = init_project(tmp_path / "zh", title="夜校最后一课", aspect="9:16")
    _, bible = load(root)
    bible.style = "电影感，夜教室，冷荧光，中国校园"
    bible.duration_hint = "75秒"
    upsert_character(
        bible,
        Character(
            id="mei",
            name=NAME,
            role="女主",
            look="二十多岁中国女生，短发，藏青连帽衫，双肩包",
            voice="平静的普通话，几乎在耳边说",
            do_not=["不要改发型", "不要加眼镜"],
            refs=["refs/mei/front.png"],
        ),
    )
    upsert_scene(
        bible,
        Scene(
            id="s01",
            title="夜教室",
            setting="深夜空教室，成排课桌，一台开着的笔记本",
            lighting="冷白日光灯，窗外城市余光",
            camera="慢推，35mm，9:16",
            cast=["mei"],
        ),
    )
    add_take(
        bible,
        Take(
            id="t001",
            scene="s01",
            character="mei",
            beat="她坐下，打开电脑，不看镜头",
            notes="锁住连帽衫和短发",
        ),
    )
    save(root, bible)

    raw = (root / "bible.yaml").read_text(encoding="utf-8")
    assert NAME in raw
    assert "夜教室" in raw
    assert "藏青连帽衫" in raw
    assert "\\u" not in raw

    _, loaded = load(root)
    assert loaded.title == "夜校最后一课"
    assert loaded.characters["mei"].name == NAME
    assert "藏青连帽衫" in loaded.characters["mei"].look
    assert loaded.scenes["s01"].title == "夜教室"
    assert loaded.takes[0].beat == "她坐下，打开电脑，不看镜头"
    assert loaded.characters["mei"].do_not == ["不要改发型", "不要加眼镜"]


def test_init_existing_raises(tmp_path: Path) -> None:
    dest = tmp_path / "dup"
    init_project(dest, title=TITLE)
    with pytest.raises(StoreError):
        init_project(dest, title=TITLE)


def test_load_non_mapping_raises(tmp_path: Path) -> None:
    root = tmp_path / "bad"
    root.mkdir()
    (root / "bible.yaml").write_text("- not-a-mapping\n", encoding="utf-8")
    with pytest.raises(StoreError):
        load(root)


def test_copy_ref_writes_under_refs(tmp_path: Path) -> None:
    root = init_project(tmp_path / "refs-proj")
    src = write_dummy_png(tmp_path / "face.png")
    rel = copy_ref(root, src, "mei")
    assert rel == "refs/mei/face.png"
    assert (root / rel).is_file()
    assert (root / rel).read_bytes().startswith(b"\x89PNG")


def test_copy_ref_does_not_overwrite_same_name(tmp_path: Path) -> None:
    root = init_project(tmp_path / "collide")
    first = write_dummy_png(tmp_path / "a" / "face.png")
    first.write_bytes(b"\x89PNG\r\n\x1a\none")
    second = write_dummy_png(tmp_path / "b" / "face.png")
    second.write_bytes(b"\x89PNG\r\n\x1a\ntwo")
    rel1 = copy_ref(root, first, "mei")
    rel2 = copy_ref(root, second, "mei")
    assert rel1 == "refs/mei/face.png"
    assert rel2 == "refs/mei/face-2.png"
    assert (root / rel1).read_bytes().endswith(b"one")
    assert (root / rel2).read_bytes().endswith(b"two")


def test_copy_take_file_lands_under_takes(tmp_path: Path) -> None:
    root = init_project(tmp_path / "clips")
    src = tmp_path / "out.mp4"
    src.write_bytes(b"fake-mp4")
    rel = copy_take_file(root, src, "t001")
    assert rel == "takes/t001/out.mp4"
    assert (root / rel).read_bytes() == b"fake-mp4"


def test_load_explicit_missing_dir_does_not_walk_up(tmp_path: Path) -> None:
    init_project(tmp_path / "parent")
    empty = tmp_path / "parent" / "empty"
    empty.mkdir()
    with pytest.raises(StoreError, match="no bible.yaml"):
        load(empty)


def test_load_bible_yaml_path(tmp_path: Path) -> None:
    root = init_project(tmp_path / "via-file", title="via-file")
    loaded_root, bible = load(root / "bible.yaml")
    assert loaded_root == root.resolve()
    assert bible.title == "via-file"


def test_load_invalid_duration_is_store_error(tmp_path: Path) -> None:
    root = init_project(tmp_path / "bad-dur")
    (root / "bible.yaml").write_text(
        "version: 1\ntitle: x\ncharacters: {}\nscenes: {}\ntakes:\n  - id: t001\n    scene: s01\n    beat: x\n    duration: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(StoreError, match="duration"):
        load(root)


def test_copy_ref_rejects_directory(tmp_path: Path) -> None:
    root = init_project(tmp_path / "refs-dir")
    folder = tmp_path / "album"
    folder.mkdir()
    with pytest.raises(StoreError, match="not a file"):
        copy_ref(root, folder, "mei")


def test_example_campus_night_loads() -> None:
    root, bible = load(EXAMPLE)
    assert root == EXAMPLE.resolve()
    assert bible.aspect == "9:16"
    assert bible.characters["mei"].name == NAME
    assert bible.characters["mei"].role == "lead"
    assert len(bible.scenes) == 2
    assert {s.title for s in bible.scenes.values()} == {"夜教室", "走廊"}
    assert len(bible.takes) == 2
    assert {t.scene for t in bible.takes} == set(bible.scenes)
