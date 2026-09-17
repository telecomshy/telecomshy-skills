---
id: REQ-0026
title: 复审发现的 REQ 文档一致性修正（假 done / 数字漂移 / 漏记）
skill: shy-skill-suite
status: in-progress
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0001, REQ-0008, REQ-0010, REQ-0014, REQ-0020, REQ-0022, REQ-0025, REQ-0030]
---

# REQ-0026 复审发现的 REQ 文档一致性修正

## 问题与目标

2026-09-17 全量复审（三轴）在**需求轴**发现的 7 处 REQ 文档与当前实现不符。全部已证伪确认（命令 + 输出见各条）。

目标：让每份 REQ 的验收标准与今天的实现一致，使 `done` 不再说谎、Spec 轴恢复可信基准。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 3 需求轴收工后，用户确认落盘。
- 用户说"把这些 REQ 文档对齐一下"。

## 行为与步骤

只改 `docs/shy-skill-suite/requirements/` 下的文档，**不改技能文件**（技能文件侧的同类问题见 REQ-0028）。

1. **`REQ-0020`（P0，假 done）**：`:58`「`commands/` 下 5 个模板存在」→ **4**；`:61`「`lifecycle.md` 列出 5 个命令」→ **4**；`:76` 迭代记录「5 模板齐」→「4 模板齐」。加一句注明 `REQ-0022` 删了 `/shy-eval`。
2. **`REQ-0008`（P1）**：`:49` 的「Step 8 完成判据含『已过证伪 + 附淘汰数』」勾为 `[x]` 但已假（`da6db4c` 删掉了该句）。与 REQ-0028 协同：先由 REQ-0028 在 `reviewing-skills.md` Step 8 补回该判据，本 REQ 再据实勾选；若决定不补，则把该条改为「已被 REQ-0018 取代」并取消勾选。
3. **`REQ-0014`（P1）**：`:46`「实测 3.12」与 `SKILL.md:4`「实测 3.14」对齐到同一版本（按实测环境）；行为步骤里的「7 个脚本」→ **8**（REQ-0019 加了 `render_report.py`）。
4. **`REQ-0010`（P2）**：`:55`「实测 150」→ 当前值（或删去具体数字，避免再次漂移）。
5. **`REQ-0001`（P2）**：`:35` 的输出 JSON 契约 `{status, skill_dir, files}` 与 `scaffold_skill.py` 对齐——或删掉实现里的 `description` 键（见 REQ-0027），或在本 REQ 登记该键。
6. **`REQ-0022`（P2）**：「脚本与资源」补 `SKILL.md`（资源清单 5→4 命令，`:74` 迭代记录已承认改了它）。
7. **`REQ-0025`（P2）**：验收 #4 的措辞与 `writing-requirements.md` §6 模板对齐。**注意**：`REQ-0030` 会删掉 `last_verified` 机制并取代 `REQ-0025`，实施顺序上以 `REQ-0030` 为准（见备注）。
8. **`superseded_by` 字段（P1，假 done 的系统性修法）**：现在"取代"只用 prose 备注表达（`REQ-0019` / `REQ-0020` 被 `REQ-0022` 取代），**机器看不见**——`REQ-0020` 的假 `[x]` 正是这么来的。在 `writing-requirements.md` frontmatter 加**可选字段** `superseded_by: REQ-NNNN`（整份 REQ 被另一份取代时用），并在 §3 说明它与 `related` 的区别；`track_requirements.py` 校验该引用不悬空（与 `blocked_by` 同款）并输出。`status` 语义不变（`done` 已不在 frontier，无需新状态值）。

**统一要求**：修完后给这些 REQ 补 `last_verified`（见「降级与边界」）。

## 脚本与资源

- 改 `docs/shy-skill-suite/requirements/REQ-0001/0008/0010/0014/0020/0022/0025-*.md`。
- 不新增文件、不改技能文件。

## 降级与边界

- **只做文档对齐**，不改任何行为语义、不改技能文件（`superseded_by` 只加字段约定，不改 `status` 语义）。
- **`last_verified` 落戳已被 `REQ-0030` 取消**：用户曾选"修完再落戳"，但 `REQ-0030` 会删掉该字段（全量扫下"是否验过"是技能级事实，不是 REQ 级），故本 REQ 不再落戳。若 `REQ-0030` 未先行，本 REQ 也不落戳（避免"落下即过期"）。
- 若某条 REQ 的验收标准在实现侧也应改（如 REQ-0001 的 `description` 键），本 REQ 只登记契约差异，实现改动归 REQ-0027。
- `superseded_by` 只用于**整份 REQ 被取代**；部分取代（如 `REQ-0020` 只有命令集那两条被 `REQ-0022` 改）仍按第 1 条直接订正数字，不置该字段。

## 验收标准

- [ ] `REQ-0020` 的模板 / 命令计数与 `Get-ChildItem skills/shy-skill-suite/commands`（4 个）、`lifecycle.md` 斜杠快捷表（4 行）一致。（**订正标注里引用旧值不算违反**——判据针对的是"把旧值当**当前**计数"。）
- [ ] `REQ-0008`:49 的勾选状态与 `reviewing-skills.md` Step 8 完成判据的实际内容一致（补回则该条 `[x]` 成立；不补则该条已注明取代）。
- [ ] `REQ-0014` 的版本号与 `SKILL.md:4` 一致（同为 `3.12`）；脚本计数与 `scripts/*.py`（去掉 `skill_utils.py` 后的 CLI 数 = 8）一致。
- [ ] `REQ-0010`:55 的数字与实测 `description` 长度一致（实测命令写入迭代记录）。
- [ ] `REQ-0001`:35 的 JSON 契约与 `scaffold_skill.py` 实际输出一致（或已登记差异）。
- [ ] `REQ-0022`「脚本与资源」含 `SKILL.md`。
- [ ] `REQ-0025` 验收 #4 的措辞与 `writing-requirements.md` §6 模板一致（若 `REQ-0030` 已先行删掉该机制，则本项按其取代说明处理）。
- [ ] `writing-requirements.md` 的 frontmatter 说明块含 `superseded_by`，且写明它与 `related` 的区别。
- [ ] `track_requirements.py` 对 `superseded_by` 悬空引用报 error（构造一个指向不存在 REQ 的样本验证，输出写入迭代记录）。
- [ ] 被修 REQ 就地加「2026-09-17 复审订正」标注，且 `updated` 改为当天。（**不**追加迭代记录——迭代记录记的是"本 REQ 被实施"，不是"被别的 REQ 改了文本"；与 `REQ-0023` 改 `REQ-0012` 时的既有做法一致。）
- [ ] `python skills/shy-skill-suite/scripts/track_requirements.py --root .` → `status: ok`、退出码 0（文档仍可解析）。

## 范围外

- 不改技能文件（`SKILL.md` / `references/` / `scripts/` / `assets/`）。
- 不改 `status` 语义、不重开已 `done` 的 REQ。
- 不做跨技能 REQ 对齐。
- 不自动回填 `last_verified` 到未扫过的 REQ。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（2026-09-17 复审需求轴 7 条 findings） | — | 待开工 |
| 2 | 2026-09-17 | 实施：REQ-0020 计数 5→4（行为步骤 + 2 条验收 + 迭代记录）；`reviewing-skills.md` Step 8 补回「附淘汰数」判据（使 REQ-0008 勾选成立）；REQ-0014 版本 3.14→3.12、脚本 7→8；REQ-0010 数字 150→166；REQ-0001 JSON 契约补 `description`；REQ-0022 脚本与资源补 `SKILL.md`；`writing-requirements.md` 加 `superseded_by` 字段与说明；`track_requirements.py` 校验其悬空 | `superseded_by` 悬空 → rc=1、error 命中；`commands/`=4 且 lifecycle 表=4 行；`实测 166`；SKILL 与 REQ-0014 同为 3.12、脚本数=8；validate ok | 待复审（阶段 3） |

## 备注 / 待办

- 来源：2026-09-17 复审 findings（需求轴 P0 ×1、P1 ×2、P2 ×4）+ 设计追加 1 条（`superseded_by`，第 8 项）。报告：`skills/shy-skill-suite-workspace/iteration-1/report.html`。
- 与 `REQ-0027`/`REQ-0028` 有交叉：REQ-0008 的修复依赖 REQ-0028 先补回 Step 8 判据；REQ-0001 的实现侧改动在 REQ-0027。
- 与 `REQ-0030` 交叉：`REQ-0030` 删 `last_verified` 并取代 `REQ-0025`，故本 REQ 第 7 项与"统一要求"的落戳部分以 `REQ-0030` 为准。
- 本 REQ 是 REQ-0025 引入的回归扫的**首次产出**——它抓到的正是"假 `done`"这一类；第 8 项则是从这一类的**根因**（取代关系只写在 prose 里）反推的系统性修法。
