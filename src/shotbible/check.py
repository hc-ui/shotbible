from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

from .models import Bible


@dataclass
class Issue:
    level: str  # "error" | "warn"
    code: str
    message: str


def check_bible(root: Path, bible: Bible) -> list[Issue]:
    root = Path(root)
    issues: list[Issue] = []

    for sid, scene in bible.scenes.items():
        for cid in scene.cast:
            if cid not in bible.characters:
                issues.append(
                    Issue(
                        "error",
                        "UNKNOWN_CHARACTER",
                        f"scene '{sid}' references unknown character '{cid}'",
                    )
                )

    taken_scenes: set[str] = set()
    for take in bible.takes:
        taken_scenes.add(take.scene)
        if take.character and take.character not in bible.characters:
            issues.append(
                Issue(
                    "error",
                    "UNKNOWN_CHARACTER",
                    f"take '{take.id}' references unknown character '{take.character}'",
                )
            )
        if take.scene not in bible.scenes:
            issues.append(
                Issue(
                    "error",
                    "UNKNOWN_SCENE",
                    f"take '{take.id}' references unknown scene '{take.scene}'",
                )
            )

    for cid, character in bible.characters.items():
        for ref in character.refs:
            if not _ref_exists(root, ref):
                issues.append(
                    Issue(
                        "error",
                        "MISSING_REF",
                        f"character '{cid}' missing ref '{ref}'",
                    )
                )
        role = character.role or ""
        if ("lead" in role.lower() or role == "lead") and not character.refs:
            issues.append(
                Issue(
                    "warn",
                    "NO_REFS",
                    f"lead character '{cid}' has no refs",
                )
            )
        if not (character.look or "").strip():
            issues.append(
                Issue(
                    "warn",
                    "EMPTY_LOOK",
                    f"character '{cid}' has empty look",
                )
            )

    for sid, scene in bible.scenes.items():
        for ref in scene.refs:
            if not _ref_exists(root, ref):
                issues.append(
                    Issue(
                        "error",
                        "MISSING_REF",
                        f"scene '{sid}' missing ref '{ref}'",
                    )
                )
        if sid not in taken_scenes:
            issues.append(
                Issue(
                    "warn",
                    "SCENE_WITHOUT_TAKES",
                    f"scene '{sid}' has no takes",
                )
            )

    look_groups: dict[str, list[str]] = {}
    for cid, character in bible.characters.items():
        key = _normalize_look(character.look)
        if not key:
            continue
        look_groups.setdefault(key, []).append(cid)
    for ids in look_groups.values():
        if len(ids) < 2:
            continue
        for left, right in combinations(sorted(ids), 2):
            issues.append(
                Issue(
                    "warn",
                    "SIMILAR_LOOK",
                    f"characters '{left}' and '{right}' have similar looks",
                )
            )

    issues.sort(key=lambda issue: (0 if issue.level == "error" else 1, issue.code, issue.message))
    return issues


def _ref_exists(root: Path, ref: str) -> bool:
    if not str(ref).strip():
        return False
    path = Path(ref)
    if path.is_absolute():
        return path.exists()
    return (root / ref).exists()


def _normalize_look(look: str) -> str:
    return " ".join((look or "").strip().lower().split())
