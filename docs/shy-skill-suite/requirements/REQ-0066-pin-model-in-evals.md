---
id: REQ-0066
title: 真跑评测必须钉模型（CLI 默认模型不可控）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0047, REQ-0063, REQ-0065]
---

# REQ-0066 真跑评测必须钉模型

## 问题与目标

2026-09-19 实测：嵌套 `opencode run "{prompt}"` 的**默认模型解析不可控**——会话记录 `model=None`，实际落到免费模型（`jev-1.13-free`），表现为循环、超时、**不加载技能**；一批 6 条聚焦用例因此全 0 作废。桌面所选模型**不会**传播给 CLI（桌面在 `deepseek/deepseek-flash`，CLI 却是另一套解析）。

反证：显式 `opencode run --model deepseek/deepseek-flash "{prompt}"` → 必触发用例**秒级命中**（输出含 `Skill "shy-skill-suite"`）。

目标：把"钉模型"写成真跑评测的硬要求——命令模板带 `--model <provider>/<id>`，且把所用模型写进报告 / 迭代记录，保证结论可复现。

## 触发与分支

- `running-evals.md` 的一切真跑评测（opencode / teleagent / cmd）。
- 用户说"同一描述两次结果不一样 / 评测怎么又变了"。

## 行为与步骤

1. `references/running-evals.md`：runner 适配节加"**必须钉模型**"要求与命令形态；说明默认模型解析不可控的实测现象。
2. `scripts/agent_runner.py` docstring/`--help`：提示"不钉 `--model` 时结果不可复现"（不改默认命令模板，模型是环境相关，不能硬编码进技能）。
3. 评测报告 / REQ 迭代记录写明：所用 runner、模型 ID、超时。

## 脚本与资源

- 改 `references/running-evals.md`、`scripts/agent_runner.py`（仅文案）。
- 不改默认命令模板（不硬编码任何具体模型）。

## 降级与边界

- 模型 ID 与环境相关；技能只要求"钉住并记录"，不指定用哪个。
- heuristic 模式不涉及模型。

## 验收标准

- [x] `running-evals.md` 写明真跑必须钉 `--model` 并记录模型 — （语义）已落
- [x] `agent_runner --help` 提示不钉模型不可复现 — （语义）已落（docstring）
- [x] 全量门禁仍绿 — `check:skill-validate-ok` / `check:skill-selftest`（35/35、26/26）

## 范围外

- 不实现"自动读取桌面当前模型"。
- 不硬编码模型 ID。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 实现：`running-evals.md` 加"必须钉模型"要求；`agent_runner` docstring 提示 | 钉 `deepseek/deepseek-flash` 后必触发用例秒级命中（含 `Skill "shy-skill-suite"`）；Gate 35/35、selftest 26/26 | 收敛 |
