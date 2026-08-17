# shotbible spec (v0.1)

Local-first continuity bible for AI image/video productions.

## Why

AI video tools forget faces, wardrobe, and lighting between takes.
shotbible stores a small production bible on disk and compiles locked prompts
from it. No API keys. No cloud.

## Layout

```
<project>/
  bible.yaml          # canonical state
  refs/               # copied or linked stills
    <character-id>/
    <scene-id>/
  takes/              # optional take notes (generated)
```

## bible.yaml

```yaml
version: 1
title: Grad short
aspect: "9:16"
duration_hint: 75s
style: "cinematic, night classroom, cool fluorescent, Chinese campus"
characters:
  mei:
    name: 阿梅
    role: lead
    look: "20s Chinese woman, short black hair, navy hoodie, backpack"
    voice: "calm narrator-adjacent, soft Mandarin"
    do_not: ["change hair length", "add glasses", "smile at camera"]
    refs: ["refs/mei/front.png"]
scenes:
  s01:
    title: 夜教室
    setting: "empty university classroom at night, rows of desks, one open laptop"
    lighting: "cool overhead fluorescent, window city glow"
    camera: "slow push-in, 35mm, 9:16"
    cast: [mei]
    refs: []
takes:
  - id: t001
    scene: s01
    character: mei
    beat: "she sits, opens the laptop, does not look at camera"
    file: ""
    model: grok-imagine-video-1.5
    duration: 6
    notes: ""
```

## Commands

- `shotbible init [dir]`
- `shotbible set --title --aspect --style --duration-hint`
- `shotbible character add ID --name --look --ref PATH`
- `shotbible character rm ID`
- `shotbible scene add ID --title --setting --cast ID`
- `shotbible scene rm ID`
- `shotbible take add SCENE --beat TEXT [--file PATH] [--model NAME]`
- `shotbible take rm ID`
- `shotbible character show ID` / `scene show` / `take show`
- `shotbible prompt SCENE [-o [FILE]]`
- `shotbible prompt --all`
- `shotbible prompt-take TAKE [-o [FILE]]`
- `shotbible check [--strict] [--json]`
- `shotbible export [--format md|json]`
- `shotbible list [--json]`

## Prompt compiler rules

Always emit, in this order:

1. Identity lock (name, look, do_not)
2. Scene lock (setting, lighting, aspect)
3. Camera / duration
4. Beat / action
5. Negative constraints
6. "same character as reference images" if refs exist

Never invent wardrobe or location details that are not in the bible.
If `prompt SCENE` is called without `--beat`, use the latest take of that scene.
A scene with multiple `cast` members emits every character, not only the first.

## Check rules

- character referenced by scene/take must exist
- ref files must exist
- take.scene must exist
- warn if a lead / 主角 / 女主 / 男主 character has zero refs (`non-lead` is not a lead)
- warn if two characters have nearly identical `look` strings
- warn if two scenes share the same setting
- warn if a scene has no takes
- error if a take `file` is set but missing
- error if two takes share an id
- warn if a character is never used
- warn if a file under `refs/` is not listed in the bible
- `take --file` is copied into `takes/<id>/` like character refs
- New projects default to `9:16`

## Privacy

Do not scan or upload anything. Read only the project directory.
