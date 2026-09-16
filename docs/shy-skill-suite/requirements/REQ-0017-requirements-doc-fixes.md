---
id: REQ-0017
title: 需求文档修正（验收去外部依赖 + 补记两条校验规则）
skill: shy-skill-suite
status: ready
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0001, REQ-0002]
---

# REQ-0017 需求文档修正（验收去外部依赖 + 补记两条校验规则）

## 问题与目标

复审（2026-09-16，需求轴 P2）在两份 `done` 的 REQ 上发现两处文档-实现不一致：

1. **验收标准依赖技能包外的 `skill-creator`**：
   - `REQ-0001` 验收："生成的 `SKILL.md` 通过官方 `quick_validate.py`"。
   - `REQ-0002` 验收："与官方 `quick_validate.py` 在其覆盖的规则上结论一致（`ok-skill` 双方通过；`bad-extra`、`bad-yaml` 双方失败）"。
   - 证据：`quick_validate.py` 只存在于 `~/.agents/skills/skill-creator/scripts/`，**不在本技能包内**。别人单独拿到 `skills/shy-skill-suite/` 无法复现这两条验收——与"技能必须自包含"的原则相悖（`REQ-0005` / `REQ-0006` / `REQ-0009` 的验收都显式查过自包含）。
2. **`REQ-0002` 漏记实现里的 2 条规则**：
   - `validate_skill.py` 实际还查 `description` 不含尖括号 `<` / `>`、`compatibility` ≤ 500 字符。
   - `REQ-0002` 的「行为与步骤」只列了 name / description 长度 / TODO warning / 字段集 / 结构 / 引用，未列这两条。
   - 注：这两条与官方 `quick_validate.py` 的 `ALLOWED_PROPERTIES` 检查一致，**不是**范围蔓延，属文档漏记。

影响：REQ 是"活文档"与事实源；验收不可复现 + 实现漏记，会让后续复审的 Spec 轴失去基准。

目标：把两条验收改写成**仓库内可复现**的断言；把两条规则补进 `REQ-0002`。

## 触发与分支

- 复审 Step 3（需求一致性审查）。
- 用户说"这个验收标准怎么跑 / 补一下需求文档"。

## 行为与步骤

1. `REQ-0001` 的验收标准：把"通过官方 `quick_validate.py`"改为仓库内可复现的断言（倾向）："生成的 `SKILL.md` 满足规范硬约束：`name` == 目录名、kebab-case、≤64；`description` 非空、≤1024、不含尖括号；frontmatter 顶层字段在允许集内。"
   - 并在「备注 / 待办」保留一句历史说明：原验收曾用外部 `quick_validate.py` 对照，结论已并入上述断言。
2. `REQ-0002` 的验收标准：把"与官方 `quick_validate.py` 结论一致"改为仓库内断言 + 已固化的对照结论（把"官方在覆盖规则上是我们的真子集"这一结论写在备注里，而不是要求每次跑外部脚本）。
3. `REQ-0002` 的「行为与步骤」补两条规则：`description` 不含尖括号；`compatibility` ≤ 500 字符。
4. 两份 REQ 各追加一条**迭代记录**（`iteration` +1、`updated` 改当天、`status` 保持 `done`——本轮只改文档不改行为）。
5. 不改 `validate_skill.py`（它的行为是对的；错的是文档）。

## 脚本与资源

- 只改 `docs/shy-skill-suite/requirements/REQ-0001-skill-scaffold.md` 与 `REQ-0002-skill-validator.md`。
- 不改技能文件、不改脚本。

## 降级与边界

- **不改验收标准的严格度**，只改可复现性：新断言与旧对照结论必须等价。
- 不把外部 `quick_validate.py` 复制进技能包（那是别人的技能，会引入来源与许可问题）。
- `status` 保持 `done`：本轮无行为变化，只是把已实现的事实写准。

## 验收标准

- [ ] `REQ-0001` 的验收标准中不再出现对技能包外文件（`quick_validate.py` / `skill-creator`）的依赖。
- [ ] `REQ-0002` 的验收标准中不再出现对技能包外文件的依赖。
- [ ] 两份 REQ 的验收标准均可只用 `skills/shy-skill-suite/scripts/` 内的脚本 + 文本检查复现。
- [ ] `REQ-0002` 的「行为与步骤」含"`description` 不含尖括号"与"`compatibility` ≤ 500 字符"两条。
- [ ] 两份 REQ 各有一条新迭代记录，`iteration` 已 +1、`updated` 为改动当天。
- [ ] 未修改 `skills/shy-skill-suite/` 下任何文件（`git diff --stat` 只含这两份 `docs/` 文件）。

## 范围外

- 不改 `validate_skill.py` 的行为；不引入外部脚本；不改其它 REQ。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |

## 备注 / 待办

- 来源：2026-09-16 复审报告，需求轴 P2（两条合并为一份：同属"把已实现的事实写准"）。
- 已固化结论（供改写时引用）：官方 `quick_validate.py` 的 `ALLOWED_PROPERTIES` = `{name, description, license, allowed-tools, metadata, compatibility}`，与我们 `REQ-0011` 之后的 `BASE_FIELDS` 相同；它**不查** `name` == 目录名、技能内 `README.md`、悬空引用——即官方规则是我们的真子集，我们的额外规则为有意收紧。
