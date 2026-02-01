#!/usr/bin/env python3
"""
convert_questions_text_to_bank.py

Convert pasted "Top 10 Questions ..." blocks into a QUESTION_BANK list
for questions.py (Signatures engine).

Usage:
  python convert_questions_text_to_bank.py input.txt --out questions_generated.py
  python convert_questions_text_to_bank.py input.txt --json --out questions_generated.json

Tips:
- Put your pasted content into input.txt.
- Review output; if a few fields are missing, you can patch them in questions.py.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


PERSONAS = ["Listener", "Motivator", "Director", "Expert"]

CATEGORY_HINTS: List[Tuple[str, str]] = [
    (r"\bheart,\s*kidney,\s*and\s*metabolic\b", "CKM"),
    (r"\bcardio.*kidney.*metabolic\b", "CKM"),
    (r"\bhigh blood pressure\b|\bhypertension\b", "HTN"),
    (r"\bheart failure\b", "HF"),
    (r"\bcoronary artery disease\b|\bCAD\b", "CAD"),
    (r"\batrial fibrillation\b|\bAFib\b", "AFIB"),
    (r"\bstroke\b", "STROKE"),
    (r"\bdiabetes\b", "DM"),
]

# Matches: Question 1: “text” OR Question 1: "text" OR Question 1: text
QUESTION_RE = re.compile(
    r"""^\s*Question\s*(\d+)\s*:\s*(?:[“"](?P<q1>.+?)[”"]|(?P<q2>.+))\s*$""",
    re.IGNORECASE,
)

# Matches persona labels, with or without bullet symbols, underscores, etc.
PERSONA_RE = re.compile(
    r"""^\s*(?:[•\-\*_]\s*)?(Listener|Motivator|Director|Expert)\b\s*(?P<rest>.*)$""",
    re.IGNORECASE,
)

ACTION_RE = re.compile(r"^\s*Action\s*Step\s*:\s*(.+)\s*$", re.IGNORECASE)
WHY_RE = re.compile(r"^\s*Why\s*:\s*(.+)\s*$", re.IGNORECASE)


@dataclass
class QuestionItem:
    category: str
    question: str
    responses: Dict[str, str]
    action_step: str = ""
    why_it_matters: str = ""
    source_title: str = ""
    source_url: str = ""


def detect_category_from_line(line: str, current: str) -> str:
    """Update category if heading-like line suggests a new category."""
    low = line.lower()
    for pat, cat in CATEGORY_HINTS:
        if re.search(pat, low, flags=re.IGNORECASE):
            return cat
    return current


def clean_quotes(s: str) -> str:
    s = s.strip()
    # Strip leading/trailing quotes if present
    s = s.strip('“”"')
    return s.strip()


def parse_blocks(lines: List[str]) -> List[QuestionItem]:
    items: List[QuestionItem] = []
    category = "GENERAL"

    current_q: Optional[QuestionItem] = None
    current_persona: Optional[str] = None

    def flush_current():
        nonlocal current_q, current_persona
        if current_q:
            # Ensure all personas exist (empty if missing)
            for p in PERSONAS:
                current_q.responses.setdefault(p, "")
            items.append(current_q)
        current_q = None
        current_persona = None

    for raw in lines:
        line = raw.strip()

        if not line:
            continue

        # Category detection based on headings
        category = detect_category_from_line(line, category)

        # New question?
        m = QUESTION_RE.match(line)
        if m:
            flush_current()
            q_text = m.group("q1") or m.group("q2") or ""
            q_text = clean_quotes(q_text)
            current_q = QuestionItem(category=category, question=q_text, responses={})
            current_persona = None
            continue

        # Persona line?
        pm = PERSONA_RE.match(line)
        if pm and current_q:
            persona = pm.group(1).capitalize()
            rest = pm.group("rest").strip()
            # Often rest begins with a quoted message
            msg = clean_quotes(rest)
            # If rest is empty, message may be on next line; we’ll accumulate later
            current_q.responses[persona] = msg if msg else current_q.responses.get(persona, "")
            current_persona = persona
            continue

        # Action / Why lines
        am = ACTION_RE.match(line)
        if am and current_q:
            current_q.action_step = clean_quotes(am.group(1))
            current_persona = None
            continue

        wm = WHY_RE.match(line)
        if wm and current_q:
            current_q.why_it_matters = clean_quotes(wm.group(1))
            current_persona = None
            continue

        # If we’re inside a persona and this line looks like continuation, append it.
        if current_q and current_persona:
            # Avoid accidentally appending new headings
            if line.lower().startswith("question "):
                continue
            prev = current_q.responses.get(current_persona, "")
            # Append with space, keeping it readable
            current_q.responses[current_persona] = (prev + " " + clean_quotes(line)).strip()
            continue

        # If we have a question but not in persona, ignore other lines (intro text etc.)

    flush_current()
    return items


def to_python(questions: List[QuestionItem]) -> str:
    data = [asdict(q) for q in questions]
    # Produce a python snippet: QUESTION_BANK = [...]
    return "QUESTION_BANK = " + json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Input text file containing pasted question blocks.")
    ap.add_argument("--out", default="questions_generated.py", help="Output file path.")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of Python.")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.readlines()

    questions = parse_blocks(lines)

    # Quick stats
    print(f"Parsed {len(questions)} questions.")
    missing = 0
    for q in questions:
        if any(not q.responses.get(p, "").strip() for p in PERSONAS):
            missing += 1
    if missing:
        print(f"Note: {missing} questions have at least one missing persona response (left blank).")

    if args.json:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([asdict(q) for q in questions], f, indent=2, ensure_ascii=False)
        print(f"Wrote JSON to {args.out}")
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("# Auto-generated by convert_questions_text_to_bank.py\n")
            f.write("# Paste QUESTION_BANK into questions.py, or import this file.\n\n")
            f.write(to_python(questions))
        print(f"Wrote Python to {args.out}")


if __name__ == "__main__":
    main()
