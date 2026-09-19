---
id: REQ-0056
title: 报告本地服务模式（--serve：页面提交 → agent 继续）
skill: shy-skill-suite
status: done
kind: feature
iteration: 1
created: 2026-09-18
updated: 2026-09-18
blocked_by: []
related: [REQ-0019, REQ-0054]
---

# REQ-0056 报告本地服务模式（--serve：页面提交 → agent 继续）

## 问题与目标

`REQ-0054` 的分拣控件只能"复制 / 下载"，用户仍要手动回贴或告知路径。用户诉求（2026-09-18）：**起一个轻量级服务器，页面上勾选后直接和 agent 交互**。

目标：`render_report.py --serve` 在本机 `127.0.0.1` 起一个**临时**服务并打开页面；页面勾选后点「提交给 agent」，服务把 `triage.json` 写入工作区、随即退出；agent 拿到结果继续。**默认仍是静态单文件（无服务器）**，`--serve` 是显式选项。

## 触发与分支

- 复审 Step 8 收尾、用户分拣时。
- 用户说"直接提交 / 起个服务 / 不想复制粘贴"。

## 行为与步骤

1. `render_report.py` 加 `--serve`（默认关）、`--serve-timeout`（默认 1800 秒）、`--serve-port`（默认 0=随机）。
2. 服务只绑 `127.0.0.1`；URL 带一次性 token；`POST /triage?t=<token>` 校验通过才写 `<iteration>/triage.json` 并 `shutdown`。
3. 页面（模板内联脚本）：`http:` 协议下显示「提交给 agent」按钮，`fetch` POST；`file:` 下沿用「复制 / 下载」。
4. 超时未提交 → 服务退出、静态 `report.html` 仍在，可回退复制 / 下载。
5. 文档同步：`running-evals.md` 报告节、`reviewing-skills.md` Step 8、`SKILL.md` 资源行。

## 脚本与资源

- 改 `scripts/render_report.py`（serve）、`assets/report-template.html`（提交按钮 + 端点占位符）。
- 改 `references/running-evals.md`、`references/reviewing-skills.md`、`SKILL.md`。
- 改 `scripts/run_checks.py`：注册 `req0056-serve`（端到端：GET 拿 token、坏 token 403、POST 写盘、进程退出；静态版无端点）。
- 不改 `findings.json` schema；`triage.json` 由服务写在工作区。

## 降级与边界

- 仍**不自动回传**：服务是 agent 进程的一部分，提交后靠该进程返回，不引入常驻服务。
- 无浏览器 / 无网络栈 / 端口不可用 → 报错并回退静态模式。
- 只写工作区内的 `triage.json`；不接收任意路径。
- 安全：回环地址 + 一次性 token + 64KB 上限；不做外网暴露。

## 验收标准

- [x] `--serve` 起服务：GET 页面含端点、坏 token → 403、正确 token POST → 写 `triage.json` 且进程退出；静态（无 `--serve`）页面无端点 — `check:req0056-serve`（实测 静态无端点=True token=True 坏token403=True POST=True triage.json=True）
- [x] `--serve` 用法与"默认静态、不自动回传"已写明（单一事实源） — （语义）2026-09-18 订正：`running-evals.md` 详述用法与**不自动回传**；Step 8 同句带过；`SKILL.md` 只给"默认静态只读"指针
- [x] 超时未提交 → 服务退出且不报失败（静态报告仍可用） — （语义）实测 `--serve-timeout 1`：`submitted=false`、`timed_out=true`、退出码 0、`report.html` 仍写出

## 范围外

- 不做常驻 / 远程服务、不做外网暴露、不做账号。
- 不改分拣三选项与 `findings.json`。
- 不做批量全选。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 实现：`render_report.py` 加 `--serve` / `--serve-timeout` / `--serve-port`（回环 + 一次性 token + 64KB 上限；POST 写 `triage.json` 即退出）；模板加「提交给 agent」按钮与端点占位符；文档三处同步；`run_checks.py` 注册端到端检查 `req0056-serve` | Gate：`validate` ok；`run_checks` 31/31（serve 端到端 PASS）；`selftest` 20/20；超时回退实测退出码 0；`untagged 0`、`converged true` | 收敛 |

## 备注 / 待办

- 来源：2026-09-18 用户诉求"下载 triage.json 太麻烦，起轻量服务器"。
- 与 `REQ-0019` 的关系：默认模式仍无服务器；`--serve` 是显式可选，属 `REQ-0054` 之后的第三次部分取代说明。
- agent 侧用法：以较长工具超时运行 `--serve`，等用户提交；命令返回即拿到结果。
