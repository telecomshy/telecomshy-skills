# shy-skill-suite · 清理台账（cleanup ledger）

> 自洽 / 卫生类问题的**唯一归宿**（设计说明 §4.3）。**不进 findings、不进工单、不阻断 done**；在收敛点或顺手时结清。
> 字段：`id` / `dedup_key`（去重键）/ `first_seen` / `status`（open / fixed / wontfix）/ `resolved_in` / evidence。
> 状态读数：`open` 须在 **N 次 Gate 运行内**转 `fixed` 或经用户决定转 `wontfix`（设计 §4.3）。

| id | dedup_key | 问题 | first_seen | status | resolved_in | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| CL-0001 | `dup:不自动再审` | 同句规则「不自动再审」在 5 处重复（`SKILL.md:33`、`lifecycle.md:79`、`reviewing-skills.md:163`、`run_checks.py:359`、`commands/shy-apply.md:5`） | iteration-3 | **fixed** | 2026-09-20 | 复验：`Select-String -Pattern '不自动再审'` → 仅 `lifecycle.md:92`（定义）+ `run_checks.py:1282/1284`（check 字面量）；`SKILL.md:33` 与 `reviewing-skills.md:181` 的重复句已删、留 `lifecycle.md` 阶段 3 指针；`commands/shy-apply.md` 已随 REQ-0073 删除 |
| CL-0002 | `dup:逐条分拣` | 「逐条分拣」在 5 处重复（`lifecycle.md:21,72`、`running-evals.md:78`、`SKILL.md:13,33`） | iteration-3 | **fixed** | 2026-09-20 | 复验：`Select-String '逐条分拣'` → 0 命中；5 处统一为术语「分拣」（定义在 `glossary.md`），去掉重复的「逐条」限定 |
| CL-0003 | `dup:静默秒级门` | 「静默秒级门」在 4 处重复（`lifecycle.md:60,62,79`、`SKILL.md:33`） | iteration-3 | **fixed** | 2026-09-20 | 复验：`Select-String '静默秒级门'` → 仅 `lifecycle.md:71`（`Gate（静默秒级门）` 别名，定义一处）；`SKILL.md:33`、`lifecycle.md:73,92` 改回术语「Gate」 |
| CL-0004 | `dup:终局产物` | 「终局产物」规则 3 处重复（`reviewing-skills.md:165`、`running-evals.md:86`、`render_report.py:350`） | iteration-3 | **fixed** | 2026-09-20 | 复验：`Select-String '终局产物'` → 仅 `reviewing-skills.md:183`（定义）；`running-evals.md:136` 与 `render_report.py:525` 改为指针（「报告只在 Step 8 生成一次」） |
| CL-0005 | `deadcheck:req0039/0041/0043` | 8 条 check 注册给 out-of-scope REQ（`req0039-*`、`req0041-*`、`req0043-*`），永不执行 | iteration-3 | **fixed** | 2026-09-18 | 8 条已从注册表移除；对应 REQ 均 out-of-scope / `superseded_by: REQ-0046` |
| CL-0006 | `metacheck:req0046-superseded` | `req0046-superseded` 断言别的 REQ 文档（meta），应退休为 episode | iteration-3 | **fixed** | 2026-09-20 | 复验：`run_checks.py --list` 不含 `req0046-superseded`；REQ-0046 验收 4 行已标 `（episode）`（`req0050-retired` 报 episode=5）；Gate 全绿 |
| CL-0007 | `meta:req0030-req0025-superseded` | 同上，`req0030-req0025-superseded` 是 meta check | iteration-3 | **fixed** | 2026-09-20 | 复验：`run_checks.py --list` 不含该名；REQ-0030:89「`REQ-0025` frontmatter 含 `superseded_by`」已标 `（episode）` |
| CL-0008 | `meta:req0042-count-free` | 同上，`req0042-count-free` 是 meta check | iteration-3 | **fixed** | 2026-09-20 | 复验：`run_checks.py --list` 不含该名；REQ-0042:57「`REQ-0026` 判据不含写死的『= 8』」已标 `（episode）` |
| CL-0009 | `meta:req0049-no-phantom-raw` | 同上，`req0049-no-phantom-raw` 是 meta check | iteration-3 | **fixed** | 2026-09-20 | 复验：`run_checks.py --list` 不含该名；REQ-0049:58「0 份 REQ 引用 raw 报告路径」已标 `（episode）` |
| CL-0010 | `doc:SKILL-md-42-lifecycle-ref` | `SKILL.md:42` 裸 `lifecycle.md` 引用缺 `references/` 前缀 | iteration-3 | **fixed** | REQ-0050 同批 | 现为 `references/lifecycle.md` |
| CL-0011 | `doc:optimize-docstring` | `optimize_description.py` docstring 称「保证两边都有正负例」，小集时 test 为空 | iteration-3 | **fixed** | REQ-0050 同批 | 改为「样本足够时尽量分层」 |
| CL-0012 | `dup:优先删其次改` | 「优先删，其次改，最后才加」两处逐字重复 | iteration-3 | **fixed** | REQ-0050 同批 | `SKILL.md:30` 改指针，仅 `reviewing-skills.md:21` 保留 |
| CL-0013 | `hygiene:pycache` | 技能目录内 `scripts/__pycache__/`（跑脚本生成） | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：`.gitignore:2` 已忽略 `__pycache__/`（`git check-ignore` 命中）；`selftest.py` 报**非致命** WARN（REQ-0042 口径）。生成物，跑脚本即重生——无法机械“修”，删了下一跑又出现，故保持 open（不删用户目录外内容） |
| CL-0014 | `design:budget-口径` | 设计文档 §8 问「`invariant_budget` 初值」、§4.7 已改「增长率上限」，两口径不同步 | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：§8 措辞已由「初值」变为「`invariant_budget_growth` 的 k 取多少（每个 feature 净增上限）」，与 §4.7「增长率上限」一致——字面不同步已消失；但 **k 取多少**仍是未决设计问题 → 待用户决策：k 的取值 |
| CL-0015 | `design:§10.4-估算` | §10.4 估算数字不闭合（各项相加 > 227，未交代重叠） | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：`ticket-contract-redesign.md:256` 粗分 40–60 + 120 + 40 + 39 = 239–259 > 227，未交代重叠——仍成立；设计文档冻结，属设计级修 |
| CL-0016 | `script:EPISODE_RE-脆弱` | `EPISODE_RE` 只认 `（episode）`/`(episode)`；全角/半角变体、方括号、大小写会静默计入未标，虚增债 | iteration-3 | **fixed** | 2026-09-20 | 复验：`EPISODE_RE` 收紧为 `[（(\[【]\s*episode\s*[）)\]】]` + `re.IGNORECASE`（覆盖全/半角括号、方/六角括号、大小写、空白）；实测 `（episode）` `(episode)` `[episode]` `【episode】` `（Episode）` `（EPISODE）` 均命中；`run_checks` 的 `（episode）` 计数 **155 不变**、Gate 全绿 |
| CL-0017 | `script:trial-run-0046-失效` | `trial-run-0046.py` 断言「措辞打磨 → 假警报」，REQ-0050 后该断言反了，脚本退出码 1 | iteration-3 | **fixed** | REQ-0050 同批 | 已退休（删除）；`pilot-0046.py` 改为幂等回归守卫 |
| CL-0018 | `design:§9§10-该搬走` | 设计文档 §9（验证）/§10（实施台账）是证据/台账，不是提案；按 §1 根因应进 REQ / 本台账，暂留设计文档 | iteration-3 | deferred | 2026-09-24 | 复验（2026-09-20）：§9/§10 仍在 `ticket-contract-redesign.md:205-258`（冻结设计，文内已自注“暂留此处待搬迁”）。搬迁是跨较大改动 → 待用户决策：是否把 §9/§10 搬进 REQ / 本台账 |
| CL-0019 | `debt:227-拆句` | **A（复审循环）的消失点**：227 条未分类散文需逐条判成 不变量 / `（episode）` / 未定，让 `untagged` 单调降到 0。Step 3 已改为"读即当场分类" | iteration-3 | **fixed** | 2026-09-20 | 复验：`run_checks.py --root . --skill shy-skill-suite` → `未分类(迁移债) 0`、`converged: true`；`state.json` `debt_targets.unclassified_criteria=0`。债已归零 |
| CL-0020 | `state:converged-budget-unread` | `state.json` 的 `converged` / `invariant_budget_growth` / `cleanup_ttl_gate_runs` 仍无脚本读（`debt_targets` 已被 Gate 读） | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-24）：`cleanup_ttl_gate_runs` **已接线**（REQ-0081：Gate 逐条计龄 + 黄告警）；`converged_since` / `invariant_budget_growth` 仍无人读。→ 待用户决策：是否接线后两者 |
| CL-0021 | `guard:episode-无护栏` | `（episode）` 是无人校验的自由文本标记——agent 把真不变量标成 episode 即可绕过 Gate；应比照"契约漂移防护"（改 episode 需挂工单 + Gate 比对快照） | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：`run_checks.py` 只计数 `EPISODE_RE`、无快照比对。属设计级护栏 → 待用户决策：（episode）是否需要“改必挂工单 + Gate 比对快照”的护栏 |
| CL-0022 | `debt:unmigrated_reqs-未算` | `state.json` 声明两个债目标，但只算了 `unclassified_criteria`（标准数），`unmigrated_reqs`（未迁移 REQ 数）无数据 | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：`Select-String` 全部脚本 → `unmigrated_reqs` 无任何读写；“未迁移 closed REQ”的判定口径未定。→ 待用户决策：`unmigrated_reqs` 是否接线、以何口径算 |
| CL-0023 | `cleanup:写权/dedup` | 台账无写命令、`dedup_key` 是自由文本、`resolved_in` 自由文本 → 关闭路径不可执行、去重不可靠 | iteration-3 | **fixed** | 2026-09-24 | 复验（2026-09-20）：`run_checks.py` 只读台账计数（`cleanup_counts`），无写命令；`dedup_key` 仍为自由文本。→ 待用户决策：是否提供台账写命令与 `dedup_key` 归一化规则 |
| CL-0024 | `design:机制无状态戳` | 设计文档各机制未标"已接线 / 仅文档"，读者分不清哪条是活的 | iteration-3 | **wontfix** | 2026-09-24（用户决定） | 复验（2026-09-20）：§6 有 `✅ 已接线` / `◐ 文档已写、脚本未强制` 标注、§10.1 有实施表，但 §4 各机制（4.4/4.5/4.7）本身仍未逐条标状态。设计文档冻结 → 待用户决策：是否逐机制标“已接线 / 仅文档” |
| CL-0025 | `readout:B-合并` | 读数 B 只打印 `cleanup_open`（一来源）；fix 工单数、红不变量数未并入 → "有多少问题"仍需手拼 | iteration-3 | **wontfix** | 2026-09-18（用户决定） | 决定**不合并**红不变量：红=阻断（Gate exit≠0）、台账/fix=积压，两类不同；合并会稀释紧迫度。且 check 跨多张 REQ 无唯一归属（`scaffold-ok` 属 REQ-0001/0027）、按归属去重复杂。B 保持两栏即可 |
| CL-0026 | `misfile:REQ-0028-doc-item` | `REQ-0028`「`SKILL.md` 资源清单不再重复路由表 / 不再抄脚本 `--help` 简介」错标 **`（行为）`**——它是文档质量 / 一次性事实，不是行为契约。A5 的 E 规则只看 episode，故被"改标 （行为）"绕过。正解：**移出验收标准** → 本台账（或 `（episode）`） | iteration-3 | **fixed** | 2026-09-18 | 验收行已删；`classify_audit.py` 复核 E=0 |
| CL-0027 | `misfile:REQ-0031-meta-item` | `REQ-0031`「`REQ-0012` 备注含 `REQ-0027` 对退出码的修订说明」错标 **`（行为）`**——meta / 文档项，同上 | iteration-3 | **fixed** | 2026-09-18 | 验收行已删 |
| CL-0028 | `misfile:REQ-0025-scripts-help-ok` | `REQ-0025`（out-of-scope）「`track --help` 含 `last_verified`」映射到 `check:scripts-help-ok`——判据与 check 语义不符，且该 REQ **永不执行**（死项）。`scripts-help-ok` 本身有效（`REQ-0012/0019/0027` 引用、会真跑），仅此条应删除或改 `（episode）` | iteration-3 | **fixed** | 2026-09-18 | `REQ-0025` 该行已删；`scripts-help-ok` 保留 |
| CL-0029 | `retire:source-field` | `source` 字段是死数据（无脚本读、49/51 未填、`retro` 语义与 `retroactive: true` 重复）→ 从 REQ 模板移除 | iteration-4 | **fixed** | 2026-09-18 | 已删 `writing-requirements.md` §3 / §6 两处；`retro` 由 `retroactive: true` 承担 |
| CL-0030 | `bookkeep:REQ-0046-unchecked` | `REQ-0046` 状态 `done`，但 64–66 三条验收仍未勾；内容已成立（`REQ-0041/0043` 有 `superseded_by`、两条 check PASS） | iteration-4 | **fixed** | 2026-09-18 | 三条已勾；Gate 对两条 check PASS |
| CL-0031 | `doc:REQ-0012-python-placeholder` | `REQ-0012:57` 语义判据用 `{python}` 模板，`agent_runner` 只替换 `{prompt}`——照抄 rc=1（WinError 2），证据不可复现 | iteration-4 | **fixed** | 2026-09-18 | 判据改为 `"<python 解释器路径>"` 并注明只有 `{prompt}` 被替换 |
| CL-0032 | `doc:REQ-0052-crossref` | `REQ-0052` 行为 3 要求 §1 ↔ §4 交叉引用；实际两节都只指 `reviewing-skills.md` Step 8，互不引用 | iteration-4 | **fixed** | 2026-09-18 | §1 路由句与 §4 各加互指 |
| CL-0033 | `dup:falsification-rule` | 「`falsification`/`evidence` 留 JSON、不进报告」在 Step 8 出现 3 次（164/169/204）+ `SKILL.md:32` 1 次 | iteration-4 | **fixed** | 2026-09-18 | 定义一处（Step 8 三字段 bullet）+ 关系一条（淘汰数 bullet）；其余已删或改指针（2026-09-18 复核） |
| CL-0034 | `dup:converged-formula` | `converged` 公式在 `glossary.md:28` / `reviewing-skills.md:168` / `lifecycle.md:108` 各写一遍，与 glossary「含义以本文件为准」冲突 | iteration-4 | **fixed** | 2026-09-18 | 公式只留 `glossary.md`；Step 8 与 `lifecycle.md` 改指针 |
| CL-0035 | `cache:SKILL-scripts-line` | `SKILL.md:41` 把 8 类脚本职责全列一遍；`running-evals.md:7-12` 与各脚本 `--help` 已可查，属 cache | iteration-4 | **fixed** | 2026-09-18 | 压成指针：接口看 `--help`、评测清单看 `running-evals.md`、Gate 三件套 |
| CL-0036 | `gap:lifecycle-stage6` | `lifecycle.md` 阶段 6（复盘）只有触发条件、无完成判据；阶段 0–5 都有 | iteration-4 | **fixed** | 2026-09-18 | 阶段 6 补完成判据（落 REQ / 台账 + 过 Gate + track ok） |
| CL-0037 | `bookkeep:REQ-0047-unchecked` | `REQ-0047` 验收第 3 条「`validate_skill.py ...` → `status: ok`」`[ ]` 未勾，但 `check:skill-validate-ok` 已绿（勾选漂移） | iteration-5 | **fixed** | 2026-09-21 | 复验：`run_checks.py --root . --skill shy-skill-suite` → `[PASS] REQ-0002 skill-validate-ok rc=0 status=ok`；已勾 `[x]` 并注明（2026-09-21 本复审 Step 8 台账机械项当轮结清） |
| CL-0038 | `drift:lifecycle-fork-count` | `lifecycle.md:57` 称 `knowledge-distill` 有「6 个分支」，实际其路由表只有 5 行 | iteration-14 | **fixed** | 2026-09-24 | 已改「5 个分支」；复验：`Select-String '5 个分支'` 命中、`'6 个分支'` 0 命中 |
| CL-0039 | `drift:wr-criteria-classes` | `writing-requirements.md:64` 写「标四类之一」却只列三类（漏 `（episode）`） | iteration-14 | **fixed** | 2026-09-24 | 已补齐四类清单（`check:` / `（行为）` / `（语义）` / `（episode）`） |
| CL-0040 | `dup:three-way-separation` | 「实现/评审/评测三路分离、不自动评审」同义重复：`SKILL.md:33`、`lifecycle.md:26/72/78/131` | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 剪枝 3 跑均报、独立裁判判「弱成立（点处强化）」；去重需重排 lifecycle 阶段 3，属较大改动 → 待用户决策 |
| CL-0041 | `dup:description-writing` | `description` 写法（祈使句/聚焦意图/pushy）与 user-invoked 整句在 `reviewing-skills.md:65-67` 与 `writing-skills.md:7/9/15` 逐字重复 | iteration-14 | **fixed** | 2026-09-24 | 复审侧「措辞」「调用方式」两条改指针（保留「硬约束」条）；复验 `Select-String '用祈使句|只有人手动调用' reviewing-skills.md` → 0 命中 |
| CL-0042 | `dup:fingerprint-rule` | 「指纹匹配则引用、否则静态/过期」在 `running-evals.md:22`、`reviewing-skills.md:74/78/89/130`、`lifecycle.md:82`、`SKILL.md:33` 重复 ≥6 处 | iteration-14 | **fixed** | 2026-09-24 | 裁判**成立**；可收为指针 |
| CL-0043 | `dup:triage-def` | 「分拣=立即修/以后修/丢弃、逐条不批量」在 `glossary.md:43`、`reviewing-skills.md:202`、`lifecycle.md:89-92`、`running-evals.md:138` 重复 | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立（分属定义/判据/操作/UI） |
| CL-0044 | `dup:converged-def` | 「`converged` 由脚本算出、agent 不得手写」在 `glossary.md:28`、`reviewing-skills.md:197/202`、`lifecycle.md:120` 重复 | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立 |
| CL-0045 | `dup:cleanup-ledger-entry` | 「自洽/卫生项进 `cleanup.md` 台账、不进 findings」在 `glossary.md:25`、`reviewing-skills.md:111`、`writing-requirements.md:12/88` 重复 4 处 | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立（跨关切应用） |
| CL-0046 | `dup:command-list` | 5 个命令名与作用在 `SKILL.md:44` 与 `lifecycle.md:18-24` 各列一遍（SKILL 已自指 lifecycle） | iteration-14 | **fixed** | 2026-09-24 | `SKILL.md:44` 压为指针（保留命令名以满足 `req0076/req0072` 断言） |
| CL-0047 | `dup:report-once` | 「报告只在 Step 8 生成一次」在 `reviewing-skills.md:204`、`running-evals.md:136`、`subagents.md:70` 重复 | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 裁判弱成立 |
| CL-0048 | `dup:delete-first` | 「先删后加」在 `SKILL.md:30`、`reviewing-skills.md:21/242` 重复 | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 裁判弱成立 |
| CL-0049 | `dup:multirun-gate-summary` | 复审多跑闸门要点在 `SKILL.md:34` 与 `reviewing-skills.md:33-38` 整段重复 | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 裁判弱成立（顶层摘要+指针） |
| CL-0050 | `dup:avoid-word-collision` | `glossary.md:8/11` 把同一 `_避免_` 词「自动检查」同时挂给 Gate 与 Discovery | iteration-14 | **fixed** | 2026-09-24 | Discovery 的 `_避免_` 改为「巡检、自动检查」，与 Gate 去撞车 |
| CL-0051 | `dup:discovery-def` | `lifecycle.md:80` 复述 `glossary.md:10` 的 Discovery 定义 | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 裁判弱成立 |
| CL-0052 | `dup:split-criteria` | 拆分判据在 `lifecycle.md:55` 与 `writing-skills.md:60-61` 重叠 | iteration-14 | **wontfix** | 2026-09-24（用户决定） | 裁判弱成立（粒度不同） |
| CL-0053 | `term:axis-misuse` | `SKILL.md:34` 把 触发/安全 叫「轴」，与 `glossary.md:31`「三轴=行为/需求/标准」冲突 | iteration-14 | **fixed** | 2026-09-24 | `SKILL.md:34` 与闸门改「触发与安全两类」；复验 `Select-String '触发轴|安全轴'` → 0 命中 |
| CL-0054 | `doc:axis-mapping` | `reviewing-skills.md:15/17` 三问（触发/有效性/需求一致性）与三轴（行为/需求/标准）映射不成立 | iteration-14 | **fixed** | 2026-09-24 | 改为「三问映射到三条轴」并说明标准轴另立、不对应三问之一 |
| CL-0055 | `index:running-evals-scripts` | `running-evals.md:26-32` 脚本表漏 `render_report.py` 与 `skill_fingerprint.py` | iteration-14 | **fixed** | 2026-09-24 | 表内补两行 |
| CL-0056 | `doc:count-attribution` | `lifecycle.md:72` 括号紧贴 `selftest.py`，易读作「episode/迁移债/台账 open」由它输出（实为 `run_checks.py`） | iteration-14 | **fixed** | 2026-09-24 | 注明该计数由 `run_checks.py` 的输出末尾给出 |
| CL-0057 | `doc:scope-objects` | `reviewing-skills.md:4` 称「完整文件集」只列 SKILL/scripts/references/assets，漏 `commands/`、`evals/` | iteration-14 | **fixed** | 2026-09-24 | 适用对象补 `commands/`、`evals/` |
| CL-0058 | `doc:running-evals-params` | `running-evals.md:11` 列出的参数与同文示例（:90/:96/:106）不一致（示例缺取证参数） | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立（示例不完整） |
| CL-0059 | `term:Tier-undefined` | `lifecycle.md:55` 用 Tier 1/2/3/4 作拆分判据，全套件未定义 Tier | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立（同句有内联解释） |
| CL-0060 | `doc:selfcontain-vs-docs` | `reviewing-skills.md:165` 自包含规则未区分「文件内链接」与「工作流运行时读写 `docs/<skill>/…`」 | iteration-14 | **fixed** | 2026-09-24 | 补「指技能文件内的链接；工作流读写 `docs/` 是开发仓库用法、部署后按非开发仓库降级」 |
| CL-0061 | `doc:triage-location-unique` | `reviewing-skills.md:202` 回写「按 `location` 对应 findings」，但同 `file:line` 可有多条 finding，映射不唯一 | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立 |
| CL-0062 | `noop:generic-batch` | 通用废话/常识批次：`reviewing-skills.md:148-155/188/244-246`、`writing-skills.md:29/33/37`、`writing-requirements.md:82/90`、`running-evals.md:163`（后半） | iteration-14 | **fixed** | 2026-09-24 | 裁判弱成立；逐条判删 |

## 备注

- 本台账 2026-09-18 建立；`CL-0010`–`CL-0012`、`CL-0017` 是建台账时顺手结清的（已 fixed）。
- **2026-09-18（`REQ-0058`）新规则**：**能当场确认并机械修的，当场修掉并标 `fixed` + `evidence`，不留 `open`**；只有需要用户决策或跨较大改动的才留 `open`。`CL-0030`–`CL-0036` 已按此结清。
- **2026-09-20（`REQ-0075`）补写权与时点**：复审的"发现"由子代理做、子代理**禁写**；**机械项由主 agent 在 Step 8（出报告前）当轮结清**，需决策项留 `open` 并在报告一句话提示。见 `skills/shy-skill-suite/references/reviewing-skills.md` Step 8。
- `open` 项的关闭路径：见设计说明 §4.3（N 次 Gate 运行内 fixed/wontfix；`wontfix` 需用户显式决定）。
- 与 `REQ-0032`/`REQ-0033`（已退休的自洽批）重叠的项，一并收进本台账，不再各自开 REQ。
- **`dedup_key` 规则（2026-09-24 定，CL-0023）**：统一为 `<类别>:<规范主体>`——类别取 `dup` / `hygiene` / `drift` / `doc` / `term` / `noop` / `cache` / `sediment` 等；主体取**规则定义句的关键词**（不是复述处），小写、去标点与空白。新建 / 复核台账前先按此归一化，再与本表已有 key 比对：**命中即视为同一条**（不改 open/fixed 状态，仅追加复验）。
- **台账写命令（待接线，CL-0023 余项）**：`fixed`/`wontfix` 仍只能手改 Markdown；如需 `run_checks --close <id>` 之类命令，另开 REQ。
- **无写权归属（评审 H5，待定）**：目前只能手改 Markdown；`fixed`/`wontfix` 无命令、无时机约定。
- 2026-09-18：`CL-0029` 是 `REQ-0052`「REQ 路由规则」的卫生项验证用例——它按新规则只登记本台账、**未开 REQ**。
- **A4 待办（非自洽类，仅登记）**：验收契约 `acceptance.md` 的 **A4（真实复审）尚无证据**——`skills/shy-skill-suite-workspace/` 无 15:00 之后产物。需跑 1 次真实复审 + 改一处无害措辞，确认 **0 假回归**，把命令与输出记下。做完 A 才算干净（A1/A2/A3/A5 已通过）。

### 2026-09-20 清理小结

- **范围**：本轮清 `status: open` 的 19 条（`CL-0001`~`CL-0004`、`CL-0006`~`CL-0009`、`CL-0013`~`CL-0016`、`CL-0018`~`CL-0024`）；只处理已有条目，未新开范围。
- **结清 10 条**（`fixed`）：`CL-0001`/`CL-0002`/`CL-0003`/`CL-0004`（重复文本去重，保留一处定义、其余改指针）、`CL-0006`~`CL-0009`（4 条 meta check 已退休、REQ 行标 `（episode）`）、`CL-0016`（`EPISODE_RE` 收紧，episode 计数 155 不变）、`CL-0019`（迁移债已归零：`未分类(迁移债) 0`）。
- **保持 9 条 `open`**（需用户决策 / 生成物 / 冻结设计）：`CL-0013`（`__pycache__` 生成物，gitignore + selftest WARN 口径）、`CL-0014`（k 取值）、`CL-0015`（§10.4 估算不闭合）、`CL-0018`（§9/§10 搬迁）、`CL-0020`（state 字段接线）、`CL-0021`（episode 护栏）、`CL-0022`（`unmigrated_reqs` 口径）、`CL-0023`（台账写权 / dedup 归一化）、`CL-0024`（机制状态戳）。**未擅自标 `wontfix`**。
- **复验**：台账旧引用的行号 / 计数多已漂移（如 `CL-0001` 的 `commands/shy-apply.md:5` 已随 `REQ-0073` 删除、`CL-0019` 的 227 已归零、`CL-0002`/`CL-0003`/`CL-0004` 行号后移）——每条均先跑命令核对再处置。
- **Gate（2026-09-20 实跑）**：`validate_skill.py skills/shy-skill-suite` → `status: ok` rc=0；`run_checks.py --root . --skill shy-skill-suite` → `60 通过 / 0 失败`、`未分类(迁移债) 0`、`converged: true` rc=0；`selftest.py` → `36/36`（1 条 `__pycache__` WARN）rc=0；`track_requirements.py --root .` → `status: ok` rc=0。
