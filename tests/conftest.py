from __future__ import annotations

from pathlib import Path

import pytest

from shotbible.models import Bible, Character, Scene, Take
from shotbible.store import init_project, save

TITLE = "毕业短片"
NAME = "阿梅"
LOOK = "20s Chinese woman, short black hair, navy hoodie, backpack"
SETTING = "empty university classroom at night, rows of desks, one open laptop"
BEAT = "she sits, opens the laptop, does not look at camera"
STYLE = "cinematic, night classroom, cool fluorescent, Chinese campus"

# Wardrobe / costume strings that must never be invented by the compiler.
INVENTED_WARDROBE = (
    "red dress",
    "evening gown",
    "ball gown",
    "tuxedo",
    "leather jacket",
    "high heels",
    "cocktail dress",
    "three-piece suit",
)


def write_dummy_png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"dummy")
    return path


def make_sample_bible(*, with_ref: bool = True, with_take: bool = True) -> Bible:
    refs = ["refs/mei/front.png"] if with_ref else []
    takes: list[Take] = []
    if with_take:
        takes.append(
            Take(
                id="t001",
                scene="s01",
                character="mei",
                beat=BEAT,
                model="grok-imagine-video-1.5",
                duration=6,
            )
        )
    return Bible(
        title=TITLE,
        aspect="9:16",
        duration_hint="75s",
        style=STYLE,
        characters={
            "mei": Character(
                id="mei",
                name=NAME,
                role="lead",
                look=LOOK,
                voice="calm narrator-adjacent, soft Mandarin",
                do_not=["change hair length", "add glasses", "smile at camera"],
                refs=refs,
            )
        },
        scenes={
            "s01": Scene(
                id="s01",
                title="夜教室",
                setting=SETTING,
                lighting="cool overhead fluorescent, window city glow",
                camera="slow push-in, 35mm, 9:16",
                cast=["mei"],
            )
        },
        takes=takes,
    )


@pytest.fixture
def dummy_png(tmp_path: Path) -> Path:
    return write_dummy_png(tmp_path / "front.png")


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    return init_project(tmp_path / "empty", title="untitled", aspect="16:9")


@pytest.fixture
def sample_project(tmp_path: Path) -> tuple[Path, Bible]:
    root = tmp_path / "campus"
    init_project(root, title=TITLE, aspect="9:16")
    write_dummy_png(root / "refs" / "mei" / "front.png")
    bible = make_sample_bible(with_ref=True, with_take=True)
    save(root, bible)
    return root, bible
