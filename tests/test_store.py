from __future__ import annotations

from pathlib import Path

import pytest

from shotbible.models import Character, Scene, Take
from shotbible.store import (
    StoreError,
    add_take,
    copy_ref,
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
