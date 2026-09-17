---
id: REQ-0039
title: 收紧 description 边界（修 near-miss 误触发）
skill: shy-skill-suite
status: out-of-scope
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0009, REQ-0010, REQ-0024, REQ-0038]
---

# REQ-0039 收紧 description 边界（修 near-miss 误触发）

## 问题与目标

`REQ-0024` 的触发复测（2026-09-17，10 条真跑）发现一条**过宽**：

```
near-miss #101「什么是 Agent Skills 标准？」→ 误触发（should_trigger=false，实际触发）
```

根因：`description` 只有**正向覆盖**（"当你在……时使用"），没有边界句——问"什么是 Agent Skills 标准"这类**概念问答**命中了"技能…标准"这些关键词。

目标：按 `writing-skills.md` §1 的「划边界（负向触发）」给 `description` 补一条否定句，把它与"概念问答 / 无关编码写作"分开；并**用行为证据验证**（重跑同一评测集）。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 1 触发审查 / description 优化环。
- 用户说"触发太宽 / 误触发了 / 收紧一下"。

## 行为与步骤

1. **`SKILL.md` 的 `description`**：末尾补「不适用于仅询问 Agent Skills / 技能标准的概念、或与技能开发无关的一般编码与写作任务。」；保持 ≤1024 字符。
2. **重跑触发评测**（行为证据）：用 `REQ-0024` 的 `skills/shy-skill-suite-workspace/evals/evals.json`（10 条），确认 **#101 不再触发**且 **5 条正例仍全过**。

## 脚本与资源

- 改 `SKILL.md`（仅 `description` 一句）。
- 改 `scripts/run_checks.py`（注册 `req0039-negative-boundary`）。
- 复用 `REQ-0024` 的评测集与命令：`optimize_description.py --runner cmd --cmd "<opencode> run {prompt} --format json" --detect shy-skill-suite`。

## 降级与边界

- 负向句**同样占 `description` 常驻预算**，只加一句、不过度列举。
- 若收紧导致**正例**触发率下降（漏触发），则回退这次收紧（宁宽勿漏 vs 边界的取舍，按证据定）。
- 评测集是 `REQ-0024` 的人工复核版，仍属小样本（10×1）。

## 验收标准

- [ ] `SKILL.md` 的 `description` 含「不适用于」且 ≤1024 字符 — `check:req0039-negative-boundary`
- [ ] 重跑触发评测：#101（"什么是 Agent Skills 标准？"）**不再触发**，且 5 条正例仍全过（重跑命令与结果写入迭代记录） — （行为）
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不改其它技能。
- 不引入自动 description 改写环（`run_loop.py` 式）。
- 不在本 REQ 扩评测集规模（复用 `REQ-0024` 的 10 条）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施：`SKILL.md` description 末尾加负向边界句「不适用于仅询问 Agent Skills / 技能标准的概念、或与技能开发无关的一般编码与写作任务。」；`run_checks.py` 注册 `req0039-negative-boundary` | `run_checks.py` 全绿；`validate_skill` ok | 待重跑触发评测（行为证据） |
| 2 | 2026-09-17 | **先证伪后回退（前提被推翻）**：加了负向句后重跑触发评测（10 条）→ #101 仍触发、其余不变（9/10）；改用**同一 prompt 连跑 3 次**做对照：**新描述 0/3**、**旧描述（git HEAD）也 0/3** → "#101 过宽"是**单跑噪声**，负向句**无可测效果**。按 `writing-skills.md §1`（"只在有真实误触发时加"）与预算原则**回退** description；`run_checks.py` 增 `skipped`（deferred/out-of-scope 的 `check:` 跳过，避免未采纳需求报红） | 探针对照：OLD desc 0/3、NEW desc 0/3；重跑报告 `iteration-1/raw/desc-opt-2.json` | **out-of-scope**：前提被证伪，变更未采纳 |

## 备注 / 待办

- **结论：前提被证伪，变更未采纳（out-of-scope）。** `REQ-0024` 报的 finding #101 来自**单跑 1 次**；做到 3 次复现时，**旧、新描述都是 0/3**，说明它根本不是稳定过宽。这正是 `AGENTS.md`「先证伪，再提建议」的价值：**差点为一次噪声加一句 no-op**。
- 残留教训（值得进方法论）：**触发类结论必须多条多次**，1 次触发/未触发都不能作数（`running-evals.md` 已要求 3 次，本次是第一次真按它执行并抓到了自己的错）。
- 与 `REQ-0024` 的关系：`REQ-0024` 取证（其 #101 判断应视为噪声，不应据此改 description）。
- 与 `REQ-0038` 的关系：无直接依赖，同为本会话"复审输出/触发质量"的收尾。
