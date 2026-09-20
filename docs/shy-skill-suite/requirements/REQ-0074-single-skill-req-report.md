---
id: REQ-0074
title: 让 /shy-reqs 生成单技能、按类型和状态分组的可折叠需求报告
skill: shy-skill-suite
status: done
kind: refactor
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0072, REQ-0073]
---

# REQ-0074 让 /shy-reqs 生成单技能、按类型和状态分组的可折叠需求报告

## 问题与目标

`REQ-0072` 落地的 `/shy-reqs` 有三处不合约：

1. **范围错**：默认把**所有技能**的 REQ 都纳入统计。但 shy-skill-suite 是辅助技能开发的套件，用户**同一时间只看一个技能**——应只针对**单一技能**。
2. **结构不合**：现在是「按技能分组 + 现在能做什么/计划做什么」的能力视图。用户要的是**按 REQ 类型（kind）分组 → 再按状态（status）分组**，展开即见每条 REQ 的**白话说明**，点击看详情。
3. **白话来源没定**：REQ 的 `title` 偏标签（有时术语）、`## 问题与目标` 偏技术论证，都**不保证普通读者读得懂**。

**目标**：`/shy-reqs` 只服务**单一技能**；报告结构为 `kind → status → REQ`；inline 直接显示**白话一句话**，点击看详情（元数据 + 背景）；白话**在源头保证**（`title` 就是面向人的白话一句话，不新增字段）。

## 触发与分支

- 用户想"看这个技能做到哪了 / 这个技能的 REQ 情况"、`/shy-reqs <skill>`。
- 路由仍在 `lifecycle.md` 斜杠快捷表与 `SKILL.md` 资源区。

## 行为与步骤

1. **命令必填技能**：`/shy-reqs <skill> [--kind <kind>]`；报告**只含该技能**的 REQ。
2. **报告结构（三级）**：
   - 一级 **kind**（白话标签 + 计数）：新增功能 / 修复缺陷 / 重构 / 文档 / 清理 / 未分类；固定顺序 `feature → fix → refactor → docs → hygiene → unspecified`。
   - 二级 **status**（白话标签 + 计数，**默认折叠**）：草稿 / 待开工 / 进行中 / 已完成 / 已延后 / 不做。
   - 展开 status → **REQ 列表，每条一行 `REQ-NNNN + title`（title 即白话说明，直接可见，无需再点）**。
   - 点某条 REQ → 展开**详情**：元数据（类型 / 状态 / 生成日期 / 更新日期 / 轮次 / 依赖）+ `## 问题与目标` 首段（背景）。
   - kind 默认展开。
3. **报告完全由 REQ 文件推导**：读各 `REQ-NNNN-*.md` 的 frontmatter（id / title / kind / status / created / updated / iteration / blocked_by）与 `## 问题与目标` 首段；**不再需要 agent 写 `reports/reqs-view.json`**，也**不再有「现在能做什么 / 计划做什么」能力视图**。
4. **白话在源头**：`references/writing-requirements.md` 的 `title` 规范改为「**面向人的白话一句话**，说清这个 REQ 做什么；必要的技术词可保留，但以人话为主」；`问题与目标` 仍是技术论证（供开发者/agent，报告详情层展示）。**不新增 `plain`/`summary` 字段**（避免与 `title`、`问题与目标` 三重描述漂移）。**存量 REQ 的 title 逐条过一遍白话化**（术语重的订正，保留必要技术词）。
5. **报告文件**：每个技能**一份固定文件** `reports/<skill>-reqs.html`，每次统计**原地覆盖**；单文件自包含、无外部资源；默认自动打开（`--no-open` / `SHY_NO_OPEN` 关闭）。
6. **终端摘要**：`track_requirements.py --view overview --skill <skill>` 给一行计数摘要（`<skill>：新增功能 N / 修复缺陷 M / …`）。
7. `run_checks.py` 注册本 REQ 检查；`selftest.py` 更新 `render_reqs` 用例。

## 脚本与资源

- 改 `commands/shy-reqs.md`（必填技能名 + 结构说明）。
- 改 `scripts/render_reqs.py`：直接读 REQ 文件渲染 `kind → status → REQ` 三级结构；`--root` / `--skill`（必填）/ `--kind` / `--out` / `--no-open` / `--help`；输出 `<root>/reports/<skill>-reqs.html`。
- 改 `scripts/track_requirements.py`（`--view overview` 支持 `--skill` 聚焦单技能；保持排期职责）。
- 改 `references/writing-requirements.md`（`title` 规范：面向人的白话一句话）。
- 改 `references/lifecycle.md`（斜杠快捷表 `/shy-reqs` 说明：单技能）。
- 改 `SKILL.md`（资源区 `/shy-reqs` 说明）。
- 改 `scripts/run_checks.py`（注册 `req0074-*`；移除/订正 `REQ-0072` 中已失效的 check）。
- 改 `scripts/selftest.py`。
- 存量 REQ：逐条订正 `title`（两技能全部）。

## 降级与边界

- **不做能力视图**：`kind=feature + status=done` ≠ 当前能力（能力会被后续 `fix`/`refactor` 改掉）——本报告回答"这个技能的 REQ 情况"，不回答"现在能做什么"。
- 无某类 kind / status 时不显示该分组。
- `问题与目标` 缺失时详情只显示元数据（正常 REQ 都应有，属异常降级）。
- 不改复审报告 `render_report.py`；不落 `reqs-view.json`。
- 报告面向**普通读者**：inline 用白话 `title`，不出现未解释的内部术语或裸 `file:line`。

## 验收标准

- [x] `/shy-reqs <skill>` 必填技能名；报告只含该技能的 REQ — `check:req0074-single-skill`（缺 `--skill` rc=2；demo 报告不含 other 技能的 REQ）
- [x] 报告三级结构：kind（白话标签 + 计数）→ status（白话标签 + 计数，折叠）→ REQ 列表（`REQ-NNNN + title`）→ 点开详情（元数据 + `问题与目标` 首段） — `check:req0074-structure`（kind 顺序 feature→fix→docs 成立、kind 默认展开）
- [x] 不再有「现在能做什么 / 计划做什么」能力视图；渲染不再依赖 `reports/reqs-view.json` — `check:req0074-no-capability-view`（源码与输出均无命中）
- [x] 输出固定文件 `reports/<skill>-reqs.html`，单文件自包含（无外部资源）、原地覆盖 — `check:req0074-report-file`（二次统计覆盖旧内容、无 http/<link/<script）
- [x] `writing-requirements.md` 的 `title` 规范为「面向人的白话一句话」 — `check:req0074-title-convention`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0 — `check:skill-validate-ok` / `check:skill-selftest`
- [x] （语义）存量 REQ 的 `title` 已逐条过白话化（术语重的已订正、保留必要技术词）；由复审人工判读 — 两技能 78 条 title 全部重写为白话一句话，H1 同步（`title`==H1，0 处不一致）；保留 `description` / `run_checks.py` / `SKILL.md` / `converged` 等必要技术词；待复审人工判读
- [x] （语义）真跑 `/shy-reqs shy-skill-suite` 产出单技能报告，层级 / 折叠 / 白话 inline 均符合；由一次真跑 + 人工判读判定 — 已真跑：`track_requirements.py --view overview --skill shy-skill-suite` → 一行白话计数；`render_reqs.py --root . --skill shy-skill-suite --no-open` → `reports/shy-skill-suite-reqs.html`（74 条、`<details open>` 5 个 kind、`<details>` 90、无外部资源，rc=0）；待复审人工判读

## 范围外

- 不做能力视图（"现在能做什么"）。
- 不新增 `plain`/`summary` 字段。
- 不做跨技能汇总报告。
- 不做报告历史归档（每技能一份固定文件、原地覆盖）。
- 不改 `问题与目标` 的技术论证风格。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现）；取代 REQ-0072 的报告契约 | — | 待实现 |
| 2 | 2026-09-20 | 实现：`render_reqs.py` 大改为单技能、直接读 REQ 文件渲染 `kind → status → REQ` 三级折叠报告（去掉 `reqs-view.json` 与能力视图，输出 `reports/<skill>-reqs.html`）；`track_requirements.py --view overview --skill` 附一行白话计数；`commands/shy-reqs.md` 必填技能；`writing-requirements.md` 的 `title` 规范改为「面向人的白话一句话」；`lifecycle.md`/`SKILL.md` 路由改单技能；`run_checks.py` 注册 5 条 `req0074-*` 并把 2 条失效的 `req0072-*` 改指向新契约；`selftest.py` 更新 `render_reqs` 用例（成功 + 缺参 / 技能不存在 / 非法 root）；两技能 78 条 REQ 的 `title` 白话化并同步 H1 | `validate_skill.py` → ok；`run_checks.py` 59/59（含 `req0074-*` 5/5）；`selftest.py` 36/36；真跑 `render_reqs.py --root . --skill shy-skill-suite --no-open` → `reports/shy-skill-suite-reqs.html`（74 REQ、自包含）；`track_requirements.py --root .` → `status: ok` | done |

## 备注 / 待办

逼问：已过 3 轮——frontier：A（范围：单技能必填）+ B′（结构：kind→status→REQ，inline 白话、点击看详情）+ C（替换能力视图）+ D″（`title` 源头白话、不新增字段）+ E（每技能一份固定文件原地覆盖）；用户逐轮确认。

- 取代：`REQ-0072` 的报告契约（范围 / 结构 / 白话来源 / 报告文件）由本 REQ 重新定义；`REQ-0072` 加 `superseded_by: REQ-0074`。`REQ-0073`（删 `/shy-apply`）不受影响。
- 依据：2026-09-20 用户反馈「报告不是我想要的：应只针对单一技能；按 kind 分类、kind 下按 status 分类、可折叠、每条 REQ 带白话解释；白话在源头写还是新增字段？」。
