---
id: REQ-0001
title: 架构扫描改三探索代理对拍，孤证候选过 deletion test 再进报告，不改上游 improve-codebase-architecture
skill: shy-improve-codebase-architecture
status: in-progress
kind: feature
iteration: 2
created: 2026-09-23
updated: 2026-09-23
blocked_by: []
related: []
---

# REQ-0001 架构扫描改三探索代理对拍，孤证候选过 deletion test 再进报告，不改上游 improve-codebase-architecture

## 问题与目标

架构深化机会的扫描是品味活（上游：凭摩擦感、不套死板启发式），单代理单跑漏掉摩擦点是常态（实验同源结论：跑多遍取并集是收益大头，3 遍是质量甜点）。目标：探索改三代理对拍、合并标票数（3/3、2/3、1/3）、孤证候选经主代理跑 deletion test 复核后再进报告。触发场景：用户要「shy 扫架构 / shy 架构审查」。

## 触发与分支

「/shy-improve-codebase-architecture」「shy 扫架构」「shy 架构审查/架构体检」→ 加载上游 `improve-codebase-architecture`（其自身加载 `codebase-design` 取词汇），仅「探索」一步改为三代理。

## 行为与步骤

1. **范围选择**照上游：热点回溯 / 用户指定方向，读 `CONTEXT.md` 与相关 ADR。
2. **三探索**：3 个子代理并行、互不可见、全量走同一范围，模型尽量不同（第三侧复跑便宜侧）；按上游摩擦清单找候选，输出结构化候选卡（文件 / 摩擦 / deletion test 论证 / 深化建议），词汇照上游要求。
3. **合并裁决**：归并标票数（3/3、2/3、1/3）；共识（≥2/3）免检进报告；孤证（1/3）逐张复核——主代理亲自跑 deletion test + 核对文件属实，站不住剔除记依据。
4. **报告 grill** 照上游（HTML、卡片、before/after、Top recommendation），每卡加发现票数徽章，孤证卡注明「经 deletion test 复核成立」。
5. **快速模式**（用户明说要快）：2 个探索者（票数 2/2、1/2）；降级同理按剩余跑数出稿并标注。

## 脚本与资源

- 技能文件：`~/.agents/skills/shy-improve-codebase-architecture/SKILL.md`（薄封装，无 scripts/references）。
- HTML 报告照上游写 OS 临时目录。

## 降级与边界

- 某探索跑失败 → 同模型重试一次；再失败按剩余跑数出报告：2 个仍算对拍（标注），仅 1 个标注「未经对拍」。
- 裁决只用 deletion test 与事实核对，不引入新候选；新想法留给 grill 阶段。
- 3 个是默认（与审查对拍同一甜点）；快速模式 2 个并标注；4 个及以上不外推。

## 验收标准

- [x] `SKILL.md` 已落盘：frontmatter `name`/`description`（≤1024 字符）+ `disable-model-invocation: true`（与上游一致），正文含三探索、合并票数、孤证复核、报告徽章、完成判据 —— 本次交付事实（episode）
- [x] `validate_skill.py <技能目录>` 输出 `status: ok` —— 判定：跑该命令看输出（语义）
- [x] SKILL.md 逐条覆盖「行为与步骤」1–5，且词汇要求（`codebase-design` 术语 + 领域名词）保留 —— 判定：对照本节逐条读（语义）
- [x] 上游 `~/.agents/skills/improve-codebase-architecture/` 未被本次交付写入 —— 本次交付事实（episode）
- [ ] 真实跑一次 `shy-improve-codebase-architecture`：候选卡带票数、孤证卡有 deletion test 复核记录 —— 判定：看一次真实运行的报告（行为）

## 范围外

- 修改上游技能与其 HTML-REPORT.md。
- 四代理及以上对拍、串行自适应探索数。
- grill 阶段的流程改动。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 骨架 + SKILL.md + 本 REQ 落盘；Gate 后订正验收标记（复合括号 → 行尾裸标记） | validate_skill `status: ok`；run_checks 绿（迁移债 0）；track_requirements 无错 | 实现交付 |
| 2 | 2026-09-23 | 探索者 2 → 3（三档票数，对齐「3 遍质量甜点」结论），加快速模式 2 个 | 本轮 Gate 重跑绿 | （行为）项待首次真实运行取证，status 留 in-progress |
| 3 | 2026-09-23 | 模型矩阵改「三模型各一、缺一凑满 3 跑」；补 `/shy-improve-codebase-architecture` command 指针；AGENTS.md 加「Shy 技能路由」（链路点名 `improve-codebase-architecture` 时改走本技能） | 本轮 Gate 重跑绿 | （行为）项仍待首验 |

## 备注 / 待办

逼问：跳过（依据：三探索 + 票数 + deletion test 裁决的方案已在本对话确定并经用户认可，B+A、shy- 命名、遍数策略均已拍板）。
静态项未走 `check:` 注册（注册表属 `shy-skill-suite`，本次范围外），以 `（语义）`+明确判定命令代替。
