from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal


Kind = Literal["image", "video"]


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(x) for x in value]


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
        duration = data.get("duration")
        if duration in ("", None):
            duration_i = None
        else:
            duration_i = int(duration)
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
    aspect: str = "16:9"
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
        return cls(
            title=str(data.get("title") or "untitled"),
            aspect=str(data.get("aspect") or "16:9"),
            duration_hint=str(data.get("duration_hint") or ""),
            style=str(data.get("style") or ""),
            characters={
                cid: Character.from_dict(str(cid), c or {})
                for cid, c in chars_raw.items()
            },
            scenes={
                sid: Scene.from_dict(str(sid), s or {})
                for sid, s in scenes_raw.items()
            },
            takes=[Take.from_dict(t) for t in takes_raw if isinstance(t, dict)],
            version=int(data.get("version") or 1),
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
