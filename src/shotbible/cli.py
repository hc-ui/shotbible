from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from . import __version__
from .check import check_bible
from .export import export_json, export_markdown
from .models import Character, ParseError, Scene, Take, parse_duration
from .prompt import compile_prompt, compile_take
from .store import (
    StoreError,
    add_take,
    copy_ref,
    copy_take_file,
    init_project,
    load,
    remove_character,
    remove_scene,
    remove_take,
    require_character,
    require_scene,
    save,
    upsert_character,
    upsert_scene,
)


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (StoreError, ParseError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-C",
        "--project",
        metavar="DIR",
        default=argparse.SUPPRESS,
        help="project root (default: walk up from cwd)",
    )

    parser = argparse.ArgumentParser(
        prog="shotbible",
        description="Local continuity bible for AI image/video productions.",
        parents=[common],
    )
    parser.add_argument("--version", action="version", version=f"shotbible {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", parents=[common], help="create a new project")
    p_init.add_argument("dir", nargs="?", default=None, help="project directory (default: .)")
    p_init.add_argument("--title", default=None, metavar="T")
    p_init.add_argument("--aspect", default=None, metavar="A")
    p_init.set_defaults(func=cmd_init)

    p_character = sub.add_parser("character", parents=[common], help="manage characters")
    char_sub = p_character.add_subparsers(dest="character_cmd", required=True)
    p_char_add = char_sub.add_parser("add", parents=[common], help="add or update a character")
    p_char_add.add_argument("id", metavar="ID")
    p_char_add.add_argument("--name", default=None)
    p_char_add.add_argument("--role", default=None)
    p_char_add.add_argument("--look", default=None)
    p_char_add.add_argument("--voice", default=None)
    p_char_add.add_argument("--ref", action="append", dest="refs", metavar="PATH")
    p_char_add.add_argument("--do-not", action="append", dest="do_not", metavar="TEXT")
    p_char_add.set_defaults(func=cmd_character_add)
    p_char_rm = char_sub.add_parser("rm", parents=[common], help="remove a character")
    p_char_rm.add_argument("id", metavar="ID")
    p_char_rm.set_defaults(func=cmd_character_rm)
    p_char_show = char_sub.add_parser("show", parents=[common], help="print one character")
    p_char_show.add_argument("id", metavar="ID")
    p_char_show.set_defaults(func=cmd_character_show)

    p_scene = sub.add_parser("scene", parents=[common], help="manage scenes")
    scene_sub = p_scene.add_subparsers(dest="scene_cmd", required=True)
    p_scene_add = scene_sub.add_parser("add", parents=[common], help="add or update a scene")
    p_scene_add.add_argument("id", metavar="ID")
    p_scene_add.add_argument("--title", default=None)
    p_scene_add.add_argument("--setting", default=None)
    p_scene_add.add_argument("--lighting", default=None)
    p_scene_add.add_argument("--camera", default=None)
    p_scene_add.add_argument("--cast", action="append", metavar="ID")
    p_scene_add.add_argument("--ref", action="append", dest="refs", metavar="PATH")
    p_scene_add.set_defaults(func=cmd_scene_add)
    p_scene_rm = scene_sub.add_parser("rm", parents=[common], help="remove a scene")
    p_scene_rm.add_argument("id", metavar="ID")
    p_scene_rm.set_defaults(func=cmd_scene_rm)
    p_scene_show = scene_sub.add_parser("show", parents=[common], help="print one scene")
    p_scene_show.add_argument("id", metavar="ID")
    p_scene_show.set_defaults(func=cmd_scene_show)

    p_take = sub.add_parser("take", parents=[common], help="manage takes")
    take_sub = p_take.add_subparsers(dest="take_cmd", required=True)
    p_take_add = take_sub.add_parser("add", parents=[common], help="add a take")
    p_take_add.add_argument("scene", metavar="SCENE")
    p_take_add.add_argument("--beat", required=True, metavar="TEXT")
    p_take_add.add_argument("--character", default=None, metavar="ID")
    p_take_add.add_argument("--file", default=None, metavar="PATH")
    p_take_add.add_argument("--model", default=None, metavar="NAME")
    p_take_add.add_argument("--duration", type=int, default=None, metavar="N")
    p_take_add.add_argument("--notes", default=None, metavar="TEXT")
    p_take_add.set_defaults(func=cmd_take_add)
    p_take_rm = take_sub.add_parser("rm", parents=[common], help="remove a take")
    p_take_rm.add_argument("take_id", metavar="TAKE_ID")
    p_take_rm.set_defaults(func=cmd_take_rm)
    p_take_show = take_sub.add_parser("show", parents=[common], help="print one take")
    p_take_show.add_argument("take_id", metavar="TAKE_ID")
    p_take_show.set_defaults(func=cmd_take_show)

    p_set = sub.add_parser("set", parents=[common], help="update project title, aspect, style")
    p_set.add_argument("--title", default=None)
    p_set.add_argument("--aspect", default=None)
    p_set.add_argument("--style", default=None)
    p_set.add_argument("--duration-hint", default=None, dest="duration_hint")
    p_set.set_defaults(func=cmd_set)

    p_prompt = sub.add_parser("prompt", parents=[common], help="compile a prompt for a scene")
    p_prompt.add_argument("scene", metavar="SCENE")
    p_prompt.add_argument("--beat", default=None, metavar="TEXT")
    p_prompt.add_argument("--character", default=None, metavar="ID")
    p_prompt.add_argument("--kind", choices=("image", "video"), default="video")
    p_prompt.add_argument(
        "-o",
        "--output",
        nargs="?",
        const="",
        default=None,
        metavar="FILE",
        help="write prompt to FILE (default: takes/<scene>.prompt.txt)",
    )
    p_prompt.set_defaults(func=cmd_prompt)

    p_prompt_take = sub.add_parser(
        "prompt-take",
        parents=[common],
        help="compile a prompt for an existing take",
    )
    p_prompt_take.add_argument("take_id", metavar="TAKE_ID")
    p_prompt_take.add_argument("--kind", choices=("image", "video"), default="video")
    p_prompt_take.add_argument(
        "-o",
        "--output",
        nargs="?",
        const="",
        default=None,
        metavar="FILE",
        help="write prompt to FILE (default: takes/<id>.prompt.txt)",
    )
    p_prompt_take.set_defaults(func=cmd_prompt_take)

    p_check = sub.add_parser("check", parents=[common], help="validate the bible")
    p_check.add_argument("--strict", action="store_true", help="treat warnings as errors")
    p_check.add_argument("--json", action="store_true", dest="as_json", help="print JSON")
    p_check.set_defaults(func=cmd_check)

    p_export = sub.add_parser("export", parents=[common], help="export markdown or JSON")
    p_export.add_argument("--format", choices=("md", "json"), default="md")
    p_export.add_argument("-o", "--output", metavar="FILE", default=None)
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", parents=[common], help="list characters, scenes, and takes")
    p_list.add_argument("--json", action="store_true", dest="as_json", help="print JSON")
    p_list.set_defaults(func=cmd_list)

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    if args.dir:
        dest = Path(args.dir)
    elif getattr(args, "project", None):
        dest = Path(args.project)
    else:
        dest = Path(".")
    dest = dest.expanduser()
    kwargs: dict[str, str] = {}
    if args.title is not None:
        kwargs["title"] = args.title
    if args.aspect is not None:
        kwargs["aspect"] = args.aspect
    path = init_project(dest, **kwargs)
    print(f"initialized {path} (title={kwargs.get('title', 'untitled')}, aspect={kwargs.get('aspect', '9:16')})")
    return 0


def cmd_character_add(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    cid = _require_id(args.id, "character")
    existed = cid in bible.characters
    if existed:
        character = bible.characters[cid]
        if args.name is not None:
            character.name = args.name
        if args.role is not None:
            character.role = args.role
        if args.look is not None:
            character.look = args.look
        if args.voice is not None:
            character.voice = args.voice
    else:
        character = Character(
            id=cid,
            name=args.name or cid,
            role=args.role or "",
            look=args.look or "",
            voice=args.voice or "",
        )

    added_constraints = _extend_unique(character.do_not, args.do_not)
    added_refs = _add_refs(root, character.refs, args.refs, cid)
    upsert_character(bible, character)
    save(root, bible)
    print(_changed_line("character", cid, existed, added_refs, added_constraints))
    return 0


def cmd_scene_add(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    sid = _require_id(args.id, "scene")
    existed = sid in bible.scenes
    if existed:
        scene = bible.scenes[sid]
        if args.title is not None:
            scene.title = args.title
        if args.setting is not None:
            scene.setting = args.setting
        if args.lighting is not None:
            scene.lighting = args.lighting
        if args.camera is not None:
            scene.camera = args.camera
    else:
        scene = Scene(
            id=sid,
            title=args.title or sid,
            setting=args.setting or "",
            lighting=args.lighting or "",
            camera=args.camera or "",
        )

    if args.cast:
        for cid in args.cast:
            require_character(bible, cid)
        added_cast = _extend_unique(scene.cast, args.cast)
    else:
        added_cast = 0
    added_refs = _add_refs(root, scene.refs, args.refs, sid)
    upsert_scene(bible, scene)
    save(root, bible)
    extra = []
    if added_cast:
        extra.append(f"cast+={added_cast}")
    if added_refs:
        extra.append(f"refs+={added_refs}")
    action = "updated" if existed else "added"
    suffix = f" ({', '.join(extra)})" if extra else ""
    print(f"scene {sid} {action}{suffix}")
    return 0


def cmd_character_show(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    character = require_character(bible, _require_id(args.id, "character"))
    _print_yaml({"id": character.id, **character.to_dict()})
    return 0


def cmd_scene_show(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    scene = require_scene(bible, _require_id(args.id, "scene"))
    _print_yaml({"id": scene.id, **scene.to_dict()})
    return 0


def cmd_take_show(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    take = _require_take(bible, args.take_id)
    _print_yaml(take.to_dict())
    return 0


def cmd_character_rm(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    cid = _require_id(args.id, "character")
    remove_character(bible, cid)
    save(root, bible)
    print(f"character {cid} removed")
    return 0


def cmd_scene_rm(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    sid = _require_id(args.id, "scene")
    remove_scene(bible, sid)
    save(root, bible)
    print(f"scene {sid} removed")
    return 0


def cmd_take_rm(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    take = remove_take(bible, _require_id(args.take_id, "take"))
    save(root, bible)
    print(f"take {take.id} removed")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    changed: list[str] = []
    if args.title is not None:
        title = args.title.strip()
        if not title:
            raise StoreError("title cannot be empty")
        bible.title = title
        changed.append("title")
    if args.aspect is not None:
        aspect = args.aspect.strip()
        if not aspect:
            raise StoreError("aspect cannot be empty")
        bible.aspect = aspect
        changed.append("aspect")
    if args.style is not None:
        bible.style = args.style
        changed.append("style")
    if args.duration_hint is not None:
        bible.duration_hint = args.duration_hint
        changed.append("duration_hint")
    if not changed:
        raise StoreError("nothing to set; pass --title, --aspect, --style, or --duration-hint")
    save(root, bible)
    print("updated " + ", ".join(changed))
    return 0


def cmd_take_add(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    sid = _require_id(args.scene, "scene")
    require_scene(bible, sid)
    character_id = args.character or ""
    if character_id:
        require_character(bible, character_id)
    duration = parse_duration(args.duration) if args.duration is not None else None
    take = add_take(
        bible,
        Take(
            id="",
            scene=sid,
            beat=args.beat,
            character=character_id,
            file="",
            model=args.model or "",
            duration=duration,
            notes=args.notes or "",
        ),
    )
    if args.file:
        take.file = copy_take_file(root, Path(args.file), take.id)
    save(root, bible)
    extra = f" file={take.file}" if take.file else ""
    print(f"take {take.id} added (scene={sid}{extra})")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    sid = _require_id(args.scene, "scene")
    require_scene(bible, sid)
    character_id = args.character or ""
    if character_id:
        require_character(bible, character_id)
    text = compile_prompt(
        bible,
        sid,
        beat=args.beat or "",
        character_id=character_id,
        kind=args.kind,
    )
    return _emit_prompt(root, text, args.output, f"{sid}.prompt.txt")


def cmd_prompt_take(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    take = _require_take(bible, args.take_id)
    text = compile_take(bible, take, kind=args.kind)
    return _emit_prompt(root, text, args.output, f"{take.id}.prompt.txt")


def cmd_check(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    issues = check_bible(root, bible)
    has_error = any(issue.level == "error" for issue in issues)
    failed = has_error or (args.strict and bool(issues))
    if args.as_json:
        payload = {
            "ok": not failed,
            "issues": [
                {"level": issue.level, "code": issue.code, "message": issue.message}
                for issue in issues
            ],
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        return 1 if failed else 0
    if not issues:
        print("ok")
        return 0
    for issue in issues:
        print(f"{issue.level:5} {issue.code}: {issue.message}")
    return 1 if failed else 0


def cmd_export(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    text = export_json(bible) if args.format == "json" else export_markdown(bible)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {out}")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    if args.as_json:
        sys.stdout.write(json.dumps(_list_payload(bible), ensure_ascii=False, indent=2) + "\n")
        return 0
    header = [bible.title, bible.aspect]
    if bible.duration_hint:
        header.append(bible.duration_hint)
    print("  ".join(header))
    if bible.style:
        print(f"style: {bible.style}")

    print(f"characters ({len(bible.characters)})")
    for cid, character in bible.characters.items():
        bits = [cid]
        if character.name and character.name != cid:
            bits.append(character.name)
        if character.role:
            bits.append(character.role)
        bits.append(f"refs={len(character.refs)}")
        print("  " + "  ".join(bits))

    counts: dict[str, int] = {}
    for take in bible.takes:
        counts[take.scene] = counts.get(take.scene, 0) + 1

    print(f"scenes ({len(bible.scenes)})")
    for sid, scene in bible.scenes.items():
        bits = [sid]
        if scene.title and scene.title != sid:
            bits.append(scene.title)
        if scene.cast:
            bits.append("cast=" + ",".join(scene.cast))
        bits.append(f"takes={counts.get(sid, 0)}")
        print("  " + "  ".join(bits))

    print(f"takes ({len(bible.takes)})")
    for take in bible.takes:
        bits = [take.id, take.scene]
        if take.character:
            bits.append(take.character)
        if take.duration is not None:
            bits.append(f"{take.duration}s")
        if take.beat:
            beat = take.beat.replace("\n", " ")
            if len(beat) > 60:
                beat = beat[:57] + "..."
            bits.append(beat)
        print("  " + "  ".join(bits))
    return 0


def _emit_prompt(root: Path, text: str, output: str | None, default_name: str) -> int:
    if output is None:
        print(text)
        return 0
    if output == "":
        dest = root / "takes" / default_name
    else:
        dest = Path(output).expanduser()
        if not dest.is_absolute():
            dest = root / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {dest}")
    return 0


def _print_yaml(data: object) -> None:
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _list_payload(bible) -> dict:
    return {
        "title": bible.title,
        "aspect": bible.aspect,
        "duration_hint": bible.duration_hint,
        "style": bible.style,
        "characters": [
            {
                "id": cid,
                "name": character.name,
                "role": character.role,
                "refs": len(character.refs),
            }
            for cid, character in bible.characters.items()
        ],
        "scenes": [
            {
                "id": sid,
                "title": scene.title,
                "cast": list(scene.cast),
                "takes": sum(1 for take in bible.takes if take.scene == sid),
            }
            for sid, scene in bible.scenes.items()
        ],
        "takes": [
            {
                "id": take.id,
                "scene": take.scene,
                "character": take.character,
                "duration": take.duration,
                "beat": take.beat,
            }
            for take in bible.takes
        ],
    }


def _load(args: argparse.Namespace):
    start = getattr(args, "project", None)
    return load(Path(start).expanduser() if start else None)


def _require_id(value: str, kind: str) -> str:
    item_id = (value or "").strip()
    if not item_id:
        raise StoreError(f"{kind} id is empty")
    if item_id in {".", ".."} or "/" in item_id or "\\" in item_id:
        raise StoreError(f"{kind} id cannot contain a path: {item_id}")
    return item_id


def _require_take(bible, take_id: str) -> Take:
    tid = _require_id(take_id, "take")
    for take in bible.takes:
        if take.id == tid:
            return take
    raise StoreError(f"unknown take: {tid}")


def _extend_unique(target: list[str], values: list[str] | None) -> int:
    if not values:
        return 0
    added = 0
    for raw in values:
        item = raw.strip() if isinstance(raw, str) else str(raw)
        if not item or item in target:
            continue
        target.append(item)
        added += 1
    return added


def _add_refs(root: Path, target: list[str], paths: list[str] | None, bucket: str) -> int:
    if not paths:
        return 0
    added = 0
    for raw in paths:
        rel = copy_ref(root, Path(raw), bucket)
        if rel not in target:
            target.append(rel)
            added += 1
    return added


def _changed_line(
    kind: str,
    item_id: str,
    existed: bool,
    added_refs: int,
    added_constraints: int = 0,
) -> str:
    action = "updated" if existed else "added"
    extra: list[str] = []
    if added_refs:
        extra.append(f"refs+={added_refs}")
    if added_constraints:
        extra.append(f"do_not+={added_constraints}")
    suffix = f" ({', '.join(extra)})" if extra else ""
    return f"{kind} {item_id} {action}{suffix}"


def _ensure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if encoding in {"utf8", "utf8sig"}:
            continue
        if encoding not in {"cp936", "gbk", "gb2312", "mbcs", "charmap", "ascii", "cp1252"}:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                continue
