# shotbible

[![CI](https://github.com/hc-ui/shotbible/actions/workflows/ci.yml/badge.svg)](https://github.com/hc-ui/shotbible/actions/workflows/ci.yml)

面向 AI 图/视频制作的本地连贯性圣经（continuity bible）。

AI 视频工具会在镜次之间忘掉脸、服装和光线。shotbible 把一份小型制作圣经存在磁盘上，并从中编译锁定提示词。

**仅本地。无需 API key。不上云。不会上传任何内容。**

[English](README.md)

## 安装

从克隆的仓库安装（推荐）：

```bash
pip install -e .
# 或：python -m shotbible --help
```

开发 / 测试：

```bash
pip install -e ".[dev]"
pytest
```

PyPI 包名为 `shotbible`（发布后可用 `pip install shotbible`）。

## 20 秒上手

```bash
shotbible init my-short
cd my-short
shotbible character add mei --name "阿梅" --look "20s Chinese woman, short black hair, navy hoodie"
shotbible scene add s01 --title "夜教室" --setting "empty classroom at night" --cast mei
shotbible take add s01 --beat "she opens the laptop, does not look at camera"
shotbible prompt s01 --character mei
shotbible check
```

现成的 9:16 校园夜戏圣经见 [`examples/campus-night/bible.yaml`](examples/campus-night/bible.yaml)。

## 命令

| 命令 | 作用 |
|------|------|
| `init [dir]` | 创建 `bible.yaml`、`refs/`、`takes/` |
| `set --title --aspect --style --duration-hint` | 改项目标题 / 画幅 / 风格 |
| `character add ID --name --look [--ref PATH]` | 锁定角色（`--ref` 会复制到 `refs/`） |
| `character rm ID` | 删除角色（仍被引用则拒绝） |
| `scene add ID --title --setting --cast ID` | 锁定场景与出场角色 |
| `scene rm ID` | 删除场景（仍有 take 则拒绝） |
| `take add SCENE --beat TEXT [--file PATH] [--model NAME]` | 记录一条 take / beat |
| `take rm ID` | 删除一条 take |
| `prompt SCENE [--beat TEXT] [--character ID] [--kind image\|video]` | 编译锁定提示词 |
| `prompt-take TAKE` | 按已存 take 编译锁定提示词 |
| `check` | 检查缺失参考图、未知角色、空场景 |
| `export [--format md\|json]` | 导出圣经 |
| `list` | 列出角色、场景、takes |

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

编译器固定输出：身份锁定 → 场景锁定 → 机位 → beat → 负面约束。不会编造圣经里没有的服装或地点。

## 许可证

MIT
