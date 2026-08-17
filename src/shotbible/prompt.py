from __future__ import annotations

from .models import Bible, Character, Scene, Take, parse_kind
from .store import require_character, require_scene

_VIDEO_CLOSER = "Single continuous shot, no jump cuts, no on-screen text, no subtitles."
_IMAGE_CLOSER = "Still frame, no motion blur text, no watermark, no subtitles."
_REF_LOCK = (
    "Keep identity consistent with the reference stills listed in the bible "
    "(do not invent a new face)."
)


def compile_prompt(
    bible: Bible,
    scene_id: str,
    *,
    beat: str = "",
    character_id: str = "",
    kind: str = "video",
) -> str:
    return _compile(
        bible,
        scene_id,
        beat=beat,
        character_id=character_id,
        kind=kind,
        duration=None,
        fill_from_takes=True,
    )


def compile_take(bible: Bible, take: Take, kind: str = "video") -> str:
    return _compile(
        bible,
        take.scene,
        beat=take.beat,
        character_id=take.character,
        kind=kind,
        duration=take.duration,
        fill_from_takes=False,
    )


def _compile(
    bible: Bible,
    scene_id: str,
    *,
    beat: str,
    character_id: str,
    kind: str,
    duration: int | None,
    fill_from_takes: bool,
) -> str:
    scene = require_scene(bible, scene_id)
    if fill_from_takes and (not (beat or "").strip() or not character_id):
        take = _latest_take(bible, scene_id)
        if take is not None:
            if not (beat or "").strip():
                beat = take.beat
            if not character_id and take.character:
                character_id = take.character
    characters = _resolve_characters(bible, scene, character_id)
    kind = parse_kind(kind)
    sections = [
        f"AI {kind} prompt — {bible.title} / {scene.title}",
        _identity_lock(characters),
        _do_not(characters),
        _scene_lock(bible, scene),
        _camera_section(bible, scene, duration),
        _beat_section(beat),
        _ref_lock(characters, scene),
        _IMAGE_CLOSER if kind == "image" else _VIDEO_CLOSER,
    ]
    text = "\n\n".join(part for part in sections if part)
    return text.strip()


def _latest_take(bible: Bible, scene_id: str) -> Take | None:
    for take in reversed(bible.takes):
        if take.scene == scene_id:
            return take
    return None


def _resolve_characters(
    bible: Bible, scene: Scene, character_id: str
) -> list[Character]:
    ordered: list[Character] = []
    seen: set[str] = set()
    if character_id:
        primary = require_character(bible, character_id)
        ordered.append(primary)
        seen.add(primary.id)
    for cid in scene.cast:
        if cid in seen:
            continue
        found = bible.characters.get(cid)
        if found is None:
            continue
        ordered.append(found)
        seen.add(cid)
    return ordered


def _one_character(character: Character) -> str:
    lines: list[str] = []
    if character.name:
        lines.append(f"Name: {character.name}")
    if character.id and character.id != character.name:
        lines.append(f"Id: {character.id}")
    if character.role:
        lines.append(f"Role: {character.role}")
    if character.look:
        lines.append(f"Look: {character.look}")
    if character.voice:
        lines.append(f"Voice: {character.voice}")
    return "\n".join(lines)


def _identity_lock(characters: list[Character]) -> str:
    if not characters:
        return ""
    if len(characters) == 1:
        return _one_character(characters[0])
    blocks = [_one_character(item) for item in characters]
    numbered = [f"[{index}] {block}" for index, block in enumerate(blocks, start=1)]
    return "Cast:\n\n" + "\n\n".join(numbered)


def _do_not(characters: list[Character]) -> str:
    items: list[str] = []
    for character in characters:
        label = character.name or character.id
        for raw in character.do_not:
            text = str(raw).strip()
            if not text:
                continue
            if len(characters) > 1 and label:
                items.append(f"{label}: {text}")
            else:
                items.append(text)
    if not items:
        return ""
    return "Do not: " + "; ".join(items)


def _scene_lock(bible: Bible, scene: Scene) -> str:
    lines: list[str] = []
    if scene.setting:
        lines.append(f"Setting: {scene.setting}")
    if scene.lighting:
        lines.append(f"Lighting: {scene.lighting}")
    if bible.aspect:
        lines.append(f"Aspect: {bible.aspect}")
    if bible.style:
        lines.append(f"Style: {bible.style}")
    return "\n".join(lines)


def _camera_section(bible: Bible, scene: Scene, duration: int | None) -> str:
    parts: list[str] = []
    if scene.camera:
        parts.append(scene.camera)
    if bible.duration_hint:
        parts.append(bible.duration_hint)
    if duration is not None:
        parts.append(f"{duration}s")
    if not parts:
        return ""
    return "Camera: " + ", ".join(parts)


def _beat_section(beat: str) -> str:
    text = (beat or "").strip()
    if not text:
        return ""
    return f"Beat: {text}"


def _ref_lock(characters: list[Character], scene: Scene) -> str:
    char_refs = any(character.refs for character in characters)
    if char_refs or scene.refs:
        return _REF_LOCK
    return ""
