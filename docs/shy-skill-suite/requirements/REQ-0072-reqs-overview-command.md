---
id: REQ-0072
title: 加 /shy-reqs 命令：一份人能读的功能视图和可展开的 HTML 报告
skill: shy-skill-suite
status: done
kind: feature
iteration: 2
created: 2026-09-20
updated: 2026-09-20
blocked_by: []
related: [REQ-0071, REQ-0046]
superseded_by: REQ-0074
---

# REQ-0072 加 /shy-reqs 命令：一份人能读的功能视图和可展开的 HTML 报告

## 问题与目标

**现状缺口**：`/shy-next` 只是跑 `track_requirements.py` 输出**原始 JSON**（frontier / blocked / deferred / 计数），既不列全部 REQ，也不解释"每个是干嘛"，更答不上普通用户真正关心的两个问题——**这个技能现在能做什么、还打算做什么**。只服务 frontier 也大材小用。

**关键歧义（本 REQ 的核心）**："功能"有两个来源，混用会骗人：

- **"已实现"不能从 `done` 的 REQ 反推**——那是**变更历史**，不等于**当前能力**（能力会被后续 REQ 改掉；`fix` / `refactor` 也是能力的一部分）。要答"现在能做什么"，必须读**技能现状**（`SKILL.md` + `references/` + `scripts/`）。
- **"待实现"才读 REQ**（`ready` / `in-progress`）。

**目标**：把 `/shy-next` 改造成 `/shy-reqs`——一份**人类可读的功能视图**：每个技能分「**现在能做什么**」（已实现）与「**计划做什么**」（待实现）两节，白话为主；REQ 统计降为脚注。输出**单文件自包含 HTML（可折叠展开）**，并在终端给一行摘要。

## 触发与分支

- 用户想"看这个技能做到哪了 / 还差什么"、"列一下 REQ"、`/shy-reqs`。
- 取代 `/shy-next`（`commands/shy-next.md` 删除，改 `commands/shy-reqs.md`）。
- 路由进 `lifecycle.md` 的「斜杠快捷」与 `SKILL.md` 资源区。

## 行为与步骤

1. **命令 `/shy-reqs [--skill <name>] [--kind <kind>]`**（user-invoked）：默认**全仓按技能分组**，可选按技能 / 类型过滤。
2. **脚本供结构化数据**：`track_requirements.py` 增加 `--view overview`——终端**人读摘要**（`kind × status` 计数 + frontier + 按技能分组列 `title`）；`--help` 补该参数。脚本仍只做排期，不出白话。
3. **agent 写白话功能段**：读**技能现状**（`SKILL.md` 路由表 + `references/` + `scripts/`）写出「现在能做什么」；读 `ready` / `in-progress` 的 REQ（`feature` 为主，影响能力的 `fix` / `refactor` 也纳入）写出「计划做什么」；落 `reports/reqs-view.json`（schema 见「脚本与资源」）。
4. **渲染 HTML**：`scripts/render_reqs.py` 合并 `reports/reqs-view.json` + `track_requirements.py` 数据，产出**单文件自包含** `reports/reqs.html`（内联样式、无外部资源）；功能按技能分节，各节用原生 `<details>` 折叠；顶部固定计数与 frontier；默认**自动打开**（`--no-open` / `SHY_NO_OPEN` 关闭）。
5. **终端摘要**：命令结束时在对话里给一行计数摘要（如 `shy-skill-suite：已实现 N 项能力 / 待做 M 个 REQ`），并指出 HTML 路径。
6. **生成物不入库**：`reports/` 加进 `.gitignore`。
7. 替换 `/shy-next`：`lifecycle.md` 斜杠快捷表与 `SKILL.md` 资源区把 `shy-next` 改为 `shy-reqs`。
8. `run_checks.py` 注册本 REQ 检查。

## 脚本与资源

- 新增 `commands/shy-reqs.md`；删除 `commands/shy-next.md`。
- 新增 `scripts/render_reqs.py`（`--root` / `--out` / `--skill` / `--kind` / `--no-open` / `--help`）。
- 改 `scripts/track_requirements.py`（`--view overview`；顺带修 `--full` 输出含控制字符导致 JSON 解析失败的问题）。
- 改 `references/lifecycle.md`（斜杠快捷表）、`SKILL.md`（资源区命令清单）。
- 改 `.gitignore`（忽略 `reports/`）。
- 改 `scripts/run_checks.py`、`scripts/selftest.py`（`render_reqs` 成功 + 失败路径用例）。
- `reports/reqs-view.json`（agent 产出，呈现层契约）：
  ```json
  {
    "generated_at": "<ISO-8601>",
    "skills": [
      {
        "name": "<skill>",
        "one_liner": "<白话：这技能干嘛>",
        "implemented": [{"capability": "<能力名>", "plain": "<白话解释>"}],
        "planned": [{"req": "REQ-NNNN", "plain": "<白话解释>"}]
      }
    ]
  }
  ```

## 降级与边界

- **报告是快照**：功能视图由 agent 每次综合，不落稳定清单（技能现状即单一事实源，避免与 `SKILL.md` 双份维护漂移）。
- 无 `ready` / `in-progress` REQ 时，「计划做什么」显示"暂无"。
- `render_reqs.py` **不复用** `render_report.py`（后者是复审报告，schema 不同）。
- 不做 REQ 的编辑 / 回写；只读。
- 报告面向**普通读者**：功能用白话，不得出现未解释的内部术语或裸 `file:line`。

## 验收标准

- [x] `commands/shy-reqs.md` 存在、`commands/shy-next.md` 删除；命令含加载技能 + `--skill` / `--kind` 说明 — `check:req0072-reqs-command`
- [x] `track_requirements.py --view overview` 输出人读终端摘要（计数 + frontier + 按技能分组），`--help` 含该参数 — `check:req0072-overview-view`
- [x] `scripts/render_reqs.py` 存在，`--help` 含简述 / 参数 / 示例 / 退出码；读 `reports/reqs-view.json` + REQ 数据，产出单文件自包含 HTML（无外部资源） — `check:req0072-render-reqs`
- [x] HTML 含计数与 frontier 区、「现在能做什么 / 计划做什么」分节、`<details>` 折叠元素 — `check:req0072-html-structure`
- [x] `.gitignore` 忽略 `reports/` — `check:req0072-gitignore`
- [x] `lifecycle.md` 斜杠快捷表与 `SKILL.md` 资源区含 `/shy-reqs`、不再有 `shy-next` — `check:req0072-skill-routing`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`；`selftest.py` 退出码 0（含 `render_reqs` 成功 + 失败路径） — `check:skill-validate-ok` / `check:skill-selftest`
- [x] （语义）HTML 对普通读者可读：功能用白话、无未解释术语 / 裸 `file:line`；由复审时人工判读 — 渲染层只透出 `reports/reqs-view.json` 的白话字段（`capability`/`plain`/`one_liner`），不引入 `file:line` 或内部术语；待复审人工判读
- [x] （语义）真跑一次 `/shy-reqs`，产出「已实现 / 待实现」功能视图且 HTML 可展开；由一次真跑 + 人工判读判定 — 已在仓库根真跑：`track_requirements.py --view overview` → `render_reqs.py --root . --no-open` → `reports/reqs.html`（77 条 REQ、frontier 3、含 `<details>`、无外部资源，rc=0）；产物已清理

## 范围外

- 不做 REQ 编辑 / 回写 / 新建。
- 不落稳定的 `docs/<skill>/features.md` 功能清单（本次明确不引入）。
- 不改 `track_requirements.py` 的排期职责（frontier / blocked / 悬空）。
- 不改复审报告 `render_report.py`。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-20 | 落需求（未实现） | — | 待实现 |
| 2 | 2026-09-20 | 实现：新增 `commands/shy-reqs.md`、删除 `shy-next.md`；`track_requirements.py` 加 `--view overview`（人读摘要）并修 `--full` 管道控制字符（stdout 改 ASCII 转义）；新增 `render_reqs.py`（单文件自包含 HTML，`<details>` 折叠 + 计数 + frontier）；`.gitignore` 忽略 `reports/`；`lifecycle.md`/`SKILL.md` 路由改 `/shy-reqs`；`run_checks.py` 注册 6 条 `req0072-*`；`selftest.py` 加 `render_reqs` 成功 + 失败路径 | `validate_skill.py` → ok；`run_checks.py` 44/44；`selftest.py` 35/35；真跑 `render_reqs.py --root . --no-open` → `reports/reqs.html`（77 REQ、frontier 3、自包含） | done |

## 备注 / 待办

逼问：已过 3 轮——frontier：A–F（命令名 / 范围 / 结构 / 数据源 / 排期保留 / 生成方式）+ G（shy-apply 去留）+ H1–H2（输出形态）+ I–L（功能视图定位 / 已实现来源 / 待实现来源 / 白话归属）；用户逐轮确认「按推荐」。

- 来源：2026-09-20 用户提案「shy-next 只列未实现 REQ 大材小用；应展示全部 REQ 并分析；最终报告要人类可读，普通用户更想知道技能已实现哪些功能、还有哪些待实现」。
- 与 REQ-0073 同改 `lifecycle.md` 斜杠快捷表与 `SKILL.md` 命令清单，实现时注意避免同文件冲突。
