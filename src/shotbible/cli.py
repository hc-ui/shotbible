from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from . import __version__
from .check import check_bible
from .export import export_json, export_markdown
from .models import Character, Scene, Take
from .prompt import compile_prompt, compile_take
from .store import (
    StoreError,
    add_take,
    copy_ref,
    init_project,
    load,
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
    except (StoreError, FileNotFoundError) as exc:
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

    p_prompt = sub.add_parser("prompt", parents=[common], help="compile a prompt for a scene")
    p_prompt.add_argument("scene", metavar="SCENE")
    p_prompt.add_argument("--beat", default=None, metavar="TEXT")
    p_prompt.add_argument("--character", default=None, metavar="ID")
    p_prompt.add_argument("--kind", choices=("image", "video"), default="video")
    p_prompt.set_defaults(func=cmd_prompt)

    p_prompt_take = sub.add_parser(
        "prompt-take",
        parents=[common],
        help="compile a prompt for an existing take",
    )
    p_prompt_take.add_argument("take_id", metavar="TAKE_ID")
    p_prompt_take.add_argument("--kind", choices=("image", "video"), default="video")
    p_prompt_take.set_defaults(func=cmd_prompt_take)

    p_check = sub.add_parser("check", parents=[common], help="validate the bible")
    p_check.set_defaults(func=cmd_check)

    p_export = sub.add_parser("export", parents=[common], help="export markdown or JSON")
    p_export.add_argument("--format", choices=("md", "json"), default="md")
    p_export.add_argument("-o", "--output", metavar="FILE", default=None)
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", parents=[common], help="list characters, scenes, and takes")
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
    print(f"initialized {path} (title={kwargs.get('title', 'untitled')}, aspect={kwargs.get('aspect', '16:9')})")
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


def cmd_take_add(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    sid = _require_id(args.scene, "scene")
    require_scene(bible, sid)
    character_id = args.character or ""
    if character_id:
        require_character(bible, character_id)
    take = add_take(
        bible,
        Take(
            id="",
            scene=sid,
            beat=args.beat,
            character=character_id,
            file=args.file or "",
            model=args.model or "",
            duration=args.duration,
            notes=args.notes or "",
        ),
    )
    save(root, bible)
    print(f"take {take.id} added (scene={sid})")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    sid = _require_id(args.scene, "scene")
    require_scene(bible, sid)
    character_id = args.character or ""
    if character_id:
        require_character(bible, character_id)
    print(
        compile_prompt(
            bible,
            sid,
            beat=args.beat or "",
            character_id=character_id,
            kind=args.kind,
        )
    )
    return 0


def cmd_prompt_take(args: argparse.Namespace) -> int:
    _root, bible = _load(args)
    take = _require_take(bible, args.take_id)
    print(compile_take(bible, take, kind=args.kind))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root, bible = _load(args)
    issues = check_bible(root, bible)
    if not issues:
        print("ok")
        return 0
    has_error = False
    for issue in issues:
        print(f"{issue.level:5} {issue.code}: {issue.message}")
        if issue.level == "error":
            has_error = True
    return 1 if has_error else 0


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
        if take.duration:
            bits.append(f"{take.duration}s")
        if take.beat:
            beat = take.beat.replace("\n", " ")
            if len(beat) > 60:
                beat = beat[:57] + "..."
            bits.append(beat)
        print("  " + "  ".join(bits))
    return 0


def _load(args: argparse.Namespace):
    start = getattr(args, "project", None)
    return load(Path(start).expanduser() if start else None)


def _require_id(value: str, kind: str) -> str:
    item_id = (value or "").strip()
    if not item_id:
        raise StoreError(f"{kind} id is empty")
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
    sys.stdout = _utf8_stream(sys.stdout)
    sys.stderr = _utf8_stream(sys.stderr)


def _utf8_stream(stream):
    if stream is None:
        return stream
    encoding = (getattr(stream, "encoding", None) or "").replace("-", "").lower()
    if encoding == "utf8":
        return stream
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
            return stream
        except (OSError, ValueError, AttributeError):
            pass
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        return stream
    return io.TextIOWrapper(buffer, encoding="utf-8", errors="replace", line_buffering=True)
