---
id: REQ-0067
title: 触发评测执行对齐 skill-creator（并发 / 快超时 / 检测锚点 / 进度与指标）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0047, REQ-0063, REQ-0065, REQ-0066]
---

# REQ-0067 触发评测执行对齐 skill-creator

## 问题与目标

对标 skill-creator 的测试方法（`scripts/run_eval.py`、`scripts/run_loop.py`）后确认四处执行层差距（其 `grader` 的主张核验 / 评测集批评、benchmark 多轮方差 **shy 已吸收**，不重复）：

1. **串行**：skill-creator 用 `ProcessPoolExecutor` 默认 10 并发；shy 串行——100 次运行要几十分钟。
2. **超时过长**：skill-creator 每查询 30s；shy 默认 120s（实测用到 180–300s），干等成本高。
3. **检测太宽**：skill-creator 用**唯一命令名**做事件级检测；shy 裸子串——"输出里提到技能名"也算触发，有假阳性风险。
4. **无进度、无 P/R 指标**：skill-creator 逐条打进度 + precision/recall/accuracy；shy 跑完才输出，只有 pass 计数。

实测证据（本次会话）：
- 3 并发全触发、总 **11.7s**；串行约 36s。
- 单条检测用时 **12 / 13.1 / 15 / 17.9s**（n=4）。
- opencode 的加载行是 `→ Skill "shy-skill-suite"`（可锚定）。

目标：`optimize_description.py` 加 `--workers`（并发）；默认超时 120→60；`agent_runner.py` 加 `--detect-mode`（auto/substring/skill-line，auto 对 opencode 用 skill-line）；报告加 precision/recall/accuracy/F1，`--verbose` 逐条进度。

## 触发与分支

- 一切真跑触发评测（`optimize_description.py` / `agent_runner.py`）。
- 用户说"评测太慢 / 结果对不上 / 看不出进度"。

## 行为与步骤

1. `scripts/agent_runner.py`：`detect(output, pattern, mode)` 支持 `skill-line`（正则 `Skill\s*"?<名>"?`）；`--detect-mode {auto,substring,skill-line}`（auto：runner/cmd 含 opencode → skill-line，否则 substring）；**默认超时保持 120**（曾试改 60，实测并发下"晚触发"用例被误杀，已回退——见迭代记录）。
2. `scripts/optimize_description.py`：`--workers`（默认 4，`ThreadPoolExecutor` 并发跑各 (用例, trial)）；`--verbose` 逐条进度（stderr）；报告 train/test 各带 `metrics`（tp/fp/fn/tn/precision/recall/accuracy/f1）；默认超时保持 120（同上）。
3. `references/running-evals.md`：命令示例加 `--workers` / `--detect-mode skill-line`；写明默认超时 60s 与理由。
4. `scripts/run_checks.py`：注册 `req0067-detect-skill-line`（"只提及名字"不算触发、"加载行"才算）。

## 脚本与资源

- 改 `scripts/agent_runner.py`、`scripts/optimize_description.py`、`scripts/run_checks.py`、`references/running-evals.md`。

## 降级与边界

- `--workers 1` 即旧行为；并发仅对 agent runner 有意义（heuristic 瞬间完成）。
- `skill-line` 依赖客户端打印加载行；其他客户端用 `substring`（auto 已分流）。跨客户端格式**待验证**（当前证据只有 opencode v2.0.6）。
- 不做 skill-creator 的"非目标工具即判 False"（其命令式暴露不适用于 opencode：技能可能在探索后才加载）。

## 验收标准

- [x] "只提及技能名"不触发、"`Skill \"名\"`"才触发（skill-line 模式） — `check:req0067-detect-skill-line`（PASS）
- [x] `optimize_description.py --help` 含 `--workers` / `--verbose`；`agent_runner.py --help` 含 `--detect-mode` — （语义）已落
- [x] 报告含 precision/recall/accuracy/f1 — （语义）实测 train/test 各带 `metrics`
- [x] 全量门禁仍绿 — `check:skill-validate-ok` / `check:skill-selftest` / `check:scripts-help-ok`（36/36、26/26）

## 范围外

- 不做自动 description 改写环（shy 的既定决策：agent 驱动）。
- 不做评测集交互编辑器（另议，见备注）。
- 不做实时 HTML 报告（与"报告只在 Step 8 生成一次"的门禁冲突）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 实现：`--workers` 并发、`--verbose` 进度、`metrics`（P/R/A/F1）、`--detect-mode`（auto/substring/skill-line）；注册 `req0067-detect-skill-line` | 全量 20 条首测（60s 超时）：负例 **10/10 全 0.0**——`#107` 的"误触发"证实为裸子串检测假象；但 `#1` 等晚触发正例被 60s 误杀 | 超时回退 120 后复测 |
| 2 | 2026-09-19 | 默认超时回退 120（并发抬高延迟，60s 误杀晚触发用例）并复测全量 20 条 | 复测：test **score 1.0 / P 1.0 / R 1.0 / F1 1.0**；train 0.75（`#6` 0.0、`#7` 0.33、`#8` 0.33）；**负例 20/20 全 0.0**；全量耗时 ~7 分钟 | 收敛；正例漏触发另议 |

## 备注 / 待办

- 对标来源：`C:\Users\18907\.agents\skills\skill-creator\scripts\run_eval.py`（10 并发 / 30s / 唯一名事件级检测）、`run_loop.py`（P/R/A 输出）。
- 尚未吸收（本次未做，留待决定）：`assets/eval_review.html` 式**评测集人工签字**；`run_loop.py` 式**自动改写环**。
