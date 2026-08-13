from __future__ import annotations

import json

from .models import Bible, Character, Scene, Take


def export_json(bible: Bible) -> str:
    return json.dumps(bible.to_dict(), ensure_ascii=False, indent=2) + "\n"


def export_markdown(bible: Bible) -> str:
    lines: list[str] = [f"# {bible.title}", ""]
    lines.append(f"- **Aspect:** {bible.aspect}")
    if bible.duration_hint:
        lines.append(f"- **Duration:** {bible.duration_hint}")
    if bible.style:
        lines.append(f"- **Style:** {bible.style}")
    lines.append("")

    lines.append("## Characters")
    lines.append("")
    if not bible.characters:
        lines.append("_None._")
        lines.append("")
    else:
        for character in bible.characters.values():
            lines.extend(_character_block(character))

    lines.append("## Scenes")
    lines.append("")
    if not bible.scenes:
        lines.append("_None._")
        lines.append("")
    else:
        for scene in bible.scenes.values():
            lines.extend(_scene_block(scene))

    lines.append("## Takes")
    lines.append("")
    if not bible.takes:
        lines.append("_None._")
        lines.append("")
    else:
        lines.extend(_takes_table(bible.takes))

    text = "\n".join(lines)
    return text if text.endswith("\n") else text + "\n"


def _heading(title: str, item_id: str) -> str:
    if title and title != item_id:
        return f"### {title} (`{item_id}`)"
    return f"### `{item_id}`"


def _character_block(character: Character) -> list[str]:
    lines = [_heading(character.name, character.id), ""]
    if character.role:
        lines.append(f"- **Role:** {character.role}")
    if character.look:
        lines.append(f"- **Look:** {character.look}")
    if character.voice:
        lines.append(f"- **Voice:** {character.voice}")
    if character.do_not:
        lines.append("- **Do not:** " + "; ".join(character.do_not))
    lines.append("- **Refs:** " + (", ".join(character.refs) if character.refs else "_none_"))
    lines.append("")
    return lines


def _scene_block(scene: Scene) -> list[str]:
    lines = [_heading(scene.title, scene.id), ""]
    if scene.setting:
        lines.append(f"- **Setting:** {scene.setting}")
    if scene.lighting:
        lines.append(f"- **Lighting:** {scene.lighting}")
    if scene.camera:
        lines.append(f"- **Camera:** {scene.camera}")
    lines.append("- **Cast:** " + (", ".join(scene.cast) if scene.cast else "_none_"))
    lines.append("- **Refs:** " + (", ".join(scene.refs) if scene.refs else "_none_"))
    lines.append("")
    return lines


def _takes_table(takes: list[Take]) -> list[str]:
    lines = [
        "| ID | Scene | Character | Duration | Model | Beat |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    extras: list[str] = []
    for take in takes:
        duration = "" if take.duration is None else str(take.duration)
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(take.id),
                    _md_cell(take.scene),
                    _md_cell(take.character),
                    _md_cell(duration),
                    _md_cell(take.model),
                    _md_cell(take.beat),
                ]
            )
            + " |"
        )
        bits: list[str] = []
        if take.file:
            bits.append(f"file: {take.file}")
        if take.notes:
            bits.append(take.notes)
        if bits:
            extras.append(f"- `{take.id}` — " + "; ".join(bits))
    lines.append("")
    if extras:
        lines.append("### Take notes")
        lines.append("")
        lines.extend(extras)
        lines.append("")
    return lines


def _md_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", "")
