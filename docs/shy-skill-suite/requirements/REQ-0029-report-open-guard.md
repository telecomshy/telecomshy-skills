---
id: REQ-0029
title: 报告呈现守卫（auto-open 只在终局，复审中途不得弹窗）
skill: shy-skill-suite
status: in-progress
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0019, REQ-0022, REQ-0028]
---

# REQ-0029 报告呈现守卫

## 问题与目标

2026-09-17 复审进行中，用户被**中途弹出的 HTML 报告**打断，路径 `file:///C:/Users/admin/AppData/Local/Temp/opencode/shy-verify/ws/iteration-1/report.html`。

**根因（已定位）**：复审的**两个子 agent** 在测试脚本时各自用临时 fixture 跑了 `render_report.py`，**未加 `--no-open`**；该脚本默认自动打开浏览器（`REQ-0022` 引入）。实测留下了两个报告：

| 路径 | 生成时间 |
| --- | --- |
| `%TEMP%\opencode\shyrev\it\report.html` | 2026-09-17 09:33:13 |
| `%TEMP%\opencode\shy-verify\ws\iteration-1\report.html` | 2026-09-17 09:33:47（09:35:42 重开） |

`shy-verify\make_fixture.py`（09:33:17）即子 agent 自建的 fixture。

这是两层缺口：

1. **脚本层**：`render_report.py` 的自动打开**没有守卫**——不判断调用是否来自终局/交互场景，任何调用都会弹浏览器。
2. **流程层**：`reviewing-skills.md` 说报告是 Step 8 的收工产物（"然后停下"），但**没有明文禁止**在 Step 8 之前生成；`subagents.md` 也没告诉子 agent "测试脚本时不得触发用户可见副作用"。

目标：**报告只在复审终局、由主 agent 打开一次**；子 agent / 中途测试一律静默。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 8 呈现门禁。
- 子 agent 执行 `subagents.md` 的 executor / grader / spec-reviewer / analyzer 角色、需要跑脚本时。
- 用户说"复审中途弹报告了"。

## 行为与步骤

1. **`render_report.py` 加守卫（脚本层）**：自动打开需同时满足——未传 `--no-open`、**且**未设禁用环境变量（`SHY_NO_OPEN` / `CI` / `NO_BROWSER` 任一）。命中禁用时照常写出 `report.html`，`opened: false`，退出码 0（headless 不报错，沿用 `REQ-0022` 的降级约定）。
2. **`reviewing-skills.md` Step 8 明文约束（流程层）**：报告是**终局**产物，**只在 Step 8 生成一次**；复审中途（Step 1–7）不得生成报告。若为验证渲染必须中途跑，用临时工作区 + `--no-open`。
3. **`subagents.md` 加一条通用禁令**：子 agent 跑脚本时**不得触发用户可见副作用**（弹浏览器、写仓库文件、改用户配置）；测试一律在临时目录 + 显式静默开关。
4. **`running-evals.md` 的 HTML 报告节**同步说明：`--no-open` 与 `SHY_NO_OPEN` 的用途（终局才打开；自动化 / 子 agent 一律关闭）。

## 脚本与资源

- 改 `scripts/render_report.py`（守卫逻辑 + `--help` 说明）。
- 改 `references/reviewing-skills.md`（Step 8）、`references/subagents.md`（禁令）、`references/running-evals.md`（HTML 报告节）。
- 不新增文件、不引入依赖（`os.environ` 属标准库）。

## 降级与边界

- **不撤销 `REQ-0022` 的自动打开**——终局自动打开仍是默认行为，本 REQ 只加"什么时候不打开"的守卫。`REQ-0022` 的验收（默认打开、`--no-open` 关闭、headless 不报错）须继续成立。
- 环境变量是**客户端无关**的守卫，不依赖 TTY 判定（主 agent 的终局调用也可能无 TTY，TTY 判定会误伤正例）。
- 写文件行为不变：任何情况下都写出 `report.html`。
- 不改报告内容与结构。

## 验收标准

- [ ] `python scripts/render_report.py <it> --no-open` → `opened` 缺失或 false，`report.html` 已写出，退出码 0。
- [ ] 设 `SHY_NO_OPEN=1` 且**不传** `--no-open` → 不打开（实测 `opened: false`）、`report.html` 已写出、退出码 0。
- [ ] 设 `CI=1` 或 `NO_BROWSER=1` 同样不打开（实测写入迭代记录）。
- [ ] 无任何禁用条件时仍默认打开（回归 `REQ-0022`，实测 `opened: true`）。
- [ ] 无显示环境（`webbrowser.open` 抛错）下仍 `status: success`、`opened: false`、退出码 0（回归 `REQ-0022`）。
- [ ] `render_report.py --help` 说明含 `--no-open` 与 `SHY_NO_OPEN`（及 `CI` / `NO_BROWSER`）。
- [ ] `reviewing-skills.md` Step 8 含「报告是终局产物，只在 Step 8 生成一次；中途不得生成」。
- [ ] `subagents.md` 含「子 agent 不得触发用户可见副作用（弹浏览器 / 写仓库 / 改配置），测试用临时目录 + 静默开关」。
- [ ] `running-evals.md` 的 HTML 报告节说明守卫。
- [ ] `python scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。

## 范围外

- 不改 `REQ-0022` 的自动打开默认行为。
- 不改报告内容 / 结构 / 样式。
- 不引入服务器、不引入依赖。
- 不做"报告已读回执"之类的交互。
- 不清理子 agent 遗留的临时目录（属会话卫生，非技能职责）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（用户报告复审中途弹报告；根因定位到子 agent 跑 `render_report.py` 未加 `--no-open`） | `shy-verify\ws\iteration-1\report.html` 09:33:47；`shyrev\it\report.html` 09:33:13；`make_fixture.py` 09:33:17 | 待开工 |
| 2 | 2026-09-17 | 实施 4 项：`render_report.py` 加 `SHY_NO_OPEN` / `CI` / `NO_BROWSER` 守卫（默认仍打开）；`reviewing-skills.md` Step 8 明文「报告只在 Step 8 生成一次」；`subagents.md` 加「副作用禁令」；`running-evals.md` HTML 报告节说明守卫 | 11/11 PASS（stub `webbrowser.open`，不真弹）：`--no-open`/`SHY_NO_OPEN=1`/`CI=true`/`NO_BROWSER=1` 均 `opened: false` + rc 0 + 仍写出 HTML；默认路径 stub 命中 1 次；headless rc 0；`--help` 与 3 处文档均含守卫 | 待复审（阶段 3） |

## 备注 / 待办

- 来源：用户 2026-09-17 报告 + 文件系统取证（`%TEMP%\opencode\shy-verify`、`shyrev`）。
- 与 `REQ-0028` 交叉：两者都可能改 `reviewing-skills.md` Step 8，合并实施时注意。
- 取证命令：`Get-ChildItem -Recurse "$env:TEMP\opencode\shy-verify" | Select CreationTime,LastWriteTime`。
