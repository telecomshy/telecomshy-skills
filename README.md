---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'eafc399c-734b-4f42-ac42-7446629e221a'
  PropagateID: 'eafc399c-734b-4f42-ac42-7446629e221a'
  ReservedCode1: 'd85d496b-8f0f-4e3b-81dc-c74a3bfabccd'
  ReservedCode2: 'd85d496b-8f0f-4e3b-81dc-c74a3bfabccd'
---

# telecomshy-skills

TeleAgent 技能集合仓库（Agent Skills for TeleAgent）。

本仓库按 [Agent Skills](https://agentskills.io) 开放标准组织：每个技能是一个**独立文件夹**，内含 `SKILL.md`（指令与元数据），并按需附带 `scripts/`、`references/`、`assets/`。技能文件夹保持纯净，仓库根提供面向人类的 README。

## 技能列表

| 技能 | 文件夹 | 说明 |
| ---- | ------ | ---- |
| 智识沉淀 (knowledge-distill) | [`skills/knowledge-distill`](skills/knowledge-distill) | 把对话沉淀为可检索、可关联、可长期复用的知识库笔记（Obsidian / 普通 Markdown） |

## 目录结构

```
telecomshy-skills/
├── README.md          # 仓库级人类说明
├── LICENSE            # MIT 许可证
└── skills/            # 所有技能存放于此
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

每个技能的使用方法见其 `SKILL.md`。首个技能【智识沉淀】的简介：

> 把用户与 AI 的对话内容沉淀为结构化、可检索、可关联、可长期复用的知识库笔记。核心是「知识库沉淀」而非「摘要概括」：完整保留方法、命令、步骤、结论依据、踩坑经验等细节；长对话涉及多个相互独立的主题时可拆分为多篇笔记。按分类归档到独立的 `AI笔记` 根目录，用双链关联已有笔记形成知识图谱，每个分类自动维护索引文件。

## 许可证

[MIT](LICENSE)

> AI生成