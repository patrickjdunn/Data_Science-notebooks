"""
signatures_engine.py (refactored)

- Persona selection (Listener / Motivator / Director / Expert)
- Preloaded question bank lives in: questions.py
- Ability to pull up a specific question by ID (e.g., CKM-01, HBP-03)
- Auto-fill behavioral core + default condition modifiers/drivers from question bank
- Reuse clinical inputs from combined_calculator.py (no re-entry)
- Optional calculators (run only if functions exist + inputs available)

Folder layout expected:
learning/
  signatures_engine.py
  combined_calculator.py
  questions.py
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Literal
import importlib.util
import json

# -----------------------------
# Question bank import (moved to questions.py)
# -----------------------------
from questions import (
    PreloadedQuestion,
    PersonaAnswer,
    Persona,
    QUESTION_BANK,
    list_questions,
    get_question,
    AHA_LINKS,
)

# -----------------------------
# 0) Calculator module loading
# -----------------------------

CALCULATOR_PATH = Path(__file__).parent / "combined_calculator.py"
CALCULATOR_MODULE_NAME = "combined_calculator_runtime"


def import_module_from_path(path: Path, module_name: str):
    if not path.exists():
        raise FileNotFoundError(f"Calculator module not found at: {path}")
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


# -----------------------------
# 1) Persona + Signatures input model
# -----------------------------

PERSONA_CHOICES: Dict[str, Persona] = {
    "1": "Listener",
    "2": "Motivator",
    "3": "Director",
    "4": "Expert",
    "L": "Listener",
    "M": "Motivator",
    "D": "Director",
    "E": "Expert",
}

DRIVER_CODES = {"PR", "RC", "SE", "GO", "ID", "HL", "DS", "TR", "FI", "HI", "AX"}


@dataclass
class SignaturesInput:
    question: str
    persona: Persona
    behavioral_core: str                 # e.g. "PA", "BP", "NUT", "MA", "PC", "HL"
    condition_modifiers: Dict[str, int]  # 0/1
    engagement_drivers: Dict[str, int]   # -1/0/+1


def normalize_codes(si: SignaturesInput) -> Dict[str, int]:
    codes: Dict[str, int] = {}
    codes[si.behavioral_core] = 1

    for c, v in si.condition_modifiers.items():
        codes[c] = 1 if int(v) == 1 else 0

    for d, v in si.engagement_drivers.items():
        if v not in (-1, 0, 1):
            raise ValueError(f"Driver {d} must be -1, 0, or 1; got {v}")
        codes[d] = v

    return codes


# -----------------------------
# 2) Payload model
# -----------------------------

@dataclass
class MeasurementResults:
    mylifecheck: Optional[Dict[str, Any]] = None
    prevent: Optional[Dict[str, Any]] = None
    chads2vasc: Optional[Dict[str, Any]] = None
    cardiac_rehab: Optional[Dict[str, Any]] = None
    healthy_day_at_home: Optional[Dict[str, Any]] = None


@dataclass
class SignaturesPayload:
    question: str
    persona: Persona
    codes: Dict[str, int]
    behavioral_core: str
    active_conditions: List[str]
    active_drivers: List[str]

    # Canonical structural outputs
    behavioral_core_messages: List[str] = field(default_factory=list)
    condition_modifier_messages: List[str] = field(default_factory=list)
    engagement_driver_messages: List[str] = field(default_factory=list)
    security_rules: List[str] = field(default_factory=list)
    action_plans: List[str] = field(default_factory=list)

    # Persona rendered answer (preloaded questions)
    persona_output: List[str] = field(default_factory=list)

    # Measurement + links
    measurement: MeasurementResults = field(default_factory=MeasurementResults)
    content_links: List[Dict[str, str]] = field(default_factory=list)


# -----------------------------
# 3) Minimal canonical layer content (engine-side)
#    (Preloaded persona answers live in questions.py)
# -----------------------------

BEHAVIOR_CORE_CANONICAL: Dict[str, str] = {
    "PA": "Start with safe, manageable movement and build consistency. Walking is a great place to begin.",
    "BP": "Know your numbers and track patterns over time. Small changes can add up to meaningful blood pressure improvement.",
    "NUT": "Focus on simple, repeatable improvements—more whole foods, fewer ultra-processed foods, and mindful portions.",
    "SL": "Aim for consistent sleep timing and a wind-down routine to support recovery and cardiometabolic health.",
    "MA": "Medications work best when taken consistently. Pair doses with daily routines and keep an updated medication list.",
    "SY": "Track symptoms and trends, not single moments. Write down what you notice and share patterns with your clinician.",
    "SM": "Stress management is a health skill. Small daily practices can lower strain and support better decisions.",
    "PC": "Build a simple plan you can repeat: track key measures, focus on one or two habits, and keep follow-ups consistent.",
    "HL": "Let’s connect the dots in plain language: what’s happening, why it matters, and what you can do next.",
}

SECURITY_RULES: Dict[Tuple[str, Optional[str]], str] = {
    ("PA", None): "SECURITY: If you feel faint, severely short of breath, or unwell during exercise, stop and seek medical guidance.",
    ("PA", "CD"): "SECURITY: If you experience chest pain, pressure, or tightness during exercise, stop immediately and contact your healthcare professional.",
    ("BP", None): "SECURITY: If your BP is 180/120 or higher with symptoms (chest pain, shortness of breath, weakness, vision/speech changes), seek emergency care.",
    ("SY", None): "SECURITY: If you have sudden severe symptoms (new chest pain, one-sided weakness, trouble speaking, severe shortness of breath), seek urgent/emergency care.",
}


# -----------------------------
# 4) Clinical inputs reuse (no re-entry)
# -----------------------------

def extract_clinical_inputs(calc_mod) -> Dict[str, Any]:
    """
    Reuse inputs from combined_calculator.py if exposed:
    - INPUTS (dict)
    - inputs (dict)
    - get_inputs() -> dict
    - get_latest_inputs() -> dict
    """
    for name in ("INPUTS", "inputs"):
        if hasattr(calc_mod, name):
            val = getattr(calc_mod, name)
            if isinstance(val, dict):
                return val

    for fn_name in ("get_inputs", "get_latest_inputs"):
        if hasattr(calc_mod, fn_name) and callable(getattr(calc_mod, fn_name)):
            try:
                val = getattr(calc_mod, fn_name)()
                if isinstance(val, dict):
                    return val
            except Exception:
                pass

    return {}


def _call_if_exists(calc_mod, fn_name: str, *args, **kwargs) -> Optional[Any]:
    if hasattr(calc_mod, fn_name) and callable(getattr(calc_mod, fn_name)):
        return getattr(calc_mod, fn_name)(*args, **kwargs)
    return None


# -----------------------------
# 5) Calculator calls (optional)
# -----------------------------

def run_mylifecheck(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_mylifecheck", clinical)
    if out is not None:
        return out
    return _call_if_exists(calc_mod, "calculate_mylifecheck", clinical)


def run_prevent(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_prevent", clinical)
    if out is not None:
        return out
    return _call_if_exists(calc_mod, "calculate_prevent", clinical)


def run_chads2vasc(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_chads2vasc", clinical)
    if out is not None:
        return out

    if hasattr(calc_mod, "calculate_chads2vasc") and callable(calc_mod.calculate_chads2vasc):
        try:
            score = calc_mod.calculate_chads2vasc(
                age=clinical.get("age"),
                gender=clinical.get("gender"),
                heart_failure=clinical.get("heart_failure", "No"),
                hypertension=clinical.get("hypertension", "No"),
                diabetes=clinical.get("diabetes", "No"),
                stroke_or_tia=clinical.get("stroke_or_tia", "No"),
                vascular_disease=clinical.get("vascular_disease", "No"),
            )
            return {"chads2vasc": score}
        except Exception:
            return None
    return None


def run_cardiac_rehab(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_cardiac_rehab_eligibility", clinical)
    if out is not None:
        return out

    if hasattr(calc_mod, "calculate_cardiac_rehab_eligibility") and callable(calc_mod.calculate_cardiac_rehab_eligibility):
        try:
            eligible = calc_mod.calculate_cardiac_rehab_eligibility(
                CABG=clinical.get("CABG", "No"),
                AMI=clinical.get("AMI", "No"),
                PCI=clinical.get("PCI", "No"),
                cardiac_arrest=clinical.get("cardiac_arrest", "No"),
                heart_failure=clinical.get("heart_failure", "No"),
            )
            return {"cardiac_rehab_eligible": eligible}
        except Exception:
            return None
    return None


def run_healthy_day_at_home(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_healthy_day_at_home", clinical)
    if out is not None:
        return out

    if hasattr(calc_mod, "healthy_day_at_home") and callable(calc_mod.healthy_day_at_home):
        try:
            result = calc_mod.healthy_day_at_home(
                symptoms=clinical.get("symptoms", 0),
                step_count=clinical.get("step_count", 0),
                unplanned_visits=clinical.get("unplanned_visits", 0),
                medication_adherence=clinical.get("medication_adherence", 0),
            )
            if isinstance(result, tuple) and len(result) == 2:
                score, note = result
                return {"healthy_day_score": score, "healthy_day_message": note}
            return {"healthy_day_at_home": result}
        except Exception:
            return None
    return None


# -----------------------------
# 6) Hook routing
# -----------------------------

def should_run_mylifecheck(behavior: str, codes: Dict[str, int]) -> bool:
    return behavior in {"PA", "BP", "NUT", "SL", "TOB", "PC"} or codes.get("CKM", 0) == 1

def should_run_prevent(behavior: str, codes: Dict[str, int]) -> bool:
    return any(codes.get(k, 0) == 1 for k in ("HT", "CD", "CKD", "CKM", "DM")) or behavior in {"PA", "BP", "PC"}

def should_run_chads2vasc(codes: Dict[str, int], clinical: Dict[str, Any]) -> bool:
    af = codes.get("AF", 0) == 1 or str(clinical.get("atrial_fibrillation", "")).strip().lower() in {"yes", "y", "true", "1"}
    return af

def should_run_cardiac_rehab(codes: Dict[str, int]) -> bool:
    return codes.get("CD", 0) == 1 or codes.get("HF", 0) == 1

def should_run_healthy_day(_: Dict[str, int]) -> bool:
    return True


# -----------------------------
# 7) Assembly (preloaded persona answer + canonical + security + links)
# -----------------------------

def assemble_messages(payload: SignaturesPayload, preloaded: Optional[PreloadedQuestion]) -> None:
    # Always include canonical behavioral core message (structure)
    core_msg = BEHAVIOR_CORE_CANONICAL.get(payload.behavioral_core)
    if core_msg:
        payload.behavioral_core_messages.append(core_msg)

    # If preloaded selected: render persona-specific answer + action + rationale
    if preloaded and payload.persona in preloaded.answers:
        ans = preloaded.answers[payload.persona]
        payload.persona_output = [
            f"{payload.persona} response to: {preloaded.question}",
            ans.text,
            "",
            f"Action Step: {ans.action_step}",
            f"Why it matters: {ans.why_it_matters}",
        ]
        payload.action_plans.append(f"ACTION: {ans.action_step}")

        # Links from question bank (usually AHA)
        for link in preloaded.links:
            if link not in payload.content_links:
                payload.content_links.append(link)

    # Security rules (prefer condition-specific then generic)
    added = False
    for cond in payload.active_conditions:
        rule = SECURITY_RULES.get((payload.behavioral_core, cond))
        if rule:
            payload.security_rules.append(rule)
            added = True
    if not added:
        rule = SECURITY_RULES.get((payload.behavioral_core, None))
        if rule:
            payload.security_rules.append(rule)

    # Always include Life’s Essential 8 link if present in AHA_LINKS
    if "MYLIFECHECK" in AHA_LINKS:
        if AHA_LINKS["MYLIFECHECK"] not in payload.content_links:
            payload.content_links.append(AHA_LINKS["MYLIFECHECK"])


# -----------------------------
# 8) Build payload end-to-end
# -----------------------------

def build_payload(sig: SignaturesInput, calc_mod, preloaded: Optional[PreloadedQuestion]) -> SignaturesPayload:
    codes = normalize_codes(sig)

    active_conditions = [
        k for k, v in codes.items()
        if v == 1 and k.isupper() and k not in DRIVER_CODES and k != sig.behavioral_core
    ]
    active_drivers = [k for k, v in codes.items() if k in DRIVER_CODES and v > 0]

    payload = SignaturesPayload(
        question=sig.question,
        persona=sig.persona,
        codes=codes,
        behavioral_core=sig.behavioral_core,
        active_conditions=active_conditions,
        active_drivers=active_drivers,
    )

    clinical = extract_clinical_inputs(calc_mod)

    if should_run_mylifecheck(sig.behavioral_core, codes):
        payload.measurement.mylifecheck = run_mylifecheck(calc_mod, clinical)

    if should_run_prevent(sig.behavioral_core, codes):
        payload.measurement.prevent = run_prevent(calc_mod, clinical)

    if should_run_chads2vasc(codes, clinical):
        payload.measurement.chads2vasc = run_chads2vasc(calc_mod, clinical)

    if should_run_cardiac_rehab(codes):
        payload.measurement.cardiac_rehab = run_cardiac_rehab(calc_mod, clinical)

    if should_run_healthy_day(codes):
        payload.measurement.healthy_day_at_home = run_healthy_day_at_home(calc_mod, clinical)

    assemble_messages(payload, preloaded)
    return payload


# -----------------------------
# 9) CLI: persona + choose preloaded question OR custom
# -----------------------------

def prompt_persona() -> Persona:
    print("\nChoose persona:")
    print("  1) Listener")
    print("  2) Motivator")
    print("  3) Director")
    print("  4) Expert")
    while True:
        raw = input("Enter 1-4 (or L/M/D/E): ").strip().upper()
        if raw in PERSONA_CHOICES:
            return PERSONA_CHOICES[raw]
        print("⚠️ Please enter 1,2,3,4 or L,M,D,E.")


def prompt_choose_preloaded_question() -> Optional[PreloadedQuestion]:
    print("\nUse a preloaded question?")
    raw = input("Enter Y to choose from the question bank, or press Enter for custom: ").strip().lower()
    if raw != "y":
        return None

    cat = input("Optional: type a category to filter (or press Enter to show all): ").strip()
    items = list_questions(category=cat if cat else None)

    if not items:
        print("⚠️ No questions found for that filter. Showing all.")
        items = list_questions()

    print("\nPreloaded Questions:")
    for q in items:
        print(f"  {q.qid}: {q.question}  [{q.category}]")

    while True:
        qid = input("\nEnter question ID (e.g., CKM-01): ").strip()
        q = get_question(qid)
        if q:
            return q
        print("⚠️ Not found. Please enter a valid ID shown above.")


def prompt_signatures_input() -> Tuple[SignaturesInput, Optional[PreloadedQuestion]]:
    print("\n=== Signatures Input (persona + question bank) ===")
    persona = prompt_persona()
    preloaded = prompt_choose_preloaded_question()

    if preloaded:
        question = preloaded.question
        behavioral_core = preloaded.behavioral_core
        condition_mods = {c: 1 for c in preloaded.default_conditions}
        drivers = dict(preloaded.default_drivers)

        print(f"\nLoaded {preloaded.qid}: {question}")
        print(f"Auto behavioral core: {behavioral_core}")
        if condition_mods:
            print(f"Auto conditions: {', '.join(condition_mods.keys())}")
        if drivers:
            print(f"Auto drivers: {drivers}")
    else:
        question = input("Enter the question: ").strip()
        behavioral_core = input("Behavioral core code (e.g., PA, BP, NUT, MA, PC, HL): ").strip().upper()

        print("\nCondition modifiers (enter codes like CKM, HT, CD, HF, AF, DM; blank to stop).")
        condition_mods: Dict[str, int] = {}
        while True:
            c = input("Condition code (blank to stop): ").strip().upper()
            if not c:
                break
            condition_mods[c] = 1

        drivers: Dict[str, int] = {}

    # Always allow adding extra modifiers even if preloaded
    print("\nAdd additional condition modifiers (optional). Press Enter to skip.")
    while True:
        c = input("Extra condition code (blank to stop): ").strip().upper()
        if not c:
            break
        condition_mods[c] = 1

    print("\nEngagement drivers (optional). Enter code + value: -1 not present, 0 unknown, 1 present; blank driver to stop.")
    while True:
        d = input("Driver code (blank to stop): ").strip().upper()
        if not d:
            break
        while True:
            raw = input("Value (-1, 0, 1): ").strip()
            if raw == "":
                print("⚠️ Please enter -1, 0, or 1.")
                continue
            try:
                v = int(raw)
            except ValueError:
                print("⚠️ Invalid. Enter -1, 0, or 1.")
                continue
            if v not in (-1, 0, 1):
                print("⚠️ Must be -1, 0, or 1.")
                continue
            drivers[d] = v
            break

    sig = SignaturesInput(
        question=question,
        persona=persona,
        behavioral_core=behavioral_core,
        condition_modifiers=condition_mods,
        engagement_drivers=drivers,
    )
    return sig, preloaded


# -----------------------------
# 10) Main
# -----------------------------

def main() -> int:
    try:
        calc_mod = import_module_from_path(CALCULATOR_PATH, CALCULATOR_MODULE_NAME)
    except Exception as e:
        print(f"ERROR importing calculator module: {e}")
        print(f"Looked for: {CALCULATOR_PATH.resolve()}")
        return 1

    # Light sanity check to help debugging
    if not QUESTION_BANK:
        print("⚠️ WARNING: QUESTION_BANK is empty. Check questions.py import and question registration.")

    sig, preloaded = prompt_signatures_input()
    payload = build_payload(sig, calc_mod, preloaded)

    if payload.persona_output:
        print("\n=== Persona Output (from preloaded content if selected) ===")
        print("\n".join(payload.persona_output))

    print("\n=== Full Signatures Payload (JSON) ===")
    print(json.dumps(asdict(payload), indent=2, default=str))

    clinical = extract_clinical_inputs(calc_mod)
    if not clinical:
        print("\n⚠️ NOTE: No clinical inputs found in combined_calculator.py.")
        print("To reuse values automatically, expose one of these in combined_calculator.py:")
        print("- INPUTS = {...}   (dict)")
        print("- inputs = {...}   (dict)")
        print("- def get_inputs(): return {...}")
        print("- def get_latest_inputs(): return {...}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


