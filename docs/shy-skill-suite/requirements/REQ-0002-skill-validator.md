---
id: REQ-0002
title: 自带技能校验器（validate_skill.py）
skill: shy-skill-suite
status: done
iteration: 1
created: 2026-09-16
updated: 2026-09-16
blocked_by: []
related: []
---

# REQ-0002 自带技能校验器（validate_skill.py）

## 问题与目标

现在校验技能 frontmatter 依赖**外部** skill-creator 的 `quick_validate.py`。套件应**自包含**：自带一个标准合规的校验器，作为脚手架产物与复审 Step 0 的前置检查。

## 触发与分支

- `lifecycle.md` 阶段 2「实现」收尾、阶段 3「复审」之前。
- 用户说"校验技能 / 检查技能结构 / validate skill"。

## 行为与步骤

1. `validate_skill.py <skill_dir>` 校验单个技能目录。
2. **frontmatter**：
   - 必填 `name`、`description`（非空）。
   - `name` 与目录同名；仅小写字母 / 数字 / 连字符；≤64；无首尾连字符、无连续连字符。
   - `description` ≤ 1024 字符；含 `TODO` → **warning**（脚手架占位未替换）。
   - 允许字段集 = `{name, description, license, compatibility, metadata, allowed-tools}`；**顶层多余字段报错**（如 `name_cn`/`description_cn`/`create_source`）。
3. **结构**：`SKILL.md` 存在（大小写精确）；技能目录内不得出现 `README.md`。
4. **引用**：`SKILL.md` 与 `references/` 内的相对 `.md` / 脚本引用必须指向存在的文件，悬空引用报错。
5. 输出 JSON：`{status, errors: [...], warnings: [...]}`；有 error 时退出码 1。

## 脚本与资源

- 新增 `scripts/validate_skill.py`（纯标准库）。
- 复用 `scripts/skill_utils.py`（frontmatter 解析、UTF-8 读写）。

## 降级与边界

- 只做**结构与规范**校验，不做语义 / 质量审查（那是 `reviewing-skills.md` 的事）。
- 只读，不改文件。
- 允许字段集以 `agentskills.io` 规范为准；规范更新时同步。

## 验收标准

- [x] 对 `skills/shy-skill-suite` 运行 → `status: ok`、退出码 0。
- [x] 顶层含 `name_cn` 的技能 → 报"多余字段"并退出码 1。
- [x] `name` 与目录不同名 → 报错。
- [x] 技能目录含 `README.md` → 报错。
- [x] 引用 `references/nope.md`（不存在）→ 报"悬空引用"。
- [x] `description` 含 `TODO`（引号包裹）→ 产出 warning（非 error）。
- [x] 未加引号的 `description: TODO: ...` → 报"疑似非法 YAML"（与官方 PyYAML 结论一致）。
- [x] 与官方 `quick_validate.py` 在**其覆盖的规则**上结论一致（`ok-skill` 双方通过；`bad-extra`、`bad-yaml` 双方失败）；我们的额外规则（`name` == 目录名、`README.md`、悬空引用）为**有意收紧**，官方未覆盖。

## 范围外

- 不修文件、不生成内容、不做评测、不做安全检查。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-16 | 落需求 + 实现 `validate_skill.py`（结构/规范，stdlib，无 PyYAML）；补"未加引号 `: `"的 YAML 隐患检查；接入 `SKILL.md` 资源与 `lifecycle.md` 阶段 2 | 8/8 验收通过；与官方在覆盖规则上一致 | 收敛（done） |

## 备注 / 待办

- 与 `REQ-0001`（脚手架）无硬依赖：脚手架只生成 frontmatter，不必调用本校验器。若后续让脚手架内联校验，再加 `blocked_by`。
- **与官方校验器的关系（实测）**：官方 `quick_validate.py` 是我们规则的**真子集**——它不查 `name` == 目录名、不查技能内 `README.md`、不查悬空引用；而我们的轻量解析器比 PyYAML 宽松（曾放过未加引号的 `: `），故补了 YAML 隐患检查以对齐。结论：**在我们覆盖的规则上不冲突；额外规则为有意收紧。**
