# AGENTS.md

本仓库是 TeleAgent 技能集合：每个技能一个文件夹（见 `skills/`），仓库根提供面向人类的 `README.md`。

## 目录约定

- **调研报告**（`research` 技能产出）→ `docs/<skill>/research/`（如 `docs/knowledge-distill/research/`）
- **技能需求文档** → `docs/<skill>/requirements/`（如 `docs/knowledge-distill/requirements/`）
- **写技能需求 / 生成后复审技能** → 技能 `skills/shy-skill-suite`

## 提建议前先证伪

对代码或文档提改进建议（复审、评审、优化）时，每条建议都必须先跑一次"能否被推翻"的检查，并附上验证命令与结果；跑不了检查的只标「待验证」，不进建议列表。

- **先证伪，再提建议**：先问"哪条命令、哪段原文能最快推翻它？"，跑完再写。
- **分清事实与推断**：依据写"我看到 X"，不写"我认为 X"。
- **报告淘汰数**：写明"N 个候选，M 个通过，其余被证伪"，让筛选可见。

## 技能必须自包含

技能会被单独复制到 `~/.config/TeleAgent/skills/` 部署，`docs/` 不随行。因此**技能文件（`SKILL.md` / `scripts/` / `references/` / `assets/`）内只引用技能自身**（相对技能根的路径，如 `references/xxx.md`），**不引用仓库级 `docs/`**——否则对他人就是悬空指针。
