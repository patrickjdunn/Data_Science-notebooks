"""
signatures_engine.py

A Signatures “orchestrator” that:
1) collects Signatures inputs (question + behavioral core + condition modifiers + engagement drivers)
2) collects clinical / biomarker inputs (for calculators)
3) runs measurement hooks using your combined_calculator.py (MyLifeCheck + PREVENT + CHA2DS2-VASc + cardiac rehab + healthy day at home)
4) emits an LLM-ready payload (JSON)

This file is designed to be robust in interactive CLI use:
- validates driver values (-1,0,1)
- never crashes on blank inputs
- supports importing a calculator module from an arbitrary file path

It expects your calculator file at:
  /mnt/data/combined_calculator (6).py   :contentReference[oaicite:0]{index=0}
You can change CALCULATOR_PATH below if needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import importlib.util
import json
import sys


# -----------------------------
# 0) Configure calculator module path
# -----------------------------

# Default to the uploaded filename (works even with spaces/parentheses)
CALCULATOR_PATH = Path("/mnt/data/combined_calculator (6).py")  # :contentReference[oaicite:1]{index=1}
CALCULATOR_MODULE_NAME = "combined_calculator_runtime"


# -----------------------------
# 1) Dynamic import helper
# -----------------------------

def import_module_from_path(path: Path, module_name: str):
    """
    Import a Python module from an arbitrary file path.
    This avoids needing to rename files like "combined_calculator (6).py".
    """
    if not path.exists():
        raise FileNotFoundError(f"Calculator module not found at: {path}")

    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


# -----------------------------
# 2) Signatures input model
# -----------------------------

DRIVER_CODES = {"PR", "RC", "SE", "GO", "ID", "HL", "DS", "TR", "FI", "HI", "AX"}
# Conditions can be whatever you use, but these are common examples:
KNOWN_CONDITION_CODES = {"CD", "HF", "HT", "DM", "CKD", "CKM", "AF", "STROKE"}

@dataclass
class SignaturesInput:
    question: str
    behavioral_core: str                 # e.g., "PA", "BP", "NUT", "MA"
    condition_modifiers: Dict[str, int]  # e.g., {"CD":1,"HT":1}
    engagement_drivers: Dict[str, int]   # -1 not present, 0 unknown, +1 present


def normalize_codes(si: SignaturesInput) -> Dict[str, int]:
    """
    Build a unified code vector.
    - behavioral core and conditions: 1 present, 0 not present
    - engagement drivers: -1, 0, +1
    """
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
# 3) Clinical inputs model (flexible dict)
# -----------------------------

@dataclass
class ClinicalInputs:
    data: Dict[str, Any]


# -----------------------------
# 4) Measurement outputs + full payload
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
    measurement: MeasurementResults = field(default_factory=MeasurementResults)

    # You can expand these later as you re-integrate your taxonomy content blocks
    security_rules: List[str] = field(default_factory=list)
    action_plans: List[str] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)


# -----------------------------
# 5) Hook routing
# -----------------------------

def should_run_mylifecheck(behavior: str, codes: Dict[str, int]) -> bool:
    # Run for most lifestyle/monitoring behaviors or CKM framing
    return behavior in {"PA", "BP", "NUT", "SL", "TOB", "WT", "GLU", "CHOL"} or codes.get("CKM", 0) == 1


def should_run_prevent(behavior: str, codes: Dict[str, int]) -> bool:
    # Run if HT/CD/CKD/CKM or exercise/BP behavior
    return any(codes.get(k, 0) == 1 for k in ("HT", "CD", "CKD", "CKM")) or behavior in {"PA", "BP"}


def should_run_chads2vasc(codes: Dict[str, int], clinical: Dict[str, Any]) -> bool:
    # Prefer AF flag; allow either a condition modifier "AF" or clinical flag
    if codes.get("AF", 0) == 1:
        return True
    val = str(clinical.get("atrial_fibrillation", "")).strip().lower()
    return val in {"yes", "y", "true", "1"}


def should_run_cardiac_rehab(codes: Dict[str, int], clinical: Dict[str, Any]) -> bool:
    # Often useful for CD/HF or after events; you can tighten this later
    return any(codes.get(k, 0) == 1 for k in ("CD", "HF")) or any(
        str(clinical.get(k, "No")).strip().lower() == "yes"
        for k in ("AMI", "PCI", "CABG", "cardiac_arrest", "heart_failure")
    )


def should_run_healthy_day_at_home(_: Dict[str, int], __: Dict[str, Any]) -> bool:
    # Useful for most self-management flows
    return True


# -----------------------------
# 6) Calculator adapters (tolerant of different function names)
# -----------------------------

def _has_attr(mod, name: str) -> bool:
    return hasattr(mod, name) and callable(getattr(mod, name))


def run_mylifecheck(calc_mod, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Try common entrypoints. If your combined_calculator already exposes a function, we call it.
    Otherwise return None and let you add a wrapper in the calculator file.
    """
    # Preferred wrapper name:
    if _has_attr(calc_mod, "run_mylifecheck"):
        return calc_mod.run_mylifecheck(inputs)

    # Common alternative:
    if _has_attr(calc_mod, "calculate_mylifecheck"):
        return calc_mod.calculate_mylifecheck(inputs)

    # If your file computes MyLifeCheck only in a main/script section, you’ll want to add a wrapper.
    return None


def run_prevent(calc_mod, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if _has_attr(calc_mod, "run_prevent"):
        return calc_mod.run_prevent(inputs)

    if _has_attr(calc_mod, "calculate_prevent"):
        return calc_mod.calculate_prevent(inputs)

    return None


def run_chads2vasc(calc_mod, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if _has_attr(calc_mod, "run_chads2vasc"):
        return calc_mod.run_chads2vasc(inputs)

    # If you expose a raw calculator:
    if _has_attr(calc_mod, "calculate_chads2vasc"):
        # Expect typical CHA2DS2-VASc inputs; fall back to defaults if missing.
        score = calc_mod.calculate_chads2vasc(
            age=inputs.get("age"),
            gender=inputs.get("gender"),
            heart_failure=inputs.get("heart_failure", "No"),
            hypertension=inputs.get("hypertension", "No"),
            diabetes=inputs.get("diabetes", "No"),
            stroke_or_tia=inputs.get("stroke_or_tia", "No"),
            vascular_disease=inputs.get("vascular_disease", "No"),
        )
        return {"chads2vasc": score}

    return None


def run_cardiac_rehab(calc_mod, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if _has_attr(calc_mod, "run_cardiac_rehab_eligibility"):
        return calc_mod.run_cardiac_rehab_eligibility(inputs)

    if _has_attr(calc_mod, "calculate_cardiac_rehab_eligibility"):
        eligible = calc_mod.calculate_cardiac_rehab_eligibility(
            CABG=inputs.get("CABG", "No"),
            AMI=inputs.get("AMI", "No"),
            PCI=inputs.get("PCI", "No"),
            cardiac_arrest=inputs.get("cardiac_arrest", "No"),
            heart_failure=inputs.get("heart_failure", "No"),
        )
        return {"cardiac_rehab_eligible": eligible}

    return None


def run_healthy_day_at_home(calc_mod, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if _has_attr(calc_mod, "run_healthy_day_at_home"):
        return calc_mod.run_healthy_day_at_home(inputs)

    if _has_attr(calc_mod, "healthy_day_at_home"):
        # Your earlier signature examples used:
        # healthy_day_at_home(symptoms, step_count, unplanned_visits, medication_adherence)
        result = calc_mod.healthy_day_at_home(
            symptoms=inputs.get("symptoms", 0),
            step_count=inputs.get("step_count", 0),
            unplanned_visits=inputs.get("unplanned_visits", 0),
            medication_adherence=inputs.get("medication_adherence", 1),
        )
        # Could be tuple or dict depending on your implementation:
        if isinstance(result, tuple) and len(result) == 2:
            score, note = result
            return {"healthy_day_score": score, "healthy_day_message": note}
        return {"healthy_day_at_home": result}

    return None


# -----------------------------
# 7) Build payload
# -----------------------------

def build_payload(sig: SignaturesInput, clinical: ClinicalInputs, calc_mod) -> SignaturesPayload:
    codes = normalize_codes(sig)

    # active conditions: present and not engagement drivers
    active_conditions = [
        k for k, v in codes.items()
        if v == 1 and k.isupper() and k not in DRIVER_CODES and k != sig.behavioral_core
    ]

    # active drivers: > 0 only
    active_drivers = [k for k, v in codes.items() if k in DRIVER_CODES and v > 0]

    payload = SignaturesPayload(
        question=sig.question,
        codes=codes,
        behavioral_core=sig.behavioral_core,
        active_conditions=active_conditions,
        active_drivers=active_drivers,
    )

    data = clinical.data

    # Measurements
    if should_run_mylifecheck(sig.behavioral_core, codes):
        payload.measurement.mylifecheck = run_mylifecheck(calc_mod, data)

    if should_run_prevent(sig.behavioral_core, codes):
        payload.measurement.prevent = run_prevent(calc_mod, data)

    if should_run_chads2vasc(codes, data):
        payload.measurement.chads2vasc = run_chads2vasc(calc_mod, data)

    if should_run_cardiac_rehab(codes, data):
        payload.measurement.cardiac_rehab = run_cardiac_rehab(calc_mod, data)

    if should_run_healthy_day_at_home(codes, data):
        payload.measurement.healthy_day_at_home = run_healthy_day_at_home(calc_mod, data)

    # Starter security rules + action plans (you can swap these for registry-driven content later)
    if sig.behavioral_core == "PA":
        payload.security_rules.append(
            "SECURITY STOP RULE: If you experience chest pain during exercise, stop immediately and contact your healthcare professional."
        )
        if codes.get("CD", 0) == 1 or str(data.get("heart_failure", "No")).strip().lower() == "yes":
            payload.action_plans.append("ACTION PLAN: Recommend a cardiac rehabilitation program if eligible.")

    if codes.get("AF", 0) == 1 and payload.measurement.chads2vasc:
        payload.action_plans.append("ACTION PLAN: Discuss stroke prevention options (anticoagulation) based on CHA₂DS₂-VASc score with your clinician.")

    return payload


# -----------------------------
# 8) CLI helpers (robust input parsing)
# -----------------------------

def _prompt_nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("⚠️  Please enter a value.")


def _prompt_int(prompt: str, *, allow_blank: bool = False, default: Optional[int] = None) -> Optional[int]:
    while True:
        raw = input(prompt).strip()
        if raw == "":
            if allow_blank:
                return default
            print("⚠️  Please enter an integer.")
            continue
        try:
            return int(raw)
        except ValueError:
            print("⚠️  Invalid integer. Try again.")


def _prompt_float(prompt: str, *, allow_blank: bool = False, default: Optional[float] = None) -> Optional[float]:
    while True:
        raw = input(prompt).strip()
        if raw == "":
            if allow_blank:
                return default
            print("⚠️  Please enter a number.")
            continue
        try:
            return float(raw)
        except ValueError:
            print("⚠️  Invalid number. Try again.")


def _prompt_yes_no(prompt: str, default: str = "No") -> str:
    """
    Returns 'Yes' or 'No'
    """
    raw = input(f"{prompt} (Yes/No) [default {default}]: ").strip().lower()
    if raw == "":
        return default
    if raw in {"y", "yes", "true", "1"}:
        return "Yes"
    if raw in {"n", "no", "false", "0"}:
        return "No"
    print("⚠️  Please enter Yes or No. Using default.")
    return default


def prompt_signatures_input() -> SignaturesInput:
    print("\n=== Signatures Input ===")
    question = _prompt_nonempty("Enter the question: ")
    behavioral_core = _prompt_nonempty("Behavioral core code (e.g., PA, BP, NUT, MA): ").upper()

    print("\nCondition modifiers (enter codes like CD, HT, CKD, AF; blank to stop).")
    condition_mods: Dict[str, int] = {}
    while True:
        c = input("Condition code (blank to stop): ").strip().upper()
        if not c:
            break
        # if you want to enforce known codes, uncomment:
        # if c not in KNOWN_CONDITION_CODES:
        #     print(f"⚠️  Unknown condition code '{c}'. Keep it anyway? (y/n)")
        #     if input().strip().lower() not in {"y","yes"}:
        #         continue
        condition_mods[c] = 1

    print("\nEngagement drivers (enter code + value: -1 not present, 0 unknown, 1 present; blank driver to stop).")
    drivers: Dict[str, int] = {}
    while True:
        d = input("Driver code (blank to stop): ").strip().upper()
        if not d:
            break

        if d not in DRIVER_CODES:
            print(f"⚠️  '{d}' not in known driver codes {sorted(DRIVER_CODES)}. Keeping anyway.")

        # Robust: re-prompt until valid (-1,0,1)
        while True:
            raw = input("Value (-1 not present, 0 unknown, 1 present): ").strip()
            if raw == "":
                print("⚠️  Please enter -1, 0, or 1 (blank is not allowed here).")
                continue
            try:
                v = int(raw)
            except ValueError:
                print("⚠️  Invalid input. Enter -1, 0, or 1.")
                continue
            if v not in (-1, 0, 1):
                print("⚠️  Value must be -1, 0, or 1.")
                continue
            drivers[d] = v
            break

    return SignaturesInput(
        question=question,
        behavioral_core=behavioral_core,
        condition_modifiers=condition_mods,
        engagement_drivers=drivers,
    )


def prompt_clinical_inputs_minimal() -> ClinicalInputs:
    """
    Minimal clinical inputs for common calculators.
    Add fields as your combined_calculator requires.
    """
    print("\n=== Clinical Inputs (minimal starter set) ===")

    age = _prompt_int("Age: ")
    gender = _prompt_nonempty("Gender (male/female): ").lower()

    sbp = _prompt_float("Systolic BP (mmHg): ")
    dbp = _prompt_float("Diastolic BP (mmHg): ")

    tc = _prompt_float("Total cholesterol (mg/dL): ", allow_blank=True, default=None)
    hdl = _prompt_float("HDL cholesterol (mg/dL): ", allow_blank=True, default=None)

    diabetes = _prompt_yes_no("Diabetes?")
    # Use your preferred encoding (string categories) if your PREVENT code expects that:
    tobacco_use = input("Tobacco use (Current user/Former smoker/Never used) [blank ok]: ").strip()

    # Optional PREVENT-ish extras (blank ok)
    bmi = _prompt_float("BMI [blank ok]: ", allow_blank=True, default=None)
    egfr = _prompt_float("eGFR [blank ok]: ", allow_blank=True, default=None)
    bptreat = _prompt_yes_no("On blood pressure medication (bptreat)?")

    # AF (for CHA2DS2-VASc routing)
    af = _prompt_yes_no("Atrial fibrillation?")

    # Cardiac rehab eligibility flags
    ami = _prompt_yes_no("History of MI/AMI?")
    pci = _prompt_yes_no("History of PCI?")
    cabg = _prompt_yes_no("History of CABG?")
    hf = _prompt_yes_no("Heart failure?")
    cardiac_arrest = _prompt_yes_no("History of cardiac arrest?")

    # Healthy day at home
    symptoms = _prompt_int("Symptoms today? (0=no, 1=yes): ")
    step_count = _prompt_int("Step count today: ", allow_blank=True, default=0)
    unplanned_visits = _prompt_int("Unplanned visits today (0+): ", allow_blank=True, default=0)
    medication_adherence = _prompt_int(
        "Medication adherence (0=good, 1=inconsistent, 2=not taking) [default 0]: ",
        allow_blank=True,
        default=0
    )

    # Assemble dict (use keys your calculator expects; you can rename here without changing UX)
    data: Dict[str, Any] = {
        "age": age,
        "gender": gender,
        "systolic_blood_pressure": sbp,
        "diastolic_blood_pressure": dbp,
        "sbp": sbp,  # sometimes calculators use sbp/dbp short names
        "dbp": dbp,

        "total_cholesterol": tc,
        "HDL_cholesterol": hdl,
        "tc": tc,
        "hdl": hdl,

        "diabetes": diabetes,
        "tobacco_use": tobacco_use,

        "bmi": bmi,
        "egfr": egfr,
        "bptreat": bptreat,

        "atrial_fibrillation": af,
        "AF": af,  # optional alias

        "AMI": ami,
        "PCI": pci,
        "CABG": cabg,
        "heart_failure": hf,
        "cardiac_arrest": cardiac_arrest,

        "symptoms": symptoms,
        "step_count": step_count,
        "unplanned_visits": unplanned_visits,
        "medication_adherence": medication_adherence,
    }

    return ClinicalInputs(data=data)


# -----------------------------
# 9) Main
# -----------------------------

def main() -> int:
    # Import calculator module dynamically
    try:
        calc_mod = import_module_from_path(CALCULATOR_PATH, CALCULATOR_MODULE_NAME)
    except Exception as e:
        print(f"ERROR importing calculator module: {e}")
        print("Tip: Update CALCULATOR_PATH at the top of this file.")
        return 1

    sig = prompt_signatures_input()
    clinical = prompt_clinical_inputs_minimal()

    payload = build_payload(sig, clinical, calc_mod)

    print("\n=== Signatures Payload (LLM-ready) ===")
    print(json.dumps(asdict(payload), indent=2, default=str))

    # Helpful warnings if wrappers are missing in the calculator module
    missing = []
    if should_run_mylifecheck(sig.behavioral_core, payload.codes) and payload.measurement.mylifecheck is None:
        missing.append("MyLifeCheck (expected function run_mylifecheck or calculate_mylifecheck)")
    if should_run_prevent(sig.behavioral_core, payload.codes) and payload.measurement.prevent is None:
        missing.append("PREVENT (expected function run_prevent or calculate_prevent)")

    if missing:
        print("\n⚠️  NOTE:")
        print("Some measurement outputs are None because the calculator module did not expose a callable wrapper.")
        print("Add wrapper functions in your combined_calculator file (recommended) or rename functions accordingly:")
        for m in missing:
            print(f"- {m}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
