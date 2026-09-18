---
id: REQ-0042
title: P2 清理批（复审 iteration-1 的 4 条 P2）
skill: shy-skill-suite
status: done
kind: fix
iteration: 2
created: 2026-09-17
updated: 2026-09-17
blocked_by: []
related: [REQ-0024, REQ-0026, REQ-0040, REQ-0041]
---

# REQ-0042 P2 清理批（复审 iteration-1 的 4 条 P2）

## 问题与目标

2026-09-17 复审（`skills/shy-skill-suite-workspace/iteration-1/findings.json`）的 4 条 **P2**（P2 不阻断 `done`，按规范**攒批一次性处理**，这条 REQ 就是那个批）：

1. **token 可能采不到** → `token_ratio` 恒 1.0，看着像"没多花"，其实是"没测到"；规范没提醒。
2. **baseline 隔离死结**没写进规范：技能内容可在磁盘搜到 + 必须读文件时，"无技能 baseline"隔离不了。
3. **`scripts/__pycache__/`** 交付卫生没有检查能发现。
4. **计数漂移**：REQ 把"脚本数 = 8"当验收标准，现为 11 → 每加脚本就制造"假 done"。

目标：一次清掉这 4 条，且**都改成不易腐的形式**（口径写成文字说明、计数改成存在性）。

## 触发与分支

- 复审 P2 攒批到收敛点。
- 用户说"清理一下那些 P2 / 修一下这些小毛病"。

## 行为与步骤

1. **`running-evals.md` 边界节**：加两条——
   - token 缺失时 `avg_tokens=0`、`token_ratio` 恒 1.0 属"没测到"，**无效，不得当结论**（耗时同理，超时/重试会污染 `time_ratio`）。
   - baseline 约定：**改技能用旧版快照**；"无技能" baseline **只适用**于内容不可搜、且不依赖读文件的技能。
2. **`selftest.py`**：末尾加**非致命** `WARN`——技能目录内若存在 `__pycache__`，提示"交付前清理"（跑脚本生成属正常，故不判失败）。
3. **REQ-0026 的计数判据去数字**：把"CLI 数 = 8"改成"脚本清单与 `scripts/` 实际一致（**不写死数量**）"。
4. **`run_checks.py`**：注册本 REQ 的检查。

## 脚本与资源

- 改 `references/running-evals.md`、`scripts/selftest.py`、`scripts/run_checks.py`。
- 改 `docs/shy-skill-suite/requirements/REQ-0026-*.md`（去数字）。
- 不改脚本行为、不改三轴结构。

## 降级与边界

- `__pycache__` 检查是**警告**不是失败：跑脚本必然生成，交付前清理即可（打包时排除见 `REQ-0036`，仍 deferred）。
- 历史 prose 里描述"当时 7→8 个脚本"的**记录不删**（那是史实）；只改会被反复重判的**验收判据**。

## 验收标准

- [x] `running-evals.md` 含 token 无效提醒（"没测到" / `token_ratio` 无效） — （episode）
- [x] `running-evals.md` 含 baseline 约定（旧版快照 + 无技能 baseline 的适用条件） — （episode）
- [x] `selftest.py` 含 `__pycache__` 的非致命警告 — （episode）
- [x] `REQ-0026` 验收判据不含写死的"= 8" — （episode）
- [x] `selftest.py` 仍全绿（加警告未破坏用例） — `check:skill-selftest`
- [x] `validate_skill.py skills/shy-skill-suite` → `status: ok`、退出码 0 — `check:skill-validate-ok`

## 范围外

- 不改各脚本行为。
- 不启动 `REQ-0036` 打包（`__pycache__` 的自动排除归它）。
- 不清洗所有历史 REQ 的数字（只修会被重判的判据）。

## 迭代记录

| 轮次 | 日期 | 本轮改动 | 证据 | 结论 / 下一步 |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-17 | 落需求并实施 4 条 P2（token 口径 / baseline 约定 / `__pycache__` 警告 / 计数去数字） | `run_checks.py` + `selftest.py` + `validate_skill` 全绿 | 待确认回写 |
| 2 | 2026-09-17 | **回写**：4 条 P2 全部修完（token 口径 / baseline 约定 / `__pycache__` 警告 / 计数去数字化），秒级门绿、无新发现 → 自动回写 `done`。附带修了自己的检查 bug（`req0042-count-free` 误把引用旧值判成违反）。 | `run_checks` 37 通过 / 0 失败；`selftest` 20/20；`validate` ok | **done** |

## 备注 / 待办

- 来源：`iteration-1/findings.json` 的 4 条 P2。
- 与 `REQ-0040` 的关系：`__pycache__` 警告加在 `selftest.py`，与脚本自测同处。