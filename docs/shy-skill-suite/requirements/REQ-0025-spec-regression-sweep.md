---
id: REQ-0025
title: 需求轴（Spec）回归扫 + 回归债跟踪
skill: shy-skill-suite
status: in-progress
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0018, REQ-0022, REQ-0023]
---

# REQ-0025 需求轴（Spec）回归扫 + 回归债跟踪

## 问题与目标

复审的三条轴里，**行为轴与标准轴本来就是全量**（Step 2 整技能对照、Step 4–7 读 `SKILL.md` 全文与全部脚本）；**只有需求轴（Step 3）按 REQ 切**——它只对**当前这份** REQ 的验收标准记账，不回归此前已 `done` 的 REQ。

技能没有编译 / 链接 / 测试期：所有 REQ 写进**同一份扁平文本**（`SKILL.md` + 少数 `references/`），REQ 与文本之间没有机械链接，`done` 只保证"写的那一刻成立"。而套件本身还鼓励破坏性编辑（`reviewing-skills.md` §1「优先删」、Step 4 剪枝、`lifecycle.md` 阶段 1 的 expand–contract"旧分支无引用后删除"），删正是最容易无声制造回归的动作。

**真实缺口（已发生、未修复）**：`REQ-0020` 仍是 `status: done`，其验收标准两条 `[x]` 均已为假：

- `commands/` 下 5 个模板存在 → 实际 4 个（`REQ-0022` 删了 `/shy-eval`）；
- `lifecycle.md` 斜杠快捷列出 5 个命令 → 实际 4 行。

修正只活在 `REQ-0020` 的一条 prose 备注里，勾选与 `status` 都没改。2026-09-16 那轮三轴复审也没抓到它——Step 4 只读**技能文件**（不读 REQ 文档的勾选），Step 3 只读**本次** REQ。**"历史 REQ 的验收标准今天还成立吗"当前规范里没有任何一步在问。**

目标：

1. 需求轴的证据集从「本次 REQ」扩为「全部 REQ」——增量 REQ 只是其中最新一批。
2. 增量 / 全量不做成两套流程，而是**成本旋钮**：默认只跑本次 REQ，满足升级条件时自动转全量。
3. `track_requirements.py` 报**回归债**：哪些 `done` REQ 需要复核，让假 `done` 可见。
4. `done` 带时效：新增 `last_verified`，`done` 不再等于"永久成立"。

## 触发与分支

- 复审（`reviewing-skills.md`）：Step 2 的对照 case set、Step 3 的验收标准范围。
- `/shy-next`（`commands/shy-next.md`）：列出回归债。
- 用户说"这轮回归扫一下 / 有没有旧 REQ 被弄坏"。

## 行为与步骤

1. **`references/reviewing-skills.md` Step 2**：对照的 case set 来源写清为「**全部 REQ 的行为类验收标准并集**」，并给增量 / 全量旋钮与升级条件。
2. **`references/reviewing-skills.md` Step 3**：把"逐条走 **REQ** 的验收标准"改为"逐条走 **全部 REQ** 的验收标准"；给出三档范围（增量 / 全量 / 降级）与**三个自动升级条件**。
3. **升级条件（写死）**——满足其一即从增量转全量：
   - 本次改动**删除了内容**（剪枝 / expand–contract 的 contract 阶段）；
   - 本次改动触及**多 REQ 共有**的文本（`description`、`SKILL.md` 路由表）；
   - `track_requirements.py` 报出**回归债**。
4. **验收标准分类（不引入新语法）**：由 agent 在 Step 3 现场判断——能用一条命令 / grep / 文件检查判定的算**确定性**（当场跑）；要 agent 实际执行才知道的算**行为类**（进 Step 2 的 eval 集）。**不**在 REQ 里加 `(auto)` / `(behavior)` 标记。
5. **`references/writing-requirements.md`**：frontmatter 增可选字段 `last_verified: YYYY-MM-DD`；§3 说明含义与更新时机（回写时更新）；§5 状态词表补一句 `done` 的时效性。
6. **`scripts/track_requirements.py`**：解析 body 的 `## 验收标准` 勾选，输出新增 `regression_debt` 数组；每项带 `reasons`：
   - `no last_verified`（从未做过回归验证）；
   - `updated after last_verified`（最近一次验证之后文档又改过）；
   - `unchecked criteria`（有未勾选且**未标「待验证」**的验收项）。
7. **`references/lifecycle.md`**：阶段 4 回写时更新 `last_verified`；阶段 5 的 frontier 之外提一句回归债；「斜杠快捷」表说明 `/shy-next` 也报回归债。
8. **`commands/shy-next.md`**：body 补"以及回归债（`regression_debt`）"。
9. **`SKILL.md`** 资源清单：`track_requirements.py` 的描述补"回归债"。

## 脚本与资源

- 改 `scripts/track_requirements.py`：`analyze()` 增 `regression_debt`；解析 `## 验收标准` 勾选；`--help` / docstring 同步。
- 改 `references/reviewing-skills.md`（Step 2、Step 3）、`references/writing-requirements.md`（frontmatter、§3、§5）、`references/lifecycle.md`（阶段 4、阶段 5、斜杠快捷）。
- 改 `commands/shy-next.md`、`SKILL.md`。
- 新增 `docs/shy-skill-suite/requirements/REQ-0025-spec-regression-sweep.md`（本文档）。

## 降级与边界

- **脚本只报债，不跑验收**：确定性验收标准的判定仍由 agent 执行（标准是 prose，不可机器执行）；`regression_debt` 只回答"该复核哪些"。
- **抓不到"假 `[x]`"**：`REQ-0020` 两条勾选都是 `[x]`，机械层抓不到它的事实为假；抓它靠 `no last_verified`——即"从未做过回归验证"。这是本 REQ 的**已知边界**，不假装覆盖。
- **分类由 agent 现场判断**，可能不一致；这是刻意的（避免新增一套标记词表，符合「先删后加」与「给默认而非菜单」）。
- 只按 `--skill` 范围回归，不做跨技能 REQ 回归。
- 不自动改任何 REQ 文档（回写仍走 `lifecycle.md` 阶段 3 → 4 的呈现门禁）。

## 验收标准

- [ ] `track_requirements.py --root .` 输出含 `regression_debt` 数组；对 `docs/shy-skill-suite` 跑，`REQ-0020` 以 `no last_verified` 出现在其中（实测命令与计数写进迭代记录）。
- [ ] `track_requirements.py --help` 的说明含 `last_verified` 与「回归债」。
- [ ] `REQ-0025` 落盘后跑一次：`REQ-0025` 自身**不**出现在 `regression_debt`（其 `status: in-progress` 不在 `done` 集）。
- [ ] `writing-requirements.md` frontmatter 模板含 `last_verified`，§3 说明其含义与更新时机。
- [ ] `reviewing-skills.md` Step 2 写明 case set = 全部 REQ 的行为类验收标准并集；Step 3 写明逐条走全部 REQ 的验收标准，并列出三个自动升级条件。
- [ ] `lifecycle.md` 阶段 4 写明回写时更新 `last_verified`；「斜杠快捷」表说明 `/shy-next` 报回归债。
- [ ] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0。
- [ ] 自包含：本轮改动只引用技能自身相对路径，无仓库级 `docs/` 悬空指针（`commands/*.md` 除外，它引用的是安装说明）。

## 范围外

- 不改 Step 1（触发）、Step 4–7（结构 / 步骤 / 脚本 / 安全）与 Step 8（裁决）。
- 不引入验收标准标记语法（`(auto)` / `(behavior)`）。
- 不做跨技能 REQ 回归。
- 不自动执行确定性验收标准。
- 不自动改 REQ 文档（含不自动勾选、不自动改 `status`）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求（用户确认方案：需求轴默认增量 + 回归债触发全量） | — | 开工 |
| 2 | 2026-09-17 | 实施：`track_requirements.py` 加 `scan_criteria` / `regression_reasons` / `regression_debt` 输出与 `--help`；`writing-requirements.md` 加 `last_verified` 与「done 的时效」；`reviewing-skills.md` Step 2 case set 来源 + Step 3 范围旋钮与三个升级条件；`lifecycle.md` 阶段 4/5 + 斜杠快捷；`commands/shy-next.md`；`SKILL.md` 资源清单 | 见下「实施证据」 | 待复审（阶段 3） |

### 实施证据

```
$ python skills/shy-skill-suite/scripts/validate_skill.py skills/shy-skill-suite
{"status": "ok", ...}  rc=0

$ python skills/shy-skill-suite/scripts/track_requirements.py --root . --skill shy-skill-suite
status: ok  total: 25  summary: {done:22, deferred:1, ready:1, in-progress:1}
frontier: [REQ-0024, REQ-0025]
debt count: 22   ← 22 条 done 全部缺 last_verified（该字段本轮才引入）
REQ-0020 in debt: True   reasons=['no last_verified']
REQ-0025 in debt: False  ← in-progress 不入债

$ python -c "from track_requirements import scan_criteria, regression_reasons; ..."
scan: {'checked': 1, 'unchecked': 2, 'pending': 1}   ← `## 范围外` 的 `[ ]` 不计
reasons(no last_verified): ['no last_verified', 'unchecked criteria (2)']
reasons(stale):            ['updated after last_verified']
reasons(clean):            []
```

**已知边界**：`REQ-0020` 两条勾选都是 `[x]`（事实已假），机械层抓不到，抓它靠 `no last_verified`。本轮**未**替 22 条历史 REQ 补 `last_verified`——补戳等于声称做过回归验证，而本轮没有。这些债留给后续复审逐条销。

## 备注 / 待办

- 来源：2026-09-17 与用户的方案讨论。三个候选方案中，方案 1（抽离增量 spec 指令）与方案 2（spec 轴完全抽离）被淘汰——都会让复审默认失去需求轴，破坏 `reviewing-skills.md` §1 的三轴结构；方案 3（单独加全量审计命令）因"可选门禁会被跳过"且与 Step 4 重叠被降级。采纳的是「需求轴默认增量 + 有债或动共有文本则转全量」。
- 与 mattpocock 的关系：他的 `code-review` 同样是 diff-scoped（需求轴只对 originating spec），全盘视角由**另一个技能** `improve-codebase-architecture` 承担（`disable-model-invocation`、按需）。本 REQ 的取舍是**不加命令**——让全量回归长在默认路径上，避免"另一个技能会被遗忘"。
- 已知未决：验收标准"确定性 vs 行为类"的分类准确率未经测量（**待验证**）。若后续观察到分类反复出错，再考虑引入标记语法。
