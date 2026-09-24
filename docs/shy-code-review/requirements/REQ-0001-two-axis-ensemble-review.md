---
id: REQ-0001
title: 给代码审查加一层三跑对拍与主代理裁决，不改上游 code-review 技能
skill: shy-code-review
status: done
kind: feature
iteration: 3
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: []
---

# REQ-0001 给代码审查加一层三跑对拍与主代理裁决，不改上游 code-review 技能

## 问题与目标

`/code-review` 换不同模型审查同一 diff 时互有增漏（实验：`docs/research/code-review-model-variance-experiment.md`，tasknotes-aireporter）。目标：漏报靠「每轴跑 3 遍取并集」压下去（3 遍是实验的质量甜点：并集召回约 9 成 5，2 遍约 8 成），误报靠「主代理逐条裁决」压回来，且**不动 mattpocock 原技能一行**。触发场景：用户要求高可信度 diff 审查、明说「shy 审查 / 对拍审查」。

## 触发与分支

「/shy-code-review」「shy 审查」「用对拍/多跑方式做代码审查」→ 加载上游 `code-review` 执行全流程，仅其第 4、5 步被覆盖。**链路内点名 `code-review`（如 `implement` 收尾）经 AGENTS.md「Shy 技能路由」改走本技能。**

## 行为与步骤

1. 加载上游 `code-review`（Skill 工具），按其执行：固定点、spec 来源、standards 来源 + 坏味基线、两轴分离。
2. **三跑**：每轴发 3 个独立子代理（运行 1–3），并行；提示词除运行标签外逐字相同、互不可见；输出结构化 finding 表（`| 位置 | 类别 | 硬违规/判断 | 描述 |`，无发现写「无发现」）。
3. 模型矩阵：A、B、C 三模型各一（ID 见仓库 `docs/agents/subagent-models.md`：`deepseek/deepseek-flash`、`xiaomi-token-plan-cn/mimo-v2.6-flash`、`hubei-science/deepseek-v4-flash`）；某模型不可用 → 用可用模型**凑满 3 跑**（一模型 2 跑 + 另一模型 1 跑）并标注实际矩阵。解析 ID 先查模型目录（`opencode.models`，缺了加 `all: true`），不猜 ID。
4. **轴内裁决**：归并同题 finding → 共识（≥2/3 跑）免检采信 → 孤证（1/3）逐条核对（`git show <fixed>:<path>` 对照钉版本；「缺失」类回仓库现状核对）→ 剔除记依据。
5. **报告**：两轴分开（照上游格式），每条标票数（3/3、2/3、1/3）与裁决（采信/复核后采信/剔除+依据），末尾加对拍统计行。
6. **降级**：某跑失败同模型重试一次，再失败按剩余跑数出报告（2 跑仍算对拍并标注；仅 1 跑标注「未经对拍」）；自审不算一跑。**快速模式**（用户明说要快）：2 跑（A、B），独报成真率高时建议补第 3 跑。

## 脚本与资源

- 技能文件：`~/.agents/skills/shy-code-review/SKILL.md`（薄封装，引用上游 `code-review`，无 scripts/references）。
- 命令指针：`~/.config/opencode/commands/shy-code-review.md`（`/shy-code-review` 入口，同款模板）。
- 外圈配套（产品仓库 tasknotes-aireporter）：`docs/agents/subagent-models.md`（A/B/C 矩阵 + 凑满 3 跑降级行）；`AGENTS.md`「Shy 技能路由」节（链路点名四个原版技能时改走 shy- 版）。

## 降级与边界

- 运行失败不是换模型的许可；换模型是显式决策（问用户或按仓库约定）。
- 轴间永不合并、不重排（上游原则）。
- 默认 3 跑（实验质量甜点）；快速模式 2 跑并标注；4 跑及以上不外推（边际≈0、噪声涨）。

## 验收标准

- [x] `SKILL.md` 已落盘：frontmatter `name`/`description`（≤1024 字符），正文含三跑协议、轴内裁决四步、完成判据、降级边界 —— 本次交付事实（episode）
- [x] `validate_skill.py <技能目录>` 输出 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] SKILL.md 逐条覆盖「行为与步骤」2–6 —— 判定：对照本节逐条读（语义）
- [x] 上游 `~/.agents/skills/code-review/` 未被本次交付写入 —— 本次交付事实（episode）
- [x] 外圈配套齐：`subagent-models.md` 运行 1–3 矩阵 + 降级行、`AGENTS.md`「Shy 技能路由」节、`/shy-code-review` command —— 判定：逐个文件读（语义）。（其中 `subagent-models.md` 外圈项**已被 REQ-0002 取代**）
- [x] 真实跑一次 `shy-code-review`：两轴报告齐、每条 finding 带票数与裁决、被剔除的有依据 —— 判定：看一次真实运行的报告（行为）

## 范围外

- 修改 `code-review` 及任何 mattpocock 技能文件。
- 修改 `shy-skill-suite` 的 `run_checks.py` 检查注册表。
- 默认 4 跑及以上、串行自适应遍数（快速模式的「补跑建议」除外：3 跑并行发出延迟≈2 跑，串行补跑反而多一轮往返）。
- 插件级 skill 工具硬拦截（OpenCode 文档站当前不可达、不猜插件 API；路由先走 AGENTS.md 指令层）。
- 实现完成后自动进评审 / 评测。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 骨架 + SKILL.md + 本 REQ 落盘；Gate 后订正验收标记（复合括号 → 行尾裸标记）；外圈 `docs/agents/subagent-models.md` 同步修订 | validate_skill `status: ok`；run_checks 绿（迁移债 0）；track_requirements 无错 | 实现交付 |
| 2 | 2026-09-23 | 默认遍数 2 → 3（对齐实验结论「3 遍质量甜点」），加快速模式 2 跑 + 补跑建议 | 本轮 Gate 重跑绿 | （行为）项仍待首次真实运行取证 |
| 3 | 2026-09-23 | 模型矩阵改 A/B/C 三模型各一、缺一凑满 3 跑；补 `/shy-code-review` command；AGENTS.md 加「Shy 技能路由」（`implement` 链点名 `code-review` 时改走本技能） | 本轮 Gate 重跑绿 | （行为）项仍待首验，status 留 in-progress |
| 4 | 2026-09-23 | 首次真实运行（shy-implement 链收尾审查，2 轴 × 3 跑矩阵 A/B/C 全成功、零降级，裁决 12 条采信 / 4 条剔除） | 本次会话的两轴报告 | （行为）项已验收，转 done |
| 5 | 2026-09-24 | 模型来源收敛为**用户级矩阵唯一来源**（REQ-0002）：本技能不再读仓库级 `docs/agents/subagent-models.md` | 本轮 Gate 重跑绿 | 外圈 `subagent-models.md` 项随之作废；status 保持 done |

## 备注 / 待办

逼问：跳过（依据：本对话已完整取舍——对照实验数据、B+A 方案、shy- 命名、遍数策略（3 默认 / 快速 2）、模型矩阵（A/B/C 各一、缺一凑满）、链路重定向均已由用户拍板或指正）。
静态项未走 `check:` 注册：注册表在 `shy-skill-suite/scripts/run_checks.py`（套件资产，本次范围外），以 `（语义）`+明确判定命令代替。
待办：OpenCode 文档站可达后评估插件级硬拦截（替换 AGENTS.md 软路由）。
