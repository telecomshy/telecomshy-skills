# knowledge-distill · 清理台账（cleanup ledger）

> 自洽 / 卫生类问题的**唯一归宿**。**不进 findings、不阻断 done**；在收敛点或顺手时结清。
> 字段：`id` / `dedup_key` / 问题 / `first_seen` / `status`（open / fixed / wontfix）/ `resolved_in` / evidence。
> 本台账 2026-09-19 复审（iteration-1）建立。

| id | dedup_key | 问题 | first_seen | status | resolved_in | evidence |
| --- | --- | --- | --- | --- | --- | --- |
| CL-0001 | `stale:REQ-0001-questions-name` | `REQ-0001` 验收标准与备注写根疑问索引为 `疑问.md`，实现与 SKILL.md 已统一为 `收录疑问.md`（`aed037e` 改名）。属过期验收文字：检查未机械执行、措辞落后 | iteration-1 | fixed | 2026-09-19 | 全文 `疑问.md` → `收录疑问.md`（验收 / 备注 / 行为与步骤 / 树图 / 脚本与资源） |
| CL-0002 | `deadcode:strip-aigc` | `skill_tools.py:512` / `:538` 的 `_strip_aigc_frontmatter_block`、`_strip_aigc_watermark_line` 无任何生产调用点，仅被自身单测覆盖 | iteration-1 | open | | `Select-String -Pattern '_strip_aigc_\w+\('` → 仅 2 处 def + 4 处 test；生产代码 0 调用 |
| CL-0003 | `declare:compatibility-missing` | SKILL.md 无 `compatibility` 声明，但实际依赖 Python 3（脚本）、首次有道配置需联网下载 CLI、单测依赖第三方 pytest | iteration-1 | open | | `Select-String -Pattern 'compatibility' skills/knowledge-distill/SKILL.md` → 0 命中 |
| CL-0004 | `legacy:00-index-name` | `_iter_notes` docstring（`skill_tools.py:303`）仍以 `00-分类索引.md` 描述被排除的索引文件；代码行为正确（兼容旧库），仅措辞停留在旧结构 | iteration-1 | open | | `skill_tools.py:61,303,309` |

## 备注

- 本次复审**未当场修**任何一条：`CL-0001` 需决定需求措辞、`CL-0002` 若删函数需同步改单测（非纯机械）、`CL-0003` 需确认客户端是否认该字段、`CL-0004` 属语义措辞。
- `CL-0002` / `CL-0004` 若确认只做卫生清理，可在下一次收敛点一并结清并标 `fixed`。
