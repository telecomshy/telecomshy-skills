# 技能需求文档 · 操作规范

> 本文件规定 `docs/requirements/` 下**每个技能需求文档**的命名、结构与写作原则，供 AI 落盘与追踪、供人后期审核。
> 依据：Anthropic Agent Skills 官方指南（agentskills.io / Claude Code 文档）、mattpocock 技能包（`to-spec` / `to-tickets` / `triage`）、`skill-creator`。见 §8。

---

## 1. 用途与何时写

- 当讨论出一个**要做的技能改动**（新功能 / 重构 / 修复）并达成一致后，落盘一份需求文档。
- **一份文档 = 一个可独立验收的需求单元**（像一张 ticket）；不要把所有需求塞进一个文件。
- 落盘的是**结论**，不是讨论过程（访谈、方案推演留在对话里）。

## 2. 文件与命名

- 位置：`docs/requirements/`
- 文件名：`REQ-NNNN-<slug>.md`
  - `NNNN`：四位序号，从 `0001` 起递增，**永不复用**。
  - `<slug>`：短横线连接的英文小写 slug（ASCII，便于检索与跨平台）。
- 文档标题（H1）：`# REQ-NNNN <中文标题>`
- 新增一份后，在 §6 登记表加一行。

## 3. 文档结构（每个需求文档必须包含）

**frontmatter**

```yaml
---
id: REQ-0001
title: <中文标题>
skill: <所属技能目录名，如 knowledge-distill>
status: draft | ready | in-progress | done | out-of-scope
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [REQ-0002]        # 可选，关联的需求
---
```

**正文各节**（按顺序）

1. **## 问题与目标** — 从**使用者视角**说清要解决什么、达成什么、为什么现在做。
2. **## 触发与分支** — 用户怎么说会触发；对应技能里的哪个分支（路由）。
3. **## 行为与步骤** — 技能应表现出的行为（有序步骤）。面向行为，不写实现细节。
4. **## 脚本与资源** — 涉及的命令：名称、参数、返回字段、失败语义；以及新增/改动的 `references/`、`assets/`。
5. **## 降级与边界** — 已知限制、平台差异、能力降级。
6. **## 验收标准** — 可勾选、可独立验证的清单（`- [ ] ...`），**必须端到端可验**。
7. **## 范围外** — 明确不做的事，防止范围蔓延。
8. **## 备注 / 待办** — 未决项、风险、参考链接。

## 4. 写作原则

- **行为 + 自包含**：写"系统该做什么"，并**写明接口与涉及的文件**——命令名 / 参数 / 返回 / 配置字段 / 章节名，以及 `SKILL.md`、`scripts/`、`references/` 等（技能文件集小且稳定，写清才自包含、可执行）。**不写行号与易变的实现细节。**
- **可验收**：每条标准能独立判定通过 / 失败，且以**具体证据**（命令输出 / 返回字段 / 计数）为准；避开过虚（"输出正确"）与过脆（精确到某句话）的措辞。
- **明确范围外**：显式列出不做的事。
- **精简**：只写 AI 无法自行推断的信息；能一句说清就不写一段。
- **单一事实源**：一个含义只在一处写；不要与 `SKILL.md` / `references/` 重复。

## 5. 状态词表

| status | 含义 |
| --- | --- |
| `draft` | 草拟中，未定稿 |
| `ready` | 已确认，可开工 |
| `in-progress` | 实现中 |
| `done` | 已实现并验收 |
| `out-of-scope` | 明确不做 |

## 6. 登记表（派生索引）

**唯一事实源是每个文档的 frontmatter**；下表只是便于总览的**派生索引**，不承载新信息。

规则：新增文档、或改动某文档的 `status` / `updated` 时，同步更新对应行。

| ID | 标题 | 技能 | 状态 | 更新 |
| --- | --- | --- | --- | --- |
| REQ-0001 | 索引结构改造（根目录「总目录 + 疑问」，分类纯笔记） | knowledge-distill | ready | 2026-09-16 |
| REQ-0002 | 有道后端 v2（lint-notes + gen-moc） | knowledge-distill | ready | 2026-09-16 |

## 7. 模板（复制即用；各节含义见 §3）

```markdown
---
id: REQ-NNNN
title: <中文标题>
skill: <skill-name>
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
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

## 备注 / 待办
…
```

## 8. 依据

Anthropic Agent Skills 官方指南（`agentskills.io`：specification / best-practices / optimizing-descriptions / using-scripts / evaluating-skills；Claude Code：skills、best-practices）、mattpocock 技能包（`to-spec` / `to-tickets` / `triage`）、`skill-creator`。
