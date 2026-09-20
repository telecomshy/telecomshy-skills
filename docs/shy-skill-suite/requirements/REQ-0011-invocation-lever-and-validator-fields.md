---
id: REQ-0011
title: 把「调用方式」写成可执行的抓手，并给校验器加扩展字段
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0002, REQ-0009]
---

# REQ-0011 把「调用方式」写成可执行的抓手，并给校验器加扩展字段

## 问题与目标

复审（2026-09-16，标准轴 P1）实测：`writing-skills.md` §2 的 lever **不可执行**，且与自家校验器**互相矛盾**。

- 证据 1：`writing-skills.md` §2 要求区分 user-invoked / model-invoked，但全技能 `grep disable-model-invocation|argument-hint` → **0 命中**——lever 从不给出落地字段名。
- 证据 2：本机 42 个已部署技能里，**22 个**用 `disable-model-invocation: true`、**4 个**用 `argument-hint` 表达该选择（共 23 个不同技能）。
- 证据 3：`validate_skill.py` 的 `ALLOWED_FIELDS` 不含这两项 → 照 §2 做出来的技能会被自家校验器判 error。实测 `validate_skill.py` 对 `retro` / `handoff` / `ask-matt` / `to-spec` 全部 `status: error`（"frontmatter 顶层多余字段"）。

目标：§2 写明落地字段；校验器把这两项客户端扩展字段列入允许集，使"选调用方式"这件事可执行、且不与校验器打架。

## 触发与分支

- `lifecycle.md` 阶段 2 按 `writing-skills.md` §2 选调用方式时。
- 用户说"这技能要不要手动调用 / user-invoked / 模型别自动触发它"。
- 跑 `validate_skill.py` 校验任何使用这两项字段的技能时。

## 行为与步骤

1. `references/writing-skills.md` §2 补一段"落地"：user-invoked 写 `disable-model-invocation: true`；需要参数提示时再写 `argument-hint: "<提示>"`；并注明二者是**客户端扩展字段**（不在 `agentskills.io` 基础字段集内），`validate_skill.py` 已列入允许集。
2. `scripts/validate_skill.py`：把字段集拆成
   - `BASE_FIELDS = {name, description, license, compatibility, metadata, allowed-tools}`（对齐 `agentskills.io`）
   - `EXTENSION_FIELDS = {disable-model-invocation, argument-hint}`（客户端扩展；TeleAgent 的 `name_cn` / `description_cn` / `create_source` 另由 `REQ-0070` 加入）
   - `ALLOWED_FIELDS = BASE_FIELDS | EXTENSION_FIELDS`
   并同步更新模块 docstring 里"顶层只允许……"那句。
3. `docs/shy-skill-suite/requirements/REQ-0002-skill-validator.md` 的「备注 / 待办」加一行：字段集已由本 REQ 扩展，以本 REQ 为准。
4. 不新增文件、不改其它脚本。

## 脚本与资源

- 改 `references/writing-skills.md`（§2 加"落地"）、`scripts/validate_skill.py`（字段集拆分 + docstring）。
- 改 `docs/shy-skill-suite/requirements/REQ-0002-skill-validator.md`（备注加一行）。

## 降级与边界

- 这是**有意放宽**（相对 `agentskills.io` 基础字段集），不是收紧：目标客户端是 opencode / Claude Code，其 `SKILL.md` 实际使用这两项。`REQ-0002` 的"额外规则为有意收紧"结论不变——本项是新增的"有意放宽"，在 `BASE_FIELDS` / `EXTENSION_FIELDS` 拆分里显式可见。
- 只加这两项；不引入任意未知字段的放行（`metadata` 仍整体放行，行为不变）。
- 不校验字段**取值**（如 `disable-model-invocation` 必须是布尔）——保持"只查结构与规范"的定位。

## 验收标准

- [x] `validate_skill.py` 对 `skills/shy-skill-suite` → `status: ok`、退出码 0（回归）。 — `check:skill-validate-ok`
- [x] `validate_skill.py` 对含 `disable-model-invocation: true` 的技能（`retro`）→ `status: ok`、退出码 0。 — `check:skill-validate-ok`
- [x] `validate_skill.py` 对含 `argument-hint` 的技能（`handoff`）→ `status: ok`、退出码 0。 — `check:skill-validate-ok`
- [x] `validate_skill.py` 对含**未列入**字段（顶层 `bogus_field`）的技能 → 仍报"多余字段"、退出码 1（未放宽过头）。 — `check:validate-rejects-bad`（原示例 `name_cn` 已由 `REQ-0070` 放行，改用中性未知字段）
- [x] 全量回归：对 `~/.agents/skills` 下 42 个已部署技能跑一遍 → **41 ok / 1 error**；改动前（`git stash` 回退本文件后实测）为 **20 ok / 22 error**。唯一残留 error 是 `setup-ts-deep-modules` 的悬空引用 `./src/packages/README.md`，与本改动无关。 — （episode）
- [x] `validate_skill.py` 源码中 `disable-model-invocation` 与 `argument-hint` 出现在 `EXTENSION_FIELDS`；`BASE_FIELDS` 与 `agentskills.io` 基础集一致（对照 `quick_validate.py:42` 的 `ALLOWED_PROPERTIES`）。 — （语义）
- [x] `references/writing-skills.md` §2 含 `disable-model-invocation` 与 `argument-hint` 两个字段名。 — （episode）
- [x] 技能自包含：改动只引用技能自身与仓库 `docs/` 下的 REQ 文档，无新增外部引用。 — （episode）

## 范围外

- 不校验扩展字段的取值合法性；不新增脚本；不做跨平台转换；不改其它 `references/`。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P1）；`writing-skills.md` §2 补落地字段；`validate_skill.py` 字段集拆 `BASE_FIELDS` / `EXTENSION_FIELDS` | 8/8 验收通过；已部署技能 20 ok/22 error → 41 ok/1 error（残留 error 与本改动无关） | 收敛（done） |
| 2 | 2026-09-19 | `REQ-0070`：`EXTENSION_FIELDS` 追加 TeleAgent 扩展字段；验收的未知字段示例由 `name_cn` 改为 `bogus_field` | `check:validate-rejects-bad` 绿；`knowledge-distill` → `status: ok` | done |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P1。
- 与 `REQ-0009` 不冲突：`REQ-0009` 把 lever **定义**收敛到 `writing-skills.md`；本 REQ 给 §2 补的是**落地字段**，仍只写在这一处（单一事实源）。
