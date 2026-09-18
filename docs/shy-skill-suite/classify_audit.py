#!/usr/bin/env python3
"""归类正确性审计（验收契约 A5）。

扫描 `docs/<skill>/requirements/REQ-*.md` 的 `## 验收标准`，找两类错标：

  E · `（episode）` 里含**行为判据**——episode 是"一次性事实、不读、不复扫"，
      把"退出码 / 报错 / status: ok"这类行为契约标成 episode，真回归会永久不可见。
  S · `（语义）` 里含**可机械判定词**——(语义) 是"只能人判"，含 `退出码 / --help /
      status: ok` 说明它本可写成 `check:`（设计 §4.2 准入）。

白名单：确实合理、但会误报的条目写进 `ALLOW`，每条附理由。**有白名单条目即不通过**
（必须显式豁免并计数，不允许默认放过）。

用法:
    python docs/shy-skill-suite/classify_audit.py [repo_root]

退出码:
    0  无错标、无白名单
    1  有错标或白名单非空
    2  参数 / 环境错误
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CRIT = re.compile(r"^\s*-\s*\[[ xX]\]")
EPISODE = re.compile(r"（episode）|\(episode\)")
SEMANTIC = re.compile(r"（语义）|\(语义\)")

# 行为判据词（出现在 episode 里 = 错标）
BEHAVIOR = re.compile(r"退出码|报错|status:\s*ok|stderr|--help|rc\s*=")
# 可机械判定词（出现在 语义 里 = 错标）
MECH = re.compile(r"退出码|--help|stderr|status:\s*ok|rc\s*=")

# 白名单：key = 行首若干字（唯一识别该条），value = 理由。非空即不通过。
ALLOW: dict[str, str] = {}


def criteria(path: Path) -> list[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if CRIT.match(ln)]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    reqdir = root / "docs" / "shy-skill-suite" / "requirements"
    if not reqdir.is_dir():
        print(f"参数错误：找不到 {reqdir}", file=sys.stderr)
        return 2

    e_hits: list[str] = []
    s_hits: list[str] = []
    for f in sorted(reqdir.glob("REQ-*.md")):
        for ln in criteria(f):
            if EPISODE.search(ln) and BEHAVIOR.search(ln):
                e_hits.append(f"{f.name}: {ln}")
            if SEMANTIC.search(ln) and MECH.search(ln):
                s_hits.append(f"{f.name}: {ln}")

    print(f"E（episode 含行为判据）: {len(e_hits)}")
    for x in e_hits:
        print("  " + x)
    print(f"S（语义 含可机械判定词）: {len(s_hits)}")
    for x in s_hits:
        print("  " + x)
    print(f"白名单: {len(ALLOW)}")
    for k, v in ALLOW.items():
        print(f"  {k} — {v}")

    bad = bool(e_hits) or bool(s_hits) or bool(ALLOW)
    print("\nA5:", "不通过" if bad else "通过")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
