---
id: REQ-0001
title: 轻量脚手架（scaffold_skill.py）
skill: shy-skill-suite
status: done
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: [REQ-0003]
---

# REQ-0001 轻量脚手架（scaffold_skill.py）

## 问题与目标

当用户说"创建技能"时，套件目前只有规范、没有生成机制，要手写目录与 frontmatter，容易漏字段或写错 `name`。

**定位（与 skill-forge 的区别）**：skill-forge 是"plan → build 直接生成整套文件"；我们把技能开发拆成**迭代阶段**，所以脚手架要**轻量**——**只生成目录结构**，不生成需求文档、不填领域内容，技能靠后续迭代完善。**需求与脚手架解耦**：需求由 `writing-requirements.md` 单独落盘。

## 触发与分支

- `lifecycle.md` 阶段 2「实现」开始时。
- 用户说"创建技能 / 新建技能 / 起个骨架"。

## 行为与步骤

1. `scaffold_skill.py <name> [--path <skills_dir>] [--description "<触发描述>"] [--force]`。
2. 创建 `<skills_dir>/<name>/SKILL.md`：
   - `name`：与目录同名（仅小写字母 / 数字 / 连字符，≤64，无首尾或连续连字符）；非法则报错退出、不创建任何文件。
   - `description`：`--description` 提供则用；省略则写**显式占位** `TODO: 一句话说明它做什么、何时触发`（便于需求明确前先起骨架）。
   - 正文：只有 H1 标题，无其它内容。
3. **不创建任何子目录**（`scripts/` / `references/` / `assets/` 在真正放入文件时再建）；**不生成 REQ**。
4. 幂等：目标已存在则报错退出、不覆盖；`--force` 才覆盖。
5. 输出 JSON：`{status, skill_dir, files: [...]}`。

## 脚本与资源

- 新增 `scripts/scaffold_skill.py`（纯标准库）。
- 复用 `scripts/skill_utils.py`（`write_text` / `force_utf8_stdio`）。

## 降级与边界

- 不联网、不装依赖、不建空目录、不写 `README.md`。
- 不生成需求文档（解耦）；不填充领域内容。

## 验收标准

- [x] `scaffold_skill.py demo --path <tmp> --description "测试用"` → 生成 `<tmp>/demo/SKILL.md`；`skill_utils.load_skill` 解析出 `name=demo`、`description="测试用"`。
- [x] 省略 `--description` → 生成含 `TODO` 的占位 `description`，文件仍可解析。
- [x] 非法 `name`（如 `Demo_Skill`）→ 报错、退出码非 0、且未创建任何文件。
- [x] 生成目录内**只有** `SKILL.md`，无 `references/`、`scripts/`、`assets/`。
- [x] 同名重复运行 → 报错且不覆盖；`--force` 才覆盖。
- [x] 生成的 `SKILL.md` 通过官方 `quick_validate.py`。

## 范围外

- 不生成需求文档、不生成子目录、不填充内容、不实现逻辑、不打包、不部署。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现 `scaffold_skill.py`（轻量骨架，仅 `SKILL.md`）；接入 `SKILL.md` 资源与 `lifecycle.md` 阶段 2 | 6/6 验收标准通过；官方 `quick_validate` 通过 | 收敛（done） |

## 备注 / 待办

- 编号已改为**按技能各自从 `0001` 起**（全局递增作废）。
