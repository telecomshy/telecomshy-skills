#!/usr/bin/env python3
"""生成触发评测集（starter eval set）。

从 SKILL.md 的 description 抽取触发短语与关键词，产出 should-trigger / should-not-trigger
查询。纯启发式、无 LLM、无第三方依赖；产出是"起手集"，需人工或 agent 复核后再用。

用法:
    python generate_eval_set.py <skill_dir> [--output evals/evals.json] [--lang auto|zh|en]

输出 schema（与 aggregate_benchmark / optimize_description 对齐）:
    {
      "skill_name": "...",
      "evals": [
        {"eval_id": 0, "eval_name": "...", "prompt": "...",
         "input_files": [], "assertions": [{"name": "...", "check": "...", "weight": 1.0}],
         "should_trigger": true}
      ]
    }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from skill_utils import force_utf8_stdio, has_cjk, load_skill, write_text

_QUOTE_PATTERNS = [
    r'"([^"]{2,60})"',
    r"'([^']{2,60})'",
    r"“([^”]{2,60})”",
    r"「([^」]{2,60})」",
    r"『([^』]{2,60})』",
]
_TRIGGER_SECTION = re.compile(
    r"(?:触发条件|触发|Triggers?|Use when|Use this skill when)\s*[:：]\s*([^\n]+)",
    re.IGNORECASE,
)
_ASCII_WORD = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_SPLIT_RE = re.compile(r"[、，,;；|/]")
_CJK_ONLY = re.compile(r"^[\u3400-\u9fff]+$")

_STOP_WORDS = {
    "use", "when", "user", "says", "the", "and", "for", "with", "that",
    "this", "from", "are", "was", "were", "been", "have", "has", "had",
    "will", "would", "could", "should", "may", "might", "can", "does",
    "not", "but", "also", "more", "into", "than", "then", "its", "all",
    "any", "each", "both", "such", "only", "own", "same", "other",
    "skill", "skills",
}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _clean_phrase(text: str) -> str:
    text = re.sub(r"[\"'“”「」『』]", "", text).strip()
    text = re.sub(r"^(?:例如|比如|如|当用户说|用户说|说)\s*[:：]?\s*", "", text).strip()
    return text.strip("。！？!?，,、；;：: 　")


def extract_trigger_phrases(description: str) -> list[str]:
    """抽取引号短语，以及 ``触发：`` 段落里各分支的短语。

    先按 ``；``/``;`` 分分支；分支内有引号则取引号内容，否则按顿号/逗号切分。
    引号内容再按 ``/`` 拆成同义说法。
    """
    raw: list[str] = []
    for pattern in _QUOTE_PATTERNS:
        raw.extend(re.findall(pattern, description))

    match = _TRIGGER_SECTION.search(description)
    if match:
        for branch in re.split(r"[；;]", match.group(1)):
            quoted: list[str] = []
            for pattern in _QUOTE_PATTERNS:
                quoted.extend(re.findall(pattern, branch))
            if quoted:
                raw.extend(quoted)
            else:
                raw.extend(_SPLIT_RE.split(branch))

    phrases: list[str] = []
    for item in raw:
        for part in _clean_phrase(item).split("/"):
            part = part.strip()
            if not (2 <= len(part) <= 60):
                continue
            if _CJK_ONLY.match(part) and len(part) < 3:
                continue
            phrases.append(part)

    return _dedupe(phrases)


def extract_keywords(description: str, phrases: list[str]) -> list[str]:
    """ASCII 关键词 + 中文触发短语（作为关键词候选）。"""
    words = [
        w for w in _ASCII_WORD.findall(description.lower())
        if len(w) > 3 and w not in _STOP_WORDS
    ]
    cjk = [p for p in phrases if has_cjk(p) and 2 <= len(p) <= 20]
    return _dedupe(words + cjk)[:20]


def _trigger_assertion(name: str, lang: str) -> dict[str, Any]:
    check = (
        f"「{name}」技能被触发并进入其工作流"
        if lang == "zh"
        else f"The {name} skill activated and began its workflow"
    )
    return {"name": "skill-activated", "check": check, "weight": 1.0}


def _no_trigger_assertion(name: str, lang: str) -> dict[str, Any]:
    check = (
        f"「{name}」技能未被触发"
        if lang == "zh"
        else f"The {name} skill did NOT activate"
    )
    return {"name": "skill-not-activated", "check": check, "weight": 1.0}


_ZH_SHOULD = [
    "帮我{kw}",
    "我想{kw}",
    "我需要{kw}，能处理吗",
    "顺便问下，{kw}怎么弄？",
    "{kw}这件事交给你了",
]
_EN_SHOULD = [
    "hey can you help me {kw} something?",
    "I've got this {kw} task I need done",
    "so my boss wants me to {kw} — can you handle that?",
    "quick question: how do I {kw} with this tool?",
    "need to {kw} asap, what's the best approach?",
]
_ZH_NEAR_MISS = [
    "解释一下{kw}这个概念",
    "给我讲讲{kw}的入门教程",
    "帮我写一段介绍{kw}的文档",
    "帮我看看这个报错，堆栈里提到了{kw}",
    "重构一下处理{kw}的这段代码",
    "给{kw}模块补单元测试",
    "审查这个改动了{kw}的 PR",
    "搜一下 GitHub 上{kw}相关的开源项目",
    "把这段{kw}相关的代码翻译成 Python",
    "给{kw}画一张架构图",
]
_EN_NEAR_MISS = [
    "Can you explain what {kw} means in general terms?",
    "Write documentation about the concept of {kw} for my README",
    "I'm learning about {kw} -- what are some good tutorials?",
    "What's the difference between {kw} and similar approaches?",
    "Search GitHub for open-source projects related to {kw}",
    "Debug this error I'm getting -- it mentions {kw} in the stack trace",
    "Refactor this function that handles {kw} logic to be more readable",
    "Add unit tests for the {kw} module in my project",
    "Review this PR that changes how we handle {kw}",
    "Set up a CI/CD pipeline that includes {kw} validation steps",
]


def _fill(templates: list[str], keywords: list[str], fallback: str, count: int) -> list[str]:
    prompts: list[str] = []
    for i in range(count):
        template = templates[i % len(templates)]
        keyword = keywords[i % len(keywords)] if keywords else fallback
        prompts.append(template.format(kw=keyword))
    return prompts


def generate_eval_set(skill_dir: str, output: str | None = None, lang: str = "auto") -> dict[str, Any]:
    path = Path(skill_dir).resolve()
    frontmatter, _body, errors = load_skill(path)
    if frontmatter is None:
        return {"error": "; ".join(errors) or "Could not parse SKILL.md frontmatter"}

    name = frontmatter.get("name", path.name)
    description = str(frontmatter.get("description", ""))

    if lang == "auto":
        lang = "zh" if has_cjk(description) else "en"

    phrases = extract_trigger_phrases(description)
    keywords = extract_keywords(description, phrases)
    fallback = "这个" if lang == "zh" else "this"

    evals: list[dict[str, Any]] = []
    eval_id = 0

    direct = phrases[:5] if phrases else []
    if not direct and keywords:
        direct = keywords[:5]
    for phrase in direct:
        prompt = phrase if lang == "zh" else f"I need to {phrase}"
        evals.append({
            "eval_id": eval_id,
            "eval_name": f"trigger-direct-{eval_id}",
            "prompt": prompt,
            "input_files": [],
            "assertions": [_trigger_assertion(name, lang)],
            "should_trigger": True,
        })
        eval_id += 1

    for prompt in _fill(_ZH_SHOULD if lang == "zh" else _EN_SHOULD, keywords, fallback, 5):
        evals.append({
            "eval_id": eval_id,
            "eval_name": f"trigger-casual-{eval_id}",
            "prompt": prompt,
            "input_files": [],
            "assertions": [_trigger_assertion(name, lang)],
            "should_trigger": True,
        })
        eval_id += 1

    near_misses = _fill(_ZH_NEAR_MISS if lang == "zh" else _EN_NEAR_MISS, keywords, fallback, 10)
    for i, prompt in enumerate(near_misses):
        evals.append({
            "eval_id": 100 + i,
            "eval_name": f"no-trigger-near-miss-{i}",
            "prompt": prompt,
            "input_files": [],
            "assertions": [_no_trigger_assertion(name, lang)],
            "should_trigger": False,
        })

    should_trigger_count = sum(1 for e in evals if e["should_trigger"])
    result: dict[str, Any] = {
        "skill_name": name,
        "skill_path": str(path),
        "generated_from": "description + trigger section",
        "lang": lang,
        "evals": evals,
        "metadata": {
            "trigger_phrases_found": len(phrases),
            "keywords_found": len(keywords),
            "total_evals": len(evals),
            "should_trigger_count": should_trigger_count,
            "should_not_trigger_count": len(evals) - should_trigger_count,
        },
    }

    if output:
        write_text(output, json.dumps(result, indent=2, ensure_ascii=False))

    return result


def main() -> int:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(description="Generate a starter trigger eval set from a SKILL.md")
    parser.add_argument("path", help="Path to skill directory containing SKILL.md")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    parser.add_argument("--lang", default="auto", choices=["auto", "zh", "en"], help="Template language")
    args = parser.parse_args()

    if not Path(args.path).is_dir():
        print(json.dumps({"error": f"Not a directory: {args.path}"}, ensure_ascii=False), file=sys.stderr)
        return 1

    result = generate_eval_set(args.path, args.output, args.lang)
    if "error" in result:
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 1

    if args.output:
        print(json.dumps({
            "status": "success",
            "output": args.output,
            "total_evals": result["metadata"]["total_evals"],
        }, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
