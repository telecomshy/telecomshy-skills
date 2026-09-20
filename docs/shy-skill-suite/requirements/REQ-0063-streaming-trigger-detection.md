---
id: REQ-0063
title: 触发评测改成流式检测（命中就停，不再空等到超时）
skill: shy-skill-suite
status: done
kind: fix
iteration: 1
created: 2026-09-19
updated: 2026-09-19
blocked_by: []
related: [REQ-0047, REQ-0056]
---

# REQ-0063 触发评测改成流式检测（命中就停，不再空等到超时）

## 问题与目标

2026-09-19 实测（首次真跑行为轴）：11 条 × 3 次的正例批次 **52 分钟仍未跑完**，且发现证据口径缺陷——

1. `agent_runner.py` 用 `subprocess.run(capture_output=True, timeout=…)`："跑完再检测"。正例触发技能后**继续干活**（读文件、反问用户）直到 300 秒超时，每个会话分钟级。
2. 超时的进程被 `TimeoutExpired` 捕获后返回 `triggered: false`、`output: ""`——**已触发的会话被误记为未触发**，污染触发率。

目标：改成**流式检测**——逐行读取输出，命中 `--detect` 标记**立即结束会话**；超时（未命中）才返回未触发 + 错误。

## 触发与分支

- `optimize_description.py --runner opencode` / `agent_runner.py` 的一切真跑评测。
- 用户说"评测怎么这么慢 / 触发率对不上"。

## 行为与步骤

1. `scripts/agent_runner.py`：`Popen` + 读取线程 + 队列；逐行 `detect`；命中即 `terminate` 并返回 `triggered: true`（携带已收集输出与退出码）；进程自然结束未命中 → `triggered: false`；墙钟超时 → 未触发 + `error: timeout`（带部分输出）。
2. 保留既有契约：坏命令 → 非 0 + stderr；缺 `{prompt}` → 非 0 + stderr；heuristic → `triggered: null`。
3. `scripts/selftest.py`：加"命中即停"用例（命令先打印标记再睡 60 秒 → 断言 rc=0、`triggered: true`、用时 < 30 秒）。
4. `scripts/run_checks.py`：注册 `req0063-streaming-stop`（同上，临时脚本夹具）。
5. `references/running-evals.md`：说明检测为流式、命中即停。

## 脚本与资源

- 改 `scripts/agent_runner.py`、`scripts/selftest.py`、`scripts/run_checks.py`、`references/running-evals.md`。
- 不改 `optimize_description.py` 的评分口径。

## 降级与边界

- 逐行检测意味着**跨行正则**不可用（单行子串 / 正则不受影响）——客户端输出触发标记都在单行。
- 早停时 `returncode` 为终止信号（负数），调用方只看 `triggered`。
- 负例（不触发）仍需等进程自然结束——这是"未触发"的必要代价。

## 验收标准

- [x] 命中标记即结束会话（不为等进程跑完而空等），坏命令 / 缺 `{prompt}` / heuristic 契约不变 — `check:req0063-streaming-stop`（实测 0.5s）/ `check:agent-runner-error`（PASS）
- [x] `selftest.py` 含"命中即停"用例且通过 — （语义）已落（26/26 通过）
- [x] `running-evals.md` 说明流式检测与跨行正则限制 — （语义）已落

## 范围外

- 不改评测集与评分口径。
- 不做并行跑（客户端并发可能冲突）；如需再议。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-19 | 实现：`agent_runner.py` 改流式检测（Popen + 读取线程 + 命中即 terminate）；selftest 加"命中即停"用例；注册 `req0063-streaming-stop`；`running-evals.md` 同步 | 夹具命令要睡 60s → 实测 **0.5s** 返回；修复后基线批 33 次会话 **~2.5 分钟**跑完（修复前同一批 52 分钟未完）；Gate 34/34、selftest 26/26 | 收敛 |
