from __future__ import annotations

from shotbible.prompt import compile_prompt

from conftest import (
    BEAT,
    INVENTED_WARDROBE,
    LOOK,
    NAME,
    SETTING,
    make_sample_bible,
)


def _text(result: object) -> str:
    if isinstance(result, str):
        return result
    text = getattr(result, "text", None)
    if isinstance(text, str):
        return text
    return str(result)


def test_compile_prompt_contains_look_setting_beat() -> None:
    bible = make_sample_bible()
    text = _text(
        compile_prompt(
            bible,
            "s01",
            beat=BEAT,
            character_id="mei",
            kind="video",
        )
    )
    assert LOOK in text
    assert SETTING in text
    assert BEAT in text
    assert NAME in text


def test_compile_prompt_does_not_invent_wardrobe() -> None:
    bible = make_sample_bible()
    text = _text(
        compile_prompt(
            bible,
            "s01",
            beat=BEAT,
            character_id="mei",
            kind="video",
        )
    )
    lowered = text.lower()
    for item in INVENTED_WARDROBE:
        assert item not in lowered, f"compiler invented wardrobe: {item}"


def test_compile_prompt_defaults_beat_from_latest_take() -> None:
    bible = make_sample_bible(with_take=True)
    text = _text(compile_prompt(bible, "s01", kind="video"))
    assert BEAT in text
    assert NAME in text


def test_compile_prompt_keeps_bible_only_details() -> None:
    bible = make_sample_bible()
    extra_beat = "she wipes the desk, still does not look at camera"
    text = _text(
        compile_prompt(
            bible,
            "s01",
            beat=extra_beat,
            character_id="mei",
            kind="image",
        )
    )
    assert extra_beat in text
    assert "navy hoodie" in text
    assert "classroom" in text
    # Location lock stays on the classroom; do not drag in the unused hallway.
    assert "hallway" not in text.lower()
    assert "走廊" not in text


def test_compile_prompt_includes_every_cast_member() -> None:
    from shotbible.models import Character

    bible = make_sample_bible()
    bible.characters["ergou"] = Character(
        id="ergou",
        name="二狗",
        role="lead",
        look="flat-faced orange tabby, navy apron, white fish embroidery",
        do_not=["remove the apron"],
    )
    bible.scenes["s01"].cast = ["mei", "ergou"]
    text = _text(compile_prompt(bible, "s01", beat=BEAT, kind="video"))
    assert NAME in text
    assert "二狗" in text
    assert "white fish embroidery" in text
    assert "Cast:" in text
    assert "remove the apron" in text
