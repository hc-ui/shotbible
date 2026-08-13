# shotbible

[![CI](https://github.com/hc-ui/shotbible/actions/workflows/ci.yml/badge.svg)](https://github.com/hc-ui/shotbible/actions/workflows/ci.yml)

Local continuity bible for AI image/video productions.

AI video tools forget faces, wardrobe, and lighting between takes. shotbible keeps a small production bible on disk and compiles locked prompts from it.

**Local only. No API keys. No cloud. Nothing is uploaded.**

[简体中文](README.zh-CN.md)

## Install

From a clone (recommended):

```bash
pip install -e .
# or: python -m shotbible --help
```

Dev / tests:

```bash
pip install -e ".[dev]"
pytest
```

The PyPI name is `shotbible` (`pip install shotbible`) when published.

## 20-second quickstart

```bash
shotbible init my-short --title "夜校最后一课" --aspect 9:16
cd my-short
shotbible character add mei --name "阿梅" --role lead --look "20s Chinese woman, short black hair, navy hoodie"
shotbible scene add s01 --title "夜教室" --setting "empty classroom at night" --cast mei
shotbible take add s01 --beat "she opens the laptop, does not look at camera"
shotbible prompt s01 -o
shotbible check
```

`prompt -o` writes `takes/s01.prompt.txt`. Paste that file into your video model. New projects default to **9:16**.

A ready-made 9:16 campus-night bible lives in [`examples/campus-night/bible.yaml`](examples/campus-night/bible.yaml).

## Commands

| Command | What it does |
|---------|----------------|
| `init [dir]` | Create `bible.yaml`, `refs/`, `takes/` |
| `set --title --aspect --style --duration-hint` | Update project metadata |
| `character add ID --name --look [--ref PATH]` | Lock a character (copies `--ref` into `refs/`) |
| `character rm ID` | Remove a character (refuses if still cast) |
| `scene add ID --title --setting --cast ID` | Lock a scene and its cast |
| `scene rm ID` / `scene show ID` | Remove or print a scene |
| `character show ID` | Print one character |
| `take add SCENE --beat TEXT [--file PATH] [--model NAME]` | Record a take (copies `--file` into `takes/`) |
| `take rm ID` / `take show ID` | Remove or print a take |
| `prompt SCENE [-o [FILE]]` | Compile a locked prompt; `-o` saves it |
| `prompt-take TAKE [-o [FILE]]` | Compile from a stored take |
| `check [--strict] [--json]` | Validate; `--strict` fails on warnings |
| `export [--format md\|json]` | Dump the bible |
| `list [--json]` | Show characters, scenes, takes |

## `bible.yaml`

```yaml
version: 1
title: 夜校最后一课
aspect: "9:16"
style: "cinematic, night classroom, cool fluorescent, Chinese campus"
characters:
  mei:
    name: 阿梅
    role: lead
    look: "20s Chinese woman, short black hair, navy hoodie, backpack"
    do_not: ["change hair length", "add glasses", "smile at camera"]
    refs: []
scenes:
  s01:
    title: 夜教室
    setting: "empty university classroom at night, rows of desks, one open laptop"
    lighting: "cool overhead fluorescent, window city glow"
    camera: "slow push-in, 35mm, 9:16"
    cast: [mei]
takes:
  - id: t001
    scene: s01
    character: mei
    beat: "she sits, opens the laptop, does not look at camera"
    duration: 6
```

The compiler always emits identity → scene → camera → beat → negatives. It never invents wardrobe or locations that are not in the bible.

## License

MIT
