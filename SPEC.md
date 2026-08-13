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
- `shotbible character add ID --name --look --ref PATH`
- `shotbible scene add ID --title --setting --cast ID`
- `shotbible take add SCENE --beat TEXT [--file PATH] [--model NAME]`
- `shotbible prompt SCENE [--beat TEXT] [--character ID] [--kind image|video]`
- `shotbible check`
- `shotbible export [--format md|json]`
- `shotbible list`

## Prompt compiler rules

Always emit, in this order:

1. Identity lock (name, look, do_not)
2. Scene lock (setting, lighting, aspect)
3. Camera / duration
4. Beat / action
5. Negative constraints
6. "same character as reference images" if refs exist

Never invent wardrobe or location details that are not in the bible.

## Check rules

- character referenced by scene/take must exist
- ref files must exist
- take.scene must exist
- warn if a lead character has zero refs
- warn if two characters have nearly identical `look` strings
- warn if a scene has no takes

## Privacy

Do not scan or upload anything. Read only the project directory.
