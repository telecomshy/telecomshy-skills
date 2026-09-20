#!/usr/bin/env python3
"""脚本自测（smoke / contract）。纯标准库，无第三方依赖。

对 `scripts/` 下每个 CLI 跑**契约用例**：成功路径 + 至少一条失败路径。
全程在**临时目录**造 fixture，不碰仓库、不弹浏览器、不装依赖；`render_report` 一律 `--no-open`。

这是"冒烟 / 契约级"，不是穷尽单测：目标是**改了脚本能立刻知道有没有弄坏外壳**。
需要真实 agent runner 的行为 eval **不在这里**（归 `running-evals.md`）。

用法:
    python selftest.py

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
import time
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
    (d / "REQ-0001.md").write_text(
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
    # 真正的契约：可被导入
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

        # --project：技能包 + 开发层（docs/<name>/requirements/ + .gitignore），不预建子目录
        proj = Path(td) / "proj"
        skills = proj / "skills"
        skills.mkdir(parents=True)
        rc5, out5, err5 = run("scaffold_skill.py", "proj-skill", "--path", skills,
                              "--project", "--description", "x")
        proj_skill = (skills / "proj-skill" / "SKILL.md").is_file()
        proj_docs = (proj / "docs" / "proj-skill" / "requirements").is_dir()
        gi = proj / ".gitignore"
        gi_lines = gi.read_text(encoding="utf-8").splitlines() if gi.is_file() else []
        gi_ok = all(e in gi_lines for e in ("*-workspace/", "reports/", "__pycache__/"))
        no_subdirs = not any((skills / "proj-skill" / d).exists()
                             for d in ("scripts", "references", "assets", "evals", "commands"))
        case("scaffold --project → 技能包 + docs + .gitignore",
             rc5 == 0 and proj_skill and proj_docs and gi_ok and no_subdirs,
             f"rc5={rc5} skill={proj_skill} docs={proj_docs} gitignore={gi_ok} 无子目录={no_subdirs}")

        rc6, out6, err6 = run("scaffold_skill.py", "proj-skill", "--path", skills, "--project")
        gi_after = gi.read_text(encoding="utf-8").splitlines()
        no_dup = all(gi_after.count(e) == 1 for e in ("*-workspace/", "reports/", "__pycache__/"))
        case("scaffold --project 幂等 → skipped + .gitignore 不重复",
             rc6 == 0 and '"skipped"' in out6 and no_dup, f"rc6={rc6} no_dup={no_dup}")

        rc7, out7, err7 = run("scaffold_skill.py", "Bad_Name", "--path", skills, "--project")
        no_leak = not (proj / "docs" / "Bad_Name").exists()
        case("scaffold --project 非法名 → 非 0 + 不落盘", rc7 != 0 and no_leak, f"rc7={rc7}")


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
    rc2, out2, err2 = run("agent_runner.py", "--runner", "heuristic", "--prompt", "hello")
    try:
        heuristic_ok = rc2 == 0 and "triggered" in json.loads(out2)
    except Exception:  # noqa: BLE001 - 解析失败即判失败
        heuristic_ok = False
    case("agent_runner heuristic → rc0 + JSON", heuristic_ok, f"rc2={rc2}")
    rc3, out3, err3 = run("agent_runner.py", "--runner", "cmd", "--cmd", "cmd /c echo hi", "--prompt", "x")
    case("agent_runner 缺 {prompt} → rc1 + stderr 非空",
         rc3 == 1 and bool(err3.strip()) and not out3.strip(), f"rc3={rc3}")
    with tempfile.TemporaryDirectory(prefix="st-ar-slow-") as td:
        marker = Path(td) / "slow_marker.py"
        marker.write_text(
            "import time\nprint('SENTINEL-TRIGGER', flush=True)\ntime.sleep(60)\n", encoding="utf-8")
        tpl = f'"{PY}" "{marker}" {{prompt}}'
        t0 = time.monotonic()
        rc4, out4, err4 = run("agent_runner.py", "--runner", "cmd", "--cmd", tpl,
                              "--detect", "SENTINEL-TRIGGER", "--prompt", "x", "--timeout", "90")
        elapsed = time.monotonic() - t0
        case("agent_runner 命中即停（不等会话跑完）",
             rc4 == 0 and '"triggered": true' in out4 and elapsed < 30, f"rc4={rc4} {elapsed:.1f}s")


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
        rc3, out3, err3 = run("track_requirements.py", "--root", root, "--view", "overview")
        overview_ok = (rc3 == 0 and "frontier" in out3 and "kind" in out3
                       and not out3.lstrip().startswith("{"))
        case("track_requirements --view overview → 人读摘要", overview_ok, f"rc3={rc3}")


def t_render_reqs():
    with tempfile.TemporaryDirectory(prefix="st-rq-") as td:
        t = Path(td)
        d = t / "docs" / "demo" / "requirements"
        d.mkdir(parents=True)
        (d / "REQ-0001.md").write_text(
            "---\nid: REQ-0001\ntitle: 演示一句话\nskill: demo\nstatus: ready\nkind: feature\n"
            "iteration: 1\ncreated: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\n---\n\n"
            "# REQ-0001 演示一句话\n\n## 问题与目标\n\n这是背景首段。\n", encoding="utf-8")
        rc, out, err = run("render_reqs.py", "--root", t, "--skill", "demo", "--no-open")
        html = t / "reports" / "demo-reqs.html"
        html_text = html.read_text(encoding="utf-8") if html.is_file() else ""
        ok = (rc == 0 and html.is_file() and '"opened": false' in out
              and "<details" in html_text and "新增功能" in html_text
              and "REQ-0001" in html_text and "演示一句话" in html_text
              and "http://" not in html_text)
        case("render_reqs --skill --no-open → rc0 + 自包含 HTML", ok, f"rc={rc} html={html.is_file()}")
        rc2, out2, err2 = run("render_reqs.py", "--root", t, "--no-open")
        case("render_reqs 缺 --skill → 非 0", rc2 != 0, f"rc2={rc2}")
        rc3, out3, err3 = run("render_reqs.py", "--root", t, "--skill", "nope", "--no-open")
        case("render_reqs 技能不存在 → 非 0 + stderr",
             rc3 != 0 and bool((err3 or "").strip()), f"rc3={rc3}")
        rc4, out4, err4 = run("render_reqs.py", "--root", t / "nope", "--skill", "demo", "--no-open")
        case("render_reqs 非法 root → 非 0", rc4 != 0, f"rc4={rc4}")


def t_run_checks():
    rc, out, err = run("run_checks.py", "--list")
    has = "skill-validate-ok" in out
    with tempfile.TemporaryDirectory(prefix="st-chk-") as td:
        root = make_reqs(Path(td), unknown_check=True)
        rc2, out2, err2 = run("run_checks.py", "--root", root)
        case("run_checks --list → rc0 + 已注册检查", rc == 0 and has, f"rc={rc}")
        case("run_checks 未注册 check → rc1", rc2 == 1, f"rc2={rc2}")
        with tempfile.TemporaryDirectory(prefix="st-chk-empty-") as td2:
            (Path(td2) / "docs" / "demo" / "requirements").mkdir(parents=True)
            rc3, out3, err3 = run("run_checks.py", "--root", Path(td2), "--skill", "demo")
            case("run_checks 零 REQ → rc≠0 + n/a",
                 rc3 != 0 and "[n/a]" in (out3 + err3), f"rc3={rc3}")
        with tempfile.TemporaryDirectory(prefix="st-chk-emptyacc-") as td3:
            d3 = Path(td3) / "docs" / "demo" / "requirements"
            d3.mkdir(parents=True)
            (d3 / "REQ-0001.md").write_text(
                "---\nid: REQ-0001\ntitle: x\nskill: demo\nstatus: done\niteration: 1\n"
                "created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\n---\n\n"
                "# REQ-0001 x\n\n## 验收标准\n\n## 范围外\n", encoding="utf-8")
            rc4, out4, err4 = run("run_checks.py", "--root", Path(td3), "--skill", "demo")
            case("run_checks 空验收标准 → rc≠0 + FAIL",
                 rc4 != 0 and "(空验收标准)" in (out4 + err4), f"rc4={rc4}")
        with tempfile.TemporaryDirectory(prefix="st-chk-deferred-") as td4:
            d4 = Path(td4) / "docs" / "demo" / "requirements"
            d4.mkdir(parents=True)
            (d4 / "REQ-0001.md").write_text(
                "---\nid: REQ-0001\ntitle: x\nskill: demo\nstatus: deferred\niteration: 1\n"
                "created: 2026-01-01\nupdated: 2026-01-01\nblocked_by: []\ndefer_reason: x\n---\n\n"
                "# REQ-0001 x\n\n## 验收标准\n\n- [ ] 未来项（行为）\n", encoding="utf-8")
            rc5, out5, err5 = run("run_checks.py", "--root", Path(td4), "--skill", "demo")
            case("run_checks 非活动 REQ 标签不计工作集",
                 rc5 == 0 and "（行为）0" in (out5 + err5), f"rc5={rc5}")


def t_skill_fingerprint():
    with tempfile.TemporaryDirectory(prefix="st-fp-") as td:
        skill = make_skill(Path(td))
        (skill / "references").mkdir()
        (skill / "references" / "r.md").write_text("x", encoding="utf-8")
        (skill / "evals").mkdir()
        (skill / "evals" / "effectiveness.json").write_text('{"cases":[]}', encoding="utf-8")
        rc, out, err = run("skill_fingerprint.py", "--skill-dir", skill)
        try:
            data = json.loads(out)
            fps = data.get("fingerprints") or {}
        except Exception:  # noqa: BLE001 - 解析失败即失败
            fps = {}
        ok = rc == 0 and bool(fps.get("trigger")) and bool(fps.get("effectiveness")) \
            and fps["trigger"] != fps["effectiveness"]
        ws = Path(td) / "iteration-1"
        rc2, out2, err2 = run("skill_fingerprint.py", "--skill-dir", skill,
                              "--write-evidence", ws, "--model", "test/model")
        ev = ws / "evidence.json"
        wrote = rc2 == 0 and ev.is_file() and "test/model" in ev.read_text(encoding="utf-8")
        rc3, out3, err3 = run("skill_fingerprint.py", "--skill-dir", Path(td) / "nope")
        case("skill_fingerprint 分轴 → rc0 + 两轴指纹", ok, f"rc={rc} fps={list(fps)}")
        case("skill_fingerprint 写证据 → evidence.json + 模型", wrote, f"rc2={rc2} wrote={wrote}")
        case("skill_fingerprint 缺 SKILL.md → 非 0", rc3 != 0, f"rc3={rc3}")


def t_run_effectiveness():
    with tempfile.TemporaryDirectory(prefix="st-eff-") as td:
        t = Path(td)
        stub = t / "stub.py"
        stub.write_text(
            "print('Skill \"other-skill\"')\nprint('ANSWER-OK')\n", encoding="utf-8")
        cases = t / "cases.json"
        cases.write_text(json.dumps({
            "skill_name": "demo",
            "cases": [{"eval_id": 0, "eval_name": "s", "prompt": "x",
                       "assertions": [{"name": "a", "check": "c"}]}],
        }, ensure_ascii=False), encoding="utf-8")
        tpl = f'"{PY}" "{stub}" {{prompt}}'
        ws = t / "ws"
        rc, out, err = run("run_effectiveness.py", "--arm", "with_skill", "--cases", cases,
                           "--ws", ws, "--trials", "1", "--workers", "1", "--cmd", tpl,
                           "--detect-skill", "demo")
        timing_p = ws / "eval-0" / "with_skill_0" / "timing.json"
        try:
            timing = json.loads(timing_p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - 缺文件即失败
            timing = {}
        ok = rc == 0 and timing.get("loaded_skills") == ["other-skill"]
        rc2, out2, err2 = run("run_effectiveness.py", "--arm", "baseline",
                              "--cases", t / "nope.json", "--ws", ws, "--cmd", tpl)
        case("run_effectiveness → rc0 + 布局 + 加载技能字段", ok, f"rc={rc}")
        case("run_effectiveness 缺用例集 → 非 0", rc2 != 0, f"rc2={rc2}")


def warn_pycache() -> None:
    """交付卫生警告（非致命）：技能目录内不应带 __pycache__。

    跑脚本时生成属正常，故**不判失败**；打包 / 复制部署前应清理。
    """
    hits = [p for p in SCRIPTS.parent.rglob("__pycache__") if p.is_dir()]
    if hits:
        print(f"[WARN] 交付卫生：技能目录内存在 __pycache__（{len(hits)} 处）——跑脚本生成属正常，交付前清理。")
        for h in hits:
            print("        ", h)


CASES = [
    t_skill_utils, t_validate_skill, t_scaffold_skill, t_generate_eval_set,
    t_optimize_description, t_agent_runner, t_run_effectiveness,
    t_aggregate_benchmark, t_skill_fingerprint,
    t_render_report, t_render_reqs, t_track_requirements, t_run_checks,
]


def main() -> int:
    from skill_utils import force_utf8_stdio

    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="脚本自测（smoke / contract）：对 scripts/ 下每个 CLI 跑成功 + 失败路径契约用例。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python selftest.py\n"
            "\n"
            "退出码:\n  0  全部通过\n  1  有失败\n  2  参数错误\n"
        ),
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
