---
id: REQ-0076
title: 开发新技能时一键起骨架（/shy-start：技能包 + 起手需求 + .gitignore）
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0001, REQ-0036, REQ-0037]
---

# REQ-0076 技能开发骨架

## 问题与目标

**现状缺口**：`scaffold_skill.py` 只生成 `skills/<name>/SKILL.md`（符合"最小结构"最佳实践，见 `docs/shy-skill-suite/research/skill-directory-structure.md`），但**没有"技能开发项目"那一层**——`docs/<name>/requirements/`（起手需求）与 `.gitignore` 条目要各自手工建；且没有一个"开始开发新技能"的显式入口（用户只能靠自然语言触发）。

**目标**：给用户一个"**开始开发新技能**"的入口（自然语言 + `/shy-start`），一次把**开发骨架**起好：技能包 + 起手需求 + `.gitignore` 条目。**技能包子目录仍按需创建**（不预建空目录）。

**依据（调研）**：技能包最小结构 = 一个目录 + 一个 `SKILL.md`；`scripts/` `references/` `assets/` 可选、**按需**创建（`agentskills.io/specification`）；开发项目骨架 = 技能包 + 同级 `<skill>-workspace/`（一手来源）；`docs/<name>/{requirements,research,...}` 是本仓库自定层（无一手来源）。详见 `docs/shy-skill-suite/research/skill-directory-structure.md`。

## 触发与分支

**两种触发方式，进同一流程**：

- **自然语言**：用户说"我想创建一个技能实现 xxx" → 技能 **model-invoked**（`description` 已含"新建或修改一个技能（含搭骨架 / 脚手架）"）→ 进 lifecycle。
- **显式命令**：`/shy-start [<skill>]`（user-invoked）→ 进同一流程。

两者都走：**逼问 → 落需求 → 起骨架 → Gate**。

## 行为与步骤

1. **命令 `/shy-start [<skill>]`**（user-invoked）：技能名**可选**——给了就直接进入；没给就先问用户要（**不默认**）。
2. **同一流程（不另立一套）**：
   - **阶段 0 逼问**（`grilling.md`：设计树 + frontier，每问附建议答案）；
   - **阶段 1 落需求**：写 `docs/<name>/requirements/REQ-0001-<slug>.md`（agent 按 `writing-requirements.md`，把逼问结果落进去，`status: ready`）；
   - **阶段 2 起骨架**：跑 `scaffold_skill.py`（见下），再按 `writing-skills.md` 写 `SKILL.md`，收尾跑 Gate。
3. **`scaffold_skill.py` 增强**：新增"开发层"选项（如 `--project`），一次建齐：
   - `skills/<name>/SKILL.md`（现状）；
   - `docs/<name>/requirements/`（目录）；
   - 追加 `.gitignore` 条目（`*-workspace/`、`reports/`、`__pycache__/`）——**仅当尚不存在时**追加，不重复、不覆盖已有内容。
   - **不预建** `scripts/` / `references/` / `assets/` / `evals/` / `commands/` 空目录（按需创建）；**不写 REQ 正文**（REQ 由阶段 1 的 agent 产出）。
   - 保持幂等：目标已存在且未 `--force` → `skipped`；`--force` 覆盖 `SKILL.md` 前先备份 `.bak`。
4. **`lifecycle.md`**：斜杠快捷表加 `/shy-start`；阶段 2 说明 scaffold 可建开发层（技能包 + `docs/<name>/requirements/` + `.gitignore`），REQ 正文由阶段 1 产生。
5. **`SKILL.md`**：资源区 commands 列表加 `shy-start`。
6. `run_checks.py` 注册本 REQ 检查；`selftest.py` 加 scaffold 新行为用例（成功 + 幂等/失败路径）。

## 脚本与资源

- 新增 `commands/shy-start.md`（加载技能 + `$ARGUMENTS` + 流程说明）。
- 改 `scripts/scaffold_skill.py`（新增开发层选项；`--help` 补简述 / 参数 / 示例 / 退出码）。
- 改 `references/lifecycle.md`（斜杠快捷表 + 阶段 2）、`SKILL.md`（commands 列表）。
- 改 `scripts/run_checks.py`、`scripts/selftest.py`。

## 降级与边界

- **不预建空的技能子目录**（最佳实践：按需创建）——这是刻意的，不是遗漏。
- **不生成 `AGENTS.md` / `README.md`**（只补 `.gitignore` 条目）。
- 技能包最小结构不变（`SKILL.md` 必需，其余可选）。
- 不自动跑 eval、不自动评审（与 lifecycle 一致）。
- 命令与自然语言**必须进同一流程**，不得分叉。

## 验收标准

- [x] `commands/shy-start.md` 存在；`/shy-start [<skill>]` 技能名可选，进"逼问 → 落需求 → 起骨架"同一流程 — `check:req0076-start-command`
- [x] `scaffold_skill.py` 支持开发层：建 `skills/<name>/SKILL.md` + `docs/<name>/requirements/` + 追加 `.gitignore` 条目；**不预建** scripts/references/assets/evals/commands 空目录 — `check:req0076-scaffold-project`
- [x] `scaffold_skill.py --help` 含新参数（简述 / 参数 / 示例 / 退出码） — `check:req0076-help`
- [x] 幂等：目标已存在且未 `--force` → `skipped`；`--force` 覆盖 `SKILL.md` 前先备份 `.bak`；`.gitignore` 不重复追加 — `check:req0076-idempotent`
- [x] `references/lifecycle.md` 斜杠快捷表含 `/shy-start`；阶段 2 说明开发层骨架 — `check:req0076-lifecycle`
- [x] `SKILL.md` 资源区 commands 列表含 `shy-start` — `check:req0076-skill-resources`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0 — `check:skill-validate-ok` / `check:skill-selftest`
- [x] （语义）自然语言"我想创建一个技能实现 xxx"与 `/shy-start` 进**同一流程**且都先逼问；由复审人工判读 — 已实现：两入口都指向 `references/lifecycle.md` 阶段 0→1→2，`commands/shy-start.md` 明写"与自然语言触发完全一致，不分叉"

## 范围外

- 不预建空的技能子目录（按需创建）。
- 不生成 `AGENTS.md` / `README.md` 模板。
- 不做技能打包 / 部署到 agent 技能目录（属 `REQ-0036` / `REQ-0037`）。
- 不自动跑 eval / 不自动评审。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现） | — | 待实现 |
| 2 | 2026-09-20 | 新增 `commands/shy-start.md`；`scaffold_skill.py` 加 `--project` 开发层（技能包 + `docs/<name>/requirements/` + `.gitignore` 仅缺失追加，opt-in 不改默认）；`lifecycle.md` 斜杠表 + 阶段 2；`SKILL.md` 资源区；`run_checks.py` 注册 `req0076-*`；`selftest.py` 加 `--project` 成功 / 幂等 / 非法名用例 | `run_checks.py` 70 条全绿；`validate_skill.py` → ok；`selftest.py` 39/39；`track_requirements.py` → ok | 收敛（done） |

## 备注 / 待办

逼问：已过 2 轮——frontier：A（骨架范围：技能包 + 开发层）+ B（子目录按需）+ C（起手 REQ 随骨架）+ D′（命令名 `/shy-start`）+ E（两种触发方式、同一流程）+ F（技能名可选）；用户逐轮确认。

- 来源：2026-09-20 用户提案「开发技能时应在当前目录建技能开发目录骨架；查最佳实践后直接帮用户建」。
- 调研：`docs/shy-skill-suite/research/skill-directory-structure.md`。
- 关联：`REQ-0001`（轻量脚手架，本 REQ 在其上加"开发层"）；`REQ-0036`/`REQ-0037`（打包 / 分发，本 REQ 不做）。
