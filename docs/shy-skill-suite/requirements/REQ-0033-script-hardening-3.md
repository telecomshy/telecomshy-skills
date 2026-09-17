---
id: REQ-0033
title: 脚本遗留硬化（第三批：输出规模 / 覆盖护栏 / 文档-实现一致 / 中文关键词）
skill: shy-skill-suite
status: out-of-scope
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0027, REQ-0032]
---

# REQ-0033 脚本遗留硬化（第三批）

## 问题与目标

2026-09-17 第二轮复审在**标准轴 · Step 6/7（脚本与资源 / 安全）**发现的 5 处问题。全部已证伪确认，且都是 `REQ-0027` 那轮硬化**没覆盖到的**。

目标：把 `REQ-0027` 立的三条契约（输出有界、覆盖有护栏、`--help` 与实际一致）补齐。

## 触发与分支

- 复审（`reviewing-skills.md`）Step 6 / Step 7 收工后，用户确认落盘。
- 用户说"把这几个脚本尾巴收一下"。

## 行为与步骤

1. **`track_requirements.py:189-190` 摘要仍有界不住（P2）**：默认摘要只对 `frontier`/`blocked`/`deferred` 做 brief，`errors`/`warnings` 仍是完整数组——实测 60 条悬空 `blocked_by` 的仓库默认输出 17570 B（`--full` 26953 B），仍可能被工具层截断。改为：摘要里 `errors`/`warnings` 给**计数 + 前 N 条**，完整仍走 `--full` / `--output`。
2. **覆盖写入无护栏（P2）**：`track_requirements.py:231` 的 `--output`、`aggregate_benchmark.py:204,234`、`render_report.py:319` 都会静默覆盖已存在文件（实测把 `ORIGINAL USER DATA` 覆盖为 JSON，无 `.bak`）。改为：目标已存在时写 `.bak` 或要求 `--force`（`scaffold_skill.py` 已有范式可复用）。
3. **`optimize_description.py:42` docstring 与实现不符（P2）**：docstring 声称「保证两边都有正负例」，实现用 `max(1, int(len*ratio))`，每类仅 1 条时 test 为空（实测 `split_eval_set` 对 2 条样本 → `train=[0,1]`、`test=[]`）。改为：docstring 写「样本足够时尽量分层」，或每类 <2 条时直接报错提示扩充评测集。
4. **`generate_eval_set.py:47-54` `_STOP_WORDS` 缺常见动词（P2）**：`wants` 被当关键词，产出语法错误的 prompt（实测 `I need to wants`）。补 `wants/wanted/need/needs/help/handles` 等。
5. **`generate_eval_set.py:291-294` `--help` 退出码表不全（P2）**：未列新增的「description 无有效触发词」这条 rc=1。补上。

## 脚本与资源

- 改 `scripts/track_requirements.py`、`scripts/aggregate_benchmark.py`、`scripts/render_report.py`、`scripts/optimize_description.py`、`scripts/generate_eval_set.py`。
- 同步各自 `--help`。
- 不新增文件、不引入依赖。

## 降级与边界

- 只改输出规模、护栏与文档一致性，**不改核心算法与产物 schema**。
- 第 1 条的摘要截断不得丢信息：完整数据仍须能通过 `--full` / `--output` 取到。
- 第 2 条只备份将要覆盖的文件，不引入目录级快照。
- 第 3 条若选"小集报错"，须给可行动的提示（怎么扩充评测集）。
- 不引入第三方依赖（仍纯标准库）。

## 验收标准

- [ ] 构造 60 条悬空 `blocked_by` 的仓库：`track_requirements.py` 默认输出显著小于 `--full`（实测两值写入迭代记录），且摘要里 `errors`/`warnings` 为计数 + 前 N 条。
- [ ] `track_requirements.py --output <已存在文件>` → 出现 `.bak`（或需 `--force`）；`aggregate_benchmark.py` / `render_report.py` 对已存在产物的行为同理并实测。
- [ ] `optimize_description.py` 对每类仅 1 条的评测集 → 要么报错并提示扩充，要么 docstring 已改为与实际一致（实测输出写入迭代记录）。
- [ ] `generate_eval_set.py` 对 `Use this skill when the user wants to refactor a module` → 不再产出含 `wants` 的 prompt。
- [ ] `generate_eval_set.py --help` 的退出码 1 含「无有效触发词」；实测全占位 description → rc=1 且文案与 `--help` 一致。
- [ ] 8 个脚本 `--help` → 退出码 0，且退出码节与实际行为一致。
- [ ] `python scripts/validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。

## 范围外

- 不改核心算法、产物 schema、参数名。
- 不引入第三方依赖、不引入 LLM。
- 不改 `references/`（见 `REQ-0032`）、不改 REQ 文档（见 `REQ-0031`）。
- 不重做 `REQ-0027` 已完成的 9 项（除非本 REQ 明确点名的）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（2026-09-17 第二轮复审标准轴 Step 6/7 的 5 条 findings） | — | 待开工 |
| 2 | 2026-09-17 | **退休（out-of-scope）**：脚本输出规模 / 覆盖备份 / 解析细节，属 **P2 脚本卫生**（不改变行为契约、不阻断 `done`）→ 按 Step 8「P2 不阻断，攒批」归入清理批；若将来出现**真实故障**再单独开 REQ。 | 前置：`REQ-0027` 已收敛（同类第二批） | **out-of-scope（退休）** |

## 备注 / 待办

- 来源：2026-09-17 第二轮复审 findings（标准轴 P2 ×5）。报告：`skills/shy-skill-suite-workspace/iteration-2/report.html`。
- 本 REQ 是 `REQ-0027`（第二批）的续；第二批立了契约，本批补没盖到的地方。
- 与 `REQ-0032` 交叉：两者都可能动 `render_report.py`（本 REQ 动覆盖护栏，`REQ-0032` 动 `--help` 文案），合并实施时注意。
- **处置（2026-09-17）**：**退休（out-of-scope）**：脚本输出规模 / 覆盖备份 / 解析细节，属 **P2 脚本卫生**（不改变行为契约、不阻断 `done`）→ 按 Step 8「P2 不阻断，攒批」归入清理批；若将来出现**真实故障**再单独开 REQ。
