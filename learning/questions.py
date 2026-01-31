"""
questions.py

This module contains the preloaded QUESTION_BANK for Signatures.

Includes:
- Step A: AHA_LINKS expanded (category landing pages + core tools like My Life Check)
- Step B: Bulk question dictionaries + registration into QUESTION_BANK

How to use from signatures_engine.py:
- from questions import list_questions, get_question, QUESTION_BANK
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Any


# -----------------------------
# Types / Data models
# -----------------------------

Persona = Literal["Listener", "Motivator", "Director", "Expert"]


@dataclass(frozen=True)
class PersonaAnswer:
    text: str
    action_step: str
    why_it_matters: str


@dataclass(frozen=True)
class PreloadedQuestion:
    qid: str
    category: str
    question: str
    behavioral_core: str
    default_conditions: List[str]
    default_drivers: Dict[str, int]
    answers: Dict[Persona, PersonaAnswer]
    links: List[Dict[str, str]]  # {org,title,url}


# -----------------------------
# AHA Links (Step A)
# -----------------------------

AHA_LINKS: Dict[str, Dict[str, str]] = {
    # Core “hooks” / tools
    "MYLIFECHECK": {
        "org": "American Heart Association",
        "title": "My Life Check (Life’s Essential 8)",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check",
    },
    "BP": {
        "org": "American Heart Association",
        "title": "Understanding Blood Pressure Readings",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
    },
    "DASH": {
        "org": "American Heart Association",
        "title": "DASH Diet",
        "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/dash-diet",
    },
    "CKM": {
        "org": "American Heart Association",
        "title": "Cardio-Kidney-Metabolic Health (Professional Resource)",
        "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health",
    },

    # Condition landing pages
    "HF": {
        "org": "American Heart Association",
        "title": "Heart Failure",
        "url": "https://www.heart.org/en/health-topics/heart-failure",
    },
    "CAD": {
        "org": "American Heart Association",
        "title": "Heart Attack / Coronary Artery Disease",
        "url": "https://www.heart.org/en/health-topics/heart-attack",
    },
    "AFIB": {
        "org": "American Heart Association",
        "title": "Atrial Fibrillation (AFib)",
        "url": "https://www.heart.org/en/health-topics/atrial-fibrillation",
    },
    "STROKE": {
        "org": "American Heart Association",
        "title": "Stroke",
        "url": "https://www.heart.org/en/health-topics/stroke",
    },
    "DIABETES": {
        "org": "American Heart Association",
        "title": "Diabetes",
        "url": "https://www.heart.org/en/health-topics/diabetes",
    },
    "MED_ADH": {
        "org": "American Heart Association",
        "title": "Medication Adherence",
        "url": "https://www.heart.org/en/health-topics/consumer-healthcare/medication-adherence",
    },
}


# -----------------------------
# In-memory Question Bank
# -----------------------------

QUESTION_BANK: Dict[str, PreloadedQuestion] = {}


def add_question(q: PreloadedQuestion) -> None:
    """Register a question in QUESTION_BANK."""
    if q.qid in QUESTION_BANK:
        raise ValueError(f"Duplicate qid: {q.qid}")
    QUESTION_BANK[q.qid] = q


def list_questions(category: Optional[str] = None) -> List[PreloadedQuestion]:
    """Return questions, optionally filtered by category."""
    items = list(QUESTION_BANK.values())
    if category:
        items = [q for q in items if q.category.lower() == category.lower()]
    return sorted(items, key=lambda x: x.qid)


def get_question(qid: str) -> Optional[PreloadedQuestion]:
    """Fetch a question by ID."""
    return QUESTION_BANK.get(qid)


def _build_answers(answers_dict: Dict[str, Dict[str, str]]) -> Dict[Persona, PersonaAnswer]:
    # Convert raw dict -> PersonaAnswer objects (and enforce 4 persona keys if present)
    out: Dict[Persona, PersonaAnswer] = {}
    for persona_key, payload in answers_dict.items():
        persona = persona_key  # type: ignore[assignment]
        out[persona] = PersonaAnswer(
            text=payload["text"],
            action_step=payload["action_step"],
            why_it_matters=payload["why_it_matters"],
        )
    return out


def _link_keys_to_links(keys: List[str]) -> List[Dict[str, str]]:
    return [AHA_LINKS[k] for k in keys if k in AHA_LINKS]


def _register_bulk(question_dicts: List[Dict[str, Any]]) -> None:
    for item in question_dicts:
        add_question(
            PreloadedQuestion(
                qid=item["qid"],
                category=item["category"],
                question=item["question"],
                behavioral_core=item["behavioral_core"],
                default_conditions=item.get("default_conditions", []),
                default_drivers=item.get("default_drivers", {}),
                answers=_build_answers(item["answers"]),
                links=_link_keys_to_links(item.get("links", [])),
            )
        )


# -----------------------------
# Step B: Bulk Question Data
# -----------------------------

# ========== CKM (Top 10) ==========
CKM_QUESTIONS: List[Dict[str, Any]] = [
    {
        "qid": "CKM-01",
        "category": "CKM",
        "question": "What does my diagnosis mean for my future?",
        "behavioral_core": "PC",
        "default_conditions": ["CKM"],
        "links": ["CKM", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "That sounds overwhelming. What are you most worried about?",
                "action_step": "Write down your top 3 concerns.",
                "why_it_matters": "Sharing helps your care team focus on what matters to you.",
            },
            "Motivator": {
                "text": "You can live a full life with support.",
                "action_step": "Set one small health goal, like a daily walk.",
                "why_it_matters": "Goals help build confidence and momentum.",
            },
            "Director": {
                "text": "Let’s monitor labs and scores every 3 months.",
                "action_step": "Schedule your next lab appointment.",
                "why_it_matters": "Staying on track helps catch changes early.",
            },
            "Expert": {
                "text": "Early action guided by PREVENT and Life’s Essential 8 makes a difference.",
                "action_step": "Ask for your PREVENT score.",
                "why_it_matters": "Personalized scores help guide care decisions.",
            },
        },
    },
    {
        "qid": "CKM-02",
        "category": "CKM",
        "question": "What can I eat—and what should I avoid?",
        "behavioral_core": "NUT",
        "default_conditions": ["CKM"],
        "links": ["DASH", "CKM"],
        "answers": {
            "Listener": {
                "text": "What foods do you enjoy? Let’s start there.",
                "action_step": "Track meals for 3 days.",
                "why_it_matters": "Helps identify strengths and needed changes.",
            },
            "Motivator": {
                "text": "Healthy food can taste great.",
                "action_step": "Try one new heart-healthy recipe.",
                "why_it_matters": "Enjoyment builds lasting habits.",
            },
            "Director": {
                "text": "Follow DASH or Mediterranean-style eating.",
                "action_step": "Replace one salty snack with fruit or veggies.",
                "why_it_matters": "Small swaps lower blood pressure.",
            },
            "Expert": {
                "text": "These diets reduce stroke and heart risk by 20–30%.",
                "action_step": "Use a food-tracking app.",
                "why_it_matters": "Tools support consistency.",
            },
        },
    },
    {
        "qid": "CKM-03",
        "category": "CKM",
        "question": "Why am I on so many medications?",
        "behavioral_core": "MA",
        "default_conditions": ["CKM"],
        "links": ["MED_ADH", "CKM"],
        "answers": {
            "Listener": {
                "text": "Do any cause side effects or confusion?",
                "action_step": "Bring all meds to your next visit.",
                "why_it_matters": "Helps avoid duplication and interactions.",
            },
            "Motivator": {
                "text": "Each one helps protect your organs.",
                "action_step": "Use a pillbox or phone reminders.",
                "why_it_matters": "Improves medication adherence.",
            },
            "Director": {
                "text": "Your meds follow evidence-based guidelines.",
                "action_step": "Ask what each one does.",
                "why_it_matters": "Understanding builds trust.",
            },
            "Expert": {
                "text": "Proper medication use reduces ER visits and complications.",
                "action_step": "Report missed doses or side effects.",
                "why_it_matters": "Your doctor can adjust your regimen.",
            },
        },
    },
    {
        "qid": "CKM-04",
        "category": "CKM",
        "question": "How do I know if my condition is getting better or worse?",
        "behavioral_core": "SY",
        "default_conditions": ["CKM"],
        "links": ["MYLIFECHECK", "CKM"],
        "answers": {
            "Listener": {
                "text": "Notice any changes in how you feel?",
                "action_step": "Keep a weekly symptom log.",
                "why_it_matters": "Tracking helps spot changes early.",
            },
            "Motivator": {
                "text": "Monitoring gives you control.",
                "action_step": "Check BP twice weekly.",
                "why_it_matters": "Prevents silent worsening.",
            },
            "Director": {
                "text": "We’ll review your data and labs regularly.",
                "action_step": "Ask your provider to explain recent results.",
                "why_it_matters": "Helps guide next steps.",
            },
            "Expert": {
                "text": "Scores like Life’s Essential 8 track real progress.",
                "action_step": "Ask how your score is trending.",
                "why_it_matters": "It reflects your health across multiple systems.",
            },
        },
    },
    {
        "qid": "CKM-05",
        "category": "CKM",
        "question": "Will I need dialysis or heart surgery?",
        "behavioral_core": "PC",
        "default_conditions": ["CKM"],
        "links": ["CKM"],
        "answers": {
            "Listener": {
                "text": "That’s a scary thought. What worries you most?",
                "action_step": "Write down questions to ask your doctor.",
                "why_it_matters": "Reduces fear and supports planning.",
            },
            "Motivator": {
                "text": "You can take steps to lower that risk.",
                "action_step": "Stick to your BP and A1c goals.",
                "why_it_matters": "These are major protective factors.",
            },
            "Director": {
                "text": "We’ll monitor kidney and heart function closely.",
                "action_step": "Stay up to date on labs.",
                "why_it_matters": "Early detection means early action.",
            },
            "Expert": {
                "text": "Managing BP and A1c cuts surgery/dialysis risk in half.",
                "action_step": "Consider seeing a specialist.",
                "why_it_matters": "Experts can tailor your plan.",
            },
        },
    },
    {
        "qid": "CKM-06",
        "category": "CKM",
        "question": "Can I still exercise?",
        "behavioral_core": "PA",
        "default_conditions": ["CKM"],
        "links": ["MYLIFECHECK", "CKM"],
        "answers": {
            "Listener": {
                "text": "What kind of movement do you enjoy?",
                "action_step": "Try a 10-minute walk after a meal.",
                "why_it_matters": "Even light activity helps control glucose.",
            },
            "Motivator": {
                "text": "Movement is medicine!",
                "action_step": "Set a weekly activity goal.",
                "why_it_matters": "Goals support consistency.",
            },
            "Director": {
                "text": "Aim for 150 minutes/week.",
                "action_step": "Ask about cardiac rehab.",
                "why_it_matters": "Rehab offers safe, tailored exercise.",
            },
            "Expert": {
                "text": "Exercise improves BP, cholesterol, and kidney function.",
                "action_step": "Use a fitness tracker.",
                "why_it_matters": "Builds motivation and routine.",
            },
        },
    },
    {
        "qid": "CKM-07",
        "category": "CKM",
        "question": "What’s a healthy blood pressure for me?",
        "behavioral_core": "BP",
        "default_conditions": ["CKM", "HT"],
        "links": ["BP", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "Do you remember your last reading?",
                "action_step": "Take a photo of your BP log.",
                "why_it_matters": "Visuals help share your progress.",
            },
            "Motivator": {
                "text": "Lower BP = better brain, heart, kidney health.",
                "action_step": "Reduce one salty item.",
                "why_it_matters": "Sodium affects your pressure.",
            },
            "Director": {
                "text": "Target is usually <130/80.",
                "action_step": "Take BP at the same time daily.",
                "why_it_matters": "Reduces variability in readings.",
            },
            "Expert": {
                "text": "Control lowers stroke and kidney failure risk.",
                "action_step": "Bring cuff to your visit.",
                "why_it_matters": "We can check its accuracy.",
            },
        },
    },
    {
        "qid": "CKM-08",
        "category": "CKM",
        "question": "How can I manage this and still live my life?",
        "behavioral_core": "PC",
        "default_conditions": ["CKM"],
        "links": ["CKM", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "What’s been hardest lately?",
                "action_step": "Write down your top 3 challenges.",
                "why_it_matters": "Knowing barriers helps us support you.",
            },
            "Motivator": {
                "text": "You’re not alone—and you’re stronger than you think.",
                "action_step": "Find a health buddy.",
                "why_it_matters": "Accountability makes it easier.",
            },
            "Director": {
                "text": "Let’s build your plan into your daily routine.",
                "action_step": "Pick a weekly planning day.",
                "why_it_matters": "Structure creates consistency.",
            },
            "Expert": {
                "text": "Digital tools can help you stay organized and connected.",
                "action_step": "Ask about a care app.",
                "why_it_matters": "Apps simplify routines and tracking.",
            },
        },
    },
    {
        "qid": "CKM-09",
        "category": "CKM",
        "question": "Are my heart, kidneys, and diabetes connected?",
        "behavioral_core": "HL",
        "default_conditions": ["CKM"],
        "links": ["CKM"],
        "answers": {
            "Listener": {
                "text": "Have you heard of CKM syndrome?",
                "action_step": "Ask your provider to explain how these are linked.",
                "why_it_matters": "Understanding helps you act sooner.",
            },
            "Motivator": {
                "text": "One healthy habit helps all 3!",
                "action_step": "Walk 10–15 minutes after dinner.",
                "why_it_matters": "A single action can improve multiple systems.",
            },
            "Director": {
                "text": "We manage this as a connected syndrome now.",
                "action_step": "Ask for coordinated care options.",
                "why_it_matters": "Team-based care is more effective.",
            },
            "Expert": {
                "text": "The AHA now treats CKM as a unified health issue.",
                "action_step": "Review your PREVENT score with your doctor.",
                "why_it_matters": "Why: It reflects your full-body risk.",
            },
        },
    },
    {
        "qid": "CKM-10",
        "category": "CKM",
        "question": "How do I avoid going back to the hospital?",
        "behavioral_core": "PC",
        "default_conditions": ["CKM"],
        "links": ["CKM"],
        "answers": {
            "Listener": {
                "text": "What happened the last time you were hospitalized?",
                "action_step": "Keep a journal of early symptoms.",
                "why_it_matters": "Spotting patterns helps avoid emergencies.",
            },
            "Motivator": {
                "text": "Every healthy choice counts.",
                "action_step": "Pick one habit to stick with this week.",
                "why_it_matters": "Small steps add up.",
            },
            "Director": {
                "text": "We’ll act early—before a crisis.",
                "action_step": "Ask about telehealth or remote monitoring.",
                "why_it_matters": "Early care reduces ER visits.",
            },
            "Expert": {
                "text": "Remote support programs reduce readmissions by 30%.",
                "action_step": "Ask if you qualify for a digital health tool.",
                "why_it_matters": "Keeps your care team connected.",
            },
        },
    },
]


# ========== High Blood Pressure (Top 10) ==========
HBP_QUESTIONS: List[Dict[str, Any]] = [
    {
        "qid": "HBP-01",
        "category": "HighBP",
        "question": "What should my blood pressure goal be?",
        "behavioral_core": "BP",
        "default_conditions": ["HT"],
        "links": ["BP", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "It’s normal to feel unsure—many people don’t know their number.",
                "action_step": "Ask your doctor, “What’s my target BP?”",
                "why_it_matters": "Clear targets help you stay on track.",
            },
            "Motivator": {
                "text": "Knowing your goal puts you in control!",
                "action_step": "Write your BP goal on your fridge or phone.",
                "why_it_matters": "Visible goals keep you focused.",
            },
            "Director": {
                "text": "For most people, the AHA recommends a goal below 130/80.",
                "action_step": "Track your BP regularly and compare it to your goal.",
                "why_it_matters": "Regular feedback supports better decisions.",
            },
            "Expert": {
                "text": "AHA guidance links lower BP with lower risk of heart attack, stroke, and kidney disease.",
                "action_step": "Review the AHA blood pressure chart.",
                "why_it_matters": "Evidence-based goals are safer and more effective.",
            },
        },
    },
    {
        "qid": "HBP-02",
        "category": "HighBP",
        "question": "Do I really need medication?",
        "behavioral_core": "MA",
        "default_conditions": ["HT"],
        "links": ["MED_ADH", "BP"],
        "answers": {
            "Listener": {
                "text": "It’s okay to feel unsure. Many people ask this.",
                "action_step": "Talk to your doctor about how meds fit your overall plan.",
                "why_it_matters": "Personalized plans reduce confusion.",
            },
            "Motivator": {
                "text": "Taking medication is one way to protect your heart—just like walking or eating well.",
                "action_step": "Pair taking your med with a daily habit (e.g., brushing teeth).",
                "why_it_matters": "It builds consistency.",
            },
            "Director": {
                "text": "Medications are usually started if lifestyle changes alone don’t lower BP.",
                "action_step": "Follow up in 4 weeks to evaluate your progress.",
                "why_it_matters": "Your needs can change over time.",
            },
            "Expert": {
                "text": "For many, medication plus healthy habits works best.",
                "action_step": "Review potential side effects with your provider.",
                "why_it_matters": "Informed patients are more successful with treatment.",
            },
        },
    },
    {
        "qid": "HBP-03",
        "category": "HighBP",
        "question": "What can I do besides taking medication?",
        "behavioral_core": "PC",
        "default_conditions": ["HT"],
        "links": ["MYLIFECHECK", "DASH"],
        "answers": {
            "Listener": {
                "text": "It’s great that you want to take action!",
                "action_step": "Choose one area: food, movement, sleep, or stress.",
                "why_it_matters": "Starting small makes change more manageable.",
            },
            "Motivator": {
                "text": "Your body responds quickly to healthy habits.",
                "action_step": "Walk 10 minutes after lunch each day this week.",
                "why_it_matters": "Consistency builds confidence.",
            },
            "Director": {
                "text": "Try the DASH diet, reduce sodium, increase activity, lose weight if needed.",
                "action_step": "Track salt intake for 3 days.",
                "why_it_matters": "Awareness is the first step to improvement.",
            },
            "Expert": {
                "text": "Lifestyle changes can reduce systolic BP meaningfully for many people.",
                "action_step": "Explore the Life’s Essential 8 tool.",
                "why_it_matters": "It connects behaviors with long-term outcomes.",
            },
        },
    },
    {
        "qid": "HBP-04",
        "category": "HighBP",
        "question": "What kind of diet should I follow?",
        "behavioral_core": "NUT",
        "default_conditions": ["HT"],
        "links": ["DASH"],
        "answers": {
            "Listener": {
                "text": "Choosing what to eat can feel confusing. You’re not alone.",
                "action_step": "Keep a simple food journal for 3 days.",
                "why_it_matters": "Reflection builds insight.",
            },
            "Motivator": {
                "text": "Small food swaps can lead to big results.",
                "action_step": "Choose one low-salt snack to try this week.",
                "why_it_matters": "Starting with snacks is manageable.",
            },
            "Director": {
                "text": "The DASH diet is rich in fruits, vegetables, whole grains, and low-fat dairy.",
                "action_step": "Add one fruit or veggie to each meal.",
                "why_it_matters": "Gradual changes lead to lasting habits.",
            },
            "Expert": {
                "text": "Clinical trials show DASH lowers BP and improves heart health.",
                "action_step": "Review DASH resources.",
                "why_it_matters": "Evidence-based tools support success.",
            },
        },
    },
    {
        "qid": "HBP-05",
        "category": "HighBP",
        "question": "Will I have high blood pressure forever?",
        "behavioral_core": "PC",
        "default_conditions": ["HT"],
        "links": ["BP", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "That’s a common fear—but there’s hope.",
                "action_step": "Ask your doctor if your condition is reversible.",
                "why_it_matters": "Opens the door for shared planning.",
            },
            "Motivator": {
                "text": "You can improve your numbers—many people do!",
                "action_step": "Celebrate any drop in BP, even a few points.",
                "why_it_matters": "Every step helps your heart.",
            },
            "Director": {
                "text": "High BP may not go away completely, but it can often be controlled.",
                "action_step": "Stick with your plan for 3 months, then reassess.",
                "why_it_matters": "Change takes time to show results.",
            },
            "Expert": {
                "text": "Long-term control is very achievable with lifestyle and medication when needed.",
                "action_step": "Use a BP tracker/log.",
                "why_it_matters": "Tracking keeps you engaged and informed.",
            },
        },
    },
    {
        "qid": "HBP-06",
        "category": "HighBP",
        "question": "How can I track my blood pressure at home?",
        "behavioral_core": "SY",
        "default_conditions": ["HT"],
        "links": ["BP"],
        "answers": {
            "Listener": {
                "text": "It can be overwhelming at first, but you’re not alone.",
                "action_step": "Write down your readings in a simple journal or notebook.",
                "why_it_matters": "It helps you notice patterns over time.",
            },
            "Motivator": {
                "text": "Tracking gives you control over your progress.",
                "action_step": "Celebrate streaks of consistent tracking.",
                "why_it_matters": "Motivation builds with momentum.",
            },
            "Director": {
                "text": "Take readings in the morning and evening, seated and rested.",
                "action_step": "Set calendar alerts to build a habit.",
                "why_it_matters": "Routine readings give reliable data.",
            },
            "Expert": {
                "text": "Proper technique matters (resting, correct cuff size, arm level).",
                "action_step": "Review proper BP measurement technique.",
                "why_it_matters": "Accurate technique = trustworthy numbers.",
            },
        },
    },
    {
        "qid": "HBP-07",
        "category": "HighBP",
        "question": "Can stress really affect my blood pressure?",
        "behavioral_core": "SM",
        "default_conditions": ["HT"],
        "links": ["MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "Yes, and life can be stressful—we get it.",
                "action_step": "Identify one stressor you can reduce this week.",
                "why_it_matters": "Small wins reduce overall tension.",
            },
            "Motivator": {
                "text": "Taking care of your mind supports your heart.",
                "action_step": "Try a 5-minute guided breathing session.",
                "why_it_matters": "Helps lower heart rate and supports BP control.",
            },
            "Director": {
                "text": "Chronic stress can lead to behaviors that increase BP—like poor sleep or diet.",
                "action_step": "Create a wind-down routine before bed.",
                "why_it_matters": "Better sleep supports better BP control.",
            },
            "Expert": {
                "text": "Mindfulness and relaxation practices can support BP control for many people.",
                "action_step": "Incorporate stress reduction into weekly goals.",
                "why_it_matters": "Over time it supports cardiovascular risk reduction.",
            },
        },
    },
    {
        "qid": "HBP-08",
        "category": "HighBP",
        "question": "What’s a dangerous blood pressure level?",
        "behavioral_core": "BP",
        "default_conditions": ["HT"],
        "links": ["BP"],
        "answers": {
            "Listener": {
                "text": "It’s scary not knowing what’s too high.",
                "action_step": "Learn your BP zones with a color-coded chart.",
                "why_it_matters": "Helps you recognize when to seek help.",
            },
            "Motivator": {
                "text": "Knowing your numbers gives you power—not fear.",
                "action_step": "Practice reading and interpreting your monitor.",
                "why_it_matters": "You can respond quickly and calmly.",
            },
            "Director": {
                "text": "180/120 or higher is a hypertensive crisis—especially with symptoms.",
                "action_step": "Program emergency contact numbers in your phone.",
                "why_it_matters": "Prepares you to act fast if needed.",
            },
            "Expert": {
                "text": "Stage 2 hypertension begins at 140/90, and crisis thresholds require urgent attention.",
                "action_step": "Review your BP history with your clinician.",
                "why_it_matters": "Trends inform treatment decisions.",
            },
        },
    },
    {
        "qid": "HBP-09",
        "category": "HighBP",
        "question": "Is low blood pressure a problem too?",
        "behavioral_core": "SY",
        "default_conditions": ["HT"],
        "links": ["BP"],
        "answers": {
            "Listener": {
                "text": "Yes—it can make you feel dizzy, tired, or weak.",
                "action_step": "Note symptoms when you take readings.",
                "why_it_matters": "Helps your care team adjust treatment.",
            },
            "Motivator": {
                "text": "It’s okay to ask questions if something doesn’t feel right.",
                "action_step": "Bring those questions to your next visit.",
                "why_it_matters": "Supports shared decision-making.",
            },
            "Director": {
                "text": "If BP is too low, especially on meds, your clinician may adjust the dose.",
                "action_step": "Share symptoms and log medication timing.",
                "why_it_matters": "Timing affects BP levels.",
            },
            "Expert": {
                "text": "Low BP can be normal for some, but concerning if it causes symptoms or falls.",
                "action_step": "Track BP plus hydration/illness factors.",
                "why_it_matters": "Dehydration and illness can drop BP too far.",
            },
        },
    },
    {
        "qid": "HBP-10",
        "category": "HighBP",
        "question": "How do I talk to my family about my high blood pressure?",
        "behavioral_core": "PC",
        "default_conditions": ["HT"],
        "links": ["BP", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "Talking about your health takes courage.",
                "action_step": "Start with one trusted family member.",
                "why_it_matters": "Support makes healthy changes easier.",
            },
            "Motivator": {
                "text": "You might inspire them to check their BP too!",
                "action_step": "Invite a loved one to join you in cooking or walking.",
                "why_it_matters": "Shared habits are easier to sustain.",
            },
            "Director": {
                "text": "Use simple language: “I’m working on my BP so I can stay healthy.”",
                "action_step": "Share one goal like reducing salt together.",
                "why_it_matters": "Shared goals build buy-in.",
            },
            "Expert": {
                "text": "Family history matters. If you have high BP, relatives may too.",
                "action_step": "Encourage BP checks and reviewing guidance together.",
                "why_it_matters": "Prevention can start with one conversation.",
            },
        },
    },
]


# ========== Heart Failure (Top 10) ==========
HF_QUESTIONS: List[Dict[str, Any]] = [
    {
        "qid": "HF-01",
        "category": "HeartFailure",
        "question": "What is heart failure and can it be managed?",
        "behavioral_core": "HL",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s okay to feel nervous. You’re not alone in this.",
                "action_step": "Ask your doctor to explain your heart’s condition in simple terms.",
                "why_it_matters": "Understanding helps reduce fear.",
            },
            "Motivator": {
                "text": "Many people with heart failure live full, active lives.",
                "action_step": "Write down one strength you want to keep using each day.",
                "why_it_matters": "Keeps your identity strong.",
            },
            "Director": {
                "text": "Heart failure means your heart isn’t pumping as well—but treatment helps.",
                "action_step": "Create a care plan with your team.",
                "why_it_matters": "Clarity boosts confidence.",
            },
            "Expert": {
                "text": "Guidance supports medicines, lifestyle changes, and symptom tracking.",
                "action_step": "Use a heart failure journal for weight and symptoms.",
                "why_it_matters": "Tracking symptoms helps detect problems early.",
            },
        },
    },
    {
        "qid": "HF-02",
        "category": "HeartFailure",
        "question": "How do I know if my heart failure is getting worse?",
        "behavioral_core": "SY",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s okay to check in with how your body feels.",
                "action_step": "Keep a log of weight, swelling, and breathing daily.",
                "why_it_matters": "Early signs help prevent hospital visits.",
            },
            "Motivator": {
                "text": "You’re learning your body’s signals—that’s powerful.",
                "action_step": "Set a reminder to weigh yourself each morning.",
                "why_it_matters": "Sudden gain may mean fluid buildup.",
            },
            "Director": {
                "text": "Watch for weight gain, shortness of breath, swelling, or fatigue.",
                "action_step": "Report changes of 2+ pounds overnight or 5+ in a week.",
                "why_it_matters": "Quick action prevents worsening.",
            },
            "Expert": {
                "text": "Daily weight and symptom monitoring helps track decompensation risk.",
                "action_step": "Use a simple symptom checklist.",
                "why_it_matters": "Patterns matter more than single events.",
            },
        },
    },
    {
        "qid": "HF-03",
        "category": "HeartFailure",
        "question": "What can I eat with heart failure?",
        "behavioral_core": "NUT",
        "default_conditions": ["HF"],
        "links": ["HF", "DASH"],
        "answers": {
            "Listener": {
                "text": "Eating can feel tricky when you’re told to ‘cut back.’",
                "action_step": "Write down your favorite heart-healthy foods.",
                "why_it_matters": "Focus on what you can enjoy.",
            },
            "Motivator": {
                "text": "Your meals can still be flavorful and fulfilling!",
                "action_step": "Try one new low-sodium recipe this week.",
                "why_it_matters": "Keeps meals exciting.",
            },
            "Director": {
                "text": "Limit sodium to under 1,500–2,000 mg/day. Watch fluids if advised.",
                "action_step": "Check one food label daily for sodium.",
                "why_it_matters": "Small steps add up.",
            },
            "Expert": {
                "text": "A DASH-style pattern with lower sodium supports heart health.",
                "action_step": "Use a grocery guide and plan ahead.",
                "why_it_matters": "Smart shopping leads to better choices.",
            },
        },
    },
    {
        "qid": "HF-04",
        "category": "HeartFailure",
        "question": "How much activity is safe for me?",
        "behavioral_core": "PA",
        "default_conditions": ["HF"],
        "links": ["HF", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "It’s natural to feel cautious.",
                "action_step": "Ask your provider about safe movement goals.",
                "why_it_matters": "Avoids fear-based inactivity.",
            },
            "Motivator": {
                "text": "Even a few steps count. Movement is medicine.",
                "action_step": "Walk for 5 minutes after each meal.",
                "why_it_matters": "Builds stamina without stress.",
            },
            "Director": {
                "text": "Most can do light-to-moderate activity, depending on symptoms.",
                "action_step": "Join a rehab or walking program if offered.",
                "why_it_matters": "Structured programs offer guidance.",
            },
            "Expert": {
                "text": "Supervised cardiac rehab improves quality of life and outcomes for many people.",
                "action_step": "Ask about a referral to home or clinic-based rehab.",
                "why_it_matters": "Rehab is proven to help.",
            },
        },
    },
    {
        "qid": "HF-05",
        "category": "HeartFailure",
        "question": "Will I always feel tired or short of breath?",
        "behavioral_core": "SY",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s frustrating when energy is low—but you’re doing your best.",
                "action_step": "Keep a fatigue and symptom journal.",
                "why_it_matters": "Patterns help your team help you.",
            },
            "Motivator": {
                "text": "Good days will come—keep going.",
                "action_step": "Celebrate energy wins, no matter how small.",
                "why_it_matters": "Builds momentum.",
            },
            "Director": {
                "text": "You may feel better as your treatment plan kicks in.",
                "action_step": "Stick to your meds, meals, and movement plan.",
                "why_it_matters": "Structure supports healing.",
            },
            "Expert": {
                "text": "Symptoms can improve as guideline-based therapy is optimized.",
                "action_step": "Ask about medication adjustments if symptoms persist.",
                "why_it_matters": "Regular reviews help fine-tune care.",
            },
        },
    },
    {
        "qid": "HF-06",
        "category": "HeartFailure",
        "question": "What medications will I need, and what do they do?",
        "behavioral_core": "MA",
        "default_conditions": ["HF"],
        "links": ["MED_ADH", "HF"],
        "answers": {
            "Listener": {
                "text": "It’s okay to ask what each pill is for. That’s smart.",
                "action_step": "Bring all your meds to your next visit and ask questions.",
                "why_it_matters": "Builds confidence in your treatment.",
            },
            "Motivator": {
                "text": "Learning about your meds is part of owning your care.",
                "action_step": "Make a simple chart with what, when, and why.",
                "why_it_matters": "Keeps things manageable.",
            },
            "Director": {
                "text": "There are core medication classes that help heart failure. Each plays a role.",
                "action_step": "Ask if you’re on guideline-directed therapies.",
                "why_it_matters": "Maximizing benefit lowers risk.",
            },
            "Expert": {
                "text": "Medication regimens may evolve; regular review helps keep them safe and effective.",
                "action_step": "Review your med list with your provider every 3–6 months.",
                "why_it_matters": "Meds may change as your body changes.",
            },
        },
    },
    {
        "qid": "HF-07",
        "category": "HeartFailure",
        "question": "Can I travel or go on vacation with heart failure?",
        "behavioral_core": "PC",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s totally okay to want some normalcy.",
                "action_step": "Talk to your provider about your plans in advance.",
                "why_it_matters": "Better to plan than guess.",
            },
            "Motivator": {
                "text": "You can still explore and enjoy—just with preparation.",
                "action_step": "Pack your meds, weight scale, and health summary.",
                "why_it_matters": "Keeps you ready anywhere.",
            },
            "Director": {
                "text": "Travel is often safe if symptoms are stable and you’re prepared.",
                "action_step": "Get travel clearance and emergency contacts.",
                "why_it_matters": "Reduces travel stress.",
            },
            "Expert": {
                "text": "Travel advice is individualized based on recent symptoms and status.",
                "action_step": "Avoid extreme temperatures or high altitude if advised.",
                "why_it_matters": "These can strain your heart.",
            },
        },
    },
    {
        "qid": "HF-08",
        "category": "HeartFailure",
        "question": "Will I need a device like a defibrillator or pacemaker?",
        "behavioral_core": "HL",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s okay to be nervous about devices. Ask away.",
                "action_step": "Ask your cardiologist if your ejection fraction qualifies you.",
                "why_it_matters": "Eligibility depends on heart strength.",
            },
            "Motivator": {
                "text": "Many people feel safer with a device protecting them.",
                "action_step": "Talk to someone who already has one (if possible).",
                "why_it_matters": "Eases anxiety.",
            },
            "Director": {
                "text": "Devices are considered based on EF and symptoms after treatment optimization.",
                "action_step": "Get an echo if not done recently.",
                "why_it_matters": "Data drives decisions.",
            },
            "Expert": {
                "text": "Device therapy is for select patients after meds are optimized.",
                "action_step": "Reassess after a few months on therapy as advised.",
                "why_it_matters": "Some improve and avoid needing devices.",
            },
        },
    },
    {
        "qid": "HF-09",
        "category": "HeartFailure",
        "question": "What should I do during a flare or worsening episode?",
        "behavioral_core": "PC",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "You’re not alone. Flares happen even when you’re doing everything right.",
                "action_step": "Write down a “When to Call” symptom checklist.",
                "why_it_matters": "Removes guesswork.",
            },
            "Motivator": {
                "text": "You can bounce back. Having a plan makes you powerful.",
                "action_step": "Pack a “go bag” with meds and notes just in case.",
                "why_it_matters": "Prepares you for any ER trip.",
            },
            "Director": {
                "text": "Call if symptoms suddenly worsen: weight gain, swelling, breathlessness.",
                "action_step": "Keep your care team’s number posted and saved.",
                "why_it_matters": "Early contact = fewer hospital stays.",
            },
            "Expert": {
                "text": "Early escalation when symptoms worsen can prevent full decompensation.",
                "action_step": "Review your emergency plan every 3–6 months.",
                "why_it_matters": "Avoids surprises when you’re vulnerable.",
            },
        },
    },
    {
        "qid": "HF-10",
        "category": "HeartFailure",
        "question": "How long can I live with heart failure?",
        "behavioral_core": "PC",
        "default_conditions": ["HF"],
        "links": ["HF"],
        "answers": {
            "Listener": {
                "text": "It’s okay to think about the future—it means you care.",
                "action_step": "Focus on today’s goals and routines.",
                "why_it_matters": "Peace comes from progress, not prediction.",
            },
            "Motivator": {
                "text": "Many people live for years—what matters is your path.",
                "action_step": "Set one long-term goal (family, travel, legacy).",
                "why_it_matters": "Purpose fuels resilience.",
            },
            "Director": {
                "text": "Life expectancy varies based on many factors.",
                "action_step": "Ask your team to track markers like EF and functional capacity.",
                "why_it_matters": "Objective data shows trends.",
            },
            "Expert": {
                "text": "Prognosis improves with adherence to evidence-based therapy and follow-up.",
                "action_step": "Schedule regular check-ins to adjust treatment as needed.",
                "why_it_matters": "Timely updates keep care effective.",
            },
        },
    },
]


# ========== CAD (Top 10) ==========
CAD_QUESTIONS: List[Dict[str, Any]] = [
    {
        "qid": "CAD-01",
        "category": "CAD",
        "question": "What caused my coronary artery disease?",
        "behavioral_core": "HL",
        "default_conditions": ["CD"],
        "links": ["CAD", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "It’s natural to wonder ‘why me?’ Many people ask this.",
                "action_step": "Ask your provider to walk through your risk factors.",
                "why_it_matters": "Understanding helps reduce blame and clarify prevention.",
            },
            "Motivator": {
                "text": "Knowing your history can help you rewrite your future.",
                "action_step": "Write down your top 3 risks and 1 way to tackle each.",
                "why_it_matters": "Personal action builds momentum.",
            },
            "Director": {
                "text": "CAD often results from cholesterol, high blood pressure, diabetes, smoking, and genes.",
                "action_step": "Request a printout of your latest labs and risk profile.",
                "why_it_matters": "You can’t manage what you don’t see.",
            },
            "Expert": {
                "text": "Atherosclerosis can build silently over decades from plaque buildup.",
                "action_step": "Review Life’s Essential 8 as your prevention framework.",
                "why_it_matters": "These address core drivers of CAD.",
            },
        },
    },
    {
        "qid": "CAD-02",
        "category": "CAD",
        "question": "What should I eat now that I have CAD?",
        "behavioral_core": "NUT",
        "default_conditions": ["CD"],
        "links": ["DASH", "CAD"],
        "answers": {
            "Listener": {
                "text": "There’s a lot of confusing advice out there. You’re not alone.",
                "action_step": "Bring a food log to your next visit.",
                "why_it_matters": "It helps your provider personalize advice.",
            },
            "Motivator": {
                "text": "You can still enjoy food—just smarter.",
                "action_step": "Try a new heart-healthy recipe this week.",
                "why_it_matters": "Small changes spark new habits.",
            },
            "Director": {
                "text": "Focus on whole grains, veggies, fruits, nuts, and lean proteins. Limit sodium and added sugars.",
                "action_step": "Reduce sodium toward <1500 mg/day if advised.",
                "why_it_matters": "Helps control BP and supports heart health.",
            },
            "Expert": {
                "text": "Mediterranean and DASH-style patterns are widely recommended for secondary prevention.",
                "action_step": "Use an evidence-based meal plan template.",
                "why_it_matters": "Reduces guesswork.",
            },
        },
    },
    {
        "qid": "CAD-03",
        "category": "CAD",
        "question": "Can I exercise safely with CAD?",
        "behavioral_core": "PA",
        "default_conditions": ["CD"],
        "links": ["CAD", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "It’s good you’re asking. Many people worry about overdoing it.",
                "action_step": "Ask about cardiac rehab or a home walking plan.",
                "why_it_matters": "Support builds confidence.",
            },
            "Motivator": {
                "text": "Movement is medicine—even 10 minutes counts.",
                "action_step": "Walk after one meal each day this week.",
                "why_it_matters": "Easy routines are powerful.",
            },
            "Director": {
                "text": "Most benefit from moderate activity unless symptoms worsen.",
                "action_step": "Track your steps or minutes daily.",
                "why_it_matters": "You’ll learn your limits and progress.",
            },
            "Expert": {
                "text": "Exercise can improve vessel health, functional capacity, and reduce risk over time.",
                "action_step": "Ask whether a stress test or 6-minute walk would guide your plan.",
                "why_it_matters": "Baseline testing helps tailor exercise.",
            },
        },
    },
    {
        "qid": "CAD-04",
        "category": "CAD",
        "question": "What are my chances of having another heart event?",
        "behavioral_core": "PC",
        "default_conditions": ["CD"],
        "links": ["CAD", "MYLIFECHECK"],
        "answers": {
            "Listener": {
                "text": "It’s totally normal to feel anxious about recurrence.",
                "action_step": "Ask for your risk estimate and what can reduce it.",
                "why_it_matters": "Knowledge replaces fear with planning.",
            },
            "Motivator": {
                "text": "Every day you take action, you lower your risk.",
                "action_step": "Commit to 1 healthy habit for the next 30 days.",
                "why_it_matters": "Your choices make a difference.",
            },
            "Director": {
                "text": "Risk depends on BP, lipids, heart function, and lifestyle.",
                "action_step": "Keep a shared checklist with your care team.",
                "why_it_matters": "Organized care is safer care.",
            },
            "Expert": {
                "text": "Secondary prevention is multi-factor: meds, lifestyle, and monitoring.",
                "action_step": "Confirm you’re on an evidence-based prevention plan.",
                "why_it_matters": "The right plan reduces repeat events.",
            },
        },
    },
    {
        "qid": "CAD-05",
        "category": "CAD",
        "question": "How do I manage stress without hurting my heart?",
        "behavioral_core": "SM",
        "default_conditions": ["CD"],
        "links": ["MYLIFECHECK", "CAD"],
        "answers": {
            "Listener": {
                "text": "Heart issues can feel overwhelming. You’re not alone.",
                "action_step": "Write down 3 things that bring you calm.",
                "why_it_matters": "Awareness helps shift energy.",
            },
            "Motivator": {
                "text": "Stress can shrink when you take control.",
                "action_step": "Try deep breathing or stretching once a day.",
                "why_it_matters": "Mind-body tools work fast.",
            },
            "Director": {
                "text": "Sleep, connection, and relaxation support better outcomes.",
                "action_step": "Set a 15-minute tech-free evening wind-down.",
                "why_it_matters": "Sleep and stress are linked to heart outcomes.",
            },
            "Expert": {
                "text": "Psychosocial stress is recognized as a contributor to cardiovascular risk.",
                "action_step": "Ask about support groups or counseling if needed.",
                "why_it_matters": "Support improves self-management.",
            },
        },
    },
    {
        "qid": "CAD-06",
        "category": "CAD",
        "question": "What should I do if I have chest pain again?",
        "behavioral_core": "SY",
        "default_conditions": ["CD"],
        "links": ["CAD"],
        "answers": {
            "Listener": {
                "text": "Chest pain can be scary. You’re not alone in this.",
                "action_step": "Keep a journal of symptoms, triggers, and duration.",
                "why_it_matters": "Helps your doctor better assess the situation.",
            },
            "Motivator": {
                "text": "Taking action right away can protect your heart.",
                "action_step": "Make a plan with loved ones for when to call 911.",
                "why_it_matters": "Confidence grows with preparation.",
            },
            "Director": {
                "text": "Call 911 if chest pain lasts more than 5 minutes or doesn’t go away with rest (or nitroglycerin if prescribed).",
                "action_step": "Keep nitroglycerin on hand if prescribed.",
                "why_it_matters": "Fast response saves lives.",
            },
            "Expert": {
                "text": "Recurrent angina can signal reduced blood flow and must be evaluated.",
                "action_step": "Schedule follow-up if pain recurs or changes pattern.",
                "why_it_matters": "Timely evaluation prevents complications.",
            },
        },
    },
    {
        "qid": "CAD-07",
        "category": "CAD",
        "question": "Should I get a stent or surgery again?",
        "behavioral_core": "PC",
        "default_conditions": ["CD"],
        "links": ["CAD"],
        "answers": {
            "Listener": {
                "text": "It’s okay to feel uncertain about procedures.",
                "action_step": "List your pros, cons, and concerns before your visit.",
                "why_it_matters": "Helps you feel heard and involved.",
            },
            "Motivator": {
                "text": "You’ve been through this before. You know your body.",
                "action_step": "Ask about non-surgical alternatives.",
                "why_it_matters": "Shared decision-making builds trust.",
            },
            "Director": {
                "text": "Repeat procedures depend on symptoms, test results, and current heart function.",
                "action_step": "Request updated imaging or stress testing if needed.",
                "why_it_matters": "Decisions should be based on current data.",
            },
            "Expert": {
                "text": "Revascularization is typically for limiting symptoms or high-risk anatomy.",
                "action_step": "Review your cath/angiogram report with your cardiologist.",
                "why_it_matters": "Context informs your next step.",
            },
        },
    },
    {
        "qid": "CAD-08",
        "category": "CAD",
        "question": "Can I travel or fly with CAD?",
        "behavioral_core": "PC",
        "default_conditions": ["CD"],
        "links": ["CAD"],
        "answers": {
            "Listener": {
                "text": "Wanting to live fully is a good sign. Let’s talk about it.",
                "action_step": "Discuss travel plans with your care team.",
                "why_it_matters": "They can help prepare for a safe trip.",
            },
            "Motivator": {
                "text": "Yes—you can still enjoy life with a heart condition!",
                "action_step": "Pack medications and emergency contacts.",
                "why_it_matters": "Preparedness reduces anxiety.",
            },
            "Director": {
                "text": "Stay active during travel, hydrate well, and avoid long sitting.",
                "action_step": "Plan stretch breaks every 2 hours.",
                "why_it_matters": "Supports circulation and lowers clot risk.",
            },
            "Expert": {
                "text": "Travel is generally safe if stable; timing after events/procedures matters.",
                "action_step": "Ask about travel clearance if you’ve had recent symptoms/events.",
                "why_it_matters": "Risk varies by person.",
            },
        },
    },
    {
        "qid": "CAD-09",
        "category": "CAD",
        "question": "What’s the role of cholesterol and statins?",
        "behavioral_core": "MA",
        "default_conditions": ["CD"],
        "links": ["CAD", "MED_ADH"],
        "answers": {
            "Listener": {
                "text": "Many people wonder about statins and side effects.",
                "action_step": "Ask about your LDL goal and if statins are helping.",
                "why_it_matters": "Knowing the “why” builds trust.",
            },
            "Motivator": {
                "text": "Lowering cholesterol protects your arteries—keep going!",
                "action_step": "Get your lipid panel rechecked in 3–6 months.",
                "why_it_matters": "It tracks your progress.",
            },
            "Director": {
                "text": "Statins reduce heart attack and stroke risk by stabilizing plaques.",
                "action_step": "Take your statin consistently at the same time daily.",
                "why_it_matters": "Consistency supports effectiveness.",
            },
            "Expert": {
                "text": "There are medication options if statins aren’t tolerated; discuss alternatives.",
                "action_step": "Review choices with your clinician.",
                "why_it_matters": "Matching therapy to the patient improves outcomes.",
            },
        },
    },
]   

