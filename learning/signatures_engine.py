"""
signatures_engine.py (refactored)

Goals:
- Reuse clinical inputs from combined_calculator.py if they already exist.
- Do NOT require re-entry; do NOT require values that aren't available.
- Provide dictionary-based message libraries for:
  behavioral core, condition modifiers, engagement drivers, security rules, action plans, and content links.

Design notes:
- "Clinical inputs" are treated as a dict and may be partial/incomplete.
- Each calculator runs only if its required minimum inputs are present.
- Messaging is assembled via a simple "message registry" (dicts).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import importlib.util
import json


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
# 1) Signatures input model
# -----------------------------

DRIVER_CODES = {"PR", "RC", "SE", "GO", "ID", "HL", "DS", "TR", "FI", "HI", "AX"}

@dataclass
class SignaturesInput:
    question: str
    behavioral_core: str                 # e.g. "PA", "BP", "NUT"
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
    codes: Dict[str, int]
    behavioral_core: str
    active_conditions: List[str]
    active_drivers: List[str]

    # Assembled messaging outputs:
    behavioral_core_messages: List[str] = field(default_factory=list)
    condition_modifier_messages: List[str] = field(default_factory=list)
    engagement_driver_messages: List[str] = field(default_factory=list)
    security_rules: List[str] = field(default_factory=list)
    action_plans: List[str] = field(default_factory=list)

    # Measurement + content
    measurement: MeasurementResults = field(default_factory=MeasurementResults)
    content_links: List[Dict[str, str]] = field(default_factory=list)  # [{"title":..., "url":..., "org":...}]


# -----------------------------
# 3) Message libraries (dictionaries)
#
# Best practice: keep these in a separate file later (e.g., signatures_content.py).
# For now, they live here for clarity.
# -----------------------------

# A) Behavioral core messages keyed by behavior code
BEHAVIORAL_CORE_MESSAGES: Dict[str, str] = {
    "PA": "Start with safe, manageable movement and build consistency. Walking is a great place to begin.",
    "BP": "Know your numbers and track patterns over time. Small changes can add up to meaningful blood pressure improvement.",
    "NUT": "Focus on simple, repeatable improvements—more whole foods, fewer ultra-processed foods, and mindful portions.",
    "SL": "Aim for consistent sleep timing and a wind-down routine to support recovery and cardiometabolic health.",
    "MA": "Medications work best when taken consistently. Pair doses with daily routines and keep an updated medication list.",
    "SY": "Track symptoms and trends, not single moments. Write down what you notice and share patterns with your clinician.",
    "SM": "Stress management is a health skill. Small daily practices can lower strain and support better decisions."
}

# B) Condition modifier messages keyed by (behavior_code, condition_code)
CONDITION_MODIFIER_MESSAGES: Dict[Tuple[str, str], str] = {
    ("PA", "CD"): "With coronary artery disease, start gradually and progress slowly. If available, begin with supervised guidance like cardiac rehab.",
    ("PA", "HF"): "With heart failure, begin with short, low-intensity activity and rest as needed. Consistency matters more than intensity.",
    ("BP", "CKD"): "With kidney disease, blood pressure targets and medications may be adjusted to protect kidney function—coordinate closely with your care team.",
    ("NUT", "CKD"): "With kidney disease, nutrition may require tailored guidance (sodium, potassium, phosphorus)—ask for kidney-specific recommendations."
}

# C) Engagement driver messages keyed by (behavior_code, driver_code)
ENGAGEMENT_DRIVER_MESSAGES: Dict[Tuple[str, str], str] = {
    ("PA", "PR"): "Set a simple starting goal (like minutes walked) and increase gradually each week.",
    ("PA", "HL"): "Keep it simple: if you can move and still talk, the intensity is usually about right.",
    ("BP", "GO"): "Write down a clear blood pressure goal and track readings consistently so you can see progress.",
    ("NUT", "SE"): "Pick one change you’re confident you can do this week—success builds confidence for the next step."
}

# D) Security rules keyed by (behavior_code, optional condition_code)
# Use (behavior, None) for generic; (behavior, "CD") etc. for condition-specific.
SECURITY_RULES: Dict[Tuple[str, Optional[str]], str] = {
    ("PA", None): "If you feel faint, severely short of breath, or unwell during exercise, stop and seek medical guidance.",
    ("PA", "CD"): "If you experience chest pain, pressure, or tightness during exercise, stop immediately and contact your healthcare professional.",
    ("BP", None): "If your blood pressure is 180/120 or higher with symptoms (chest pain, shortness of breath, weakness, vision/speech changes), seek emergency care."
}

# E) Action plans keyed by (behavior_code, optional condition_code)
ACTION_PLANS: Dict[Tuple[str, Optional[str]], str] = {
    ("PA", None): "Start with a short daily walk plan and increase time gradually. Consider a weekly schedule you can repeat.",
    ("PA", "CD"): "Ask about enrolling in a cardiac rehabilitation program for supervised exercise and education.",
    ("BP", None): "Use a home blood pressure monitor, log readings (morning/evening), and review trends with your clinician."
}

# F) Content links keyed by topic tags (behavior, condition, or a named topic)
# You can attach multiple links per question.
CONTENT_LINKS: Dict[str, Dict[str, str]] = {
    "PA": {"org": "American Heart Association", "title": "Physical Activity Recommendations", "url": "https://www.heart.org/en/healthy-living/fitness"},
    "BP": {"org": "American Heart Association", "title": "Understanding Blood Pressure Readings", "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings"},
    "CD": {"org": "American Heart Association", "title": "Exercise and Heart Disease", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/exercise-and-heart-disease"},
    "CARDIAC_REHAB": {"org": "American Heart Association", "title": "Cardiac Rehabilitation", "url": "https://www.heart.org/en/health-topics/cardiac-rehab"},
    "MYLIFECHECK": {"org": "American Heart Association", "title": "My Life Check (Life’s Essential 8)", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check"}
}


# -----------------------------
# 4) Clinical inputs reuse: pull from combined_calculator if available
# -----------------------------

def extract_clinical_inputs(calc_mod) -> Dict[str, Any]:
    """
    Attempts to reuse clinical input values from combined_calculator.py so they don't need reentry.

    Supported patterns (any one is enough):
    - calc_mod.INPUTS  (dict)
    - calc_mod.inputs  (dict)
    - calc_mod.get_inputs() -> dict
    - calc_mod.get_latest_inputs() -> dict

    If none found, returns {}.
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


# -----------------------------
# 5) Calculator runners with "only if available" behavior
# -----------------------------

def _call_if_exists(calc_mod, fn_name: str, *args, **kwargs) -> Optional[Any]:
    if hasattr(calc_mod, fn_name) and callable(getattr(calc_mod, fn_name)):
        return getattr(calc_mod, fn_name)(*args, **kwargs)
    return None


def have_keys(d: Dict[str, Any], keys: List[str]) -> bool:
    return all(k in d and d[k] not in (None, "") for k in keys)


def run_mylifecheck(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # If combined_calculator exposes a wrapper, use it.
    out = _call_if_exists(calc_mod, "run_mylifecheck", clinical)
    if out is not None:
        return out

    # Otherwise: if it has a known calculator fn name, try it.
    out = _call_if_exists(calc_mod, "calculate_mylifecheck", clinical)
    return out


def run_prevent(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_prevent", clinical)
    if out is not None:
        return out
    out = _call_if_exists(calc_mod, "calculate_prevent", clinical)
    return out


def run_chads2vasc(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_chads2vasc", clinical)
    if out is not None:
        return out

    # Try raw calc if present and minimum inputs exist
    if hasattr(calc_mod, "calculate_chads2vasc") and callable(calc_mod.calculate_chads2vasc):
        required = ["age", "gender"]
        if not have_keys(clinical, required):
            return None
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

    return None


def run_cardiac_rehab(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_cardiac_rehab_eligibility", clinical)
    if out is not None:
        return out

    if hasattr(calc_mod, "calculate_cardiac_rehab_eligibility") and callable(calc_mod.calculate_cardiac_rehab_eligibility):
        # These can be missing; default "No"
        eligible = calc_mod.calculate_cardiac_rehab_eligibility(
            CABG=clinical.get("CABG", "No"),
            AMI=clinical.get("AMI", "No"),
            PCI=clinical.get("PCI", "No"),
            cardiac_arrest=clinical.get("cardiac_arrest", "No"),
            heart_failure=clinical.get("heart_failure", "No"),
        )
        return {"cardiac_rehab_eligible": eligible}

    return None


def run_healthy_day_at_home(calc_mod, clinical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = _call_if_exists(calc_mod, "run_healthy_day_at_home", clinical)
    if out is not None:
        return out

    if hasattr(calc_mod, "healthy_day_at_home") and callable(calc_mod.healthy_day_at_home):
        # If missing, default gently
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

    return None


# -----------------------------
# 6) Hook routing: decide what to run (based on codes + availability)
# -----------------------------

def should_run_mylifecheck(behavior: str, codes: Dict[str, int]) -> bool:
    return behavior in {"PA", "BP", "NUT", "SL", "TOB"} or codes.get("CKM", 0) == 1

def should_run_prevent(behavior: str, codes: Dict[str, int]) -> bool:
    return any(codes.get(k, 0) == 1 for k in ("HT", "CD", "CKD", "CKM")) or behavior in {"PA", "BP"}

def should_run_chads2vasc(codes: Dict[str, int], clinical: Dict[str, Any]) -> bool:
    af_flag = codes.get("AF", 0) == 1 or str(clinical.get("atrial_fibrillation", "")).strip().lower() in {"yes", "y", "true", "1"}
    return af_flag

def should_run_cardiac_rehab(codes: Dict[str, int]) -> bool:
    return codes.get("CD", 0) == 1 or codes.get("HF", 0) == 1

def should_run_healthy_day(_: Dict[str, int]) -> bool:
    return True


# -----------------------------
# 7) Messaging assembly (using dictionaries)
# -----------------------------

def assemble_messages(payload: SignaturesPayload) -> None:
    b = payload.behavioral_core
    codes = payload.codes

    # Behavioral core message
    if b in BEHAVIORAL_CORE_MESSAGES:
        payload.behavioral_core_messages.append(BEHAVIORAL_CORE_MESSAGES[b])

    # Condition modifier messages (only if condition present == 1)
    for cond in payload.active_conditions:
        msg = CONDITION_MODIFIER_MESSAGES.get((b, cond))
        if msg:
            payload.condition_modifier_messages.append(msg)

    # Engagement driver messages (only drivers > 0)
    for drv in payload.active_drivers:
        msg = ENGAGEMENT_DRIVER_MESSAGES.get((b, drv))
        if msg:
            payload.engagement_driver_messages.append(msg)

    # Security rules: prefer condition-specific, fallback to generic
    # If multiple conditions, add those that exist; always consider generic too.
    added_any = False
    for cond in payload.active_conditions:
        rule = SECURITY_RULES.get((b, cond))
        if rule:
            payload.security_rules.append(rule)
            added_any = True
    generic_rule = SECURITY_RULES.get((b, None))
    if generic_rule and not added_any:
        payload.security_rules.append(generic_rule)

    # Action plans: prefer condition-specific, fallback to generic
    added_any = False
    for cond in payload.active_conditions:
        plan = ACTION_PLANS.get((b, cond))
        if plan:
            payload.action_plans.append(plan)
            added_any = True
    generic_plan = ACTION_PLANS.get((b, None))
    if generic_plan and not added_any:
        payload.action_plans.append(generic_plan)

    # Content links: attach by behavior + any key conditions + named topics
    if b in CONTENT_LINKS:
        payload.content_links.append(CONTENT_LINKS[b])
    for cond in payload.active_conditions:
        if cond in CONTENT_LINKS:
            payload.content_links.append(CONTENT_LINKS[cond])

    # If action plan implies cardiac rehab, attach link
    if any("cardiac rehabilitation" in p.lower() for p in payload.action_plans):
        payload.content_links.append(CONTENT_LINKS["CARDIAC_REHAB"])

    # Always include MyLifeCheck link when hooks are possible (optional)
    payload.content_links.append(CONTENT_LINKS["MYLIFECHECK"])


# -----------------------------
# 8) Build payload end-to-end
# -----------------------------

def build_payload(sig: SignaturesInput, calc_mod) -> SignaturesPayload:
    codes = normalize_codes(sig)

    active_conditions = [
        k for k, v in codes.items()
        if v == 1 and k.isupper() and k not in DRIVER_CODES and k != sig.behavioral_core
    ]
    active_drivers = [k for k, v in codes.items() if k in DRIVER_CODES and v > 0]

    payload = SignaturesPayload(
        question=sig.question,
        codes=codes,
        behavioral_core=sig.behavioral_core,
        active_conditions=active_conditions,
        active_drivers=active_drivers,
    )

    # Pull clinical inputs from combined_calculator if available (no re-entry)
    clinical = extract_clinical_inputs(calc_mod)

    # Measurements (only run if:
    # - routing says yes
    # - calculator wrappers exist
    # - and/or minimum inputs exist inside the calculator)
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

    # Assemble messages + links
    assemble_messages(payload)

    return payload


# -----------------------------
# 9) CLI: Signatures inputs only (no clinical re-entry)
# -----------------------------

def prompt_signatures_input() -> SignaturesInput:
    print("\n=== Signatures Input (no clinical re-entry) ===")
    question = input("Enter the question: ").strip()

    behavioral_core = input("Behavioral core code (e.g., PA, BP, NUT, MA): ").strip().upper()

    print("\nCondition modifiers (enter codes like CD, HT, CKD, AF; blank to stop).")
    condition_mods: Dict[str, int] = {}
    while True:
        c = input("Condition code (blank to stop): ").strip().upper()
        if not c:
            break
        condition_mods[c] = 1

    print("\nEngagement drivers (enter code + value: -1 not present, 0 unknown, 1 present; blank driver to stop).")
    drivers: Dict[str, int] = {}
    while True:
        d = input("Driver code (blank to stop): ").strip().upper()
        if not d:
            break

        while True:
            raw = input("Value (-1, 0, 1): ").strip()
            if raw == "":
                print(" Please enter -1, 0, or 1.")
                continue
            try:
                v = int(raw)
            except ValueError:
                print(" Invalid. Enter -1, 0, or 1.")
                continue
            if v not in (-1, 0, 1):
                print(" Must be -1, 0, or 1.")
                continue
            drivers[d] = v
            break

    return SignaturesInput(
        question=question,
        behavioral_core=behavioral_core,
        condition_modifiers=condition_mods,
        engagement_drivers=drivers,
    )


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

    sig = prompt_signatures_input()
    payload = build_payload(sig, calc_mod)

    print("\n=== Signatures Payload (LLM-ready) ===")
    print(json.dumps(asdict(payload), indent=2, default=str))

    # Gentle notes if clinical inputs couldn't be reused
    clinical = extract_clinical_inputs(calc_mod)
    if not clinical:
        #print("\n NOTE: No clinical inputs found in combined_calculator.py.")
        #print("To reuse values automatically, expose one of these in combined_calculator.py:")
        print("- INPUTS = {...}   (dict)")
        print("- inputs = {...}   (dict)")
        print("- def get_inputs(): return {...}")
        print("- def get_latest_inputs(): return {...}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
