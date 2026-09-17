---
id: REQ-0028
title: 文档去重与判据补齐（单一事实源 / 悬空指针 / 阶段 4 完成判据 / 引用约定）
skill: shy-skill-suite
status: in-progress
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0008, REQ-0009, REQ-0015, REQ-0016, REQ-0018, REQ-0025, REQ-0026, REQ-0027, REQ-0030]
---

# REQ-0028 文档去重与判据补齐

## 问题与目标

2026-09-17 全量复审（三轴）在**标准轴 · Step 4（结构/预算）与 Step 5（步骤/完成判据）**发现的 9 处问题。全部已证伪确认。其中 2 处（回归债定义去重、§6 模板补 `last_verified`）被 `REQ-0030` 吸收——该 REQ 把回归债机制整个删掉，故本 REQ 只保留 **7 处**。

判据来源：`references/writing-skills.md` §3–§8。核心是三类：

- **悬空指针**：`reviewing-skills.md:21` 让复审抓 `duplication` / `sprawl`，但这两个词在全技能**没有定义** → Step 4 完成判据（`:107`）不可判定。
- **单一事实源被破坏**："不读技能反推 REQ" 3 处重复、`SKILL.md` 管线串 3 处重复、`SKILL.md:30` 与 `reviewing-skills.md:21` 同一规则两套措辞。
- **缺完成判据**：`lifecycle.md` 阶段 4（回写需求）无完成判据，而它是**唯一批量改写 REQ 的破坏性步骤**，且无验证回路。

目标：判据可判定、同一含义只写一处、引用约定唯一。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 4 / Step 5 收工后，用户确认落盘。
- 用户说"把这些重复和悬空指针清一下"。

## 行为与步骤

只改技能文件（`SKILL.md` / `references/`），**不改 REQ 文档**（REQ 侧见 REQ-0026）。

1. **`reviewing-skills.md:21` 悬空指针（P1）**：删掉 `duplication`、`sprawl`，改用 `writing-skills.md` §7 已有词（「无 duplication（单一事实源）/ sediment」）；`:21` 的指针从「各自定义见 Step 2、Step 4」改为「见 `writing-skills.md` §7」。同时核对 Step 4 完成判据（`:107`）的词表与之逐字对齐。
2. **`lifecycle.md:66` 阶段 4 补完成判据（P1）**：「每条验收项已勾选或转成新 REQ；迭代记录新增一行；`status` / `iteration` / `updated` 已更新」。
3. **`lifecycle.md:62` vs `:64` 措辞矛盾（P2）**：`:64` 的「只呈现、不落盘」改为「只呈现、**不回写 REQ**」，把"落盘"专用于 REQ；与 `commands/shy-review.md:11`、`writing-requirements.md:14` 统一。
4. **「不读技能反推 REQ」去重（P2）**：定义留在 `grilling.md:35-37`（该动作的归属地），`reviewing-skills.md:35`、`writing-requirements.md:17` 改为一行引用。
5. **`SKILL.md:13,19,35` 管线串去重（P2）**：管线链只留 `:13` 一次；「资源」清单只留路由表未覆盖的（`subagents.md`、`scripts/`、`assets/`、`commands/`），并**不要**逐条抄各脚本 `--help` 已有的一行简介（§7 cache）。
6. **`references/` 内互引用路径统一（P2）**：现为同级裸文件名（`[lifecycle.md](lifecycle.md)`），与 `writing-skills.md:24`「相对技能根」不一致。统一为技能根相对（`references/lifecycle.md`），或把 §3 措辞改成"同目录同级可省略前缀"。
7. **`SKILL.md:30` 否定式（P2）**：「能删的不要改，能改的不要加」→ 换成 `reviewing-skills.md:21` 的正面句「优先删，其次改，最后才加」。

## 脚本与资源

- 改 `SKILL.md`、`references/reviewing-skills.md`、`references/lifecycle.md`、`references/writing-requirements.md`、`references/grilling.md`。
- 不新增文件、不改脚本。

## 降级与边界

- **只做减法与搬迁**，不新增规则。第 4/5 条是删重复、留指针，不是改写语义。
- 第 1 条不得引入新词表：只能用 `writing-skills.md` §7 已有的四个词。
- 第 2 条新增的完成判据必须**可判定**（命令 / 文件 / 计数），不用"回写完整"这类虚词。
- 第 6 条二选一，不两套并存。
- 安全 / 规则类否定句（"不得出现密钥"）**保留**，§6 只针对"本可正面表达却用了否定"的措辞。

## 验收标准

- [ ] `grep -n "sprawl\|duplication" skills/shy-skill-suite/references/writing-skills.md` → `duplication` 有定义（或已改为 §7 用词）；`sprawl` 在全技能 0 命中。
- [ ] `reviewing-skills.md` Step 4 完成判据里的每个词都能在 `writing-skills.md` §7 找到定义。
- [ ] `lifecycle.md` 阶段 4 段内含「完成判据」，且该判据逐条可判定。
- [ ] `grep -n "不落盘" skills/shy-skill-suite/references/lifecycle.md` → 不再与 `:62` 的「落盘 findings.json」冲突（改为「不回写 REQ」）。
- [ ] `grep -rn "反推" skills/shy-skill-suite/references` → 1 处定义 + 引用，不再是 3 处完整规则。
- [ ] `grep -n "逼问 → 落需求" skills/shy-skill-suite/SKILL.md` → 只命中 1 处。
- [ ] `SKILL.md` 资源清单不再逐条重复路由表的描述，且不再抄脚本 `--help` 的一行简介。
- [ ] `grep -rn "](.*\.md)" skills/shy-skill-suite/references` → 引用基准唯一（全带 `references/` 前缀，或 §3 措辞已改）。
- [ ] `python scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。
- [ ] 改动后 `SKILL.md` 行数不增（只做减法或持平）。

## 范围外

- 不改 REQ 文档（见 REQ-0026）。
- 不改脚本行为（见 REQ-0027）、不改 `render_report.py`（见 REQ-0029）。
- 不新增 lever、不改 `writing-skills.md` §1–§10 的 lever 集合。
- 不重写 `reviewing-skills.md` 的三轴结构。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（2026-09-17 复审标准轴 Step 4/5 的 9 条 findings，其中 2 条被 REQ-0030 吸收，实落 7 条） | — | 待开工 |
| 2 | 2026-09-17 | 实施 7 项：删 `sprawl`、`duplication` 改用 §7 词；`lifecycle.md` 阶段 4 补完成判据；「不落盘」→「不回写 REQ」（lifecycle / running-evals / commands）；「不读技能反推」收敛为 grilling 定义 + 2 处引用；SKILL.md 管线串去重 + 资源清单只留路由表未覆盖的；`writing-skills.md` §3 明确同级引用可省略前缀；`SKILL.md` 「先删后加」改正面句 | `sprawl` 0、`duplication` 0；`逼问 → 落需求` 仅 SKILL.md:13；`不落盘` 仅剩「不落盘索引文件」（另一含义）；SKILL.md 49→45 行；validate ok | 待复审（阶段 3） |

## 备注 / 待办

- 来源：2026-09-17 复审 findings（标准轴 P1 ×2、P2 ×5）。报告：`skills/shy-skill-suite-workspace/iteration-1/report.html`。
- **2 条被 `REQ-0030` 吸收**（原第 2 项「回归债定义 4 处去重」、原第 9 项「§6 模板补 `last_verified`」）：`REQ-0030` 把回归债 / `last_verified` 机制整个删掉，无重复可去、无字段可补。若 `REQ-0030` 未先行，本 REQ 也不做这两项。
- **与 REQ-0008 的依赖**：REQ-0026 修 REQ-0008 的假 `[x]` 之前，本 REQ 需先决定 Step 8 完成判据是否补回「附淘汰数」。
- 与 `REQ-0029` 交叉：`reviewing-skills.md` Step 8 也可能被 REQ-0029 碰（报告生成时机），注意合并。
- 与 `REQ-0030` 交叉：都改 `reviewing-skills.md`（本 REQ 改 Step 4/5，`REQ-0030` 改 Step 2/3），合并实施时注意。
