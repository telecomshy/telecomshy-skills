# 技能开发生命周期（迭代环）

把「逼问 → 落需求 → 实现 → 复审 → **回写需求** → 再实现」串成一条闭环。skill-forge 有 eval 驱动的迭代，但**没有把复审结果回写成需求**这一环——本文件补上它。

## 产物

| 产物 | 位置 | 角色 |
| --- | --- | --- |
| 需求文档 `REQ-NNNN` | `docs/<skill>/requirements/` | **活文档**、事实源：目标、验收、范围、迭代记录 |
| 技能文件 | `skills/<skill>/` | 被开发的产物（`SKILL.md` / `scripts/` / `references/` / `assets/`） |
| 复审 findings | 对话或临时报告 | 带优先级 P0/P1/P2 |
| 评测证据 | `<skill>-workspace/iteration-N/` | with_skill vs baseline 的 delta（见 `running-evals.md`） |

## 六个阶段

### 0 · 逼问（grill）

把模糊想法逼成明确需求。机制（设计树 + frontier）、要问透的项、三个动作（术语规范化 / 场景压测 / 与实现核对）、完成判据与"可跳过"规则，见 [`grilling.md`](grilling.md)。

### 1 · 落需求（REQ）

按 `writing-requirements.md` 落盘。**大改动拆增量**：

- 每个增量是一次**可独立验收的行为变化**（不是"写完 `SKILL.md`"这类层级切片）。
- 一个增量应能在一个上下文窗口内完成，且能单独演示 / 验证。
- 声明**阻塞关系**：用 `blocked_by` 指向必须先 `done` 的前置 REQ。若一个增量依赖另一个，就把它们拆成多个 REQ 并连边，而不是塞进一个文件。
- **大重构走 expand–contract**：先让新分支与新表述和旧的并存（expand）→ 分批切换，每批一个增量 → 旧分支无引用后删除（contract）。任何一步都不该让技能"半坏"。
- 小改动就是一个增量，不必拆。

**要不要拆成套件？** 只有满足其一才升 Tier 3/4（orchestrator + 子技能，或再加 `agents/`）：子流程有**独立触发词**、需要并行或子 agent、需要对外发布。否则停在 Tier 1/2——没人手动调用、无独立触发、一个上下文窗口装得下，就不拆。

- 正例：`knowledge-distill` 有 6 个分支仍是一个技能（同一 `description` 触发、共享上下文）。
- 反例：一个技能要按**互不相关的用户或触发词**走两条工作流时，才考虑拆。

### 2 · 实现

生成 / 改写技能文件，按增量推进；**每完成一个增量就进入复审**，而不是全部写完再审。

新建技能时用 `python "<SKILL_DIR>/scripts/scaffold_skill.py" <name> --description "<触发描述>"` 起骨架——**轻量，只生成 `SKILL.md`**（不建子目录、不生成 REQ），内容靠后续迭代补。改完后先跑 `python "<SKILL_DIR>/scripts/validate_skill.py" <skill_dir>` 做结构与规范校验，再进入复审。

### 3 · 复审

按 `reviewing-skills.md` 执行（行为轴：触发 + 有效性；需求轴：需求一致性 Spec；标准轴：结构 / 脚本 / 安全），用 `running-evals.md` 的脚本取证据。产出**分轴**、带优先级的 findings。

### 4 · 回写需求（本环的关键，skill-forge 缺）

复审后**必须**把结果折回 REQ，而不是只留一份报告：

- 已满足的验收项 → 勾选 `- [x]`。
- 未满足 / 新发现 → 转成新的验收标准，或新开一份 REQ。
- 范围变化 → 更新「范围外」。
- 追加一条**迭代记录**（格式见 `writing-requirements.md`）。
- `status`：全部验收过且无 P0/P1 → `done`；仍有下一轮 → `in-progress`；`iteration` 加一、`updated` 改为当天。

### 5 · 下一轮

**从 frontier 取下一个**：`python "<SKILL_DIR>/scripts/track_requirements.py" --root .` 列出现在能开始的 REQ（`blocked_by` 全部 `done`），按依赖顺序推进。

回到阶段 2，直到：

- 验收标准全过；
- 无 P0/P1；
- 对照 delta 稳定，或再做也不见有意义的改进（过约束时**做减法**，见 `reviewing-skills.md` §3）。

### 6 · 复盘（retro）

改的是**套件 / 环境**本身（模板、指针、脚本、检查项），不是被开发的技能。只在被开发的技能已收敛、或观察到套件本身反复导致问题时做。

## 一句话

需求是**活文档**：每轮复审都回写它。技能与需求一起演进，而不是需求写完就冻结。
