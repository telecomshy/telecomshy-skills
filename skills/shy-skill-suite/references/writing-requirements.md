# 技能需求文档 · 操作规范

> 本文件规定 `docs/<skill>/requirements/` 下**每个技能需求文档**的命名、结构与写作原则，供 AI 落盘、供人后期审核。
> 配套：开发闭环见 [`lifecycle.md`](lifecycle.md)；复审见 [`reviewing-skills.md`](reviewing-skills.md)。
> 依据见 §7。

---

## 1. 用途与何时写

- 当讨论出一个**要做的技能改动**（新功能 / 重构 / 修复）并达成一致后，落盘一份需求文档。
- **改动必须源于真实缺口**：来自一次真实任务、一个可复现的失败、或用户明确提出的诉求——不是"照最佳实践加个功能"。写不出触发它的真实场景，就先别写。
- **一份文档 = 一个可独立验收的内聚需求单元**（像一张 ticket）；不要把所有需求塞进一个文件。
- **需求是活文档**：用户确认落盘后回写（勾选验收、追加迭代记录、更新 `status`/`iteration`），不是写完就冻结；评审后先**呈现**、由用户决定何时回写（门禁见 `lifecycle.md` 阶段 3 → 4）。
- **可跟踪**：`blocked_by` 声明前置依赖；`status` + `iteration` + 迭代记录构成进度；"现在能开始"的 frontier 由 `scripts/track_requirements.py` 扫描得出。
- **可延后**：确定要做但暂缓 → `status: deferred` + `defer_reason`（不算 frontier、不算 done）。恢复时改回 `ready`，并在迭代记录记一句。
- **可回溯补写**：给**既有技能**补 REQ 时，走 `grilling.md` 从**意图**问出来（产出"**应该**做什么"，不是"现在做了什么"），**不得**读技能反推；标 `retroactive: true`。
- 落盘的是**结论**，不是讨论过程（访谈、方案推演留在对话里）。

## 2. 文件与命名

- 位置：`docs/<skill>/requirements/`
- 文件名：`REQ-NNNN-<slug>.md`
  - `NNNN`：四位序号，**每个技能各自从 `0001` 起**递增，**永不复用**（唯一性按 `(skill, id)` 判定）。
  - `<slug>`：短横线连接的英文小写 slug（ASCII，便于检索与跨平台）。
- 文档标题（H1）：`# REQ-NNNN <中文标题>`

## 3. 文档结构（每个需求文档必须包含）

**frontmatter**

```yaml
---
id: REQ-0001
title: <中文标题>
skill: <所属技能目录名，如 knowledge-distill>
status: draft | ready | in-progress | done | deferred | out-of-scope
iteration: 1               # 当前轮次；每轮回写后 +1
created: YYYY-MM-DD
updated: YYYY-MM-DD
blocked_by: [REQ-0002]     # 可选，必须先 done 的前置需求
defer_reason: <为什么延后>  # 仅 status: deferred 时必填
retroactive: true          # 可选，仅"回溯补写（从意图补、非从实现）"时加
related: [REQ-0003]        # 可选，关联的需求
last_verified: YYYY-MM-DD  # 可选，最近一次做过回归验证的日期（见 §5「done 的时效」）
---
```

**`blocked_by` 与 frontier**：`blocked_by` 声明前置 REQ（必须先 `done`）；同技能内写 `REQ-NNNN`，跨技能写 `<skill>:REQ-NNNN`。**现在能开始的 REQ**（frontier）= `status ∈ {ready, in-progress}` 且 `blocked_by` 全部 `done`；用 `scripts/track_requirements.py` 扫描得出（并检查悬空引用），**不落盘索引文件**。

**正文各节**（按顺序）

1. **## 问题与目标** — 从**使用者视角**说清要解决什么、达成什么、为什么现在做；附触发它的真实场景 / 缺口。
2. **## 触发与分支** — 用户怎么说会触发；对应技能里的哪个分支（路由）。
3. **## 行为与步骤** — 技能应表现出的行为（有序步骤）。面向行为，不写实现细节。
4. **## 脚本与资源** — 涉及的命令：名称、参数、返回字段、失败语义；以及新增/改动的 `references/`、`assets/`。
5. **## 降级与边界** — 已知限制、平台差异、能力降级。
6. **## 验收标准** — 可勾选、可独立验证的清单（`- [ ] ...`），**必须端到端可验**。
7. **## 范围外** — 明确不做的事，防止范围蔓延。
8. **## 迭代记录** — 用户确认落盘后的回写：改了什么、证据、结论（格式见下）。
9. **## 备注 / 待办** — 未决项、风险、参考链接。

**## 迭代记录** 用表格，每轮一行；这是需求"活文档"的体现（回写规则见 `lifecycle.md` 阶段 4）：

```markdown
## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | YYYY-MM-DD | … | 触发率 / 对照 delta | 继续 / 收敛 |
```

## 4. 写作原则

- **行为 + 自包含**：写"系统该做什么"，并**写明接口与涉及的文件**——命令名 / 参数 / 返回 / 配置字段 / 章节名，以及 `SKILL.md`、`scripts/`、`references/` 等（技能文件集小且稳定，写清才自包含、可执行）。**不写行号与易变的实现细节。**
- **可验收**：每条标准能独立判定通过 / 失败，且以**具体证据**（命令输出 / 返回字段 / 计数）为准；避开过虚（"输出正确"）与过脆（精确到某句话）的措辞。
- **明确范围外**：显式列出不做的事。
- **精简**：只写 AI 无法自行推断的信息；能一句说清就不写一段。
- **单一事实源**：见 [`writing-skills.md`](writing-skills.md) §7。

## 5. 状态词表

| status | 含义 |
| --- | --- |
| `draft` | 草拟中，未定稿 |
| `ready` | 已确认，可开工 |
| `in-progress` | 实现中 |
| `done` | 已实现并验收（**有时效**，见下） |
| `deferred` | 确定要做，但**延后**；不在 frontier（必须附 `defer_reason`） |
| `out-of-scope` | 明确不做 |

**`done` 的时效**：技能没有编译期，后续 REQ 会改同一份文本（`SKILL.md` / `references/`），旧验收可能静默失效。所以 `done` 只表示"验收那一刻成立"，不是永久。回写时（`lifecycle.md` 阶段 4）在 frontmatter 记 `last_verified: YYYY-MM-DD`。**回归债** = `done` 但需复核的 REQ，由 `scripts/track_requirements.py` 报出（缺 `last_verified` / `updated` 晚于 `last_verified` / 有未勾选且未标「待验证」的验收项）；复审的需求轴据此决定是否从增量转全量（`reviewing-skills.md` Step 3）。

## 6. 模板（复制即用；各节含义见 §3）

```markdown
---
id: REQ-NNNN
title: <中文标题>
skill: <skill-name>
status: draft
iteration: 1
created: YYYY-MM-DD
updated: YYYY-MM-DD
blocked_by: []
related: []
---

# REQ-NNNN <中文标题>

## 问题与目标
…

## 触发与分支
…

## 行为与步骤
…

## 脚本与资源
…

## 降级与边界
…

## 验收标准
- [ ] …

## 范围外
…

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | YYYY-MM-DD | … | … | … |

## 备注 / 待办
…
```

## 7. 依据

Anthropic Agent Skills 官方指南（`agentskills.io`：specification / best-practices / optimizing-descriptions / using-scripts / evaluating-skills；Claude Code：skills、best-practices）、mattpocock 技能包（`to-spec` / `to-tickets` / `triage`）、`skill-creator`。
