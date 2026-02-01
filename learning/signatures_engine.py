# signatures_engine.py
# Runs the Signatures question flow + persona messaging.
# Place this file in: hi5304-notebooks/learning/signatures_engine.py

from __future__ import annotations

import os
import sys
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from questions import (
    PERSONAS,
    QUESTION_BANK,
    list_categories,
    list_question_summaries,
    filter_questions_by_category,
    get_question,
    validate_question_bank,
)

# ---------------------------------------
# Optional calculator integration
# (works even if combined_calculator.py is absent)
# ---------------------------------------
CALCULATOR_FILENAME = "combined_calculator.py"  # same folder as this engine


def _load_calculator_module() -> Optional[Any]:
    """
    Attempts to import combined_calculator.py from the current directory.
    Returns module or None.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, CALCULATOR_FILENAME)
    if not os.path.exists(path):
        return None

    try:
        spec = importlib.util.spec_from_file_location("combined_calculator", path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        return module
    except Exception as e:
        print(f"⚠️ Calculator module found but failed to import: {e}")
        return None


CALC = _load_calculator_module()


# ---------------------------------------
# Signatures structures
# ---------------------------------------
@dataclass
class SignaturesInput:
    persona: str
    question_text: str
    behavioral_core: str
    condition_modifiers: List[str]
    engagement_drivers: Dict[str, int]  # -1/0/+1
    # optional clinical inputs (may be empty)
    values: Dict[str, Any]


# Simple dictionaries for extendability
BEHAVIORAL_CORE_MESSAGES: Dict[str, Dict[str, str]] = {
    "PC": {
        "title": "Preventive Care & Self-Management",
        "generic": "Focus on one or two habits you can sustain, track progress, and review results with your care team.",
    },
    "NUT": {
        "title": "Nutrition",
        "generic": "Choose a heart-healthy eating pattern, start with small swaps, and reduce highly processed foods and excess sodium.",
    },
    "MA": {
        "title": "Medication Adherence",
        "generic": "Take medications as prescribed, use reminders, and tell your clinician about side effects or barriers.",
    },
    "SY": {
        "title": "Monitoring & Symptoms",
        "generic": "Track key numbers/symptoms consistently, watch trends, and escalate care when red flags appear.",
    },
    "PA": {
        "title": "Physical Activity",
        "generic": "Start low and go slow—build a routine that is safe, consistent, and fits your current health status.",
    },
    "BP": {
        "title": "Blood Pressure",
        "generic": "Know your numbers, measure correctly, and work toward your clinician-recommended goal using lifestyle and medication as needed.",
    },
    "HL": {
        "title": "Health Literacy",
        "generic": "Ask for simple explanations, repeat-back what you heard, and use trusted sources to guide decisions.",
    },
}

# Condition modifier message add-ons (extend this freely)
CONDITION_MODIFIER_MESSAGES: Dict[str, str] = {
    "CKM": "Because CKM health connects heart, kidney, and metabolic risk, focus on actions that improve BP, glucose, weight, and kidney-friendly habits together.",
    "HT": "For high blood pressure, prioritize accurate home monitoring, sodium reduction, activity, and medication adherence if prescribed.",
    "CAD": "With coronary artery disease risk, start activity gradually and ask about cardiac rehab or a supervised plan if symptoms or history suggest higher risk.",
    "HF": "With heart failure risk, watch for fluid symptoms (rapid weight gain, swelling, shortness of breath) and follow a sodium/fluid plan from your clinician.",
    "AF": "With atrial fibrillation risk, ask about stroke prevention plans and safe exercise pacing; report palpitations or dizziness promptly.",
    "ST": "After stroke risk/events, prioritize BP control, medication adherence, and rehab plans; safety and prevention are key.",
    "DM": "With diabetes risk, align activity and nutrition with glucose monitoring, and ask how to prevent lows during exercise.",
}

# Engagement driver message add-ons (only applied when > 0)
ENGAGEMENT_DRIVER_MESSAGES: Dict[str, str] = {
    "PR": "Proactive framing: pick a small next step today and schedule a check-in to review progress.",
    "HL": "Plain-language support: keep instructions simple, one step at a time, and use visuals/tools when possible.",
    "SE": "Self-efficacy support: start with a goal you’re confident you can hit this week to build momentum.",
    "GO": "Goal orientation: define a measurable goal and a review date (e.g., 2 weeks) to evaluate progress.",
    "TR": "Trust support: bring questions to your clinician and confirm the plan aligns with your preferences and values.",
}

# Security rules (stop rules)
SECURITY_RULES: Dict[str, str] = {
    "EXERCISE_CHEST_PAIN_STOP": "If you experience chest pain during exercise, stop immediately and contact your healthcare professional.",
}

# Action plans
ACTION_PLANS: Dict[str, str] = {
    "CARDIAC_REHAB": "Action plan: Ask your clinician about a referral to cardiac rehabilitation (clinic-based or home-based). It provides supervised exercise, education, and coaching tailored to your condition.",
}

# Links to content (can be expanded)
CONTENT_LINKS: Dict[str, Dict[str, str]] = {
    "AHA_FITNESS": {
        "org": "American Heart Association",
        "title": "Fitness Basics",
        "url": "https://www.heart.org/en/healthy-living/fitness",
    },
    "AHA_BP_READINGS": {
        "org": "American Heart Association",
        "title": "Understanding Blood Pressure Readings",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
    },
    "AHA_MYLIFECHECK": {
        "org": "American Heart Association",
        "title": "My Life Check — Life’s Essential 8",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check--lifes-essential-8",
    },
}


# ---------------------------------------
# Menu selection (prevents Not Found errors)
# ---------------------------------------
def choose_from_menu(items: List[Tuple[str, str, str]]) -> Optional[str]:
    """
    items: [(id, category, question), ...]
    Returns selected id or None.
    """
    if not items:
        print("⚠️ No questions available.")
        return None

    print("\nPreloaded Questions:")
    for idx, (qid, cat, qtext) in enumerate(items, start=1):
        print(f"{idx:>2}. [{cat}] {qid} — {qtext}")

    while True:
        choice = input("\nEnter a number (or press Enter to cancel): ").strip()
        if choice == "":
            return None
        if not choice.isdigit():
            print("⚠️ Please enter a valid number.")
            continue
        n = int(choice)
        if 1 <= n <= len(items):
            return items[n - 1][0]
        print("⚠️ Number out of range.")


def pick_preloaded_question() -> Optional[Dict[str, Any]]:
    category = input("Optional: type a category to filter (or press Enter to show all): ").strip()
    if category:
        filtered = filter_questions_by_category(category)
        if not filtered:
            print("⚠️ No questions found for that filter. Showing all.")
            items = list_question_summaries()
        else:
            items = [(q["id"], q["category"], q["question"]) for q in filtered]
    else:
        items = list_question_summaries()

    selected_id = choose_from_menu(items)
    if not selected_id:
        return None

    return get_question(selected_id)


# ---------------------------------------
# Persona selection
# ---------------------------------------
def prompt_persona() -> str:
    print("\nChoose a communication style:")
    for i, p in enumerate(PERSONAS, start=1):
        print(f"{i}. {p}")
    while True:
        s = input("Enter 1-4 (default 1): ").strip()
        if s == "":
            return PERSONAS[0]
        if s.isdigit() and 1 <= int(s) <= len(PERSONAS):
            return PERSONAS[int(s) - 1]
        print("⚠️ Please enter 1, 2, 3, or 4.")


# ---------------------------------------
# Optional clinical values:
# pull from calculator if available; otherwise allow skip
# ---------------------------------------
def get_values_from_calculator_if_possible() -> Dict[str, Any]:
    """
    Tries to use combined_calculator.py if it exposes a function that returns inputs.
    If not, returns {} and the rest of the engine still runs.
    """
    if CALC is None:
        return {}

    # Common patterns you might have in combined_calculator.py:
    # - prompt_inputs()
    # - get_inputs()
    # - main() returning dict
    for fn_name in ("prompt_inputs", "get_inputs", "collect_inputs", "prompt_user_inputs"):
        fn = getattr(CALC, fn_name, None)
        if callable(fn):
            try:
                out = fn()
                if isinstance(out, dict):
                    return out
            except Exception as e:
                print(f"⚠️ Calculator inputs failed ({fn_name}): {e}")
                return {}

    return {}


# ---------------------------------------
# Driver prompting (optional, safe)
# ---------------------------------------
def prompt_engagement_drivers() -> Dict[str, int]:
    """
    Engagement drives: 0 = unknown, -1 = not present, +1 = present
    Press Enter to keep default (0).
    """
    drivers = {"PR": 0, "HL": 0, "SE": 0, "GO": 0, "TR": 0}

    print("\nEngagement Drivers (Enter = unknown/0). Use -1 (not present) or 1 (present).")
    print("PR=Proactive, HL=Health Literacy, SE=Self-Efficacy, GO=Goal Orientation, TR=Trust")

    for k in list(drivers.keys()):
        while True:
            raw = input(f"  {k} value (-1,0,1) [default 0]: ").strip()
            if raw == "":
                drivers[k] = 0
                break
            if raw in ("-1", "0", "1"):
                drivers[k] = int(raw)
                break
            print("⚠️ Please enter -1, 0, 1, or press Enter.")
    return drivers


def prompt_condition_modifiers(defaults: Optional[List[str]] = None) -> List[str]:
    """
    Simple comma-separated modifiers. Enter to accept defaults.
    """
    defaults = defaults or []
    print("\nCondition Modifiers examples: CKM, HT, CAD, HF, AF, ST, DM")
    d = ", ".join(defaults) if defaults else "(none)"
    raw = input(f"Enter condition modifiers (comma-separated) [default: {d}]: ").strip()
    if raw == "":
        return defaults
    mods = [m.strip().upper() for m in raw.split(",") if m.strip()]
    return mods


# ---------------------------------------
# Scoring hooks (MyLifeCheck + PREVENT)
# ---------------------------------------
def compute_mylifecheck(values: Dict[str, Any]) -> Optional[Any]:
    """
    Attempts to compute Life’s Essential 8 / MyLifeCheck using combined_calculator if available.
    Returns object or None.
    """
    if CALC is None:
        return None

    for fn_name in ("mylifecheck_score", "my_life_check", "calculate_mylifecheck", "calc_mylifecheck"):
        fn = getattr(CALC, fn_name, None)
        if callable(fn):
            try:
                return fn(values)  # many implementations accept dict
            except TypeError:
                try:
                    return fn()  # some prompt internally
                except Exception:
                    return None
            except Exception:
                return None
    return None


def compute_prevent(values: Dict[str, Any]) -> Optional[Any]:
    """
    Attempts to compute PREVENT using combined_calculator if available.
    """
    if CALC is None:
        return None

    for fn_name in ("prevent_risk", "calculate_prevent", "calc_prevent", "prevent_score"):
        fn = getattr(CALC, fn_name, None)
        if callable(fn):
            try:
                return fn(values)
            except TypeError:
                try:
                    return fn()
                except Exception:
                    return None
            except Exception:
                return None
    return None


# ---------------------------------------
# Rendering the Signatures output
# ---------------------------------------
def render_sources(sources: List[Dict[str, str]]) -> None:
    if not sources:
        return
    print("\nSource(s):")
    for s in sources:
        org = s.get("org", "").strip()
        title = s.get("title", "").strip()
        url = s.get("url", "").strip()
        if org and title and url:
            print(f"- {org}: {title} — {url}")
        elif title and url:
            print(f"- {title} — {url}")
        elif url:
            print(f"- {url}")


def run_signatures(sig: SignaturesInput, preloaded: Optional[Dict[str, Any]] = None) -> None:
    print("\n" + "=" * 72)
    print("SIGNATURES OUTPUT")
    print("=" * 72)

    # 1) Behavioral Core
    bc = sig.behavioral_core.upper()
    bc_info = BEHAVIORAL_CORE_MESSAGES.get(bc, {"title": bc, "generic": "Start with a safe, practical first step and build consistency."})
    print(f"\nBehavioral Core [{bc}]: {bc_info.get('title')}")
    print(f"- {bc_info.get('generic')}")

    # 2) Condition Modifiers
    if sig.condition_modifiers:
        print("\nCondition Modifiers:")
        for cm in sig.condition_modifiers:
            msg = CONDITION_MODIFIER_MESSAGES.get(cm, "")
            if msg:
                print(f"- [{cm}] {msg}")
            else:
                print(f"- [{cm}] (no custom message yet)")

    # 3) Engagement drivers (>0)
    active_drivers = {k: v for k, v in sig.engagement_drivers.items() if v > 0}
    if active_drivers:
        print("\nEngagement Drivers (>0):")
        for k in active_drivers.keys():
            msg = ENGAGEMENT_DRIVER_MESSAGES.get(k, "")
            if msg:
                print(f"- [{k}] {msg}")
            else:
                print(f"- [{k}] (no custom message yet)")

    # 4) Persona answer (from question bank if preloaded; otherwise generic)
    print(f"\nPersona: {sig.persona}")
    if preloaded and preloaded.get("answers", {}).get(sig.persona):
        ans = preloaded["answers"][sig.persona]
        print("\nMessage:")
        print(f"- {ans.get('text','')}")
        print("\nAction Step:")
        print(f"- {ans.get('action_step','')}")
        print("\nWhy It Matters:")
        print(f"- {ans.get('why_it_matters','')}")
    else:
        print("\nMessage:")
        print(f"- Start with one small step this week, track it, and adjust based on how you feel and your data.")
        print("\nAction Step:")
        print(f"- Pick one action you can do 3–5 days this week.")
        print("\nWhy It Matters:")
        print(f"- Small—done consistently—creates measurable progress.")

    # 5) Security rule
    print("\nSecurity Rule:")
    print(f"- {SECURITY_RULES['EXERCISE_CHEST_PAIN_STOP']}")

    # 6) Action plan
    print("\nAction Plan:")
    print(f"- {ACTION_PLANS['CARDIAC_REHAB']}")

    # 7) Scoring hooks (MyLifeCheck + PREVENT)
    print("\nScoring Hooks:")
    mylc = compute_mylifecheck(sig.values)
    prev = compute_prevent(sig.values)

    if mylc is None:
        print("- MyLifeCheck (Life’s Essential 8): (hook ready) — no calculator output available.")
    else:
        print(f"- MyLifeCheck (Life’s Essential 8): {mylc}")

    if prev is None:
        print("- PREVENT: (hook ready) — no calculator output available.")
    else:
        print(f"- PREVENT: {prev}")

    # 8) Sources (prefer AHA; from the question bank if present)
    if preloaded:
        render_sources(preloaded.get("sources", []))
    else:
        render_sources([CONTENT_LINKS["AHA_MYLIFECHECK"]])

    print("\n" + "=" * 72 + "\n")


# ---------------------------------------
# Main CLI flow
# ---------------------------------------
def main() -> None:
    # Validate bank once at startup (non-fatal)
    issues = validate_question_bank(raise_on_error=False)
    if issues:
        print("⚠️ Question bank issues detected (non-fatal). First 5:")
        for x in issues[:5]:
            print("-", x)

    print("Signatures Engine\n")

    persona = prompt_persona()

    use_preloaded = input("Use a preloaded question? (Y/n): ").strip().lower()
    if use_preloaded in ("", "y", "yes"):
        q = pick_preloaded_question()
        if q is None:
            print("No preloaded question selected. Switching to custom question.")
            q = None
    else:
        q = None

    if q:
        question_text = q["question"]
        behavioral_core = q.get("behavioral_core", "PC")
        default_conditions = q.get("default_conditions", [])
        default_drivers = q.get("default_drivers", {})
    else:
        question_text = input("\nEnter your question: ").strip()
        behavioral_core = input("Behavioral core code (e.g., PC, PA, NUT) [default PC]: ").strip().upper() or "PC"
        default_conditions = []
        default_drivers = {}

    # Condition modifiers + drivers
    condition_modifiers = prompt_condition_modifiers(defaults=default_conditions)
    drivers = prompt_engagement_drivers()
    # merge defaults if provided (defaults do not override user input)
    for k, v in default_drivers.items():
        drivers.setdefault(k, v)

    # Clinical values (optional)
    print("\nClinical values: pulling from combined_calculator.py if available (otherwise skipped).")
    values = get_values_from_calculator_if_possible()

    sig = SignaturesInput(
        persona=persona,
        question_text=question_text,
        behavioral_core=behavioral_core,
        condition_modifiers=condition_modifiers,
        engagement_drivers=drivers,
        values=values,
    )

    run_signatures(sig, preloaded=q)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)



