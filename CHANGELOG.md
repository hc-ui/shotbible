# Changelog

## 0.1.1 — 2026-08-13

- `check` no longer treats `non-lead` as a lead role
- Two reference files with the same name no longer overwrite each other
- `-C` / explicit project path no longer walks up to a parent bible
- `take --duration` rejects 0 and negatives; YAML `6s` is accepted
- `set`, `character rm`, `scene rm`, `take rm`
- `check` reports missing take files and duplicate take ids
- `init` writes a starter `.gitignore`
- Load `bible.yaml` directly; invalid YAML/duration become store errors
- `prompt SCENE` without `--beat` uses the latest take
- Character / scene / take ids cannot be path fragments
- CI includes Python 3.13

## 0.1.0 — 2026-08-13

- First release: local `bible.yaml` for characters, scenes, and takes
- Compile locked image/video prompts from the bible
- `check` for missing refs, unknown cast, empty looks, and similar looks
- Export markdown or JSON
- CLI works on Windows and Linux; no API keys
