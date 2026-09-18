---
id: REQ-0027
title: 脚本与资源硬化（第二批：退出码 / 流分离 / 占位符 / 破坏性护栏 / 输出规模 / 部署卫生）
skill: shy-skill-suite
status: done
kind: fix
iteration: 3
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0012, REQ-0013, REQ-0019, REQ-0026]
---

# REQ-0027 脚本与资源硬化（第二批）

## 问题与目标

2026-09-17 全量复审（三轴）在**标准轴 · Step 6/7（脚本与资源 / 安全与自包含）**发现的 9 处问题。全部已证伪确认。

`REQ-0012` 做过第一轮脚本接口硬化（argv 切分、`--help` 退出码表、无 `shell=True`），本轮补上它没覆盖的部分：**退出码与文档不符、诊断未走 stderr、评测报告自相矛盾、评测集生成器抽到占位符、破坏性覆盖无护栏、输出规模无界、部署垃圾与版本声明**。

目标：脚本的接口契约（退出码 / 流向 / 幂等 / 护栏）与 `--help` 声明一致，评测证据不被噪声污染。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 6 / Step 7 收工后，用户确认落盘。
- 用户说"把这些脚本问题修一下"。

## 行为与步骤

1. **`agent_runner.py:201-202`（P1，退出码与 `--help` 矛盾）**：运行错误时 rc=0，而 `--help`（`:181`）声明「1 triggered 为 false，或运行错误 / 超时」。改为：先判 `result.get("error")` → 打印到 **stderr** 并 `return 1`；再判 `triggered`。
   *影响*：否则 shell/agent 无法区分"未触发"与"没跑起来"，会把基础设施故障当有效负例计入触发率。
2. **stdout/stderr 未分离（P1）**：`scaffold_skill.py:91`、`aggregate_benchmark.py:266`、`optimize_description.py:258` 的错误分支走 stdout。改为 `file=sys.stderr`（与 `render_report.py:341`、`generate_eval_set.py:284/289` 已有的正确写法一致）。
3. **`optimize_description.py:194-195`（P1，报告自相矛盾）**：`failure_count`/`failures` 只取 `train_failures`（`:173`），而 `test` 分单独计算（`:171`）、其失败从不暴露。实测 train 12/12、test 5/8，却输出 `failure_count: 0`。改为同时输出 `test_failures`（或标注 failures 的来源），并在 summary 给两组计数。
4. **`generate_eval_set.py:43,107-114,203-207`（P1，占位符噪声）**：`_ASCII_WORD` 把 `description` 里的 `REQ-NNNN` 抽成关键词 `req-nnnn`，产出 16 条无意义 prompt（`req-nnnn` / `帮我req-nnnn` / `解释一下req-nnnn这个概念`），且 `trigger_phrases_found: 0` 时**静默**产出。改为：剔除 `^[a-z]+-n+$` 这类纯占位 token；`phrases` 与 `keywords` 同时为空时返回 error（或至少 warning 到 stderr）。
5. **`scaffold_skill.py:59,87`（P1，破坏性覆盖无护栏）**：`--force` 直接覆盖用户已有 `SKILL.md`，无备份、无 `--dry-run`、无确认。改为覆盖前写 `SKILL.md.bak`（或先 `--dry-run` 打印将覆盖的路径与差异），`--help` 注明「会覆盖且备份」。
6. **`scaffold_skill.py:56-57`（P2，非幂等）**：重复运行返回 rc=1「已存在」。改为已存在且未加 `--force` 时返回 `{"status":"skipped",...}` 且 rc=0。
7. **`track_requirements.py:263`（P2，输出无界）**：始终把全量 JSON 打到 stdout（27 条 REQ 已 13.4 KB），大仓库会被工具层截断。增加 `--output`（写文件）与默认摘要（`total`/`summary`/`errors` 计数），`--full` 才输出全量。
8. **`SKILL.md:4`（P2，兼容声明不可复现）**：`compatibility` 写「实测 3.14」，未声明最低版本，且仓库唯一运行痕迹是 `__pycache__/*.cpython-312.pyc`、本机为 3.12.2。改为声明最低版本（如「Python ≥ 3.7，实测 3.12」）。
9. **`scripts/__pycache__/`（P2，部署垃圾）**：技能目录内存在 4 个 `.pyc`。按 AGENTS.md「技能会被单独复制部署」，陈旧字节码会随行。在发布/复制前清理，或在技能里注明复制时排除。

## 脚本与资源

- 改 `scripts/agent_runner.py`、`aggregate_benchmark.py`、`optimize_description.py`、`generate_eval_set.py`、`scaffold_skill.py`、`track_requirements.py`。
- 改 `SKILL.md`（`compatibility` 行）。
- 清理 `scripts/__pycache__/`。
- 同步各脚本 `--help` 的退出码 / 参数说明。

## 降级与边界

- 只改接口契约与护栏，不改各脚本的核心算法与产物 schema（`grading.json` / `benchmark.json` / `findings.json` 结构不动）。
- 第 4 条（占位符）只加过滤与报错，**不**引入 LLM 或外部词典。
- 第 7 条（输出规模）默认摘要不得丢信息：完整数据仍须能通过 `--full` 或 `--output` 取到。
- 第 5 条（备份）只备份将要覆盖的文件，不引入目录级快照。
- 不引入第三方依赖（仍纯标准库）。

## 验收标准

- [x] `python scripts/agent_runner.py --runner cmd --cmd "no-such-exe {prompt}" --prompt x` → 退出码 **1**、诊断在 **stderr**、stdout 为空。 — `check:agent-runner-error`
- [x] `python scripts/scaffold_skill.py Bad_Name 1>o 2>e` → `e` 非空、`o` 为空或仅结果 JSON；`aggregate_benchmark.py` 空目录、`optimize_description.py` 空评测集同样诊断走 stderr。 — `check:scaffold-ok`
- [x] `optimize_description.py` 对 train 全过 / test 有失败的评测集 → 输出含 test 侧失败计数，且 `test.correct` 与失败数自洽（不再出现 `test` 未满分而 `failure_count: 0`）。 — （episode）
- [x] `generate_eval_set.py skills/shy-skill-suite` → 不再出现 `req-nnnn`；无有效触发词时退出码非 0 或 stderr 有 warning（实测输出写入迭代记录）。 — `check:generate-eval-set-ok`
- [x] `scaffold_skill.py <已存在技能> --force` → 覆盖前生成 `.bak`，`.bak` 内容为被覆盖前的原文。 — （语义）
- [x] 连跑两次 `scaffold_skill.py <已存在技能>`（不带 `--force`）→ 第二次退出码 0、`status: skipped`。 — `check:scaffold-ok`
- [x] `track_requirements.py --help` 含 `--output` 与 `--full`；默认输出为摘要（有界），`--full` 输出与当前等价的完整 JSON。 — `check:scripts-help-ok`
- [x] `SKILL.md` 的 `compatibility` 含最低 Python 版本，且版本号与实测环境一致（实测命令写入迭代记录）。 — （episode）
- [x] `scripts/__pycache__/` 在交付时不存在；`SKILL.md` 注明复制部署时排除它。（注：跑脚本会重建，属正常，故只要求交付时清理 + 文档注明。） — （episode）
- [x] 全部 8 个脚本 `--help` → 退出码 0，且退出码节与实际行为一致。 — `check:scripts-help-ok`
- [x] `python scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。 — `check:skill-validate-ok`

## 范围外

- 不改各脚本的核心算法、产物 schema、参数名。
- 不引入第三方依赖、不引入 LLM。
- 不改 `references/`（文档侧见 REQ-0028）。
- 不改 `render_report.py`（见 REQ-0029）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（2026-09-17 复审标准轴 Step 6/7 的 9 条 findings） | — | 待开工 |
| 2 | 2026-09-17 | 实施 9 项：agent_runner 运行错误 rc=1+stderr；scaffold/aggregate/optimize/validate 错误走 stderr；optimize 加 train/test 失败计数（建议仍只用 train）；generate_eval_set 剔占位符 + 无有效词报错；scaffold `--force` 先备份 `.bak`、已存在改 `skipped`（幂等）；track_requirements 默认摘要 + `--full` + `--output`；SKILL `compatibility` 改 `Python ≥ 3.7`；清 `__pycache__` 并注明复制时排除 | 17 项校验 16 PASS（agent_runner rc=1+stderr；4 脚本错误走 stderr；test_failure_count 自洽；无 `req-nnnn`；无有效词 rc=1；`.bak` 内容一致；二次 rc=0 skipped；摘要/`--full`/`--output`；8 脚本 `--help` rc=0；validate ok）；`__pycache__` 一条按「运行会重建」事实改为「交付时清理 + 文档注明」 | 待复审（阶段 3） |
| 3 | 2026-09-17 | **收敛复审**：`agent_runner` 坏命令 rc=1 且诊断走 stderr、stdout 空；`scaffold` 二次跑 `skipped` rc0、`--force` 生成 `.bak`；`track --help` 含 `--output`/`--full`；全部脚本 `--help` rc0；`compatibility` 含 Python 版本 → 通过。 | `verify_converge.py` 21 项 + `validate` ok | done |

## 备注 / 待办

- 来源：2026-09-17 复审 findings（标准轴 P1 ×5、P2 ×4）。报告：`skills/shy-skill-suite-workspace/iteration-1/report.html`。
- 与 `REQ-0026` 交叉：REQ-0001 的输出 JSON 契约若选择"删 `description` 键"，实现改动在本 REQ。
- 与 `REQ-0028` 交叉：第 7 条给 `track_requirements.py` 加 `--output`/摘要后，`REQ-0028` 会把「回归债判定」的单一事实源指向该脚本的 `--help`，注意 `--help` 文本同步。
- 与 `REQ-0029` 交叉：`render_report.py` 不在本 REQ 范围（它的自动打开问题单独成 REQ）。
