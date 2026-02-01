# questions.py
"""
questions.py

Stores the Question Bank + helper functions:
- Auto-generates IDs per category (HTN-01, CAD-02, etc.) deterministically
- Lists categories
- Lists question summaries
- Search mode
- Validation: catches missing persona responses, missing fields, etc.

Add new question sets by appending to RAW_QUESTION_SETS in this file,
OR generate from text using converter script: convert_questions_from_text.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import re


PERSONAS = ["Listener", "Motivator", "Director", "Expert"]


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    question: str
    responses: Dict[str, str]
    action_step: str
    why: str
    signatures_tags: Dict[str, List[str]]
    security_rule_codes: List[str]
    action_plan_codes: List[str]
    sources: List[Dict[str, str]]


# -----------------------------
# Raw question sets (starter)
# -----------------------------
# NOTE:
# To keep this repo manageable, this file includes:
# - A complete HTN top 10 (from your pasted set)
# - A complete CKM top 10 (from your pasted set)
# - A few example items for CAD/HF/AFIB/STROKE/DM
#
# Use the converter script to generate full sets for the others from a text file.
#
# Each item in RAW_QUESTION_SETS is:
#   (category, [ {question fields...}, ... ])
#
# IDs are auto-generated later.

RAW_QUESTION_SETS: List[Tuple[str, List[Dict[str, Any]]]] = []

# ---- CKM (Top 10) ----
CKM_ITEMS: List[Dict[str, Any]] = [
    {
        "question": "What does my diagnosis mean for my future?",
        "responses": {
            "Listener": "That sounds overwhelming. What are you most worried about?",
            "Motivator": "You can live a full life with support.",
            "Director": "Let’s monitor labs and scores every 3 months.",
            "Expert": "Early action guided by PREVENT and Life’s Essential 8 makes a difference.",
        },
        "action_step": "Write down your top 3 concerns.",
        "why": "Sharing helps your care team focus on what matters to you.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["TR", "RC"],
        },
        "security_rule_codes": ["CKM_WORSENING_SYMPTOMS"],
        "action_plan_codes": ["CKM_MONITORING", "PREVENT_REVIEW", "MLE8_BASELINE"],
        "sources": [
            {
                "org": "AHA",
                "title": "Cardiovascular-Kidney-Metabolic (CKM) Health",
                "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health",
            }
        ],
    },
    {
        "question": "What can I eat—and what should I avoid?",
        "responses": {
            "Listener": "What foods do you enjoy? Let’s start there.",
            "Motivator": "Healthy food can taste great.",
            "Director": "Follow DASH or Mediterranean-style eating.",
            "Expert": "These diets reduce stroke and heart risk by 20–30%.",
        },
        "action_step": "Track meals for 3 days.",
        "why": "Helps identify strengths and needed changes.",
        "signatures_tags": {
            "behavioral_core": ["NUT"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["HL"],
        },
        "security_rule_codes": ["CKD_DIET_CAUTION"],
        "action_plan_codes": ["DASH", "MEDITERRANEAN"],
        "sources": [
            {
                "org": "AHA",
                "title": "Healthy Eating",
                "url": "https://www.heart.org/en/healthy-living/healthy-eating",
            }
        ],
    },
    {
        "question": "Why am I on so many medications?",
        "responses": {
            "Listener": "Do any cause side effects or confusion?",
            "Motivator": "Each one helps protect your organs.",
            "Director": "Your meds follow evidence-based guidelines.",
            "Expert": "Proper medication use reduces ER visits and complications.",
        },
        "action_step": "Bring all meds to your next visit.",
        "why": "Helps avoid duplication and interactions.",
        "signatures_tags": {
            "behavioral_core": ["MA"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["TR", "DS"],
        },
        "security_rule_codes": ["MEDS_NO_STOP_WITHOUT_CLINICIAN"],
        "action_plan_codes": ["MED_RECONCILIATION"],
        "sources": [
            {
                "org": "AHA",
                "title": "Medication Adherence",
                "url": "https://www.heart.org/en/health-topics/consumer-healthcare/medication-adherence",
            }
        ],
    },
    {
        "question": "How do I know if my condition is getting better or worse?",
        "responses": {
            "Listener": "Notice any changes in how you feel?",
            "Motivator": "Monitoring gives you control.",
            "Director": "We’ll review your data and labs regularly.",
            "Expert": "Scores like Life’s Essential 8 track real progress.",
        },
        "action_step": "Keep a weekly symptom log.",
        "why": "Tracking helps spot changes early.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["GO", "PR"],
        },
        "security_rule_codes": ["CKM_RED_FLAGS"],
        "action_plan_codes": ["HOME_BP", "WEIGHT_LOG", "PREVENT_REVIEW", "MLE8_TREND"],
        "sources": [
            {
                "org": "AHA",
                "title": "My Life Check (Life’s Essential 8)",
                "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check",
            }
        ],
    },
    {
        "question": "Will I need dialysis or heart surgery?",
        "responses": {
            "Listener": "That’s a scary thought. What worries you most?",
            "Motivator": "You can take steps to lower that risk.",
            "Director": "We’ll monitor kidney and heart function closely.",
            "Expert": "Managing BP and A1c cuts surgery/dialysis risk in half.",
        },
        "action_step": "Write down questions to ask your doctor.",
        "why": "Reduces fear and supports planning.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["CKM", "CKD"],
            "engagement_drivers": ["TR"],
        },
        "security_rule_codes": ["CHEST_PAIN_EMERGENCY", "RAPID_KIDNEY_DECLINE"],
        "action_plan_codes": ["SPECIALIST_REFERRAL", "GOAL_BP_A1C"],
        "sources": [
            {
                "org": "AHA",
                "title": "Preventing Heart Failure",
                "url": "https://www.heart.org/en/health-topics/heart-failure/preventing-heart-failure",
            }
        ],
    },
    {
        "question": "Can I still exercise?",
        "responses": {
            "Listener": "What kind of movement do you enjoy?",
            "Motivator": "Movement is medicine!",
            "Director": "Aim for 150 minutes/week.",
            "Expert": "Exercise improves BP, cholesterol, and kidney function.",
        },
        "action_step": "Try a 10-minute walk after a meal.",
        "why": "Even light activity helps control glucose.",
        "signatures_tags": {
            "behavioral_core": ["PA"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["SE", "PR"],
        },
        "security_rule_codes": ["STOP_CHEST_PAIN_EXERCISE"],
        "action_plan_codes": ["CARDIAC_REHAB_REFERRAL"],
        "sources": [
            {
                "org": "AHA",
                "title": "Fitness and Physical Activity",
                "url": "https://www.heart.org/en/healthy-living/fitness",
            }
        ],
    },
    {
        "question": "What’s a healthy blood pressure for me?",
        "responses": {
            "Listener": "Do you remember your last reading?",
            "Motivator": "Lower BP = better brain, heart, kidney health.",
            "Director": "Target is usually <130/80.",
            "Expert": "Control lowers stroke and kidney failure risk.",
        },
        "action_step": "Take a photo of your BP log.",
        "why": "Visuals help share your progress.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["HTN", "CKM"],
            "engagement_drivers": ["HL"],
        },
        "security_rule_codes": ["HTN_CRISIS"],
        "action_plan_codes": ["SMBP", "BRING_CUFF_VISIT"],
        "sources": [
            {
                "org": "AHA",
                "title": "Understanding Blood Pressure Readings",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
            }
        ],
    },
    {
        "question": "How can I manage this and still live my life?",
        "responses": {
            "Listener": "What’s been hardest lately?",
            "Motivator": "You’re not alone—and you’re stronger than you think.",
            "Director": "Let’s build your plan into your daily routine.",
            "Expert": "Digital tools can help you stay organized and connected.",
        },
        "action_step": "Write down your top 3 challenges.",
        "why": "Knowing barriers helps us support you.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["SE", "ID"],
        },
        "security_rule_codes": ["CARE_GAPS_AVOID"],
        "action_plan_codes": ["REMOTE_MONITORING", "CARE_APP"],
        "sources": [
            {
                "org": "AHA",
                "title": "Healthy Living",
                "url": "https://www.heart.org/en/healthy-living",
            }
        ],
    },
    {
        "question": "Are my heart, kidneys, and diabetes connected?",
        "responses": {
            "Listener": "Have you heard of CKM syndrome?",
            "Motivator": "One healthy habit helps all 3!",
            "Director": "We manage this as a connected syndrome now.",
            "Expert": "The AHA now treats CKM as a unified health issue.",
        },
        "action_step": "Ask your provider to explain how these are linked.",
        "why": "Understanding helps you act sooner.",
        "signatures_tags": {
            "behavioral_core": ["HL"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["HL"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["COORDINATED_CARE", "PREVENT_REVIEW"],
        "sources": [
            {
                "org": "AHA",
                "title": "Cardiovascular-Kidney-Metabolic (CKM) Health",
                "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health",
            }
        ],
    },
    {
        "question": "How do I avoid going back to the hospital?",
        "responses": {
            "Listener": "What happened the last time you were hospitalized?",
            "Motivator": "Every healthy choice counts.",
            "Director": "We’ll act early—before a crisis.",
            "Expert": "Remote support programs reduce readmissions by 30%.",
        },
        "action_step": "Keep a journal of early symptoms.",
        "why": "Spotting patterns helps avoid emergencies.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["CKM"],
            "engagement_drivers": ["PR", "GO"],
        },
        "security_rule_codes": ["CKM_RED_FLAGS"],
        "action_plan_codes": ["REMOTE_MONITORING", "FOLLOW_UP_PLAN"],
        "sources": [
            {
                "org": "AHA",
                "title": "Preventive Care",
                "url": "https://www.heart.org/en/health-topics/consumer-healthcare/preventive-care",
            }
        ],
    },
]

RAW_QUESTION_SETS.append(("CKM", CKM_ITEMS))


# ---- HTN (Top 10) ----
HTN_ITEMS: List[Dict[str, Any]] = [
    {
        "question": "What should my blood pressure goal be?",
        "responses": {
            "Listener": "It’s normal to feel unsure—many people don’t know their number.",
            "Motivator": "Knowing your goal puts you in control!",
            "Director": "For most people, the AHA recommends a goal below 130/80.",
            "Expert": "AHA guidance emphasizes: lower BP reduces risk of heart attack, stroke, and kidney disease.",
        },
        "action_step": "Ask your doctor, “What’s my target BP?”",
        "why": "Clear targets help you stay on track.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["HL", "GO"],
        },
        "security_rule_codes": ["HTN_CRISIS"],
        "action_plan_codes": ["SMBP", "GOAL_SETTING"],
        "sources": [
            {
                "org": "AHA",
                "title": "Understanding Blood Pressure Readings",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
            }
        ],
    },
    {
        "question": "Do I really need medication?",
        "responses": {
            "Listener": "It’s okay to feel unsure. Many people ask this.",
            "Motivator": "Taking medication is one way to protect your heart—like walking or eating well.",
            "Director": "Medications are usually started if lifestyle changes alone don’t lower BP.",
            "Expert": "For many, combining medication + healthy habits is most effective and safest.",
        },
        "action_step": "Talk to your doctor about how meds fit your overall plan.",
        "why": "Personalized plans reduce confusion.",
        "signatures_tags": {
            "behavioral_core": ["MA"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["TR", "DS"],
        },
        "security_rule_codes": ["MEDS_NO_STOP_WITHOUT_CLINICIAN"],
        "action_plan_codes": ["MED_REVIEW"],
        "sources": [
            {
                "org": "AHA",
                "title": "High Blood Pressure Treatment",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/high-blood-pressure-tools-and-resources",
            }
        ],
    },
    {
        "question": "What can I do besides taking medication?",
        "responses": {
            "Listener": "It’s great that you want to take action!",
            "Motivator": "Your body responds quickly to healthy habits.",
            "Director": "Try DASH, reduce sodium, increase activity, lose weight if needed.",
            "Expert": "Lifestyle changes can meaningfully reduce BP; tools like Life’s Essential 8 help track progress.",
        },
        "action_step": "Choose one area: food, movement, sleep, or stress.",
        "why": "Starting small makes change more manageable.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["SE", "GO"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["DASH", "SODIUM_TRACK", "PA_150"],
        "sources": [
            {
                "org": "AHA",
                "title": "Life’s Essential 8 / My Life Check",
                "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check",
            }
        ],
    },
    {
        "question": "What kind of diet should I follow?",
        "responses": {
            "Listener": "Choosing what to eat can feel confusing. You’re not alone.",
            "Motivator": "Small food swaps can lead to big results.",
            "Director": "The DASH diet is rich in fruits, vegetables, whole grains, and low-fat dairy.",
            "Expert": "Clinical trials show DASH lowers BP and supports heart health.",
        },
        "action_step": "Keep a simple food journal for 3 days.",
        "why": "Reflection builds insight.",
        "signatures_tags": {
            "behavioral_core": ["NUT"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["HL"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["DASH"],
        "sources": [
            {
                "org": "AHA",
                "title": "DASH Eating Plan",
                "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/dash-diet",
            }
        ],
    },
    {
        "question": "Will I have high blood pressure forever?",
        "responses": {
            "Listener": "That’s a common fear—but there’s hope.",
            "Motivator": "You can improve your numbers—many people do!",
            "Director": "High BP may not go away completely, but it can often be controlled.",
            "Expert": "Long-term control comes from sustained habits and, when needed, medication.",
        },
        "action_step": "Ask your doctor if your condition is reversible.",
        "why": "Opens the door for shared planning.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["SE", "TR"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["FOLLOW_UP_3_MONTHS", "MLE8_TREND"],
        "sources": [
            {
                "org": "AHA",
                "title": "High Blood Pressure",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            }
        ],
    },
    {
        "question": "How can I track my blood pressure at home?",
        "responses": {
            "Listener": "It can be overwhelming at first, but you’re not alone.",
            "Motivator": "Tracking gives you control over your progress.",
            "Director": "Take readings in the morning and evening, seated and rested.",
            "Expert": "Proper technique matters: arm level with heart, no caffeine 30 minutes before.",
        },
        "action_step": "Write down your readings in a simple journal or notebook.",
        "why": "It helps you notice patterns over time.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["SE", "GO"],
        },
        "security_rule_codes": ["HTN_CRISIS"],
        "action_plan_codes": ["SMBP", "TECHNIQUE_CHECK"],
        "sources": [
            {
                "org": "AHA",
                "title": "Home Blood Pressure Monitoring",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings/monitoring-your-blood-pressure-at-home",
            }
        ],
    },
    {
        "question": "Can stress really affect my blood pressure?",
        "responses": {
            "Listener": "Yes, and life can be stressful—we get it.",
            "Motivator": "Taking care of your mind supports your heart.",
            "Director": "Chronic stress can drive behaviors that raise BP—poor sleep, diet, inactivity.",
            "Expert": "Stress-reduction strategies can support BP control as part of a whole plan.",
        },
        "action_step": "Identify one stressor you can reduce this week.",
        "why": "Small wins reduce overall tension.",
        "signatures_tags": {
            "behavioral_core": ["ST"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["SE"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["BREATHING_5MIN", "SLEEP_ROUTINE"],
        "sources": [
            {
                "org": "AHA",
                "title": "Stress Management",
                "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management",
            }
        ],
    },
    {
        "question": "What’s a dangerous blood pressure level?",
        "responses": {
            "Listener": "It’s scary not knowing what’s too high.",
            "Motivator": "Knowing your numbers gives you power—not fear.",
            "Director": "180/120 or higher is a hypertensive crisis—especially with symptoms.",
            "Expert": "Stage 2 hypertension starts at 140/90; crisis thresholds require urgent action.",
        },
        "action_step": "Learn your BP zones with a color-coded chart.",
        "why": "Helps you recognize when to seek help.",
        "signatures_tags": {
            "behavioral_core": ["HL"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["HL"],
        },
        "security_rule_codes": ["HTN_CRISIS"],
        "action_plan_codes": ["EMERGENCY_PLAN"],
        "sources": [
            {
                "org": "AHA",
                "title": "Hypertensive Crisis",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings/hypertensive-crisis-when-you-should-call-911-for-high-blood-pressure",
            }
        ],
    },
    {
        "question": "Is low blood pressure a problem too?",
        "responses": {
            "Listener": "Yes—it can make you feel dizzy, tired, or weak.",
            "Motivator": "It’s okay to ask questions if something doesn’t feel right.",
            "Director": "If BP is too low, especially on meds, we may need to adjust your dose.",
            "Expert": "BP under 90/60 can be concerning if it causes symptoms; hydration and meds timing matter.",
        },
        "action_step": "Note symptoms when you take readings.",
        "why": "Helps your care team adjust treatment safely.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["TR"],
        },
        "security_rule_codes": ["DIZZY_FAINTING_SAFETY"],
        "action_plan_codes": ["SYMPTOM_LOG", "MED_TIMING_REVIEW"],
        "sources": [
            {
                "org": "AHA",
                "title": "Understanding Blood Pressure Readings",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
            }
        ],
    },
    {
        "question": "How do I talk to my family about my high blood pressure?",
        "responses": {
            "Listener": "Talking about your health takes courage.",
            "Motivator": "You might inspire them to check their BP too!",
            "Director": "Use simple language: ‘I’m working on my BP so I can stay healthy.’",
            "Expert": "Family history matters; encouraging screening supports prevention.",
        },
        "action_step": "Start with one trusted family member.",
        "why": "Support makes healthy changes easier.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["HTN"],
            "engagement_drivers": ["TR", "ID"],
        },
        "security_rule_codes": [],
        "action_plan_codes": ["FAMILY_PLAN"],
        "sources": [
            {
                "org": "AHA",
                "title": "High Blood Pressure",
                "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
            }
        ],
    },
]

RAW_QUESTION_SETS.append(("HTN", HTN_ITEMS))


# ---- Examples for other categories (use converter to expand) ----
RAW_QUESTION_SETS.append(("CAD", [
    {
        "question": "Can I exercise safely with CAD?",
        "responses": {
            "Listener": "It’s good you’re asking. Many people worry about overdoing it.",
            "Motivator": "Movement is medicine—even 10 minutes counts.",
            "Director": "Most CAD patients benefit from moderate activity like walking, unless symptoms worsen.",
            "Expert": "Exercise improves vessel health and reduces future cardiac risk; cardiac rehab can guide you safely.",
        },
        "action_step": "Ask your provider about cardiac rehab or a home walking plan.",
        "why": "Support builds confidence and safety.",
        "signatures_tags": {
            "behavioral_core": ["PA"],
            "condition_modifiers": ["CAD"],
            "engagement_drivers": ["SE"],
        },
        "security_rule_codes": ["STOP_CHEST_PAIN_EXERCISE"],
        "action_plan_codes": ["CARDIAC_REHAB_REFERRAL"],
        "sources": [{"org": "AHA", "title": "Coronary Artery Disease", "url": "https://www.heart.org/en/health-topics/heart-attack"}],
    }
]))

RAW_QUESTION_SETS.append(("HF", [
    {
        "question": "How do I know if my heart failure is getting worse?",
        "responses": {
            "Listener": "It’s okay to check in with how your body feels.",
            "Motivator": "You’re learning your body’s signals—that’s powerful.",
            "Director": "Watch for weight gain, shortness of breath, swelling, or fatigue.",
            "Expert": "Daily weights and symptom tracking help catch fluid overload early.",
        },
        "action_step": "Weigh yourself each morning and write it down.",
        "why": "Sudden weight gain may signal fluid buildup.",
        "signatures_tags": {
            "behavioral_core": ["SY"],
            "condition_modifiers": ["HF"],
            "engagement_drivers": ["GO"],
        },
        "security_rule_codes": ["HF_WEIGHT_GAIN_RED_FLAG"],
        "action_plan_codes": ["WEIGHT_LOG", "CALL_TEAM_PLAN"],
        "sources": [{"org": "AHA", "title": "Heart Failure", "url": "https://www.heart.org/en/health-topics/heart-failure"}],
    }
]))

RAW_QUESTION_SETS.append(("AFIB", [
    {
        "question": "Do I need a blood thinner?",
        "responses": {
            "Listener": "It’s common to be nervous about bleeding risk.",
            "Motivator": "Blood thinners help prevent strokes—they protect you.",
            "Director": "Many AFib patients need anticoagulation depending on stroke risk.",
            "Expert": "Stroke-risk tools like CHA₂DS₂-VASc help guide anticoagulation decisions.",
        },
        "action_step": "Ask your doctor to explain your stroke risk score.",
        "why": "Knowing your risk helps you choose the safest prevention plan.",
        "signatures_tags": {
            "behavioral_core": ["HL"],
            "condition_modifiers": ["AFIB"],
            "engagement_drivers": ["TR"],
        },
        "security_rule_codes": ["MEDS_NO_STOP_WITHOUT_CLINICIAN"],
        "action_plan_codes": ["CHADS_VASC_CALC"],
        "sources": [{"org": "AHA", "title": "Atrial Fibrillation (AFib)", "url": "https://www.heart.org/en/health-topics/atrial-fibrillation"}],
    }
]))

RAW_QUESTION_SETS.append(("STROKE", [
    {
        "question": "Am I at risk of having another stroke?",
        "responses": {
            "Listener": "It’s natural to worry—it means you care about your future.",
            "Motivator": "You’ve already taken the first step—asking the question.",
            "Director": "Yes, but your risk can be lowered with the right care.",
            "Expert": "Secondary prevention focuses on BP, cholesterol, diabetes, and AFib management when present.",
        },
        "action_step": "Schedule regular follow-ups to monitor risk factors.",
        "why": "Tracking and adjusting early lowers recurrence risk.",
        "signatures_tags": {
            "behavioral_core": ["PC"],
            "condition_modifiers": ["STROKE"],
            "engagement_drivers": ["GO"],
        },
        "security_rule_codes": ["STROKE_SIGNS_EMERGENCY"],
        "action_plan_codes": ["SECONDARY_PREVENTION_CHECKLIST"],
        "sources": [{"org": "AHA", "title": "Stroke", "url": "https://www.heart.org/en/health-topics/stroke"}],
    }
]))

RAW_QUESTION_SETS.append(("DM", [
    {
        "question": "Can I still exercise safely with diabetes?",
        "responses": {
            "Listener": "Exercise can be intimidating at first, especially if you’ve had a scare.",
            "Motivator": "Moving your body is one of the best things you can do.",
            "Director": "Monitor blood sugar before/after workouts if on insulin; carry fast carbs.",
            "Expert": "Regular activity improves insulin sensitivity and supports BP, weight, and lipid control.",
        },
        "action_step": "Start with short walks after meals.",
        "why": "This can gently lower blood sugar and build confidence.",
        "signatures_tags": {
            "behavioral_core": ["PA"],
            "condition_modifiers": ["DM"],
            "engagement_drivers": ["SE"],
        },
        "security_rule_codes": ["HYPOGLYCEMIA_SAFETY"],
        "action_plan_codes": ["PA_150", "FAST_CARBS_PLAN"],
        "sources": [{"org": "AHA", "title": "Diabetes and Heart Health", "url": "https://www.heart.org/en/health-topics/diabetes"}],
    }
]))


# -----------------------------
# Build bank + ID generation
# -----------------------------

def _slug_category(cat: str) -> str:
    cat = cat.strip().upper()
    cat = re.sub(r"[^A-Z0-9]+", "", cat)
    return cat or "GEN"


def _build_bank() -> List[Question]:
    bank: List[Question] = []
    for (category, items) in RAW_QUESTION_SETS:
        cat = _slug_category(category)
        for item in items:
            bank.append(_to_question(cat, item))
    return _assign_ids(bank)


def _to_question(category: str, item: Dict[str, Any]) -> Question:
    # Defaults to keep validation resilient
    responses = item.get("responses") or {}
    action_step = item.get("action_step") or "Choose one small next step you can do today."
    why = item.get("why") or "Small steps build momentum and confidence."
    tags = item.get("signatures_tags") or {"behavioral_core": ["GEN"], "condition_modifiers": [], "engagement_drivers": []}

    return Question(
        id=item.get("id") or "",  # assigned later
        category=category,
        question=str(item.get("question", "")).strip(),
        responses={k: str(v).strip() for k, v in responses.items()},
        action_step=str(action_step).strip(),
        why=str(why).strip(),
        signatures_tags={
            "behavioral_core": list(tags.get("behavioral_core", [])),
            "condition_modifiers": list(tags.get("condition_modifiers", [])),
            "engagement_drivers": list(tags.get("engagement_drivers", [])),
        },
        security_rule_codes=list(item.get("security_rule_codes") or []),
        action_plan_codes=list(item.get("action_plan_codes") or []),
        sources=list(item.get("sources") or []),
    )


def _assign_ids(bank: List[Question]) -> List[Question]:
    # Stable: sort by category then question text; then assign sequential within category
    sorted_bank = sorted(bank, key=lambda q: (q.category, q.question.lower()))
    counters: Dict[str, int] = {}
    out: List[Question] = []
    for q in sorted_bank:
        n = counters.get(q.category, 0) + 1
        counters[q.category] = n
        new_id = f"{q.category}-{n:02d}"
        out.append(Question(**{**q.__dict__, "id": new_id}))  # type: ignore
    return out


QUESTION_BANK: List[Question] = _build_bank()


# -----------------------------
# Public helper functions
# -----------------------------

def all_categories() -> List[str]:
    cats = sorted({q.category for q in QUESTION_BANK})
    return cats


def list_question_summaries(category: Optional[str] = None, limit: int = 200) -> List[Question]:
    items = QUESTION_BANK
    if category:
        cat = _slug_category(category)
        items = [q for q in items if q.category == cat]
    return items[:limit]


def get_question_by_id(qid: str) -> Optional[Question]:
    qid = qid.strip().upper()
    for q in QUESTION_BANK:
        if q.id == qid:
            return q
    return None


def search_questions(query: str, category: Optional[str] = None, limit: int = 50) -> List[Question]:
    q = query.strip().lower()
    items = QUESTION_BANK
    if category:
        cat = _slug_category(category)
        items = [x for x in items if x.category == cat]
    if not q:
        return items[:limit]
    hits = []
    for item in items:
        blob = " ".join([item.question] + list(item.responses.values())).lower()
        if q in blob:
            hits.append(item)
    return hits[:limit]


def validate_question_bank(raise_on_error: bool = False) -> List[str]:
    issues: List[str] = []
    if not QUESTION_BANK:
        issues.append("Question bank is empty.")

    for q in QUESTION_BANK:
        if not q.id:
            issues.append(f"{q.category}: missing id (should be auto-assigned)")
        if not q.question:
            issues.append(f"{q.id}: missing question text")

        # Responses: allow empty for CUSTOM, but for preloaded require at least one persona response
        if q.category != "CUSTOM":
            if not q.responses:
                issues.append(f"{q.id}: missing responses")
            else:
                # If responses exist, ensure keys are valid personas and values non-empty
                for persona in list(q.responses.keys()):
                    if persona not in PERSONAS:
                        issues.append(f"{q.id}: invalid persona key '{persona}'")
                for persona in PERSONAS:
                    if persona in q.responses and not q.responses[persona].strip():
                        issues.append(f"{q.id}: blank response for {persona}")

        # tags sanity
        tags = q.signatures_tags or {}
        for key in ("behavioral_core", "condition_modifiers", "engagement_drivers"):
            if key not in tags:
                issues.append(f"{q.id}: missing signatures_tags.{key}")

    if raise_on_error and issues:
        raise ValueError("Question bank validation failed:\n" + "\n".join(issues))
    return issues



