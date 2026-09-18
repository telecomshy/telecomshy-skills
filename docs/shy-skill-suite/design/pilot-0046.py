#!/usr/bin/env python3
"""试点 / 回归守卫（设计说明 §6 step 0）：在 `REQ-0046` 上验证"退休子串 check、留行为不变量"。

在**隔离副本**上跑（不碰仓库）。步骤：
  1. 若副本里还有 4 条子串 check 的验收标准 → 删掉（降为 episode）；
     仓库已迁移时这步为空操作，脚本退化为**回归守卫**。
  2. 基线 → 记录实际条数。
  3. 无害措辞打磨 → 期望 **0 假警报**（子串 check 已退休）。
  4. 注入真回归 → 期望 **仍被抓**（行为不变量在）。

验收：3 得 rc=0、4 得 rc≠0。

用法:
    python docs/shy-skill-suite/design/pilot-0046.py [repo_root]

退出码:
    0  通过（(a) 0 假警报 + (b) 抓到真回归）
    1  失败
    2  参数 / 环境错误
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = "shy-skill-suite"
REQ_FILE = "REQ-0046-implement-review-separation.md"
RETIRE = ("req0046-two-paths", "req0046-user-triggered", "req0046-triage", "req0046-skill-rule")
WORDING = [
    ("不自动再审", "不再自动复审"),
    ("实现路", "实现路径"),
    ("评审路", "评审路径"),
    ("逐条分拣", "逐条筛选"),
]


def run(root: Path, script_rel: str, *args: str) -> tuple[int, str]:
    script = root / "skills" / SKILL / "scripts" / script_rel
    p = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def checks(root: Path) -> tuple[int, str, list[str]]:
    rc, out = run(root, "run_checks.py", "--root", ".", "--skill", SKILL)
    lines = out.splitlines()
    tail = [ln for ln in lines if ln.startswith("check:")]
    fails = [ln for ln in lines if ln.startswith("[FAIL]")]
    return rc, (tail[-1] if tail else out.strip()[-200:]), fails


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    src_skill = repo / "skills" / SKILL
    src_docs = repo / "docs" / SKILL / "requirements"
    if not src_skill.is_dir() or not src_docs.is_dir():
        print("参数错误：找不到技能 / 需求目录", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="pilot-0046-") as tmp:
        root = Path(tmp)
        shutil.copytree(src_skill, root / "skills" / SKILL)
        shutil.copytree(src_docs, root / "docs" / SKILL / "requirements")

        # 1. 迁移：删掉 4 条子串 check 的验收标准（降为 episode）。
        #    仓库已迁移时这里自然为空操作，脚本退化为"回归守卫"（(a)(b) 仍有效）。
        req = root / "docs" / SKILL / "requirements" / REQ_FILE
        lines = req.read_text(encoding="utf-8").splitlines()
        kept = [ln for ln in lines if not any(r in ln for r in RETIRE)]
        dropped = len(lines) - len(kept)
        if dropped:
            req.write_text("\n".join(kept) + "\n", encoding="utf-8")
            print(f"[迁移] REQ-0046 删掉 {dropped} 条子串 check 验收标准（本副本内），保留行为不变量")
        else:
            print("[迁移] REQ-0046 已迁移（0 条待删）——退化为回归守卫，只跑 (a)(b)")

        rc0, base, _ = checks(root)
        print(f"[基线]   rc={rc0}  {base}")

        # 3. 无害措辞打磨 → 期望 0 假警报
        lc = root / "skills" / SKILL / "references" / "lifecycle.md"
        t = lc.read_text(encoding="utf-8")
        for a, b in WORDING:
            t = t.replace(a, b)
        lc.write_text(t, encoding="utf-8")
        rc1, after, fails1 = checks(root)
        print(f"[A 措辞] rc={rc1}  {after}")
        for ln in fails1:
            print(f"         FAIL: {ln}")

        # 4. 注入真回归 → 期望仍被抓
        rcf = root / "skills" / SKILL / "scripts" / "run_checks.py"
        src = rcf.read_text(encoding="utf-8")
        old = 'skip_exec = (fm.get("status") or "").strip() not in ("in-progress", "done")'
        new = 'skip_exec = (fm.get("status") or "").strip() in ("deferred", "out-of-scope")'
        if old not in src:
            print("参数错误：run_checks.py 锚点未找到", file=sys.stderr)
            return 2
        rcf.write_text(src.replace(old, new), encoding="utf-8")
        rc2, regr, fails2 = checks(root)
        print(f"[B 回归] rc={rc2}  {regr}")
        for ln in fails2:
            print(f"         FAIL: {ln}")

        a_ok = rc1 == 0
        b_ok = rc2 != 0
        print(f"\n验收 (a) 措辞打磨 0 假警报: {a_ok}")
        print(f"验收 (b) 真回归被抓:       {b_ok}")
        ok = rc0 == 0 and a_ok and b_ok
        print("试点结果:", "通过" if ok else "失败")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
