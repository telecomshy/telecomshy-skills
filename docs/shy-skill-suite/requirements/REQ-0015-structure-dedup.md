---
id: REQ-0015
title: 去掉重复表述（把「自包含」「单一事实源」收敛到单一事实源）
skill: shy-skill-suite
status: done
kind: hygiene
iteration: 2
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0009]
---

# REQ-0015 去掉重复表述（把「自包含」「单一事实源」收敛到单一事实源）

## 问题与目标

复审（2026-09-16，标准轴 P2）：技能自己违反了自己的「单一事实源」原则——两个原则被多处近逐字复述。

- **自包含**：
  - `SKILL.md`「共用原则」：「技能必须自包含：技能文件（`SKILL.md` / `scripts/` / `references/` / `assets/`）只引用技能自身（相对技能根的路径），不引用仓库级 `docs/` 等外部路径——技能会被单独复制部署，外部引用就是悬空指针。」
  - `references/reviewing-skills.md` Step 7：「自包含：技能文件只引用技能自身（相对技能根），不引用仓库级 `docs/` 等外部路径——技能会被单独复制部署，外部引用就是悬空指针。」
  → 后半句逐字相同。
- **单一事实源**：出现在 `SKILL.md` 共用原则、`references/writing-skills.md` §7、`references/writing-requirements.md` §4、`references/reviewing-skills.md` Step 4 共 4 处。

影响：`REQ-0009` 刚把 lever **定义**收敛到 `writing-skills.md`，但"自包含"与"单一事实源"两条没走同一收敛，留下双份措辞；将来改一处忘另一处就会漂移。

目标：这两条含义各只在一处**定义**，其余位置改为**指针**。

## 触发与分支

- 复审 Step 4（结构与预算审查，剪枝 / 单一事实源）。
- 用户说"技能内容有重复 / 精简一下 SKILL.md"。

## 行为与步骤

1. 选定各条的**定义处**（倾向）：
   - 「自包含」→ `references/reviewing-skills.md` Step 7（它是检查动作，且 `REQ-0005/0006/0009` 的验收都指向它）。
   - 「单一事实源」→ `references/writing-skills.md` §7（`REQ-0009` 已确立它是 lever 定义的单一事实源）。
2. 其余位置（`SKILL.md` 共用原则、`writing-requirements.md` §4、`reviewing-skills.md` Step 4）改为一句指针，不重述定义。
3. `SKILL.md` 共用原则保留"这四条原则存在"的清单与各自指针（它们是各分支都要遵守的入口），只删掉重复的定义正文。

## 脚本与资源

- 改 `SKILL.md`、`references/writing-skills.md`、`references/writing-requirements.md`、`references/reviewing-skills.md`。
- 不改脚本。

## 降级与边界

- 这是**删减**，不新增章节；若某处删掉后该分支失去可读性，则保留"一句定义 + 指针"，不强行只留指针。
- `SKILL.md` 是常驻激活内容，优先从它删（省激活后的上下文）。

## 验收标准

- [x] 「不引用仓库级 `docs/` 等外部路径——技能会被单独复制部署，外部引用就是悬空指针」定义句全技能只出现 1 次（`reviewing-skills.md:118`，grep `外部引用就是悬空指针` → 1）。 — （episode）
- [x] 「单一事实源」定义句只出现 1 次（`writing-skills.md:40` 的「一个含义只写一处」，grep → 1）；`SKILL.md`、`writing-requirements.md` 改为指针。 — （episode）
- [x] `SKILL.md` 共用原则仍列出 4 条原则名 + 各自指针。 — （episode）
- [x] `SKILL.md` 去重后**字符净删**（两行 188 → 108，净删 80）。**原判据「行数减少」被证伪**：两条定义各是**单行长文本**，替换成单行指针后行数不变（仍 38 行）；故改用字符数取证。 — （episode）
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0（引用无悬空）。 — `check:skill-validate-ok`
- [x] 抽样验证：`SKILL.md` 指针 → `references/writing-skills.md` §7（单一事实源）、`references/reviewing-skills.md` Step 7（自包含），两条均可达。 — （episode）

## 范围外

- 不重写 `reviewing-skills.md` 的检查项、不改脚本、不改 `REQ-*` 文档。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求（复审 P2），未实施 | — | 待开工 |
| 2 | 2026-09-16 | 实施：`SKILL.md` 共用原则两条定义改短指针；`writing-requirements.md` §4 改指针；定义家定为 `writing-skills.md:40`（单一事实源）与 `reviewing-skills.md:118`（自包含） | grep `一个含义只在一处写`→0、`一个含义只写一处`→1、`外部引用就是悬空指针`→1；`SKILL.md` 两行 188→108（净删 80）；正文行数 38 不变（原「行数减少」判据被证伪，已改字符数）；`validate_skill` → ok | 收敛（done） |

## 备注 / 待办

- 来源：2026-09-16 复审报告，标准轴 P2。
- 与 `REQ-0009` 同源：`REQ-0009` 收敛的是 lever 定义，本 REQ 收敛的是被它漏掉的两条原则。
