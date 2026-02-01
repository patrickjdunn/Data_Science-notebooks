# signatures_engine.py
"""
Signatures Engine (CLI)

Design goals:
- Keep the clean, simple input experience:
  1) Choose persona (Listener/Motivator/Director/Expert)
  2) Choose preloaded question OR enter custom
  3) (Optionally) run combined_calculator prompts once, and reuse its inputs/outputs
- Add Signatures fundamentals:
  - Behavioral core
  - Condition modifiers
  - Engagement drivers
  - Security rules
  - Action plans
- Add MyLifeCheck + PREVENT hooks (from combined_calculator.py outputs)
- Add robust question bank browsing + search mode
- Be LLM-friendly: optionally emit JSON output structure

Folder expectation:
- Put this file in: hi5304-notebooks/learning/signatures_engine.py
- Put questions.py, signatures_content.py, signatures_rules.py in same folder
- Put combined_calculator.py in same folder (your existing file)
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from questions import (
    Question,
    all_categories,
    get_question_by_id,
    list_question_summaries,
    search_questions,
    validate_question_bank,
)

from signatures_rules import build_signatures_output, render_signatures_output


PERSONAS = ["Listener", "Motivator", "Director", "Expert"]


# -----------------------------
# Calculator integration (safe)
# -----------------------------

def import_calculator_module() -> Optional[Any]:
    """
    Imports combined_calculator.py from the same directory as this file.
    Uses importlib so users don't need to modify PYTHONPATH.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "combined_calculator.py")
    if not os.path.exists(candidate):
        # Also allow "combined_calculator (6).py" renamed incorrectly
        # (won't auto-import that; just help the user)
        return None

    spec = importlib.util.spec_from_file_location("combined_calculator", candidate)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_calculators_once(calc_mod: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Runs combined_calculator in a flexible way.

    Returns:
      inputs_used: dict
      results: dict
    """
    # Try common function names in a non-breaking way.
    # You can adapt these names to match your combined_calculator.py.
    inputs_used: Dict[str, Any] = {}
    results: Dict[str, Any] = {}

    # 1) If module offers a single runner that returns (inputs, results)
    for fn_name in ("run_all", "run", "main_run"):
        fn = getattr(calc_mod, fn_name, None)
        if callable(fn):
            out = fn()
            if isinstance(out, tuple) and len(out) == 2:
                inputs_used, results = out  # type: ignore
                return inputs_used or {}, results or {}
            if isinstance(out, dict):
                results = out
                return {}, results

    # 2) If module offers prompt_inputs + calculate_all
    prompt_fn = None
    for fn_name in ("prompt_inputs", "prompt_user_inputs", "get_user_inputs"):
        if callable(getattr(calc_mod, fn_name, None)):
            prompt_fn = getattr(calc_mod, fn_name)
            break

    calc_fn = None
    for fn_name in ("calculate_all", "calculate", "compute_all"):
        if callable(getattr(calc_mod, fn_name, None)):
            calc_fn = getattr(calc_mod, fn_name)
            break

    if prompt_fn and calc_fn:
        inputs_used = prompt_fn() or {}
        results = calc_fn(inputs_used) or {}
        return inputs_used, results

    # 3) If module already exposes results builders without prompts
    #    (we won't force anything; keep safe)
    return {}, {}


# -----------------------------
# CLI helpers (keep clean)
# -----------------------------

def ask_choice(prompt: str, choices: List[str], default_index: int = 0) -> str:
    print(prompt)
    for i, c in enumerate(choices, start=1):
        print(f"{i}. {c}")
    raw = input(f"Enter 1-{len(choices)} (default {default_index+1}): ").strip()
    if not raw:
        return choices[default_index]
    try:
        idx = int(raw)
        if 1 <= idx <= len(choices):
            return choices[idx - 1]
    except ValueError:
        pass
    print("⚠️ Invalid choice. Using default.")
    return choices[default_index]


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    suffix = " (Y/n): " if default_yes else " (y/N): "
    raw = input(prompt + suffix).strip().lower()
    if not raw:
        return default_yes
    return raw in ("y", "yes")


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70 + "\n")


def wrap(s: str, width: int = 78) -> str:
    return "\n".join(textwrap.wrap(s, width=width))


# -----------------------------
# Question selection modes
# -----------------------------

def pick_preloaded_question() -> Question:
    """
    Clean selection:
    - optional category filter
    - optional search mode
    - pick by number (1..N) or by ID
    """
    cat_filter = input(
        f"Optional: type a category to filter (or press Enter to show all)\n"
        f"Available: {', '.join(all_categories())}\n> "
    ).strip()

    mode = input(
        "Pick mode: (L)ist / (S)earch / (I)D (default L): "
    ).strip().lower() or "l"

    if mode.startswith("s"):
        query = input("Search query (keywords): ").strip()
        results = search_questions(query=query, category=cat_filter or None, limit=50)
        if not results:
            print("⚠️ No matches. Falling back to list.")
            mode = "l"
        else:
            print("\nSearch Results:")
            for i, item in enumerate(results, start=1):
                print(f"{i:>2}. [{item.category}] {item.id} — {item.question}")
            pick = input("\nEnter number or ID: ").strip()
            q = resolve_pick(pick, results)
            if q:
                return q
            print("⚠️ Not found. Falling back to list.")
            mode = "l"

    if mode.startswith("i"):
        pick_id = input("Enter question ID (e.g., HTN-01): ").strip().upper()
        q = get_question_by_id(pick_id)
        if q:
            return q
        print("⚠️ Not found. Falling back to list.")

    # default list mode
    items = list_question_summaries(category=cat_filter or None, limit=200)
    if not items:
        print("⚠️ No questions found for that filter. Showing all.")
        items = list_question_summaries(category=None, limit=200)

    print("\nPreloaded Questions:")
    for i, item in enumerate(items, start=1):
        print(f"{i:>2}. [{item.category}] {item.id} — {item.question}")

    pick = input("\nEnter number or ID: ").strip()
    q = resolve_pick(pick, items)
    if q:
        return q

    # If still not resolved, keep asking (clean UX)
    while True:
        pick = input("⚠️ Not found. Enter a valid number or ID shown above: ").strip()
        q = resolve_pick(pick, items)
        if q:
            return q


def resolve_pick(pick: str, items: List[Question]) -> Optional[Question]:
    if not pick:
        return None
    p = pick.strip()
    # Number?
    try:
        idx = int(p)
        if 1 <= idx <= len(items):
            return items[idx - 1]
    except ValueError:
        pass
    # ID?
    return get_question_by_id(p.upper())


def prompt_custom_question() -> Question:
    """
    Minimal custom question object. The Signatures engine can still run:
    - It will use generic Signatures tags (behavioral core = "GEN")
    - You can add tags later
    """
    qtext = input("Enter your question: ").strip()
    if not qtext:
        qtext = "How do I start an exercise program?"

    # Create a lightweight Question instance (not stored in bank)
    return Question(
        id="CUSTOM-01",
        category="CUSTOM",
        question=qtext,
        responses={},  # no persona responses; engine will fall back to core messages
        action_step="Write down one small next step you can do today.",
        why="Small steps build momentum and confidence.",
        signatures_tags={
            "behavioral_core": ["GEN"],
            "condition_modifiers": [],
            "engagement_drivers": [],
        },
        security_rule_codes=[],
        action_plan_codes=[],
        sources=[],
    )


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    # 1) Validate question bank (non-fatal)
    issues = validate_question_bank(raise_on_error=False)
    if issues:
        print("⚠️ Question bank issues detected (non-fatal). First 5:")
        for msg in issues[:5]:
            print(f"- {msg}")

    print_header("Signatures Engine")

    # 2) Persona selection (keep clean)
    persona = ask_choice("Choose a communication style:", PERSONAS, default_index=0)

    # 3) Question selection (keep clean)
    use_preloaded = ask_yes_no("Use a preloaded question?", default_yes=True)
    if use_preloaded:
        q = pick_preloaded_question()
    else:
        q = prompt_custom_question()

    # 4) Calculator outputs (MyLifeCheck + PREVENT etc.) — do NOT re-prompt elsewhere
    calc_mod = import_calculator_module()
    calc_inputs: Dict[str, Any] = {}
    calc_results: Dict[str, Any] = {}
    if calc_mod:
        try:
            calc_inputs, calc_results = run_calculators_once(calc_mod)
        except Exception as e:
            print(f"⚠️ Calculator error (continuing without scores): {e}")
    else:
        print("ℹ️ combined_calculator.py not found in this folder. Scores will be skipped.")

    # 5) Build Signatures output object (LLM-friendly)
    output = build_signatures_output(
        question=q,
        persona=persona,
        calculator_inputs=calc_inputs,
        calculator_results=calc_results,
    )

    # 6) Render for CLI
    render_signatures_output(output)

    # 7) Optional JSON emit (LLM-friendly)
    if ask_yes_no("\nOutput JSON too?", default_yes=False):
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()



