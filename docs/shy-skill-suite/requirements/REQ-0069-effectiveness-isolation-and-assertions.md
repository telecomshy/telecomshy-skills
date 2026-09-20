---
id: REQ-0069
title: 把有效性对照做扎实（环境隔离、屏蔽技能、污染扫描、断言强化）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0024, REQ-0067, REQ-0068]
---

# REQ-0069 把有效性对照做扎实（环境隔离、屏蔽技能、污染扫描、断言强化）

## 问题与目标

首次 with/without 有效性对照（`iteration-13`，delta 4.86×）暴露三个方法缺口，经独立子代理复核**全部属实**：

1. **临时目录未隔离**：harness 只隔离单次 cwd，agent 会上溯父目录搜索——baseline 从 `C:\WINDOWS\TEMP\opencode\req0030_pilot\fakerepo2\...` 读到旧版技能（日志出现 77/70 次）；且 temp 下仍存有 `desc-probe/`、`old-snapshot/` 两份完整旧版技能。
2. **非目标技能抢答**：baseline 18 次**零次**加载目标技能；eval-1 三次全加载 `skill-creator`、eval-2 两次加载 `writing-for-agents`（5/9 是"别的指导"）。
3. **断言偏弱**：不查 `status`/`kind` 取值（实例 `status: ready` 照样过）、不查 H1 格式、`criteria-tagged` 不要求覆盖率、"不开 REQ" 无独立断言。

另：`iteration-13` 的 `grading.json` 只落 `pass_rate`，逐断言明细/`claims`/`eval_feedback` 未落盘。

目标：把有效性对照做成**技能内可复用、可自证隔离**的一步——每批独立隔离根、可临时屏蔽技能、逐 run 记录"加载了哪些技能 / 读没读运行目录外的文件"；断言按复核清单加强；`grading.json` 落全量明细。

## 触发与分支

- `reviewing-skills.md` Step 2（有效性审查）与一切 with/without 对照。
- 用户说"技能到底有没有用 / 跑一轮对照"。

## 行为与步骤

1. 新增 `scripts/run_effectiveness.py`（纯标准库）：每批在系统临时目录新建**唯一隔离根**（跑完删除，`--keep` 保留）；每次运行前把 `--disable-skills` 列出的技能临时移出 `--skills-dir`、`finally` 恢复；逐 run 写 `outputs/response.txt`、`outputs/workspace/`、`timing.json`（含 `loaded_skills` 与 `contamination`：运行目录外的读取、非目标技能加载）。
2. 新增 `evals/effectiveness.json`：3 条任务式用例（写 REQ 文档 / 实现后第一步 / 过期数字处置），断言按复核清单加强（frontmatter 取值、H1 格式、四类标记**覆盖率**、"不开 REQ" 独立项等）。
3. `references/running-evals.md`：加「有效性对照」节——布局、命令、隔离与屏蔽要求、污染口径、以及"内容可被搜到 → 无技能 baseline 天然偏弱"的边界。
4. `scripts/run_checks.py`：注册 `req0069-effectiveness-harness`（桩命令端到端：布局 + 污染字段）与 `req0069-effectiveness-set`（用例集结构）。

## 脚本与资源

- 新增 `scripts/run_effectiveness.py`、`evals/effectiveness.json`。
- 改 `references/running-evals.md`、`scripts/run_checks.py`。
- 回填 `iteration-13` 的 `grading.json` 全量明细。

## 降级与边界

- 屏蔽技能需要写权限；无权限时至少**记录**加载了哪些技能，不得静默。
- 无法完全阻止 agent 全盘搜索；靠"隔离根 + 屏蔽 + 污染扫描"把污染变成**可见字段**，由复审判读。
- 不改 `agent_runner.py`（触发轴）与评分口径。

## 验收标准

- [x] 桩命令端到端：产出 `eval-N/<arm>_<t>/{outputs/response.txt,outputs/workspace/,timing.json}`；`timing.json` 含 `loaded_skills` / `contamination`；默认跑完删除隔离根 — `check:req0069-effectiveness-harness`
- [x] `evals/effectiveness.json` 存在且 ≥3 条用例、每条 ≥1 断言 — `check:req0069-effectiveness-set`
- [x] `running-evals.md` 写明隔离 / 屏蔽 / 污染口径与 baseline 边界 — （语义）读文档
- [x] `iteration-13` 的 `grading.json` 含 assertions/claims/eval_feedback 明细 — （语义）读文件

## 范围外

- 不自动安装 / 卸载技能；屏蔽仅在显式给出 `--skills-dir` + `--disable-skills` 时执行。
- 不改评测集与评分口径（`REQ-0044`）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 新增 `run_effectiveness.py`（唯一隔离根 + 技能屏蔽 + 污染扫描）、`evals/effectiveness.json`（断言加强）、`running-evals.md` 对照节、2 条 check + selftest 用例；回填 `iteration-13` 18 份 `grading.json` 全量明细 | Gate 38/38、selftest 28/28；`iteration-13/benchmark.json` delta 4.86× 不变 | 完成 |

## 备注 / 待办

- 复核证据：`iteration-13/blind/*/response.txt`（`req0030_pilot` 77/70 次；baseline 0/18 加载目标技能）。
- 关键边界：**内容可被搜到 → 无技能 baseline 天然偏弱**；4.86× 是保守值（污染把 baseline 从 0.25 抬到 0.75）。
