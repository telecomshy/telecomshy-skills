# 调研：多技能仓库的说明文档管理惯例

- 检索日：2026-09-23
- 问题：技能仓库怎么组织说明文档？每个技能目录下要不要各放一个 `README.md`？
- 方法：按仓库 AGENTS.md「提建议前先证伪」——每个候选先问"哪条命令能最快推翻它"，跑完再写；报告淘汰数。

## 结论

**仓库根 README（面向人）+ 每技能 `SKILL.md`（面向 agent 的完整说明）**；技能目录内**不放** `README.md`——`SKILL.md` 就是该技能的单一说明文档（agentskills.io 标准里技能解剖 = `SKILL.md` + 可选 `scripts/`/`references/`/`assets/`，README 不在标准内）。根 README 承担：技能清单索引、安装方法、每技能一小节概览并指回 `SKILL.md`。

## 候选与证伪（3 候选，通过 1、证伪 1、待验证 1）

| 候选 | 判定 | 最快推翻它的检查 → 结果 |
| --- | --- | --- |
| 每技能目录各放一个 README.md 是惯例 | **证伪** | `Get-ChildItem <两个本地技能包 + 本仓库 skills> -Recurse -Filter README.md` → **0 命中**（13+ 个技能目录）；anthropics/skills 根布局亦为 README + `skills/*/SKILL.md` |
| SKILL.md 即技能说明，README 只在仓库根做索引 | **通过** | agentskills.io 技能解剖无 README；anthropics/skills、alirezarezvani/claude-skills、block/agent-skills 均为根 README 索引；本仓库 AGENTS.md 亦写明「每个技能一个文件夹……仓库根提供面向人类的 README.md」 |
| 用户提到的 "alaude" 仓库的布局 | **待验证** | 检索未命中该名称的技能仓库（名称可能有出入）；不进建议依据 |

淘汰数：候选 3 个 → 通过 1、证伪 1、待验证 1。

## 验证命令与结果

```powershell
Get-ChildItem C:\Users\admin\.agents\skills,D:\code\my_projects\telecomshy-skills\skills -Recurse -Filter README.md
# →（无输出；技能目录内 README.md 命中 0）
```

## 补充观察（事实，非建议）

- alirezarezvani/claude-skills（380 技能）除根 README 外还有**仓库级**规范文档 `SKILL-AUTHORING-STANDARD.md` 与 `SKILL_PIPELINE.md`——多技能仓库把"写技能的标准"独立成文的先例。本仓库对应物是 `skills/shy-skill-suite`。
- 大型技能仓库的根 README 常含徽章与按 agent 分组的安装命令；小型仓库（block/agent-skills）仅一张清单表。

## 来源（上游版本 pin）

- https://github.com/anthropics/skills —— README + `skills/` 布局；pin：commit `34040c9`（2026-09-10）
- https://github.com/alirezarezvani/claude-skills —— 根 README 索引 + `SKILL-AUTHORING-STANDARD.md`；pin：commit `a80eec2`（2026-08-21）
- https://github.com/block/agent-skills —— 根 README（技能清单）
- agentskills.io《What are skills》——技能解剖（`SKILL.md` + `scripts/`/`references/`/`assets/`）
- 本地：mattpocock 工程技能包（`~/.agents/skills`）、telecomshy-skills（`skills/`）
