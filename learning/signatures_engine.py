"""
signatures_engine.py (persona-enabled)

Adds:
- Persona selection (Listener/Motivator/Director/Expert) via an input prompt
- Persona-specific content dictionaries for behavioral core, condition modifiers, engagement drivers,
  security rules, and action plans
- Persona-aware assembly so output includes BOTH:
  - canonical structural sections (behavior, conditions, drivers, security, actions)
  - persona-rendered messages

Keeps:
- Reuse clinical inputs from combined_calculator.py (if exposed)
- Optional inputs: calculators run only if available and/or wrappers exist

Folder layout expected:
learning/
  signatures_engine.py
  combined_calculator.py
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Literal
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
# 1) Persona + Signatures input model
# -----------------------------

Persona = Literal["Listener", "Motivator", "Director", "Expert"]

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

    # Persona-rendered outputs (ready to display)
    persona_output: List[str] = field(default_factory=list)

    # Measurement + content
    measurement: MeasurementResults = field(default_factory=MeasurementResults)
    content_links: List[Dict[str, str]] = field(default_factory=list)  # [{"title":..., "url":..., "org":...}]


# -----------------------------
# 3) Persona content dictionaries
#
# Strategy:
# - Provide persona-specific variants for each content layer.
# - Use fallback order:
#   (behavior, condition/driver) persona-specific -> generic persona-specific -> canonical -> nothing
# -----------------------------

# A) Behavioral core (persona-specific)
BEHAVIOR_CORE_PERSONA: Dict[Tuple[str, Persona], str] = {
    ("PA", "Listener"):  "It can feel like a lot at first. Let’s start with what feels doable and safe for you.",
    ("PA", "Motivator"): "You’re building momentum. Even small walks count—and they add up fast.",
    ("PA", "Director"):  "Start with a simple weekly plan: short walks most days, then increase time gradually.",
    ("PA", "Expert"):    "Begin with moderate activity and progressive overload. Monitor symptoms and intensity using talk test/RPE.",
    ("BP", "Listener"):  "It’s normal to feel unsure about numbers. We can take this one step at a time.",
    ("BP", "Motivator"): "Knowing your numbers puts you in control. You can improve them with consistent habits.",
    ("BP", "Director"):  "Measure BP consistently and compare to your target. Use home averages to guide decisions.",
    ("BP", "Expert"):    "Use validated home BP technique; interpret based on guideline categories and longitudinal trends."
}

# Canonical fallback (non-persona) behavioral core
BEHAVIOR_CORE_CANONICAL: Dict[str, str] = {
    "PA": "Start with safe, manageable movement and build consistency. Walking is a great place to begin.",
    "BP": "Know your numbers and track patterns over time. Small changes can add up to meaningful blood pressure improvement.",
    "NUT": "Focus on simple, repeatable improvements—more whole foods, fewer ultra-processed foods, and mindful portions.",
    "SL": "Aim for consistent sleep timing and a wind-down routine to support recovery and cardiometabolic health.",
    "MA": "Medications work best when taken consistently. Pair doses with daily routines and keep an updated medication list.",
    "SY": "Track symptoms and trends, not single moments. Write down what you notice and share patterns with your clinician.",
    "SM": "Stress management is a health skill. Small daily practices can lower strain and support better decisions."
}

# B) Condition modifiers (persona-specific)
# keyed by (behavior, condition, persona)
CONDITION_PERSONA: Dict[Tuple[str, str, Persona], str] = {
    ("PA", "CD", "Listener"):  "Because of your heart history, it makes sense to be cautious. We’ll start gently and keep you safe.",
    ("PA", "CD", "Motivator"): "You can absolutely build fitness safely—steady progress is the goal, not pushing hard.",
    ("PA", "CD", "Director"):  "With coronary artery disease, start gradually and consider supervised exercise (cardiac rehab) before increasing intensity.",
    ("PA", "CD", "Expert"):    "CAD warrants graded activity progression; cardiac rehab or stress-test–guided prescription may be appropriate.",

    ("BP", "CKD", "Listener"): "Kidney and blood pressure health are connected. We can make a plan that protects both.",
    ("BP", "CKD", "Motivator"): "Protecting your kidneys is a powerful reason to stay consistent with BP habits.",
    ("BP", "CKD", "Director"):  "With CKD, BP targets and meds may be tailored—coordinate closely with your clinician.",
    ("BP", "CKD", "Expert"):    "CKD changes risk and treatment thresholds; individualized targets often prioritize renal protection."
}

# Canonical fallback (non-persona)
CONDITION_CANONICAL: Dict[Tuple[str, str], str] = {
    ("PA", "CD"): "With coronary artery disease, start gradually and progress slowly. If available, begin with supervised guidance like cardiac rehab.",
    ("PA", "HF"): "With heart failure, begin with short, low-intensity activity and rest as needed. Consistency matters more than intensity.",
    ("BP", "CKD"): "With kidney disease, blood pressure targets and medications may be adjusted to protect kidney function—coordinate closely with your care team.",
    ("NUT", "CKD"): "With kidney disease, nutrition may require tailored guidance (sodium, potassium, phosphorus)—ask for kidney-specific recommendations."
}

# C) Engagement drivers (persona-specific)
# keyed by (behavior, driver, persona)
DRIVER_PERSONA: Dict[Tuple[str, str, Persona], str] = {
    ("PA", "PR", "Listener"):  "Would you like to pick just one small next step so it feels less overwhelming?",
    ("PA", "PR", "Motivator"): "Let’s set a baseline today and beat it by a tiny amount next week.",
    ("PA", "PR", "Director"):  "Set a starting goal (minutes/week) and increase gradually each week.",
    ("PA", "PR", "Expert"):    "Use a progression rule (e.g., +10% weekly volume) and monitor response.",

    ("PA", "HL", "Listener"):  "We’ll keep the plan simple—nothing complicated.",
    ("PA", "HL", "Motivator"): "Simple works. Start with a pace that feels comfortable and repeat it.",
    ("PA", "HL", "Director"):  "Use the talk test: you should be able to speak in full sentences while moving.",
    ("PA", "HL", "Expert"):    "Use RPE/talk test; moderate intensity generally aligns with conversational ability.",

    ("BP", "GO", "Listener"):  "Would it help to write down your goal so it feels clearer?",
    ("BP", "GO", "Motivator"): "A clear goal keeps you focused—your future self will thank you.",
    ("BP", "GO", "Director"):  "Write your BP goal and compare home averages weekly.",
    ("BP", "GO", "Expert"):    "Track HBPM averages and variability; review in follow-up for therapy titration."
}

# Canonical fallback (non-persona)
DRIVER_CANONICAL: Dict[Tuple[str, str], str] = {
    ("PA", "PR"): "Set a simple starting goal (like minutes walked) and increase gradually each week.",
    ("PA", "HL"): "Keep it simple: if you can move and still talk, the intensity is usually about right.",
    ("BP", "GO"): "Write down a clear blood pressure goal and track readings consistently so you can see progress.",
    ("NUT", "SE"): "Pick one change you’re confident you can do this week—success builds confidence for the next step."
}

# D) Security rules (persona-neutral on purpose, but allow persona variants if you want later)
SECURITY_RULES: Dict[Tuple[str, Optional[str]], str] = {
    ("PA", None): "SECURITY: If you feel faint, severely short of breath, or unwell during exercise, stop and seek medical guidance.",
    ("PA", "CD"): "SECURITY: If you experience chest pain, pressure, or tightness during exercise, stop immediately and contact your healthcare professional.",
    ("BP", None): "SECURITY: If your BP is 180/120 or higher with symptoms (chest pain, shortness of breath, weakness, vision/speech changes), seek emergency care."
}

# E) Action plans (persona-specific optional; default to canonical)
ACTION_PERSONA: Dict[Tuple[str, Optional[str], Persona], str] = {
    ("PA", None, "Listener"):  "ACTION: Start with a short walk most days. We’ll adjust based on how you feel.",
    ("PA", None, "Motivator"): "ACTION: Pick a daily walk time you can keep this week—consistency first.",
    ("PA", None, "Director"):  "ACTION: Walk most days this week; increase total time gradually.",
    ("PA", None, "Expert"):    "ACTION: Prescribe a progressive walking plan; document dose (FITT) and response.",

    ("PA", "CD", "Director"):  "ACTION: Ask about enrolling in a cardiac rehabilitation program for supervised exercise and education.",
    ("PA", "CD", "Expert"):    "ACTION: Cardiac rehab is recommended when eligible; it supports graded exercise, risk factor control, and outcomes."
}

ACTION_CANONICAL: Dict[Tuple[str, Optional[str]], str] = {
    ("PA", None): "ACTION: Start with a short daily walk plan and increase time gradually. Consider a weekly schedule you can repeat.",
    ("PA", "CD"): "ACTION: Ask about enrolling in a cardiac rehabilitation program for supervised exercise and education.",
    ("BP", None): "ACTION: Use a home blood pressure monitor, log readings (morning/evening), and review trends with your clinician."
}

# F) Content links (AHA)
CONTENT_LINKS: Dict[str, Dict[str, str]] = {
    "PA": {"org": "American Heart Association", "title": "Physical Activity Recommendations", "url": "https://www.heart.org/en/healthy-living/fitness"},
    "BP": {"org": "American Heart Association", "title": "Understanding Blood Pressure Readings", "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings"},
    "CD": {"org": "American Heart Association", "title": "Exercise and Heart Disease", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/exercise-and-heart-disease"},
    "CARDIAC_REHAB": {"org": "American Heart Association", "title": "Cardiac Rehabilitation", "url": "https://www.heart.org/en/health-topics/cardiac-rehab"},
    "MYLIFECHECK": {"org": "American Heart Association", "title": "My Life Check (Life’s Essential 8)", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check"},
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


# -----------------------------
# 5) Calculator calls (optional inputs allowed)
# -----------------------------

def _call_if_exists(calc_mod, fn_name: str, *args, **kwargs) -> Optional[Any]:
    if hasattr(calc_mod, fn_name) and callable(getattr(calc_mod, fn_name)):
        return getattr(calc_mod, fn_name)(*args, **kwargs)
    return None


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
    # If raw function exists, it may require inputs; let it handle missing if it can.
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
    return behavior in {"PA", "BP", "NUT", "SL", "TOB"} or codes.get("CKM", 0) == 1

def should_run_prevent(behavior: str, codes: Dict[str, int]) -> bool:
    return any(codes.get(k, 0) == 1 for k in ("HT", "CD", "CKD", "CKM")) or behavior in {"PA", "BP"}

def should_run_chads2vasc(codes: Dict[str, int], clinical: Dict[str, Any]) -> bool:
    af = codes.get("AF", 0) == 1 or str(clinical.get("atrial_fibrillation", "")).strip().lower() in {"yes", "y", "true", "1"}
    return af

def should_run_cardiac_rehab(codes: Dict[str, int]) -> bool:
    return codes.get("CD", 0) == 1 or codes.get("HF", 0) == 1

def should_run_healthy_day(_: Dict[str, int]) -> bool:
    return True


# -----------------------------
# 7) Persona-aware message assembly
# -----------------------------

def _get_behavior_msg(behavior: str, persona: Persona) -> Optional[str]:
    return BEHAVIOR_CORE_PERSONA.get((behavior, persona)) or BEHAVIOR_CORE_CANONICAL.get(behavior)

def _get_condition_msg(behavior: str, cond: str, persona: Persona) -> Optional[str]:
    return CONDITION_PERSONA.get((behavior, cond, persona)) or CONDITION_CANONICAL.get((behavior, cond))

def _get_driver_msg(behavior: str, drv: str, persona: Persona) -> Optional[str]:
    return DRIVER_PERSONA.get((behavior, drv, persona)) or DRIVER_CANONICAL.get((behavior, drv))

def _get_action_msg(behavior: str, cond: Optional[str], persona: Persona) -> Optional[str]:
    return ACTION_PERSONA.get((behavior, cond, persona)) or ACTION_CANONICAL.get((behavior, cond))

def assemble_messages(payload: SignaturesPayload) -> None:
    b = payload.behavioral_core
    persona = payload.persona

    # Behavioral core
    core = _get_behavior_msg(b, persona)
    if core:
        payload.behavioral_core_messages.append(core)

    # Condition modifiers
    for cond in payload.active_conditions:
        msg = _get_condition_msg(b, cond, persona)
        if msg:
            payload.condition_modifier_messages.append(msg)

    # Engagement drivers
    for drv in payload.active_drivers:
        msg = _get_driver_msg(b, drv, persona)
        if msg:
            payload.engagement_driver_messages.append(msg)

    # Security rules (persona-neutral; prefer condition-specific)
    added = False
    for cond in payload.active_conditions:
        rule = SECURITY_RULES.get((b, cond))
        if rule:
            payload.security_rules.append(rule)
            added = True
    if not added:
        rule = SECURITY_RULES.get((b, None))
        if rule:
            payload.security_rules.append(rule)

    # Action plans (persona-aware; prefer condition-specific then generic)
    added = False
    for cond in payload.active_conditions:
        plan = _get_action_msg(b, cond, persona)
        if plan:
            payload.action_plans.append(plan)
            added = True
    if not added:
        plan = _get_action_msg(b, None, persona)
        if plan:
            payload.action_plans.append(plan)

    # Content links
    if b in CONTENT_LINKS:
        payload.content_links.append(CONTENT_LINKS[b])
    for cond in payload.active_conditions:
        if cond in CONTENT_LINKS:
            payload.content_links.append(CONTENT_LINKS[cond])
    if any("cardiac rehab" in p.lower() or "cardiac rehabilitation" in p.lower() for p in payload.action_plans):
        payload.content_links.append(CONTENT_LINKS["CARDIAC_REHAB"])
    payload.content_links.append(CONTENT_LINKS["MYLIFECHECK"])

    # Persona output (a neat “final view” for display)
    payload.persona_output = []
    payload.persona_output.append(f"{persona} response to: {payload.question}")
    payload.persona_output.append("")
    payload.persona_output.append("Behavioral Core:")
    payload.persona_output.extend([f"- {m}" for m in payload.behavioral_core_messages])

    if payload.condition_modifier_messages:
        payload.persona_output.append("")
        payload.persona_output.append("Condition Modifiers:")
        payload.persona_output.extend([f"- {m}" for m in payload.condition_modifier_messages])

    if payload.engagement_driver_messages:
        payload.persona_output.append("")
        payload.persona_output.append("Engagement Drivers:")
        payload.persona_output.extend([f"- {m}" for m in payload.engagement_driver_messages])

    if payload.security_rules:
        payload.persona_output.append("")
        payload.persona_output.append("Security Rules:")
        payload.persona_output.extend([f"- {m}" for m in payload.security_rules])

    if payload.action_plans:
        payload.persona_output.append("")
        payload.persona_output.append("Action Plan:")
        payload.persona_output.extend([f"- {m}" for m in payload.action_plans])

    if payload.content_links:
        payload.persona_output.append("")
        payload.persona_output.append("Sources:")
        for link in payload.content_links:
            payload.persona_output.append(f"- {link['org']}: {link['title']} — {link['url']}")


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

    assemble_messages(payload)
    return payload


# -----------------------------
# 9) CLI: Persona + Signatures inputs only
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


def prompt_signatures_input() -> SignaturesInput:
    print("\n=== Signatures Input (persona-enabled; no clinical re-entry) ===")
    persona = prompt_persona()
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

    return SignaturesInput(
        question=question,
        persona=persona,
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

    print("\n=== Persona Output (human-readable) ===")
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

