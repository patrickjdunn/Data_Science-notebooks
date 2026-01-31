"""
questions.py

Holds the Signatures Question Bank:
- Preloaded questions
- Persona-specific responses
- Action steps + rationale
- Source links (AHA)

No engine logic lives here.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

Persona = Literal["Listener", "Motivator", "Director", "Expert"]


# -----------------------------
# Data models
# -----------------------------

@dataclass
class PersonaAnswer:
    text: str
    action_step: str
    why_it_matters: str


@dataclass
class PreloadedQuestion:
    qid: str
    category: str
    question: str
    behavioral_core: str
    default_conditions: List[str] = field(default_factory=list)
    default_drivers: Dict[str, int] = field(default_factory=dict)
    answers: Dict[Persona, PersonaAnswer] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)


# -----------------------------
# AHA links (centralized)
# -----------------------------

AHA_LINKS = {
    "CKM": {
        "org": "American Heart Association",
        "title": "Cardiovascular–Kidney–Metabolic Health",
        "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health",
    },
    "BP": {
        "org": "American Heart Association",
        "title": "High Blood Pressure",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
    },
    "MYLIFECHECK": {
        "org": "American Heart Association",
        "title": "My Life Check (Life’s Essential 8)",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check",
    },
    "FITNESS": {
        "org": "American Heart Association",
        "title": "Physical Activity",
        "url": "https://www.heart.org/en/healthy-living/fitness",
    },
    "DASH": {
        "org": "American Heart Association",
        "title": "DASH Eating Plan",
        "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/dash-diet",
    },
}


# -----------------------------
# Question bank
# -----------------------------

QUESTION_BANK: Dict[str, PreloadedQuestion] = {}


def add_question(q: PreloadedQuestion):
    """Register a question in the global question bank."""
    QUESTION_BANK[q.qid] = q


# -----------------------------
# CKM EXAMPLES (you can add more)
# -----------------------------

add_question(
    PreloadedQuestion(
        qid="CKM-01",
        category="CKM",
        question="What does my diagnosis mean for my future?",
        behavioral_core="PC",
        default_conditions=["CKM"],
        answers={
            "Listener": PersonaAnswer(
                text="That sounds overwhelming. What are you most worried about?",
                action_step="Write down your top 3 concerns.",
                why_it_matters="Sharing helps your care team focus on what matters to you.",
            ),
            "Motivator": PersonaAnswer(
                text="You can live a full life with support.",
                action_step="Set one small health goal, like a daily walk.",
                why_it_matters="Goals help build confidence and momentum.",
            ),
            "Director": PersonaAnswer(
                text="Let’s monitor labs and scores every 3 months.",
                action_step="Schedule your next lab appointment.",
                why_it_matters="Staying on track helps catch changes early.",
            ),
            "Expert": PersonaAnswer(
                text="Early action guided by PREVENT and Life’s Essential 8 makes a difference.",
                action_step="Ask for your PREVENT score.",
                why_it_matters="Personalized scores help guide care decisions.",
            ),
        },
        links=[AHA_LINKS["CKM"], AHA_LINKS["MYLIFECHECK"]],
    )
)

add_question(
    PreloadedQuestion(
        qid="CKM-02",
        category="CKM",
        question="What can I eat—and what should I avoid?",
        behavioral_core="NUT",
        default_conditions=["CKM"],
        answers={
            "Listener": PersonaAnswer(
                text="What foods do you enjoy? Let’s start there.",
                action_step="Track meals for 3 days.",
                why_it_matters="Helps identify strengths and needed changes.",
            ),
            "Motivator": PersonaAnswer(
                text="Healthy food can taste great.",
                action_step="Try one new heart-healthy recipe.",
                why_it_matters="Enjoyment builds lasting habits.",
            ),
            "Director": PersonaAnswer(
                text="Follow DASH or Mediterranean-style eating.",
                action_step="Replace one salty snack with fruit or veggies.",
                why_it_matters="Small swaps lower blood pressure.",
            ),
            "Expert": PersonaAnswer(
                text="These diets reduce cardiovascular risk by 20–30%.",
                action_step="Use a food-tracking app.",
                why_it_matters="Tools support consistency.",
            ),
        },
        links=[AHA_LINKS["DASH"], AHA_LINKS["CKM"]],
    )
)


# -----------------------------
# Helpers (used by the engine)
# -----------------------------

def list_questions(category: Optional[str] = None):
    items = sorted(QUESTION_BANK.values(), key=lambda q: q.qid)
    if category:
        items = [q for q in items if q.category.lower() == category.lower()]
    return items


def get_question(qid: str) -> Optional[PreloadedQuestion]:
    return QUESTION_BANK.get(qid.strip())
