---
id: REQ-0024
title: 为 shy-skill-suite 取真实行为证据（触发率 + with/baseline delta）
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: [REQ-0022]
related: [REQ-0010, REQ-0019, REQ-0021]
---

# REQ-0024 为 shy-skill-suite 取真实行为证据

## 问题与目标

2026-09-16 复审行为轴 **P1**：`shy-skill-suite` 没有任何真实行为证据——触发（`REQ-0021` 的逼问触发词、`REQ-0010` 的收窄）只有描述层面的判断；整技能也没有 with_skill vs baseline 的 delta。按 `reviewing-skills.md` Step 2「只有 delta 才算证据」，当前只能说技能"没坏"，**不能说"有效"**。

证据（复审时）：
- 本会话 `available_skills` 不含 `shy-skill-suite`（安装晚于会话启动）→ 无法取触发轨迹。
- `REQ-0020` / `REQ-0021` 的验收已自标「待验证」。

目标：部署后取到**真实轨迹**：触发率（正例 + near-miss）与至少一条 with/baseline 对照。

## 触发与分支

- 复审 Step 1（触发审查）/ Step 2（有效性审查）。
- 用户说"实测一下 / 跑一遍看触发准不准"。

## 行为与步骤

1. 重启 opencode 后（技能与命令已装入 `~/.config/opencode/`），用合并入口 `/shy-review` 对 `shy-skill-suite` 自己跑：
   - **触发**：`scripts/optimize_description.py <skill_dir> --eval-set evals/evals.json --runner opencode --detect shy-skill-suite` 取真实触发率；正例（逼问 / 复审 / 写需求）+ near-miss（"澄清这段代码要做什么"）。
   - **对照**：2–3 条真实 prompt，各跑 with_skill 与 baseline（无技能），记录 pass_rate / token / 耗时；`aggregate_benchmark.py` 聚合。
2. 把触发率与 delta 写入 `<skill>-workspace/` 的 `findings.json` / `benchmark.json`，并由 `render_report.py` 出报告。
3. 回写本 REQ：勾选验收、追加迭代记录。

## 脚本与资源

- 用 `scripts/generate_eval_set.py`（起手集，需复核）、`optimize_description.py --runner opencode`、`agent_runner.py`、`aggregate_benchmark.py`、`render_report.py`。
- 工作区：`skills/shy-skill-suite-workspace/`。
- 不改技能文件（除非证据指向要改，另开 REQ）。

## 降级与边界

- 无可用 agent runner（opencode 非交互不可用）→ 标「待验证」，**不伪造**触发率/delta。
- 对照的 baseline「无技能」在本机指"不加载 shy-skill-suite"；须确保 baseline 真没加载（`subagents.md` 的 executor 规则）。
- 评测集是启发式起手集，须人工/agent 复核后再用其结论。

## 验收标准

- [ ] 触发正例有真实轨迹（命令 + 输出 + 命中技能的证据）。
- [ ] near-miss 有真实轨迹（命令 + 输出 + 未落盘/未进入技能流程）。
- [ ] 至少 1 条 `benchmark.json` 含 with_skill vs baseline 的 `pass_rate` / `token_ratio` / `time_ratio`。
- [ ] `<skill>-workspace/report.html` 的评测区非"无数据"。
- [ ] 结论（触发率、delta、是否有效）写入本 REQ 迭代记录；跑不了的项明确标「待验证」。

## 范围外

- 不改命令 / 脚本 / 文档（发现要改的另开 REQ）。
- 不做跨平台评测。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审行为轴 P1） | — | 待开工 |

## 备注 / 待办

- 来源：2026-09-16 复审 findings #1（行为轴 P1）。
- 依赖 `REQ-0022`：用合并后的单一入口跑，避免 review/eval 两套。
- 这是**取证**任务，不是改代码；产出是 `findings.json` / `benchmark.json` / 报告。
