# AGENTS.md

本仓库是 TeleAgent 技能集合：每个技能一个文件夹（见 `skills/`），仓库根提供面向人类的 `README.md`。

## 目录约定

- **调研报告**（`research` 技能产出）→ `docs/research/`
- **技能需求文档** → `docs/requirements/`（先读 `docs/requirements/README.md` 的命名与写作规范，按其模板落盘）

## 技能必须自包含

技能会被单独复制到 `~/.config/TeleAgent/skills/` 部署，`docs/` 不随行。因此**技能文件（`SKILL.md` / `scripts/` / `references/` / `assets/`）内只引用技能自身**（相对技能根的路径，如 `references/xxx.md`），**不引用仓库级 `docs/`**——否则对他人就是悬空指针。
