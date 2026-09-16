---
id: REQ-0014
title: SKILL.md 声明运行前提（compatibility）
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0014 SKILL.md 声明运行前提（compatibility）

## 问题与目标

复审（2026-09-16，标准轴 P2）：整个 `scripts/` 层依赖 Python 3（纯标准库），但 `SKILL.md` 没有任何运行前提声明。

- 证据：`SKILL.md` frontmatter 只有 `name` / `description` / `metadata`，无 `compatibility`。
- 影响：`lifecycle.md` 阶段 2 直接让 agent 跑 `python "<SKILL_DIR>/scripts/scaffold_skill.py" ...`；环境无 Python（或只有 Python 2）时，agent 拿到的是 `command not found` 或语法错误，而不是"这个技能需要 Python 3"。
- 依据：`reviewing-skills.md` Step 6 要求"技能是否需要 `compatibility` 声明运行前提"。

目标：agent 与人在加载技能前就知道运行前提；缺失时能给出可行动的替代路径（手动写 frontmatter）。

## 触发与分支

- 加载 `shy-skill-suite` 后、准备跑 `scripts/` 里任一脚本前。
- 用户说"这脚本跑不起来 / 没有 python 怎么办"。

## 行为与步骤

1. `SKILL.md` frontmatter 增 `compatibility`，写明：
   - 需要 Python 3（纯标准库，无第三方依赖）；
   - 7 个脚本的作用域（只在校验 / 评测 / 需求跟踪时用到）；
   - 缺 Python 时的降级：不跑脚本，手工按 `writing-requirements.md` / `reviewing-skills.md` 的规范执行。
2. `compatibility` 长度 ≤ 500 字符（`validate_skill.py` 与官方 `quick_validate.py` 都查这条）。
3. `SKILL.md` 正文不改（运行前提属元信息，不进正文，避免占激活后的上下文）。

## 脚本与资源

- 只改 `SKILL.md` 的 frontmatter；不改脚本、不改 `references/`。

## 降级与边界

- `compatibility` 不在 `agentskills.io` 必填集内，是可选字段；写了不影响其它客户端。
- 不声明具体 Python 次版本号（脚本用了 `from __future__ import annotations`，3.8+ 即可）——写"Python 3"并注明"实测 3.12"，避免脆弱的精确版本断言。

## 验收标准

- [ ] `SKILL.md` frontmatter 含非空 `compatibility`。
- [ ] `compatibility` ≤ 500 字符。
- [ ] `compatibility` 写明"需要 Python 3（纯标准库）"与"缺 Python 时的手工降级路径"。
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。
- [ ] `SKILL.md` 正文行数不变（运行前提只进 frontmatter）。

## 范围外

- 不改脚本、不做依赖打包、不引入 `requirements.txt`。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P2。
