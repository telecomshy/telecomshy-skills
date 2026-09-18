---
id: REQ-0023
title: 复审发现的一致性修正（闭环串 / 阶段计数 / 报告兜底名 / REQ-0012 矛盾）
skill: shy-skill-suite
status: done
kind: hygiene
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0012, REQ-0018, REQ-0022]
---

# REQ-0023 复审发现的一致性修正

## 问题与目标

2026-09-16 复审（三轴）发现的 4 处文档/实现一致性缺陷，均已证伪确认：

1. **SKILL.md 闭环串缺「呈现」门禁**（标准轴 P2）：`SKILL.md:13,19,35` 仍写「复审 → 回写需求」；`lifecycle.md:3` 已在 `REQ-0018` 改为「复审 → **呈现** →（用户确认）回写需求」。
2. **`lifecycle.md:26` 标题「六个阶段」但实际 0–6 共 7 个**（标准轴 P2）。
3. **`render_report.py` skill_name 兜底不可读**（标准轴 P3）：无 benchmark.skill_name、findings 无 skill、未传 `--skill-name` 时，`itdir.name.replace("-workspace","")` 对 `iteration-N` 返回 `iteration-N`（实测标题变「评估报告 · iteration-1」）。
4. **`REQ-0012` 自相矛盾**（需求轴 P2）：`:44`「不改 `references/`」vs `:49`"在 `running-evals.md` 里显式标注"；实施按后者改了 `running-evals.md:93`。

目标：四处对齐，使文档与实现、文档内部自洽。

## 触发与分支

- 复审 Step 3（需求一致性）/ Step 4（结构）收工后。
- 用户说"把这些一致性小修一下"。

## 行为与步骤

1. `SKILL.md:13,19,35` 三处闭环串补「呈现 →（用户确认）」。
2. `references/lifecycle.md:26` 标题改「七个阶段」（或去掉数字）。
3. `scripts/render_report.py`：`skill_name` 兜底时，若目录名匹配 `^iteration-\d+`，改为取父目录名并去 `-workspace` 后缀；仍可被 `--skill-name` 覆盖。
4. `docs/.../REQ-0012-script-interface-hardening.md`「脚本与资源」改为：改 `scripts/agent_runner.py`、其余 6 脚本的 argparse，**并改 `references/running-evals.md`**（注明 argv / 无 shell 约定）。

## 脚本与资源

- 改 `skills/shy-skill-suite/SKILL.md`、`references/lifecycle.md`、`scripts/render_report.py`。
- 改 `docs/shy-skill-suite/requirements/REQ-0012-script-interface-hardening.md`（文档）。

## 降级与边界

- 只做一致性修正，不改行为语义（第 3 条只改兜底名，不改正路径）。
- 不新增文件、不新增依赖。

## 验收标准

- [x] `grep "复审 → 回写" SKILL.md` → 0 命中；三处均含「呈现」（命中 3）。 — （episode）
- [x] `lifecycle.md` 标题与阶段数一致（改为「七个阶段」）。 — （episode）
- [x] `render_report.py` 对不含 skill 字段的 `iteration-1` 运行 → 报告标题取父目录名（实测 `<h1>评估报告 · nofield</h1>`，不再是 `iteration-1`）。 — （episode）
- [x] `REQ-0012`「脚本与资源」与「降级与边界」不再矛盾（`:44` 现为"改 `references/running-evals.md`"）。 — （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。 — `check:skill-validate-ok`

## 范围外

- 不改命令集 / 自动打开（`REQ-0022`）。
- 不改 `render_report.py` 的报告结构。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 findings #2/#3/#5/#4） | — | 待开工 |
| 2 | 2026-09-16 | 实施：SKILL.md 三处闭环补「呈现」；lifecycle 标题改「七个阶段」；render_report 加 `_fallback_skill_name`（iteration-N 取父目录名）；REQ-0012「脚本与资源」补改 `running-evals.md` | `复审 → 回写`→0、含呈现→3；标题「七个阶段」；兜底实测 `评估报告 · nofield`；REQ-0012 两节一致；`validate_skill` ok | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 复审 findings（标准轴 P2/P3 ×3、需求轴 P2 ×1）。
- 与 `REQ-0022` 独立，可并行（不同文件；仅 `render_report.py` 都碰，合并实现时注意）。
