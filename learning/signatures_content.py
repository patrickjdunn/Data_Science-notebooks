# signatures_content.py
"""
signatures_content.py

Central message libraries (easy to extend):
- Behavioral core messages
- Condition modifier messages
- Engagement driver messages
- Security rules
- Action plans
- Content links (AHA links, etc.)

These are intentionally "LLM-friendly":
- consistent keys (codes)
- persona variants optional
- plain-language variants optional (HL)
"""

from __future__ import annotations
from typing import Dict, Any

PERSONAS = ["Listener", "Motivator", "Director", "Expert"]


# -----------------------------
# Behavioral Core (examples)
# -----------------------------
BEHAVIORAL_CORE_MESSAGES: Dict[str, Dict[str, Any]] = {
    "GEN": {
        "label": "General Support",
        "default": "Start with one small, safe step today and build gradually.",
        "persona": {
            "Listener": "It’s okay to start small. What feels doable right now?",
            "Motivator": "You’ve got this—small steps add up fast.",
            "Director": "Pick one step, schedule it, and track it for 7 days.",
            "Expert": "Gradual, consistent behavior change is associated with better long-term adherence.",
        },
    },
    "PA": {
        "label": "Physical Activity",
        "default": "Begin with low-to-moderate activity and increase gradually.",
        "persona": {
            "Listener": "What kind of movement do you actually enjoy?",
            "Motivator": "A little movement today is a win—let’s stack wins.",
            "Director": "Start with 10 minutes/day, add 5 minutes each week as tolerated.",
            "Expert": "Guidelines commonly target ~150 min/week moderate activity plus strength training.",
        },
        "hl_plain": "Start with short walks or light movement and build slowly.",
    },
    "NUT": {"label": "Nutrition", "default": "Focus on a heart-healthy eating pattern you can sustain."},
    "MA": {"label": "Medication Adherence", "default": "Use routines and reminders to take medications safely and consistently."},
    "SY": {"label": "Monitoring & Symptoms", "default": "Track key numbers and symptoms to spot patterns early."},
    "PC": {"label": "Preventive Care", "default": "Build a plan with your care team and review progress regularly."},
    "HL": {"label": "Health Literacy", "default": "Let’s translate the medical stuff into clear, actionable steps."},
    "ST": {"label": "Stress/Sleep", "default": "Support your heart and brain by improving stress and sleep routines."},
}


# -----------------------------
# Condition Modifiers (examples)
# -----------------------------
CONDITION_MODIFIER_MESSAGES: Dict[str, Dict[str, Any]] = {
    "CKM": {
        "label": "Cardio-Kidney-Metabolic Health",
        "default": "Because heart, kidney, and metabolic health are connected, we’ll focus on BP, glucose, weight, activity, and kidney protection together.",
    },
    "HTN": {
        "label": "High Blood Pressure",
        "default": "Blood pressure control protects your heart, brain, and kidneys—home monitoring and lifestyle changes can make a big difference.",
    },
    "CAD": {
        "label": "Coronary Artery Disease",
        "default": "With CAD, safe activity and risk-factor control (BP, cholesterol, glucose, tobacco) reduce future events—cardiac rehab can help.",
    },
    "HF": {
        "label": "Heart Failure",
        "default": "With heart failure, daily weights and symptom tracking help detect fluid changes early—follow your care plan closely.",
    },
    "AFIB": {
        "label": "Atrial Fibrillation",
        "default": "AFib can raise stroke risk. Rhythm/rate control plus stroke prevention planning are key parts of care.",
    },
    "STROKE": {
        "label": "Stroke",
        "default": "After stroke, secondary prevention targets BP, cholesterol, diabetes, activity, and (when present) AFib management.",
    },
    "DM": {
        "label": "Diabetes",
        "default": "Diabetes affects blood vessels and the heart; activity, food, meds, and monitoring work best together.",
    },
    "CKD": {
        "label": "Kidney Disease",
        "default": "Kidney health can change diet and medication choices—coordinate dietary changes with your care team.",
    },
    "CD": {  # your earlier modifier example
        "label": "Cardiac Disease (general)",
        "default": "Because you may have cardiac risk, we’ll emphasize safe progression and symptom-based stopping rules.",
    },
}


# -----------------------------
# Engagement Drivers (examples)
# -----------------------------
ENGAGEMENT_DRIVER_MESSAGES: Dict[str, Dict[str, Any]] = {
    "PR": {
        "label": "Proactive framing",
        "default": "We’ll focus on the next best step you can take before problems escalate.",
        "persona": {
            "Listener": "What’s one small step you feel ready to try now?",
            "Motivator": "Let’s get ahead of this—small choices today protect your future.",
            "Director": "Pick one measurable step and commit for 7 days.",
            "Expert": "Upstream prevention reduces downstream complications and healthcare utilization.",
        },
    },
    "HL": {
        "label": "Health literacy shift",
        "default": "I’ll use plain language and a few key numbers so it’s easy to act on.",
        "hl_plain": "I’ll keep it simple and practical.",
    },
    "SE": {"label": "Self-efficacy", "default": "We’ll build confidence by starting small and tracking wins."},
    "TR": {"label": "Trust", "default": "We’ll make decisions together and connect actions to clear reasons."},
    "GO": {"label": "Goal orientation", "default": "We’ll set a clear target and measure progress over time."},
    "ID": {"label": "Independence", "default": "We’ll build a plan you can run on your own, with support when needed."},
    "DS": {"label": "Decision style", "default": "We’ll match how you like to decide—options first or one clear recommendation."},
    "RC": {"label": "Readiness for change", "default": "We’ll choose a step that matches your readiness today."},
}


# -----------------------------
# Security Rules (stop rules)
# -----------------------------
SECURITY_RULES: Dict[str, Dict[str, Any]] = {
    "STOP_CHEST_PAIN_EXERCISE": {
        "label": "Chest pain stop rule",
        "message": "If you experience chest pain during exercise, stop immediately and contact your healthcare professional.",
        "severity": "high",
    },
    "CHEST_PAIN_EMERGENCY": {
        "label": "Emergency chest pain",
        "message": "If chest pain is severe, lasts >5 minutes, or comes with shortness of breath, sweating, or fainting, call emergency services.",
        "severity": "high",
    },
    "HTN_CRISIS": {
        "label": "Hypertensive crisis",
        "message": "If BP is around 180/120 or higher, especially with symptoms (chest pain, shortness of breath, weakness, vision changes), seek urgent care.",
        "severity": "high",
    },
    "HF_WEIGHT_GAIN_RED_FLAG": {
        "label": "Heart failure fluid red flag",
        "message": "Report rapid weight gain (e.g., ~2+ pounds overnight or ~5+ in a week) or worsening swelling/shortness of breath.",
        "severity": "high",
    },
    "MEDS_NO_STOP_WITHOUT_CLINICIAN": {
        "label": "Medication safety",
        "message": "Do not stop or change prescribed medications without talking to your clinician.",
        "severity": "medium",
    },
    "CKM_RED_FLAGS": {
        "label": "CKM red flags",
        "message": "Seek care if you have new or worsening shortness of breath, chest pain, fainting, sudden swelling, or rapid weight gain.",
        "severity": "high",
    },
    "HYPOGLYCEMIA_SAFETY": {
        "label": "Low blood sugar safety",
        "message": "If you feel shaky/sweaty/confused, check glucose if possible and treat low blood sugar promptly; seek help if severe.",
        "severity": "high",
    },
    "STROKE_SIGNS_EMERGENCY": {
        "label": "Stroke warning signs",
        "message": "If you notice face droop, arm weakness, speech difficulty, or sudden severe symptoms, call emergency services immediately.",
        "severity": "high",
    },
    "DIZZY_FAINTING_SAFETY": {
        "label": "Dizziness/fainting",
        "message": "If you are dizzy or fainting, sit/lie down and contact your clinician—especially if it happens repeatedly or after medication changes.",
        "severity": "medium",
    },
    "CKD_DIET_CAUTION": {
        "label": "Kidney diet caution",
        "message": "If you have kidney disease, discuss major diet changes (potassium, phosphorus, protein) with your care team.",
        "severity": "medium",
    },
    "CARE_GAPS_AVOID": {
        "label": "Avoid care gaps",
        "message": "If symptoms worsen or you’re unsure about your plan, contact your care team rather than waiting it out.",
        "severity": "medium",
    },
    "RAPID_KIDNEY_DECLINE": {
        "label": "Kidney decline",
        "message": "If labs show a rapid drop in kidney function or you develop severe swelling or shortness of breath, seek prompt evaluation.",
        "severity": "high",
    },
}


# -----------------------------
# Action Plans
# -----------------------------
ACTION_PLANS: Dict[str, Dict[str, Any]] = {
    "CARDIAC_REHAB_REFERRAL": {
        "label": "Cardiac Rehabilitation",
        "message": "Ask about enrolling in a cardiac rehabilitation program for supervised, personalized exercise and education.",
    },
    "CKM_MONITORING": {"label": "CKM monitoring", "message": "Plan regular check-ins for BP, labs (kidney function, A1c), and symptoms."},
    "PREVENT_REVIEW": {"label": "PREVENT", "message": "Review your PREVENT risk score at least yearly or when risk factors change."},
    "MLE8_BASELINE": {"label": "MyLifeCheck baseline", "message": "Get a baseline Life’s Essential 8 / MyLifeCheck score and choose one domain to improve."},
    "MLE8_TREND": {"label": "MyLifeCheck trend", "message": "Track your Life’s Essential 8 score over time to see which habits are improving."},
    "SMBP": {"label": "Home BP monitoring", "message": "Use home BP monitoring with good technique; share readings with your care team."},
    "DASH": {"label": "DASH plan", "message": "Use a DASH-style eating pattern; reduce sodium and prioritize fruits/vegetables/whole grains."},
    "MEDITERRANEAN": {"label": "Mediterranean plan", "message": "Use a Mediterranean-style pattern emphasizing plants, healthy fats, fish, and whole foods."},
    "GOAL_SETTING": {"label": "Goal setting", "message": "Write your health goal where you’ll see it daily and track progress weekly."},
    "FOLLOW_UP_PLAN": {"label": "Follow-up plan", "message": "Set a follow-up schedule and know what symptoms should trigger earlier contact."},
    "WEIGHT_LOG": {"label": "Daily weights", "message": "Weigh yourself daily (if advised) and record results to detect fluid changes."},
    "HOME_BP": {"label": "Home BP", "message": "Measure BP at consistent times and bring your log to visits."},
    "SODIUM_TRACK": {"label": "Sodium awareness", "message": "Track sodium intake for 3 days to identify your biggest sources."},
    "PA_150": {"label": "Activity target", "message": "Aim for gradual progression toward ~150 minutes/week moderate activity if safe for you."},
    "BREATHING_5MIN": {"label": "Breathing practice", "message": "Try 5 minutes of slow breathing daily as a quick stress reset."},
    "SLEEP_ROUTINE": {"label": "Sleep routine", "message": "Create a consistent wind-down routine; sleep supports BP and glucose control."},
    "EMERGENCY_PLAN": {"label": "Emergency plan", "message": "Save urgent numbers and know when to seek emergency care."},
    "SYMPTOM_LOG": {"label": "Symptom log", "message": "Track symptoms with timing, triggers, and severity so your team can adjust care."},
    "MED_TIMING_REVIEW": {"label": "Medication timing", "message": "Log medication timing and symptoms to review possible dose/timing adjustments."},
    "FAMILY_PLAN": {"label": "Family support", "message": "Share one simple goal with a family member and invite them to support you."},
    "REMOTE_MONITORING": {"label": "Remote monitoring", "message": "Ask about telehealth/remote monitoring programs to catch changes early."},
    "CARE_APP": {"label": "Care app", "message": "Ask if your clinic offers an app for reminders, messaging, and tracking."},
    "COORDINATED_CARE": {"label": "Coordinated care", "message": "Ask for coordinated heart-kidney-metabolic care if multiple conditions are present."},
    "MED_REVIEW": {"label": "Medication review", "message": "Ask your clinician to review medication benefits, side effects, and alternatives."},
    "MED_RECONCILIATION": {"label": "Medication reconciliation", "message": "Bring all meds/supplements so your team can reduce duplication and interactions."},
    "BRING_CUFF_VISIT": {"label": "Cuff accuracy", "message": "Bring your home BP cuff to your visit to verify accuracy and technique."},
    "TECHNIQUE_CHECK": {"label": "Technique", "message": "Use proper BP technique: seated, rested, arm supported at heart level, no caffeine right before."},
    "CALL_TEAM_PLAN": {"label": "Call plan", "message": "Make a ‘when to call’ plan with your care team for symptoms and rapid changes."},
    "SECONDARY_PREVENTION_CHECKLIST": {"label": "Secondary prevention", "message": "Build a checklist for BP, cholesterol, diabetes, activity, and medication adherence."},
    "CHADS_VASC_CALC": {"label": "CHA2DS2-VASc", "message": "Ask your clinician about your CHA₂DS₂-VASc score to guide stroke prevention decisions."},
    "FAST_CARBS_PLAN": {"label": "Fast carbs plan", "message": "Carry fast-acting carbs when active if you’re at risk for low blood sugar."},
}


# -----------------------------
# Content links (AHA-first)
# -----------------------------
CONTENT_LINKS: Dict[str, Dict[str, str]] = {
    "AHA_BP": {"title": "High Blood Pressure", "url": "https://www.heart.org/en/health-topics/high-blood-pressure"},
    "AHA_MYLE8": {"title": "My Life Check (Life’s Essential 8)", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check"},
    "AHA_FITNESS": {"title": "Fitness", "url": "https://www.heart.org/en/healthy-living/fitness"},
    "AHA_CKM": {"title": "CKM Health", "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health"},
}
