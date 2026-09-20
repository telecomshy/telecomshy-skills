---
id: REQ-0036
title: 把技能打包成 .skill 文件（打包前先过校验）
skill: shy-skill-suite
status: deferred
kind: feature
iteration: 1
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0002, REQ-0034]
defer_reason: 当前技能部署走 junction 本地连接（不导出包）；"对外分发"的真实场景尚未出现。等真有分发需求（要把技能发给别人 / 发布）再开。
---

# REQ-0036 把技能打包成 .skill 文件（打包前先过校验）

> **状态：deferred（暂不做）。** 本条只是把调研结论落盘，避免遗忘；不在 frontier、不算 done。

## 问题与目标

两份对标调研都点名 shy **完全没有分发能力**：

- `docs/shy-skill-suite/research/skill-forge.md` §4.1：`package_skill.py` 把技能目录打成 `.skill`。
- `docs/shy-skill-suite/research/skill-creator.md` §4.1：**第二个来源**，并额外贡献「打包前强制跑 `quick_validate`」与「只在技能根排除 `evals/`」。

目标（待启动时）：提供 `package_skill.py`，把技能目录打成 ZIP 换扩展名 `.skill`，**打包前跑 `validate_skill.py` 门控**，排除 `__pycache__` / `*.pyc` / `.git` 等。

## 触发与分支

- 用户说"打包 / 发布 / 发给别人 / 导出技能"。

## 行为与步骤

（待启动时细化）

1. 新增 `scripts/package_skill.py <skill_dir> [-o out.skill]`。
2. 打包前**强制**跑 `validate_skill.py`，失败即拒绝打包。
3. 打包白名单：技能主目录及其 `scripts/` / `references/` / `assets/` / `commands/`；排除 `__pycache__` / `*.pyc` / `.git` / `node_modules` / `.env`。
4. Release checklist：任何文件无密钥 / token / 个人路径。

## 脚本与资源

（待启动时确定）

## 降级与边界

- 不做跨平台转换（那是 `REQ-0037`）。
- 不做发布元数据 / 版本号（先只做本地打包）。

## 验收标准

（待启动时按 `writing-requirements.md` §4 逐条写成可执行检查；当前为草稿，故未标 `check:`。）

- [ ] `package_skill.py` 产出 `.skill`（ZIP）；含技能全部必需文件。 — （语义）
- [ ] 打包前校验失败 → 拒绝打包、退出码非 0。 — （行为）
- [ ] 产物不含 `__pycache__` / `*.pyc` / 密钥类文件。 — （语义）

## 范围外

- 跨客户端转换（见 `REQ-0037`）。
- 自动发布到任何 registry / marketplace。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落盘（deferred）：记录两份调研的打包候选与"校验门控"要点 | — | 暂不做 |

## 备注 / 待办

- 恢复条件：出现真实分发需求（要把技能交给别人 / 发布）。
- 参考实现：skill-creator `scripts/package_skill.py:19-39,70-101`；skill-forge `package_skill.py`。
- **不要照抄** skill-forge 的 `token_savings_ratio` 反向命名等已知坑（见 `skill-forge.md §5`）。
