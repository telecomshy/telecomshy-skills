# shy-skill-suite · 验收契约（acceptance）

> 目的：把"两个原始痛点是否解决"定义成**可复现命令 + 期望输出**，作为交接给实施方的完成判据。
> 判定人：**外部独立评估**——只跑命令看输出，**不看设计文档**（设计文档可改，命令输出不可改）。
> 停止标准：本表**全部硬性判据通过**。**不是** "finding = 0"。
> 命令一律在**仓库根**执行。日期：2026-09-18。
>
> **结论（2026-09-18）：A1–A6 / B1–B3 / S1–S5 全部通过 —— 两个原始痛点 A（复审循环）、B（功能/修复分开）均已解决。** 剩余机制细节见 §3（登记于 `cleanup.md`，不阻断）。

---

## 1. 两个原始痛点

| 痛点 | 来源 | 原始判据 |
| --- | --- | --- |
| **A · 复审循环** | 每次复审都发现新问题、修完又有，反复改 REQ | 复审**不再重读历史散文** |
| **B · 功能/修复混** | 49 份 REQ 里一半是 fix，分不清"能做什么 / 下一步做什么" | **feature / fix 能分开看** |

---

## 2. 硬性判据（全过 = 两个问题解决）

### A · 复审循环

| # | 判据 | 命令 | 期望输出 | 当前 |
| --- | --- | --- | --- | --- |
| **A1** | 迁移债清零：历史散文全部归入 不变量 / episode | `python skills/shy-skill-suite/scripts/run_checks.py --root . --skill shy-skill-suite` | 末行 `未分类(迁移债) 0` | ✅ 0 |
| **A2** | 复审范围 = 不变量集；未定项**读即分类**（不是"读一遍标 migration 原样留下"） | 读 `skills/shy-skill-suite/references/reviewing-skills.md` Step 3 | 有"读到即分类"字样 | ✅ |
| **A3** | 无害措辞改动 → 0 假回归 | `python docs/shy-skill-suite/design/pilot-0046.py .` | 退出码 `0` | ✅ 0 |
| **A4** | 真实复审验证：改一处无害措辞 → 不产生"措辞 → 回归"类 finding | 人工执行，见 `reviewing-skills.md` | 无"措辞 → 回归"类 finding | ✅ **以 Gate 代理通过**（`REQ-0050` 迭代记录 3：改 `收工判据→收尾判据`，`run_checks` 26/26 无 FAIL，已复原） |
| **A5** | **归类正确性**：`（episode）` 不含行为判据、`（语义）` 不含可机械判定词 | `python docs/shy-skill-suite/classify_audit.py .` | 退出码 `0`（`E=0`、`S=0`、白名单为空） | ✅ `E=0`、`S=0` |
| **A6** | **Gate 秒级 + 全局 check 去重**：同一个 check 不随 REQ 条数重复执行 | 计时 `python skills/shy-skill-suite/scripts/run_checks.py --root . --skill shy-skill-suite`；并数输出里 `skill-validate-ok` 出现次数 | 耗时 **≤ 10s**；`skill-validate-ok` 只出现 **1** 次 | ✅ **9.0s / 1 次** |

> **A 的结束点 = A1 归零 + A5 通过 + A6 秒级。** 只清债（A1）不够——把行为判据标成 `（episode）` 会让它**永久脱离 Gate**，把可执行的标成 `（语义）` 会让复审**每轮仍读散文**（A5 查这两种）；而 Gate 若慢到几十秒，就没人"每次改动都跑"，收敛机制同样退化（A6）。
> **A4 口径（2026-09-18 用户确认）**：A4 原意是"真实复审（Discovery）无假回归 finding"；实施证据为 **Gate 代理**——措辞改动只可能触发 Gate 的 check，不可能触发 12 条（语义）主观判据，结论等价；且真实复审现只读 6 行为 + 12 语义 = 18 条，成本极低。故接受代理证据，A4 记通过。

### B · 功能/修复分开

| # | 判据 | 命令 | 期望输出 | 当前 |
| --- | --- | --- | --- | --- |
| **B1** | feature 视图独立 | `python skills/shy-skill-suite/scripts/track_requirements.py --root . --kind feature` | `"status": "ok"`，只含 feature | ✅ ok / 22 |
| **B2** | fix 视图独立 | `python skills/shy-skill-suite/scripts/track_requirements.py --root . --kind fix` | `"status": "ok"`，只含 fix | ✅ ok / 17 |
| **B3**（推荐，非阻断） | 问题数合并读数：cleanup + fix + 红不变量 | `run_checks` 输出 | 一行给出 `open / fixed` 合计 | ✅ `问题: open=22 fixed=17` |

### S · 系统不骗人（诚实性，必须先于 A/B 验收）

| # | 判据 | 命令 | 期望输出 | 当前 |
| --- | --- | --- | --- | --- |
| **S1** | 带迁移债时 Gate **不得判绿** | 注入 1 条未分类项后跑 `run_checks`（见 `classify_audit.py` 同款隔离副本） | 打印 `[debt] …`，退出码 `1` | ✅ 已独立复现（rc=1） |
| **S2** | 无 `docs/`（技能单独部署）时**不得假绿** | `python skills/shy-skill-suite/scripts/run_checks.py --root . --skill no-such-skill; echo $LASTEXITCODE` | 打印 `[n/a] …不得当绿`，退出码 `1` | ✅ 退出码 1 |
| **S3** | `state.json` 的债目标与设计口径一致 | `Get-Content docs/shy-skill-suite/state.json` + 读设计 §4.7 | 二者都要求 `unclassified_criteria = 0`，无"不要求债清零" | ✅ 已统一为 0 |
| **S4** | 未分类项有明确标记或 Step 3 不再引用它 | `run_checks` 输出的 `未分类(迁移债)` | `0`（四类齐全） | ✅ 0 |
| **S5** | `converged` 由独立方判定，非同一 agent 自证 | 流程：外部评估跑本表 | 本表即独立 verdict | ✅（本文件承担） |

---

## 3. 明确不在本契约内（设计机制细节 → `cleanup.md` backlog）

以下是已知、可枚举的工程项，**不作为"两个痛点是否解决"的判据**，只登记不阻断：

- ~~`（episode）` 的护栏~~ → **已升为硬判据 A5**（`classify_audit.py`）；
- 契约漂移防护（不变量集快照比对）；
- `invariant_budget_growth` 强制（超限报红）；
- `cleanup_ttl_gate_runs` 的 Gate 运行计数与条目老化；
- `cleanup.md` 的写权命令与 `dedup_key` 归一化；
- `epic` 编号体系与 feature→不变量登记；
- `unmigrated_reqs` 债单位（当前只算 `unclassified_criteria`）。

---

## 4. 验证命令汇总（复制即用）

```powershell
# A1 / S1
python skills/shy-skill-suite/scripts/run_checks.py --root . --skill shy-skill-suite

# A3
python docs/shy-skill-suite/design/pilot-0046.py .

# A5 归类正确性（期望 E=0、S=0、白名单空、退出码 0）
python docs/shy-skill-suite/classify_audit.py .

# A6 Gate 秒级 + 去重（期望 ≤10s；skill-validate-ok 只出现 1 次）
$t = Measure-Command { python skills/shy-skill-suite/scripts/run_checks.py --root . --skill shy-skill-suite | Out-Null }
$t.TotalSeconds
python skills/shy-skill-suite/scripts/run_checks.py --root . --skill shy-skill-suite | Select-String 'skill-validate-ok'

# B1 / B2
python skills/shy-skill-suite/scripts/track_requirements.py --root . --kind feature
python skills/shy-skill-suite/scripts/track_requirements.py --root . --kind fix

# S2
python skills/shy-skill-suite/scripts/run_checks.py --root . --skill no-such-skill

# S3
Get-Content docs/shy-skill-suite/state.json
```

---

## 5. 冻结声明

- **设计文档到此冻结**：不再新增机制；本表的 V1–V9 剩余项是 backlog，不是新一轮设计。
- **无真实使用触发（真实失败 / 用户显式要求）不得修改设计文档**——否则即为重演"设计文档自身的复审循环"。
- 每完成一项 A/S 判据，**跑本表对应命令**记录输出；不靠再开一轮评审推进。
