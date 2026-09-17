#!/usr/bin/env python3
"""脚本自测（smoke / contract）。纯标准库，无第三方依赖。

对 `scripts/` 下每个 CLI 跑**契约用例**：成功路径 + 至少一条失败路径。
全程在**临时目录**造 fixture，不碰仓库、不弹浏览器、不装依赖；`render_report` 一律 `--no-open`。

这是"冒烟 / 契约级"，不是穷尽单测：目标是**改了脚本能立刻知道有没有弄坏外壳**。
需要真实 agent runner 的行为 eval **不在这里**（归 `running-evals.md`）。

用法:
    python selftest.py [--verbose]

退出码:
    0  全部用例通过
    1  有失败
    2  参数错误
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PY = sys.executable
RESULTS: list[tuple[str, bool, str]] = []


def run(script: str, *args: object, cwd: Path | None = None, env: dict | None = None,
        timeout: int = 60) -> tuple[int, str, str]:
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["SHY_NO_OPEN"] = "1"  # 防弹浏览器
    if env:
        e.update(env)
    proc = subprocess.run(
        [PY, str(SCRIPTS / script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd) if cwd else None, env=e, timeout=timeout,
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def case(name: str, ok: bool, evidence: str) -> None:
    RESULTS.append((name, ok, evidence))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {evidence}")


# --------------------------------------------------------------------------- #
# fixtures（全部落在调用方给的临时目录里）
# --------------------------------------------------------------------------- #

def make_skill(base: Path, name: str = "demo-skill", bad_name: bool = False) -> Path:
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    fm_name = "Bad Name" if bad_name else name
    (d / "SKILL.md").write_text(
        f"---\nname: {fm_name}\ndescription: 演示用技能；当需要演示时使用。\n---\n\n"
        "# Demo\n\n一个用于自测的演示技能。\n",
        encoding="utf-8",
    )
    return d


def make_iteration(base: Path, with_findings: bool = False) -> Path:
    it = base / "iteration-1"
    for run_name, pr in (("with_skill", 1.0), ("baseline", 0.5)):
        d = it / "eval-0" / run_name
        d.mkdir(parents=True, exist_ok=True)
        (d / "grading.json").write_text(json.dumps({"pass_rate": pr}), encoding="utf-8")
        (d / "timing.json").write_text(
            json.dumps({"total_tokens": 10, "total_duration_seconds": 1.0}), encoding="utf-8")
    (it / "eval-0" / "eval_metadata.json").write_text(
        json.dumps({"eval_id": 0, "eval_name": "e0"}), encoding="utf-8")
    if with_findings:
        (it / "findings.json").write_text(json.dumps(
            {"skill": "demo-skill", "verdict": "可合入", "summary": {"candidates": 1, "passed": 1, "falsified": 0},
             "findings": []}, ensure_ascii=False), encoding="utf-8")
    return it


def make_eval_set(base: Path) -> Path:
    p = base / "evals.json"
    p.write_text(json.dumps({
        "skill_name": "demo-skill",
        "evals": [
            {"eval_id": 0, "eval_name": "t0", "prompt": "需要演示时怎么办？",
             "input_files": [], "assertions": [{"name": "a", "check": "c", "weight": 1.0}], "should_trigger": True},
            {"eval_id": 1, "eval_name": "t1", "prompt": "今天天气如何？",
             "input_files": [], "assertions": [{"name": "a", "check": "c", "weight": 1.0}], "should_trigger": False},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return p


def make_reqs(base: Path, dangling: bool = False, unknown_check: bool = False) -> Path:
    d = base / "docs" / "demo-skill" / "requirements"
    d.mkdir(parents=True, exist_ok=True)
    sup = "\nsuperseded_by: REQ-9999" if dangling else ""
    tag = "no-such-check" if unknown_check else "skill-validate-ok"
    (d / "REQ-0001-a.md").write_text(
        f"---\nid: REQ-0001\ntitle: a\nskill: demo-skill\nstatus: done\niteration: 1\n"
        f"created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []{sup}\n---\n\n"
        f"# REQ-0001 a\n\n## 验收标准\n\n- [ ] x — `check:{tag}`\n",
        encoding="utf-8",
    )
    return base


# --------------------------------------------------------------------------- #
# 用例
# --------------------------------------------------------------------------- #

def t_skill_utils():
    rc, out, err = run("skill_utils.py", "--help")  # 非 CLI，--help 会被忽略
    # 真正的契约：可被导入
    rc2, out2, err2 = run("validate_skill.py", "--help")
    p = subprocess.run([PY, "-c", "import sys; sys.path.insert(0, r'%s'); import skill_utils; print('ok')" % SCRIPTS],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    case("skill_utils 可导入", p.returncode == 0 and "ok" in p.stdout, f"rc={p.returncode}")


def t_validate_skill():
    with tempfile.TemporaryDirectory(prefix="st-val-") as td:
        good = make_skill(Path(td))
        rc, out, err = run("validate_skill.py", good)
        rc2, out2, err2 = run("validate_skill.py", good.parent / "nope")
        case("validate_skill 好技能 → ok rc0", rc == 0 and '"status": "ok"' in out, f"rc={rc}")
        case("validate_skill 不存在 → 非 0", rc2 != 0, f"rc={rc2}")


def t_scaffold_skill():
    with tempfile.TemporaryDirectory(prefix="st-scaf-") as td:
        rc, out, err = run("scaffold_skill.py", "new-skill", "--path", td)
        created = (Path(td) / "new-skill" / "SKILL.md").is_file()
        rc2, out2, err2 = run("scaffold_skill.py", "new-skill", "--path", td)
        rc3, out3, err3 = run("scaffold_skill.py", "new-skill", "--path", td, "--force")
        bak = (Path(td) / "new-skill" / "SKILL.md.bak").is_file()
        case("scaffold 新建 → rc0 + SKILL.md", rc == 0 and created, f"rc={rc} created={created}")
        case("scaffold 幂等 → skipped rc0", rc2 == 0 and '"skipped"' in out2, f"rc2={rc2}")
        case("scaffold --force → .bak", rc3 == 0 and bak, f"rc3={rc3} bak={bak}")
        rc4, out4, err4 = run("scaffold_skill.py")
        case("scaffold 缺参 → 非 0", rc4 != 0, f"rc4={rc4}")


def t_generate_eval_set():
    with tempfile.TemporaryDirectory(prefix="st-gen-") as td:
        skill = make_skill(Path(td))
        out = Path(td) / "evals.json"
        rc, so, se = run("generate_eval_set.py", skill, "-o", out)
        ok = rc == 0 and out.is_file() and "evals" in out.read_text(encoding="utf-8")
        rc2, so2, se2 = run("generate_eval_set.py", Path(td) / "nope", "-o", Path(td) / "x.json")
        case("generate_eval_set → rc0 + JSON", ok, f"rc={rc}")
        case("generate_eval_set 缺技能目录 → 非 0", rc2 != 0, f"rc2={rc2}")


def t_optimize_description():
    with tempfile.TemporaryDirectory(prefix="st-opt-") as td:
        skill = make_skill(Path(td))
        es = make_eval_set(Path(td))
        rc, out, err = run("optimize_description.py", skill, "--eval-set", es)
        ok = rc == 0 and '"train"' in out and '"test"' in out
        rc2, out2, err2 = run("optimize_description.py", skill, "--eval-set", Path(td) / "nope.json")
        case("optimize_description(heuristic) → rc0 + train/test", ok, f"rc={rc}")
        case("optimize_description 缺评测集 → 非 0", rc2 != 0, f"rc2={rc2}")


def t_agent_runner():
    rc, out, err = run("agent_runner.py", "--runner", "cmd", "--cmd", "no-such-exe {prompt}", "--prompt", "x")
    case("agent_runner 坏命令 → rc1 + stderr + stdout 空",
         rc == 1 and err.strip() and not out.strip(), f"rc={rc} err={bool(err.strip())} out={bool(out.strip())}")


def t_aggregate_benchmark():
    with tempfile.TemporaryDirectory(prefix="st-agg-") as td:
        it = make_iteration(Path(td))
        rc, out, err = run("aggregate_benchmark.py", it, "--skill-name", "demo")
        ok = rc == 0 and (it / "benchmark.json").is_file()
        empty = Path(td) / "empty" / "iteration-1"
        empty.mkdir(parents=True)
        rc2, out2, err2 = run("aggregate_benchmark.py", empty, "--skill-name", "demo")
        case("aggregate_benchmark → rc0 + benchmark.json", ok, f"rc={rc}")
        case("aggregate_benchmark 空目录 → 非 0", rc2 != 0, f"rc2={rc2}")


def t_render_report():
    with tempfile.TemporaryDirectory(prefix="st-rr-") as td:
        it = make_iteration(Path(td), with_findings=True)
        rc, out, err = run("render_report.py", it, "--no-open")
        ok = rc == 0 and '"opened": false' in out and (it / "report.html").is_file()
        empty = Path(td) / "empty" / "iteration-1"
        empty.mkdir(parents=True)
        rc2, out2, err2 = run("render_report.py", empty, "--no-open")
        case("render_report --no-open → rc0 + report.html + 不打开", ok, f"rc={rc}")
        case("render_report 无数据 → 非 0", rc2 != 0, f"rc2={rc2}")


def t_track_requirements():
    with tempfile.TemporaryDirectory(prefix="st-track-") as td:
        root = make_reqs(Path(td))
        rc, out, err = run("track_requirements.py", "--root", root)
        ok = rc == 0 and '"status": "ok"' in out
        root2 = make_reqs(Path(td) / "dangling", dangling=True)
        rc2, out2, err2 = run("track_requirements.py", "--root", root2)
        case("track_requirements → rc0 ok", ok, f"rc={rc}")
        case("track_requirements 悬空 superseded_by → rc1", rc2 == 1, f"rc2={rc2}")


def t_run_checks():
    rc, out, err = run("run_checks.py", "--list")
    has = "skill-validate-ok" in out
    with tempfile.TemporaryDirectory(prefix="st-chk-") as td:
        root = make_reqs(Path(td), unknown_check=True)
        rc2, out2, err2 = run("run_checks.py", "--root", root)
        case("run_checks --list → rc0 + 已注册检查", rc == 0 and has, f"rc={rc}")
        case("run_checks 未注册 check → rc1", rc2 == 1, f"rc2={rc2}")


def warn_pycache() -> None:
    """交付卫生警告（非致命）：技能目录内不应带 __pycache__。

    跑脚本时生成属正常，故**不判失败**；打包 / 复制部署前应清理（仓库 .gitignore 已忽略）。
    """
    hits = [p for p in SCRIPTS.parent.rglob("__pycache__") if p.is_dir()]
    if hits:
        print(f"[WARN] 交付卫生：技能目录内存在 __pycache__（{len(hits)} 处）——跑脚本生成属正常，交付前清理。")
        for h in hits:
            print("        ", h)


CASES = [
    t_skill_utils, t_validate_skill, t_scaffold_skill, t_generate_eval_set,
    t_optimize_description, t_agent_runner, t_aggregate_benchmark,
    t_render_report, t_track_requirements, t_run_checks,
]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="脚本自测（smoke / contract）：对 scripts/ 下每个 CLI 跑成功 + 失败路径契约用例。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出码:\n  0  全部通过\n  1  有失败\n  2  参数错误\n",
    )
    ap.parse_args()
    for fn in CASES:
        fn()
    warn_pycache()
    failed = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS)} 条用例：{len(RESULTS) - len(failed)} 通过 / {len(failed)} 失败")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
