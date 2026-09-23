---
name: shy-improve-codebase-architecture
description: 三探索代理 + 共识/孤证合并的架构深化机会扫描，是 mattpocock improve-codebase-architecture 的强化封装（原技能不变）。当用户要「/shy-improve-codebase-architecture」「shy 扫架构」「shy 架构审查/架构体检」，或想找浅模块、想让代码更好测更好懂时使用。三个探索子代理（三个模型各一）各走一遍代码库找摩擦点，主代理合并候选并用 deletion test 裁决孤证，再按原技能出 HTML 报告，候选卡标注发现票数。用户明说要快可降为 2 个探索者（快速模式）。
disable-model-invocation: true
---

# shy-improve-codebase-architecture

`improve-codebase-architecture` 的强化封装。**上游技能是流程事实源**：先用 Skill 工具加载 `improve-codebase-architecture`（它会再加载 `codebase-design` 取词汇表），按它执行（范围选择、CONTEXT.md / ADR、HTML 报告、grill 选定候选），仅「探索」一步从单代理改为三代理对拍。

分工依据：探索是品味活（上游原话：凭摩擦感、不套死板启发式），不同眼睛看到不同摩擦——对拍直接适用。探索者数取 3（三档票数 `3/3`、`2/3`、`1/3`，与审查对拍同一甜点）；并行发出，3 个与 2 个延迟几乎相同。

## 覆盖点

### 1. 范围选择（照上游）

热点回溯 / 用户指定方向、读 `CONTEXT.md` 与相关 ADR，都照上游。范围定了再发探索。

### 2. 三探索（原「单个探索子代理」）

发 **3 个探索子代理**，并行、互不可见、各自全量走同一范围，模型 = **三个不同模型各一**（ID 查找顺序：仓库 `docs/agents/subagent-models.md` → 用户级 `~/.config/opencode/shy-models.md` → 问用户；某模型不可用则凑满 3 个：一模型 2 个 + 另一模型 1 个）。解析模型 ID 先查模型目录，看不到想要的加 `all: true`；不猜 ID。brief 沿用上游的摩擦清单与 deletion test 要求，输出改为结构化候选卡（每卡：涉及文件 / 摩擦 / deletion test 论证 / 深化建议），词汇按上游要求用 `codebase-design` 术语 + `CONTEXT.md` 领域名词。

**快速模式**（仅当用户明说要快 / 要省）：2 个探索者（票数 `2/2`、`1/2`）。

### 3. 合并与裁决（主代理）

1. 归并两份清单为候选集（同题合并），标**票数**（`3/3`、`2/3`、`1/3`）；
2. **共识候选**（≥2/3）免检进报告；
3. **孤证候选**（`1/3`）逐张复核：亲自跑 **deletion test**（删掉它是集中复杂度还是平移？）并核对引用的文件属实；站不住 → 剔除，记一句依据。

### 4. 报告与 grill（照上游 + 票数）

HTML 报告照上游（临时目录、卡片、before/after、Top recommendation），每张卡加**发现票数**徽章；孤证卡注明「经 deletion test 复核成立」。报告后照上游问用户选哪个候选 grill。

## 完成判据

- 每张候选卡有票数；孤证卡都有 deletion test 复核记录；剔除的有依据。
- 词汇符合上游要求（`codebase-design` 术语 + 领域名词），与 ADR 冲突的卡照上游标注。
- HTML 已写到临时目录并告知用户绝对路径（照上游）。

## 降级与边界

- 某探索跑失败 → 同模型重试一次；再失败按剩余跑数出报告：2 个仍算对拍（标注），仅 1 个标注「未经对拍」。
- 裁决只用 deletion test 与事实核对，不引入新候选；新想法留给 grill 阶段。
- 3 个是默认；快速模式 2 个并标注；4 个及以上不外推。
