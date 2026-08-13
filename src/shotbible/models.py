from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

Kind = Literal["image", "video"]
VALID_KINDS = ("image", "video")


class ParseError(ValueError):
    pass


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]
    raise ParseError(f"expected a list, got {type(value).__name__}")


def parse_duration(value: Any) -> int | None:
    if value in ("", None):
        return None
    if isinstance(value, bool):
        raise ParseError("duration cannot be a boolean")
    if isinstance(value, (int, float)):
        if int(value) != value:
            raise ParseError("duration must be a whole number of seconds")
        result = int(value)
    else:
        text = str(value).strip().lower()
        if text.endswith("s") and text[:-1].lstrip("-").isdigit():
            text = text[:-1]
        try:
            result = int(text)
        except ValueError as exc:
            raise ParseError(f"invalid duration: {value!r}") from exc
    if result <= 0:
        raise ParseError("duration must be a positive integer")
    return result


def parse_kind(value: Any) -> Kind:
    kind = str(value or "video").strip().lower()
    if kind not in VALID_KINDS:
        raise ParseError(f"unknown kind: {value!r} (use image or video)")
    return kind  # type: ignore[return-value]


@dataclass
class Character:
    id: str
    name: str = ""
    role: str = ""
    look: str = ""
    voice: str = ""
    do_not: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, cid: str, data: dict[str, Any] | None) -> "Character":
        data = data or {}
        return cls(
            id=cid,
            name=str(data.get("name") or cid),
            role=str(data.get("role") or ""),
            look=str(data.get("look") or ""),
            voice=str(data.get("voice") or ""),
            do_not=_list(data.get("do_not")),
            refs=_list(data.get("refs")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "look": self.look,
            "voice": self.voice,
            "do_not": list(self.do_not),
            "refs": list(self.refs),
        }


@dataclass
class Scene:
    id: str
    title: str = ""
    setting: str = ""
    lighting: str = ""
    camera: str = ""
    cast: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, sid: str, data: dict[str, Any] | None) -> "Scene":
        data = data or {}
        return cls(
            id=sid,
            title=str(data.get("title") or sid),
            setting=str(data.get("setting") or ""),
            lighting=str(data.get("lighting") or ""),
            camera=str(data.get("camera") or ""),
            cast=_list(data.get("cast")),
            refs=_list(data.get("refs")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "setting": self.setting,
            "lighting": self.lighting,
            "camera": self.camera,
            "cast": list(self.cast),
            "refs": list(self.refs),
        }


@dataclass
class Take:
    id: str
    scene: str
    beat: str
    character: str = ""
    file: str = ""
    model: str = ""
    duration: int | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Take":
        duration_i = parse_duration(data.get("duration"))
        return cls(
            id=str(data.get("id") or ""),
            scene=str(data.get("scene") or ""),
            beat=str(data.get("beat") or ""),
            character=str(data.get("character") or ""),
            file=str(data.get("file") or ""),
            model=str(data.get("model") or ""),
            duration=duration_i,
            notes=str(data.get("notes") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload["duration"] is None:
            payload.pop("duration")
        return payload


@dataclass
class Bible:
    title: str = "untitled"
    aspect: str = "9:16"
    duration_hint: str = ""
    style: str = ""
    characters: dict[str, Character] = field(default_factory=dict)
    scenes: dict[str, Scene] = field(default_factory=dict)
    takes: list[Take] = field(default_factory=list)
    version: int = 1

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Bible":
        data = data or {}
        chars_raw = data.get("characters") or {}
        scenes_raw = data.get("scenes") or {}
        takes_raw = data.get("takes") or []
        if chars_raw and not isinstance(chars_raw, dict):
            raise ParseError("characters must be a mapping of id -> record")
        if scenes_raw and not isinstance(scenes_raw, dict):
            raise ParseError("scenes must be a mapping of id -> record")
        if takes_raw and not isinstance(takes_raw, list):
            raise ParseError("takes must be a list")
        version_raw = data.get("version") or 1
        try:
            version = int(version_raw)
        except (TypeError, ValueError) as exc:
            raise ParseError(f"invalid version: {version_raw!r}") from exc
        return cls(
            title=str(data.get("title") or "untitled"),
            aspect=str(data.get("aspect") or "9:16"),
            duration_hint=str(data.get("duration_hint") or ""),
            style=str(data.get("style") or ""),
            characters={
                str(cid): Character.from_dict(str(cid), c if isinstance(c, dict) else {})
                for cid, c in chars_raw.items()
            },
            scenes={
                str(sid): Scene.from_dict(str(sid), s if isinstance(s, dict) else {})
                for sid, s in scenes_raw.items()
            },
            takes=[Take.from_dict(t) for t in takes_raw if isinstance(t, dict)],
            version=version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "title": self.title,
            "aspect": self.aspect,
            "duration_hint": self.duration_hint,
            "style": self.style,
            "characters": {cid: c.to_dict() for cid, c in self.characters.items()},
            "scenes": {sid: s.to_dict() for sid, s in self.scenes.items()},
            "takes": [t.to_dict() for t in self.takes],
        }

    def next_take_id(self) -> str:
        n = 1
        existing = {t.id for t in self.takes}
        while True:
            tid = f"t{n:03d}"
            if tid not in existing:
                return tid
            n += 1
