# signatures_rules.py
"""
signatures_rules.py

Rules for assembling the Signatures output in a deterministic, LLM-friendly way.

Inputs:
- selected question (includes signatures_tags, action_plan_codes, security_rule_codes, sources)
- persona
- calculator inputs/results from combined_calculator.py (optional)

Outputs:
- dict with:
  - persona
  - question metadata
  - signatures blocks
  - scores (MyLifeCheck/PREVENT if present)
  - sources
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from questions import Question
from signatures_content import (
    BEHAVIORAL_CORE_MESSAGES,
    CONDITION_MODIFIER_MESSAGES,
    ENGAGEMENT_DRIVER_MESSAGES,
    SECURITY_RULES,
    ACTION_PLANS,
)


def _pick_message(block: Dict[str, Any], persona: str) -> str:
    # Prefer persona-specific message; fall back to default
    if isinstance(block.get("persona"), dict) and persona in block["persona"]:
        return str(block["persona"][persona]).strip()
    if block.get("default"):
        return str(block["default"]).strip()
    if block.get("message"):
        return str(block["message"]).strip()
    return ""


def extract_mylifecheck(calculator_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction.
    Your combined_calculator.py may return:
      results["mylifecheck"] or results["MyLifeCheck"] or results["life8"]
    """
    for key in ("mylifecheck", "MyLifeCheck", "life8", "lifes_essential_8", "les8"):
        if key in calculator_results and isinstance(calculator_results[key], dict):
            return calculator_results[key]
    return None


def extract_prevent(calculator_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction.
    Your combined_calculator.py may return:
      results["prevent"] or results["PREVENT"]
    """
    for key in ("prevent", "PREVENT"):
        if key in calculator_results and isinstance(calculator_results[key], dict):
            return calculator_results[key]
    return None


def build_signatures_output(
    question: Question,
    persona: str,
    calculator_inputs: Dict[str, Any],
    calculator_results: Dict[str, Any],
) -> Dict[str, Any]:
    tags = question.signatures_tags or {}
    core_codes = tags.get("behavioral_core", []) or []
    mod_codes = tags.get("condition_modifiers", []) or []
    drv_codes = tags.get("engagement_drivers", []) or []

    # Behavioral core: always at least one (GEN if missing)
    if not core_codes:
        core_codes = ["GEN"]

    behavioral_core = []
    for code in core_codes:
        block = BEHAVIORAL_CORE_MESSAGES.get(code, {"label": code, "default": ""})
        behavioral_core.append({
            "code": code,
            "label": block.get("label", code),
            "message": _pick_message(block, persona),
        })

    condition_modifiers = []
    for code in mod_codes:
        block = CONDITION_MODIFIER_MESSAGES.get(code, {"label": code, "default": ""})
        condition_modifiers.append({
            "code": code,
            "label": block.get("label", code),
            "message": _pick_message(block, persona),
        })

    engagement_drivers = []
    for code in drv_codes:
        block = ENGAGEMENT_DRIVER_MESSAGES.get(code, {"label": code, "default": ""})
        engagement_drivers.append({
            "code": code,
            "label": block.get("label", code),
            "message": _pick_message(block, persona),
        })

    # Security rules: include any suggested by the question + a few inferred from context
    security_rules = []
    for code in (question.security_rule_codes or []):
        block = SECURITY_RULES.get(code, {"label": code, "message": ""})
        security_rules.append({
            "code": code,
            "label": block.get("label", code),
            "message": _pick_message(block, persona),
            "severity": block.get("severity", "unknown"),
        })

    # Action plans
    action_plans = []
    for code in (question.action_plan_codes or []):
        block = ACTION_PLANS.get(code, {"label": code, "message": ""})
        action_plans.append({
            "code": code,
            "label": block.get("label", code),
            "message": _pick_message(block, persona),
        })

    # Persona response: use question bank response if present; else fall back to core message
    persona_response = question.responses.get(persona, "").strip()
    if not persona_response:
        persona_response = behavioral_core[0]["message"] or "Start with one small step today and build gradually."

    # Scores (hooks)
    mylifecheck = extract_mylifecheck(calculator_results) or None
    prevent = extract_prevent(calculator_results) or None

    out: Dict[str, Any] = {
        "persona": persona,
        "question": {
            "id": question.id,
            "category": question.category,
            "text": question.question,
        },
        "response": {
            "message": persona_response,
            "action_step": question.action_step,
            "why_it_matters": question.why,
        },
        "signatures": {
            "behavioral_core": behavioral_core,
            "condition_modifiers": condition_modifiers,
            "engagement_drivers": engagement_drivers,
            "security_rules": security_rules,
            "action_plans": action_plans,
        },
        "scores": {
            "mylifecheck": mylifecheck,
            "prevent": prevent,
        },
        "sources": question.sources or [],
        "calculator": {
            "inputs_used": calculator_inputs or {},
            "results_available": list(calculator_results.keys()) if isinstance(calculator_results, dict) else [],
        },
    }
    return out


def render_signatures_output(out: Dict[str, Any]) -> None:
    """
    CLI renderer (keeps output consistent and readable).
    """
    q = out.get("question", {})
    resp = out.get("response", {})
    sig = out.get("signatures", {})
    scores = out.get("scores", {})
    sources = out.get("sources", [])

    print(f"[{q.get('category')}] {q.get('id')} — {q.get('text')}\n")
    print(f"{out.get('persona')}: {resp.get('message')}\n")

    print("Action Step:")
    print(f"  {resp.get('action_step')}")
    print("Why it matters:")
    print(f"  {resp.get('why_it_matters')}")

    print("\n--- Signatures Structure ---")
    _print_block("Behavioral Core", sig.get("behavioral_core", []))
    _print_block("Condition Modifiers", sig.get("condition_modifiers", []))
    _print_block("Engagement Drivers", sig.get("engagement_drivers", []))
    _print_block("Security Rules", sig.get("security_rules", []), include_severity=True)
    _print_block("Action Plans", sig.get("action_plans", []))

    print("\n--- Scoring Hooks ---")
    mylife = scores.get("mylifecheck")
    prev = scores.get("prevent")
    if not mylife and not prev:
        print("  (No MyLifeCheck / PREVENT scores available — missing inputs or calculator not run.)")
    else:
        if mylife:
            print("  MyLifeCheck / Life’s Essential 8:")
            for k, v in list(mylife.items())[:20]:
                print(f"    - {k}: {v}")
        if prev:
            print("  PREVENT:")
            for k, v in list(prev.items())[:20]:
                print(f"    - {k}: {v}")

    print("\n--- Source (AHA preferred) ---")
    if sources:
        for s in sources[:3]:
            org = s.get("org", "Source")
            title = s.get("title", "")
            url = s.get("url", "")
            print(f"  {org}: {title}\n    {url}")
    else:
        print("  (No source attached.)")


def _print_block(name: str, items: List[Dict[str, Any]], include_severity: bool = False) -> None:
    print(f"\n{name}:")
    if not items:
        print("  (none)")
        return
    for it in items:
        code = it.get("code", "")
        label = it.get("label", "")
        msg = it.get("message", "")
        if include_severity:
            sev = it.get("severity", "unknown")
            print(f"  - {code} ({label}) [{sev}]: {msg}")
        else:
            print(f"  - {code} ({label}): {msg}")
