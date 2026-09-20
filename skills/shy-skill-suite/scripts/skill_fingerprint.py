#!/usr/bin/env python3
"""算技能的证据指纹（分轴、确定性），可选写进 iteration 的 evidence.json。

复审要判断手上的 eval 证据是不是**当前技能版本**产的，就得有指纹。指纹刻意分轴：

- 触发轴 = ``hash(description)``——改 SKILL.md 正文不作废触发证据，改 description 才作废。
- 有效性轴 = ``hash(SKILL.md + references/ + scripts/ + assets/ + evals/effectiveness.json)``。

确定性：文件按相对路径排序、路径统一为 ``/``、只 hash 内容（不掺 mtime / 绝对路径）。

用法:
    python skill_fingerprint.py --skill-dir skills/my-skill
    python skill_fingerprint.py --skill-dir skills/my-skill --axis trigger
    python skill_fingerprint.py --skill-dir skills/my-skill --write-evidence my-skill-workspace/iteration-1 --model deepseek/deepseek-flash
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skill_utils import force_utf8_stdio, merge_evidence, skill_fingerprints

AXES = ("trigger", "effectiveness")


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="算技能的证据指纹（触发轴 = hash(description)；有效性轴 = hash(SKILL.md + references + scripts + assets + evals/effectiveness.json)）。",
        epilog=(
            "示例:\n"
            "  python skill_fingerprint.py --skill-dir skills/my-skill\n"
            "  python skill_fingerprint.py --skill-dir skills/my-skill --axis trigger\n"
            "  python skill_fingerprint.py --skill-dir skills/my-skill --write-evidence ws/iteration-1 --model deepseek/deepseek-flash\n"
            "\n"
            "退出码:\n"
            "  0  成功\n"
            "  1  技能目录无效（缺 SKILL.md）\n"
            "  2  参数错误\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skill-dir", required=True, help="技能目录（含 SKILL.md）")
    parser.add_argument("--axis", default="both", choices=["trigger", "effectiveness", "both"],
                        help="算哪条轴（默认 both）")
    parser.add_argument("--write-evidence", help="iteration 目录；给定则把指纹 + 模型 + 时间写进 <dir>/evidence.json")
    parser.add_argument("--model", help="所用模型 ID（写证据时记录；不钉模型的结论不可复现）")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not (skill_dir / "SKILL.md").is_file():
        print(json.dumps({"error": f"技能目录无效（缺 SKILL.md）: {skill_dir}"}, ensure_ascii=False),
              file=sys.stderr)
        return 1

    fingerprints = skill_fingerprints(skill_dir)
    selected = list(AXES) if args.axis == "both" else [args.axis]
    result = {
        "skill_dir": str(skill_dir),
        "fingerprints": {axis: fingerprints[axis] for axis in selected},
    }
    if args.write_evidence:
        path = merge_evidence(args.write_evidence, skill_dir, tuple(selected),
                              model=args.model)
        result["evidence"] = str(path)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
