---
id: REQ-0012
title: 加固脚本接口（agent_runner 注入面 + 7 个脚本的 --help 补全）
skill: shy-skill-suite
status: done
kind: fix
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0012 加固脚本接口（agent_runner 注入面 + 7 个脚本的 --help 补全）

## 问题与目标

复审（2026-09-16，标准轴 P2）发现两处"脚本作为 agent 接口"的缺陷：

1. **命令注入面**：`agent_runner.run_prompt` 只把 prompt 里的 `"` 转义，就用 `shell=True` 执行模板。prompt 里的 `&` / `|` / 反引号会被 shell 解释。
   - 证据（实测）：`agent_runner.py --runner cmd --cmd "echo {prompt}" --detect INJECTED --prompt "hi & echo INJECTED_MARKER"`
     → `command` 为 `echo hi & echo INJECTED_MARKER`，`output` 含 `INJECTED_MARKER`，即第二条命令真的执行了。
2. **`--help` 不完整**：`reviewing-skills.md` Step 6 要求 `--help` 含"简述 + 参数 + 示例 + 退出码含义——这是 agent 了解接口的主要途径"。7 个脚本都只有 argparse 的 usage + 一行 description。
   - 证据（实测）：`validate_skill.py --help` 输出仅 `usage: validate_skill.py [-h] path` + `Validate a skill's structure and frontmatter (spec only)`；示例只写在模块 docstring 里，`--help` 取不到；退出码（0 / 1 / 2）全无说明。

目标：prompt 不再被 shell 解释；每个脚本的 `--help` 能独立讲清接口。

## 触发与分支

- 复审 Step 6（脚本与资源审查）。
- 用户说"脚本报错看不懂 / 不知道怎么用这个脚本 / 脚本会不会被注入"。

## 行为与步骤

1. `scripts/agent_runner.py`：改用 `shlex.split(command)` + `shell=False`；Windows 下用 `shlex.split(..., posix=False)` 或显式记录平台差异。模板与 prompt 的拼接改成先解析模板、再把 prompt 作为独立 argv 元素传入（不再做字符串替换）。
   - 保留 `--runner cmd` 的"任意命令模板"能力，但明确：模板按 argv 解析，prompt 永远是**一个**参数，不参与解析。
2. 7 个脚本（`scaffold_skill` / `validate_skill` / `generate_eval_set` / `optimize_description` / `agent_runner` / `aggregate_benchmark` / `track_requirements`）：
   - 把模块 docstring 里的「用法」示例搬进 `argparse` 的 `description` / `epilog`，使 `--help` 自带示例。
   - `epilog` 补退出码表（如 `0 成功 / 1 校验失败或运行错误 / 2 参数错误`）。
3. 不改任何脚本的**成功路径行为**（参数、返回字段、退出码语义保持兼容）。

## 脚本与资源

- 改 `scripts/agent_runner.py`（命令构造）、其余 6 个脚本（argparse `description` / `epilog`）。
- 改 `references/running-evals.md`：注明命令模板按 argv 切分、`{prompt}` 作单参数（无 shell 语法）。
- 不改 `SKILL.md`。

## 降级与边界

- `shlex.split` 在 Windows 的引号规则与 POSIX 不同；须在 REQ 的实现轮次里用真实 Windows 路径与含空格 prompt 各跑一次取证。
- 若某客户端要求"整条命令字符串"而非 argv（无法避免 shell），则在 `--help` 与 `running-evals.md` 里显式标注该注入面，不静默。
- `--help` 变长属预期（示例 + 退出码），仍须精简到"能独立看懂"为止。

## 验收标准

- [x] `agent_runner.py` 中不再出现 `shell=True`（`grep shell\s*=\s*True scripts/*.py` 无命中）。 — （episode）
- [x] 回归（注入）：模板 `"<python 解释器路径>" "argv_dump.py" {prompt}`（只有 `{prompt}` 会被替换，解释器路径需手填）、prompt=`hi & echo PWNED` → 目标程序收到的 `argv[1:]` **恰为单元素** `["hi & echo PWNED"]`，无第二个命令被执行。 — （语义）
  - 原判据「`--cmd "echo {prompt}"` → `output` 不含 `INJECTED_MARKER`」**被证伪**：回显程序会把 prompt 原文打印，substring 无法区分"被执行"与"作为数据被打印"；且 Windows 无 `echo.exe`，原命令本身跑不通。
- [x] 回归（正常）：含空格与中文的 prompt（`帮 我 写 个 技能需求`）→ 目标程序收到**单参数原全文**，无截断、无拆分。 — （episode）
- [x] 边界：不存在的命令 → 返回可行动 `error`（`could not run command: ...`），抛未捕获异常已消除。 — （episode）
- [x] 7 个脚本的 `--help` 输出均含：一句简述、参数说明、至少 1 个示例、退出码含义。 — `check:scripts-help-ok`
- [x] 7 个脚本的 `--help` 退出码仍为 0；缺必填参数时退出码仍为 2（抽查 `validate_skill` / `aggregate_benchmark`）。 — `check:scripts-help-ok`
- [x] 成功路径行为不变：对 `skills/shy-skill-suite` 跑 `validate_skill.py` → 仍 `status: ok`、退出码 0；`optimize_description.py` 启发式路径仍 `mode: heuristic`、退出码 0。 — `check:skill-validate-ok`

## 范围外

- 不新增脚本；不改脚本的成功路径参数 / 返回字段 / 退出码语义；不引入第三方依赖。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |
| 2 | 2026-09-16 | `agent_runner.py` 改 `shlex.split(posix=False)` + 逐 token 去引号 + `shell=False`，prompt 作为单参数注入；新增 `build_argv`；补 `OSError` 处理。7 个脚本 argparse 补 `description` + `epilog`（示例 + 退出码 + `RawDescriptionHelpFormatter`） | 注入回归：`argv[1:] == ["hi & echo PWNED"]`（单元素）；正常回归：中文+空格全文传入；`grep shell=True` 无命中；7×`--help` exit 0、缺参 exit 2；`validate_skill` ok | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P2（两条合并为一份：同属"脚本作为 agent 接口"）。
- 注入面的现实风险较低（prompt 来自用户自己的评测集），但 `running-evals.md` 把它当"可脚本化"接口对外，仍应硬化。
- 实施时**证伪并修正了一处判据**：原注入回归用 substring（`output 不含 INJECTED_MARKER`）不可判定——回显程序会原样打印 prompt，且 Windows 无 `echo.exe`。已改为"目标程序收到 `argv[1:]` 恰为单元素"。记录于此，避免下次重走。
