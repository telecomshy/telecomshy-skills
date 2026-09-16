---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '42c47d9c-d490-40bb-819a-3ce4bc1b7f9a'
  PropagateID: '42c47d9c-d490-40bb-819a-3ce4bc1b7f9a'
  ReservedCode1: 'ed474c83-e060-4fbf-8724-224250c08a5d'
  ReservedCode2: 'ed474c83-e060-4fbf-8724-224250c08a5d'
---

# telecomshy-skills

TeleAgent 技能集合仓库（Agent Skills for TeleAgent）。

本仓库按 [Agent Skills](https://agentskills.io) 开放标准组织：每个技能是一个**独立文件夹**，内含 `SKILL.md`（指令与元数据），并按需附带 `scripts/`、`references/`、`assets/`。技能文件夹保持纯净，仓库根提供面向人类的 README。

## 技能列表

| 技能 | 文件夹 | 说明 |
| ---- | ------ | ---- |
| 智识沉淀 (knowledge-distill) | [`skills/knowledge-distill`](skills/knowledge-distill) | 把对话沉淀为可检索、可关联、可长期复用的知识库笔记（Obsidian / 普通 Markdown / 有道云笔记） |
| 技能开发套件 (shy-skill-suite) | [`skills/shy-skill-suite`](skills/shy-skill-suite) | 技能全流程操作规范：写技能需求文档（REQ-NNNN），以及生成/改写后复审技能、提出改进并迭代 |

## 目录结构

```
telecomshy-skills/
├── README.md            # 仓库级人类说明
├── AGENTS.md            # 面向 agent 的仓库约定（目录约定等）
├── LICENSE              # MIT 许可证
├── docs/
│   └── knowledge-distill/
│       ├── research/        # 调研报告（research 技能产出，仅本地留存）
│       └── requirements/    # 技能需求文档（REQ-NNNN-*.md）
└── skills/              # 所有技能存放于此
    └── knowledge-distill/
        ├── SKILL.md
        ├── scripts/
        ├── references/
        └── assets/
```

## 安装方法

1. 克隆本仓库：
   ```bash
   git clone https://github.com/telecomshy/telecomshy-skills.git
   ```
2. 将需要的技能文件夹（如 `skills/knowledge-distill`）复制到 TeleAgent 的 skills 目录：
   - Windows：`C:\Users\<你的用户名>\.config\TeleAgent\skills\`
   - Linux / macOS：`~/.config/TeleAgent/skills/`
3. 重启 / 重载 TeleAgent，使技能生效。

## 各技能使用说明

每个技能的**完整使用说明**见其目录下的 `SKILL.md`（智能体运行时读取的文件）。此处仅提供概览，便于快速判断该技能是否适用。

### 智识沉淀（knowledge-distill）

把一段与 AI 的对话沉淀为**可检索、可关联、可长期复用**的知识库笔记。核心是"知识库沉淀"而非"摘要概括"。

关键能力：

- **保留细节**：完整保留方法、命令、步骤、参数、结论依据、示例与踩坑经验，不因追求简洁而过度压缩。
- **按分类归档**：笔记归档到独立的 `AI笔记` 根目录，遵守"分类子目录 + 笔记"层级。
- **链接成图谱**：用双链（Obsidian）/ 标准链接（普通 Markdown）关联已有笔记，每个分类自动维护索引文件。
- **智能拆分**：长对话涉及多个相互独立的主题时，可拆分为多篇笔记，同类合并、异类拆分。
- **真实可靠**：绝不编造事实，区分事实与推断（`(推断)` / `(待核实)`），易变事实标注日期；对客观、易失效的外部事实必要时联网核验准确性并标注出处，且只核验不沉淀外部内容。
- **检索与维护**：检索已有笔记（按标题命中 / 命中次数 / 新近度排序）、笔记库健康检查（断链 / 索引对齐 / **疑似重复笔记候选**）。
- **可回退**：每次改写前自动备份，可列出历史版本并整篇恢复（撤销上次改写）。
- **可选云端存储**：除本地 Obsidian / 普通 Markdown 外，可选用**有道云笔记**作为唯一存储——经官方 `youdaonote` CLI 读写云端；标签、双链、版本回退、全文检索等按有道能力降级（详见技能内 `references/youdao-best-practices.md`）。

> 完整指令、触发条件与配置详见 [`skills/knowledge-distill/SKILL.md`](skills/knowledge-distill/SKILL.md)。

### 技能开发套件（shy-skill-suite）

面向"技能"这一产物本身的操作规范，覆盖 **需求 → 生成 → 复审 → 迭代** 的生命周期。两条分支按用户意图路由：

- **写技能需求文档**：落盘 `docs/<skill>/requirements/REQ-NNNN-<slug>.md`——命名、frontmatter、正文各节、验收标准、状态词表与模板。
- **复审技能**：AI 生成 / 改写技能后，按"触发 + 有效性"两问给出有证据的判断（真实轨迹、有/无技能对照基线、预算视角 no-op/cache/sprawl/sediment），并产出带优先级的改进清单。

> 完整规范见 [`skills/shy-skill-suite/SKILL.md`](skills/shy-skill-suite/SKILL.md) 及其 `references/`。

## 许可证

[MIT](LICENSE)

> AI生成