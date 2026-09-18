---
id: REQ-0020
title: opencode 斜杠命令集 + 调用方式落地（model-invoked 技能 + user 侧 command）
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-16
updated: 2026-09-17
blocked_by: [REQ-0018, REQ-0019]
related: [REQ-0011, REQ-0010]
---

# REQ-0020 opencode 斜杠命令集 + 调用方式落地

## 问题与目标

用户要"能手动触发的 `/` 快捷方式"，并要把 mattpocock 的 **model-invoked / user-invoked** 机制引入 shy。但 shy 的 `writing-skills.md §2` 只覆盖了 Claude Code 的字段，且对当前客户端（opencode）**不成立**：

- 证据（opencode 官方文档 `opencode.ai/docs/skills`）：skill frontmatter「Unknown frontmatter fields are **ignored**」——只认 `name`/`description`/`license`/`compatibility`/`metadata`。**`disable-model-invocation` 在 opencode 不生效**（本机 `~/.agents/skills` 下 `retro`/`handoff` 等虽写了该字段，仍以带 description 的 model-invoked 技能被列出）。
- 证据（`opencode.ai/docs/commands`）：opencode 的 user 侧入口是 **commands**——`~/.config/opencode/commands/<name>.md`，frontmatter `description/agent/model`，body 为模板（`$ARGUMENTS`/`$1`/`` !`shell` ``/`@file`），调用即 `/name`。
- `REQ-0010` 备注已论证：shy **不能**改成 user-invoked（会丢"AI 生成/改写技能后自动复审"），故主体保持 model-invoked。

目标：① 把 mattpocock 的调用方式机制**在 opencode 语义下写准**；② 为"必须人工触发"的动作提供 `/shy-*` 斜杠命令入口。

## 触发与分支

- `lifecycle.md` 阶段 2 按 `writing-skills.md §2` 选调用方式时。
- 用户说"这个技能要不要手动调用 / 模型别自动触发 / 给我个斜杠命令"。

## 行为与步骤

1. 新增技能内 `commands/` 目录（当时 5 个可复制模板，body 指向对应分支；`REQ-0022` 后为 4 个）：
   - `shy-grill.md` → `references/grilling.md`（逼问；`$ARGUMENTS` 传技能名/主题）。
   - `shy-review.md` → `references/reviewing-skills.md`（只复审，跑完走 `REQ-0018` 呈现门禁）。
   - `shy-eval.md` → `references/running-evals.md` + `scripts/render_report.py`（评测并出 HTML）。
   - `shy-apply.md` → `REQ-0018` 的落盘动作（把 `findings.json` 落成 REQ / 勾选验收 / 追加迭代记录）。
   - `shy-next.md` → `scripts/track_requirements.py`（列 frontier）。
   每个模板 frontmatter 只写 `description`（+ 必要时 `agent`），body 是"加载 shy-skill-suite 技能并进入 <分支>，参数：$ARGUMENTS"。
2. `references/writing-skills.md §2` 补「opencode 路线」：技能一律 model-invoked（description 驱动）；**user 侧快捷 = 客户端 command**；给出 `~/.config/opencode/commands/<name>.md` 位置；显式注明「`disable-model-invocation` 是 Claude Code 字段，opencode 忽略它」。
3. `references/lifecycle.md` 加「斜杠快捷」小节：五个命令各进入哪个分支；并说明 `commands/` 是**分发模板**，需复制到客户端 command 目录（技能无法向客户端注入 command）。
4. `SKILL.md` 资源列表加 `commands/`。
5. 自包含：模板只引用技能自身相对路径；"复制到 `~/.config/opencode/commands/`"是安装说明，不是技能运行时依赖。

## 脚本与资源

- 新增 `commands/shy-{grill,review,eval,apply,next}.md`。
- 改 `references/writing-skills.md`（§2 补 opencode 路线）、`references/lifecycle.md`（斜杠快捷小节）、`SKILL.md`（资源清单）。

## 降级与边界

- command 是**客户端配置**，不在技能包内自动生效；技能只能提供模板 + 说明。这条限制写进 `writing-skills.md §2`，不静默。
- TeleAgent 的 slash 机制**未核实**：本 REQ 只承诺 opencode；TeleAgent 留待确认后另开 REQ（标「待验证」）。
- `commands/` 不属于 `agentskills.io` 标准结构，但 `validate_skill.py` 不校验该目录，不影响 `ok`。
- 不改 shy 的 `description`（逼问触发词是 `REQ-0021`）。

## 验收标准

- [x] `commands/` 下 **4** 个模板存在（`shy-grill/review/apply/next.md`），各含 `description` 且 body 引用技能内正确相对路径（`references/*.md`、`scripts/*.py`）。（`shy-eval` 已被 `REQ-0022` 删除；原写 5 个，2026-09-17 复审订正。） — （episode）
- [x] `/shy-apply` 的模板明确写"仅在用户显式确认后执行——没有这一步就停在呈现门禁"，与 `REQ-0018` 一致。 — （episode）
- [x] `writing-skills.md §2` 含 opencode command 路线，且含"opencode 忽略 `disable-model-invocation`"这一句。 — （episode）
- [x] `lifecycle.md` 的「斜杠快捷」小节列出 **4** 个命令与对应分支；`SKILL.md` 资源清单含 `commands/`。（原写 5 个，2026-09-17 复审订正。） — （episode）
- [x] 技能自包含：`commands/*.md` 无仓库级外部路径引用（grep `docs/`、绝对路径 → 0）；`validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。 — `check:skill-validate-ok`
- [ ] **待验证**：复制到 `~/.config/opencode/commands/` 后 `/shy-next` 真跑列出 frontier。按用户决策**只交模板、不碰本机配置**，故未安装、未取得真实轨迹；命令 body 只是 prompt 模板，其核心动作（`track_requirements.py --root .`）已单独验证通过。 — （episode）

## 范围外

- 不做 TeleAgent 命令（待核实另开）。
- 不把 shy 改成 user-invoked；不动 `description`（`REQ-0021`）。
- 不做跨平台转换（不引入 skill-forge 的 `convert_skill` 机制）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（用户诉求：引入调用方式机制 + `/` 快捷） | — | 待开工 |
| 2 | 2026-09-16 | 新增 `commands/shy-{grill,review,eval,apply,next}.md`；`writing-skills.md §2` 补 opencode command 路线 + "忽略 `disable-model-invocation`"；`lifecycle.md` 加「斜杠快捷」小节；`SKILL.md` 资源清单加 `commands/` | 4 模板齐（原 5，`REQ-0022` 删了 `shy-eval`；2026-09-17 复审订正）、含 description 与分支指针；自包含 grep 0；`validate_skill` ok；`track_requirements --root .` 已单独验证。**命令安装后真跑：待验证**（按用户决策未碰本机配置） | 收敛（done，附 1 条待验证） |

## 备注 / 待办

- 来源：2026-09-16 用户诉求；决策：先落地 **opencode** + 加域限定触发词。
- **命名决策（用户确认）**：命令名带横线 `/shy-<分支>`（`/shy-grill` 等），**不支持** `/shy <分支>` 空格式。因 opencode **以文件名作命令名**，每个分支一个文件；无法用单文件响应多个 `/shy-xxx`。
- **命令集被 `REQ-0022` 取代**：原 5 个命令合并为 4 个（删 `/shy-eval`，评测并入 `/shy-review`）。验收标准里的 5 已于 2026-09-17 复审订正为 4（`REQ-0026`）。
- 与 `REQ-0011` 不冲突：`REQ-0011` 把 Claude Code 字段写进 §2 并放进校验器白名单；本 REQ 补的是 **opencode 的 command 路线**，仍只写在 §2 一处（单一事实源）。
- opencode 文档依据：<https://opencode.ai/docs/skills>、<https://opencode.ai/docs/commands>（access date 2026-09-16）。
