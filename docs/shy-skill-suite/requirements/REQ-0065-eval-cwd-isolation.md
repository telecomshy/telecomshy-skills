---
id: REQ-0065
title: 评测隔离：每次运行都用独立的空目录，防止跨轮污染
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0047, REQ-0063]
---

# REQ-0065 评测隔离：每次运行都用独立的空目录，防止跨轮污染

## 问题与目标

2026-09-19 实测发现：触发评测共用一个 `--cwd`，而嵌套 agent 会往里写文件（README.md、报告 JSON 等）。**后跑的用例在"脏"目录里行为改变**——同一描述、同一条负例 `#102`：
- 脏目录里触发率 1.0（候选 B/C 两批均出现 5 条"误触发"）；
- 换**全新空目录**重跑 3 次：**0/3 不触发**。

即：候选 B/C 的"精度崩溃"主要是 cwd 污染造成的**测量假象**，不是描述改坏。评测必须隔离。

目标：`optimize_description.py` 加 `--isolate-cwd`——每次预测在 `--cwd` 下新建空目录、跑完即删；基目录不被污染，用例之间互不影响。

## 触发与分支

- 一切真跑（opencode/cmd）的触发评测。
- 用户/agent 发现"同样的描述两次结果不一样"。

## 行为与步骤

1. `scripts/optimize_description.py`：`build_predictor` 在 agent 分支支持 `isolate_cwd`——每次 `tempfile.mkdtemp(dir=cwd)` 作运行目录，`finally` 删除。
2. `--isolate-cwd` 进 CLI 与 `--help`；`running-evals.md` 说明用法与原因。
3. `scripts/run_checks.py` 注册 `req0065-cwd-isolation`：用 `cmd` runner 的"写文件 + 打标记"夹具，断言基目录零残留。

## 脚本与资源

- 改 `scripts/optimize_description.py`、`scripts/run_checks.py`、`references/running-evals.md`。

## 降级与边界

- 只在显式传 `--isolate-cwd` 时启用；默认行为不变（共享 cwd）。
- 基目录里的既有文件不动（隔离在子目录里做，不删基目录内容）。

## 验收标准

- [x] `--isolate-cwd` 下基目录零残留（夹具写文件也不留） — `check:req0065-cwd-isolation`（PASS：基目录残留=[]）
- [x] `running-evals.md` 说明用法与"防跨轮污染"原因 — （语义）已落
- [x] `validate_skill` / `run_checks` / `selftest` 全绿 — `check:skill-validate-ok` / `check:skill-selftest`（35/35、26/26）

## 范围外

- 不改 `agent_runner.py` 的 cwd 语义。
- 不做并行评测。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 实现：`optimize_description.py` 加 `--isolate-cwd`（每次运行独立空目录、跑完即删）；注册 `req0065-cwd-isolation`；`running-evals.md` 说明 | 净/脏目录对照：#102 全新空目录 0/3 vs 脏目录 1.0；`req0065-cwd-isolation` PASS；Gate 35/35、selftest 26/26 | 收敛 |
