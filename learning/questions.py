# questions.py
# Central question bank for Signatures (preloaded questions + persona responses)
# Place this file in: hi5304-notebooks/learning/questions.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

PERSONAS = ("Listener", "Motivator", "Director", "Expert")

# -----------------------------
# AHA + tool links (stable pages)
# -----------------------------
AHA_LINKS: Dict[str, Dict[str, str]] = {
    # Core hooks
    "MYLIFECHECK": {
        "org": "American Heart Association",
        "title": "My Life Check — Life’s Essential 8",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/my-life-check--lifes-essential-8",
    },
    "LIFES_ESSENTIAL_8": {
        "org": "American Heart Association",
        "title": "Life’s Essential 8",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8",
    },
    "CKM": {
        "org": "American Heart Association",
        "title": "Cardiovascular-Kidney-Metabolic (CKM) Health",
        "url": "https://www.heart.org/en/professional/quality-improvement/cardio-kidney-metabolic-health",
    },
    "BP": {
        "org": "American Heart Association",
        "title": "High Blood Pressure",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure",
    },
    "BP_CHART": {
        "org": "American Heart Association",
        "title": "Understanding Blood Pressure Readings",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings",
    },
    "DASH": {
        "org": "American Heart Association",
        "title": "DASH Eating Plan",
        "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/dash-diet",
    },
    "FITNESS": {
        "org": "American Heart Association",
        "title": "Fitness Basics",
        "url": "https://www.heart.org/en/healthy-living/fitness",
    },
    "MED_ADH": {
        "org": "American Heart Association",
        "title": "Medication Adherence",
        "url": "https://www.heart.org/en/health-topics/consumer-healthcare/medication-adherence",
    },
    "STRESS": {
        "org": "American Heart Association",
        "title": "Stress Management",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management",
    },
}


def _norm(s: str) -> str:
    return (s or "").strip()


def _mk_answer(text: str, action_step: str, why_it_matters: str) -> Dict[str, str]:
    return {
        "text": _norm(text),
        "action_step": _norm(action_step),
        "why_it_matters": _norm(why_it_matters),
    }


def _mk_question(
    category: str,
    question: str,
    behavioral_core: str,
    default_conditions: Optional[List[str]] = None,
    default_drivers: Optional[Dict[str, int]] = None,
    links: Optional[List[str]] = None,
    answers: Optional[Dict[str, Dict[str, str]]] = None,
    qid: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Note: qid is optional. If omitted, IDs will be auto-assigned via assign_ids().
    """
    cat = _norm(category).upper()
    return {
        "id": _norm(qid).upper() if qid else "",
        "category": cat,
        "question": _norm(question),
        "behavioral_core": _norm(behavioral_core).upper(),
        "default_conditions": default_conditions or [],
        "default_drivers": default_drivers or {},
        "answers": answers or {},
        "sources": [AHA_LINKS[k] for k in (links or []) if k in AHA_LINKS],
    }


def assign_ids(questions: List[Dict[str, Any]], category: str, prefix: Optional[str] = None, start: int = 1) -> List[Dict[str, Any]]:
    """
    Ensures each question has a stable ID like CKM-01, CKM-02, ...
    If an ID already exists, it is preserved (and normalized).
    """
    cat = (category or "GEN").upper()
    pfx = (prefix or cat).upper()
    n = start

    for q in questions:
        q["category"] = cat
        if not q.get("id"):
            q["id"] = f"{pfx}-{n:02d}"
            n += 1
        else:
            q["id"] = str(q["id"]).upper().strip()
    return questions


# -----------------------------
# CKM question set (10)
# -----------------------------
CKM_QUESTIONS: List[Dict[str, Any]] = [
    _mk_question(
        "CKM",
        "What does my diagnosis mean for my future?",
        behavioral_core="PC",
        default_conditions=["CKM"],
        links=["CKM", "MYLIFECHECK", "LIFES_ESSENTIAL_8"],
        answers={
            "Listener": _mk_answer(
                "That sounds overwhelming. What are you most worried about?",
                "Write down your top 3 concerns.",
                "Sharing helps your care team focus on what matters to you.",
            ),
            "Motivator": _mk_answer(
                "You can live a full life with support.",
                "Set one small health goal, like a daily walk.",
                "Goals help build confidence and momentum.",
            ),
            "Director": _mk_answer(
                "Let’s monitor labs and scores every 3 months.",
                "Schedule your next lab appointment.",
                "Staying on track helps catch changes early.",
            ),
            "Expert": _mk_answer(
                "Early action guided by PREVENT and Life’s Essential 8 can make a meaningful difference.",
                "Ask for your PREVENT score and your Life’s Essential 8 (My Life Check) score.",
                "Personalized scores help guide care decisions and track progress over time.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "What can I eat—and what should I avoid?",
        behavioral_core="NUT",
        default_conditions=["CKM"],
        links=["DASH", "CKM", "LIFES_ESSENTIAL_8"],
        answers={
            "Listener": _mk_answer(
                "What foods do you enjoy? Let’s start there.",
                "Track meals for 3 days.",
                "It helps identify strengths and where small changes could help most.",
            ),
            "Motivator": _mk_answer(
                "Healthy food can taste great.",
                "Try one new heart-healthy recipe this week.",
                "Enjoyment builds habits that last.",
            ),
            "Director": _mk_answer(
                "Follow DASH or Mediterranean-style eating and reduce sodium.",
                "Replace one salty snack with fruit or veggies.",
                "Small swaps can lower blood pressure and improve cardiometabolic health.",
            ),
            "Expert": _mk_answer(
                "DASH-style patterns are supported by evidence for blood pressure and cardiovascular risk reduction.",
                "Use a food-tracking app (even for 1 week) to learn your sodium and fiber patterns.",
                "Data helps you and your clinician tailor changes that match your CKM needs.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "Why am I on so many medications?",
        behavioral_core="MA",
        default_conditions=["CKM"],
        links=["MED_ADH", "CKM"],
        answers={
            "Listener": _mk_answer(
                "Do any cause side effects or confusion?",
                "Bring all meds (or a photo of the labels) to your next visit.",
                "It helps avoid duplication, interactions, and missed doses.",
            ),
            "Motivator": _mk_answer(
                "Each one helps protect your organs.",
                "Use a pillbox or phone reminders for the next 2 weeks.",
                "Consistency improves protection for heart, kidney, and metabolic health.",
            ),
            "Director": _mk_answer(
                "Your meds follow evidence-based guidelines for your risk factors.",
                "Ask what each one does and when you should take it.",
                "Understanding the “why” reduces errors and builds confidence.",
            ),
            "Expert": _mk_answer(
                "In CKM care, medication combinations often target blood pressure, cholesterol, glucose, and kidney protection together.",
                "Report missed doses or side effects quickly rather than stopping on your own.",
                "Adjustments can improve safety and adherence without losing benefit.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "How do I know if my condition is getting better or worse?",
        behavioral_core="SY",
        default_conditions=["CKM"],
        links=["MYLIFECHECK", "CKM"],
        answers={
            "Listener": _mk_answer(
                "Notice any changes in how you feel?",
                "Keep a weekly symptom log (energy, swelling, breathing, sleep).",
                "Tracking helps spot changes early and makes visits more productive.",
            ),
            "Motivator": _mk_answer(
                "Monitoring gives you control.",
                "Check your BP twice weekly (or as advised) and record it.",
                "Catching trends early helps prevent setbacks.",
            ),
            "Director": _mk_answer(
                "We’ll review your data and labs regularly.",
                "Ask your provider to explain your most recent results in 1–2 key takeaways.",
                "Clear interpretation guides next steps.",
            ),
            "Expert": _mk_answer(
                "Scores like Life’s Essential 8 help summarize progress across key domains over time.",
                "Ask how your Life’s Essential 8 score is trending and how it relates to your labs.",
                "Trends often matter more than single readings.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "Will I need dialysis or heart surgery?",
        behavioral_core="PC",
        default_conditions=["CKM"],
        links=["CKM"],
        answers={
            "Listener": _mk_answer(
                "That’s a scary thought. What worries you most?",
                "Write down questions to ask your doctor before your next visit.",
                "It reduces fear and supports shared planning.",
            ),
            "Motivator": _mk_answer(
                "You can take steps to lower that risk.",
                "Stick to your BP and A1c goals this month.",
                "These are major protective factors for heart and kidneys.",
            ),
            "Director": _mk_answer(
                "We’ll monitor kidney and heart function closely and adjust the plan if trends change.",
                "Stay up to date on labs and follow-up visits.",
                "Early detection allows early action.",
            ),
            "Expert": _mk_answer(
                "Risk is individualized and depends on kidney function, symptoms, imaging, and response to therapy.",
                "Consider a specialist visit if your care team recommends it.",
                "Specialists can tailor prevention and timing decisions to your profile.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "Can I still exercise?",
        behavioral_core="PA",
        default_conditions=["CKM"],
        links=["FITNESS", "MYLIFECHECK"],
        answers={
            "Listener": _mk_answer(
                "What kind of movement do you enjoy?",
                "Try a 10-minute walk after a meal.",
                "Even light activity can help glucose control and energy.",
            ),
            "Motivator": _mk_answer(
                "Movement is medicine!",
                "Set a weekly activity goal you can realistically hit.",
                "Goals build consistency and confidence.",
            ),
            "Director": _mk_answer(
                "Aim for about 150 minutes/week of moderate activity if your clinician agrees.",
                "Ask whether cardiac rehab or a supervised start is appropriate for you.",
                "A structured plan is safer and easier to follow.",
            ),
            "Expert": _mk_answer(
                "Activity can improve BP, lipid profile, insulin sensitivity, and functional capacity.",
                "Use a fitness tracker (steps/minutes) and review trends monthly.",
                "Objective tracking helps personalize progression safely.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "What’s a healthy blood pressure for me?",
        behavioral_core="BP",
        default_conditions=["CKM", "HT"],
        links=["BP", "BP_CHART"],
        answers={
            "Listener": _mk_answer(
                "Do you remember your last reading?",
                "Take a photo of your BP log (or start one).",
                "Visuals help you and your clinician see trends quickly.",
            ),
            "Motivator": _mk_answer(
                "Lower BP supports your brain, heart, and kidney health.",
                "Reduce one salty item this week.",
                "Sodium often has a fast impact on BP.",
            ),
            "Director": _mk_answer(
                "Targets are individualized, but many people aim for under 130/80 if clinically appropriate.",
                "Take BP at the same time daily for 1–2 weeks to establish a baseline.",
                "Consistency reduces noise and improves decisions.",
            ),
            "Expert": _mk_answer(
                "BP goals depend on risk, comorbidities, and treatment tolerance.",
                "Bring your home cuff to your visit to check accuracy.",
                "Correct measurement improves safety and treatment precision.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "How can I manage this and still live my life?",
        behavioral_core="PC",
        default_conditions=["CKM"],
        links=["CKM", "MYLIFECHECK"],
        answers={
            "Listener": _mk_answer(
                "What’s been hardest lately?",
                "Write down your top 3 challenges.",
                "Naming barriers helps your team support you more effectively.",
            ),
            "Motivator": _mk_answer(
                "You’re not alone—and you’re stronger than you think.",
                "Find a health buddy for one habit (walks, meals, meds).",
                "Accountability makes change easier.",
            ),
            "Director": _mk_answer(
                "Let’s build your plan into your routine.",
                "Pick one weekly planning day to prep meds, meals, and schedule.",
                "Structure creates consistency.",
            ),
            "Expert": _mk_answer(
                "Digital tools can support adherence and monitoring when used simply.",
                "Ask whether your clinic offers a care app or remote monitoring.",
                "Connectivity can reduce gaps and improve early intervention.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "Are my heart, kidneys, and diabetes connected?",
        behavioral_core="HL",
        default_conditions=["CKM"],
        links=["CKM"],
        answers={
            "Listener": _mk_answer(
                "Have you heard of CKM syndrome?",
                "Ask your provider to explain how these are linked in your case.",
                "Understanding helps you act sooner and with less fear.",
            ),
            "Motivator": _mk_answer(
                "One healthy habit can help all three systems.",
                "Walk 10–15 minutes after dinner for the next week.",
                "A single action can improve glucose, BP, and energy.",
            ),
            "Director": _mk_answer(
                "We manage this as a connected syndrome now.",
                "Ask about coordinated care options (team-based approach).",
                "Integrated care tends to be more effective.",
            ),
            "Expert": _mk_answer(
                "CKM framing emphasizes shared risk pathways and unified prevention targets.",
                "Review your PREVENT outputs alongside kidney and metabolic labs.",
                "It helps align prevention intensity with overall risk.",
            ),
        },
    ),
    _mk_question(
        "CKM",
        "How do I avoid going back to the hospital?",
        behavioral_core="PC",
        default_conditions=["CKM"],
        links=["CKM", "MYLIFECHECK"],
        answers={
            "Listener": _mk_answer(
                "What happened the last time you were hospitalized?",
                "Keep a journal of early symptoms or triggers you noticed.",
                "Spotting patterns helps prevent emergencies.",
            ),
            "Motivator": _mk_answer(
                "Every healthy choice counts.",
                "Pick one habit to stick with this week.",
                "Small steps add up to big protection.",
            ),
            "Director": _mk_answer(
                "We’ll act early—before a crisis.",
                "Ask about telehealth check-ins or remote monitoring if available.",
                "Early care can reduce ER visits and admissions.",
            ),
            "Expert": _mk_answer(
                "Programs combining monitoring, lifestyle coaching, and rapid follow-up reduce avoidable utilization.",
                "Ask if you qualify for a digital support or rehab program.",
                "Support systems help catch decompensation earlier.",
            ),
        },
    ),
]

CKM_QUESTIONS = assign_ids(CKM_QUESTIONS, category="CKM", prefix="CKM", start=1)


# -----------------------------
# High blood pressure question set (10)
# Category: HTN
# -----------------------------
HTN_QUESTIONS: List[Dict[str, Any]] = [
    _mk_question(
        "HTN",
        "What should my blood pressure goal be?",
        behavioral_core="BP",
        default_conditions=["HT"],
        links=["BP_CHART", "BP"],
        answers={
            "Listener": _mk_answer(
                "It’s normal to feel unsure—many people don’t know their number.",
                "Ask your doctor, “What’s my target BP?”",
                "Clear targets help you stay on track.",
            ),
            "Motivator": _mk_answer(
                "Knowing your goal puts you in control!",
                "Write your BP goal on your fridge or phone.",
                "Visible goals keep you focused.",
            ),
            "Director": _mk_answer(
                "For many people, a common goal is below 130/80 if clinically appropriate.",
                "Track your BP regularly and compare it to your goal.",
                "Regular feedback supports better decisions.",
            ),
            "Expert": _mk_answer(
                "Lower blood pressure is strongly associated with lower cardiovascular risk over time.",
                "Review the AHA blood pressure chart and discuss what applies to you.",
                "Evidence-based targets support safer and more effective treatment plans.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "Do I really need medication?",
        behavioral_core="MA",
        default_conditions=["HT"],
        links=["BP", "MED_ADH"],
        answers={
            "Listener": _mk_answer(
                "It’s okay to feel unsure. Many people ask this.",
                "Talk to your doctor about how meds fit your overall plan.",
                "Personalized plans reduce confusion.",
            ),
            "Motivator": _mk_answer(
                "Medication is one way to protect your heart—like walking or eating well.",
                "Pair taking your med with a daily habit (like brushing your teeth).",
                "Habit pairing builds consistency.",
            ),
            "Director": _mk_answer(
                "Medications are often started if lifestyle changes alone don’t lower BP enough—or if risk is high.",
                "Follow up in about 4 weeks (or as directed) to evaluate progress.",
                "Your needs can change as your numbers change.",
            ),
            "Expert": _mk_answer(
                "Many people do best with a combination of lifestyle and medication tailored to their risk profile.",
                "Review benefits and potential side effects with your provider.",
                "Informed patients tend to do better with long-term adherence and safety.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "What can I do besides taking medication?",
        behavioral_core="PC",
        default_conditions=["HT"],
        links=["LIFES_ESSENTIAL_8", "MYLIFECHECK", "DASH", "FITNESS"],
        answers={
            "Listener": _mk_answer(
                "It’s great that you want to take action!",
                "Choose one area to start: food, movement, sleep, or stress.",
                "Starting small makes change more manageable.",
            ),
            "Motivator": _mk_answer(
                "Your body can respond quickly to healthy habits.",
                "Walk 10 minutes after lunch each day this week.",
                "Consistency builds confidence.",
            ),
            "Director": _mk_answer(
                "Try DASH-style eating, reduce sodium, increase activity, and work toward a healthy weight if needed.",
                "Track sodium for 3 days.",
                "Awareness is the first step to improvement.",
            ),
            "Expert": _mk_answer(
                "Lifestyle changes can meaningfully reduce blood pressure for many people.",
                "Use Life’s Essential 8 / My Life Check to pick the highest-impact next step.",
                "It connects daily behaviors to long-term cardiovascular outcomes.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "What kind of diet should I follow?",
        behavioral_core="NUT",
        default_conditions=["HT"],
        links=["DASH"],
        answers={
            "Listener": _mk_answer(
                "Choosing what to eat can feel confusing. You’re not alone.",
                "Keep a simple food journal for 3 days.",
                "Reflection builds insight.",
            ),
            "Motivator": _mk_answer(
                "Small food swaps can lead to big results.",
                "Choose one low-salt snack to try this week.",
                "Starting with snacks is manageable.",
            ),
            "Director": _mk_answer(
                "The DASH plan emphasizes fruits, vegetables, whole grains, and low-fat dairy while reducing sodium.",
                "Add one fruit or veggie to each meal.",
                "Gradual changes lead to lasting habits.",
            ),
            "Expert": _mk_answer(
                "DASH is strongly supported by evidence for lowering BP and improving heart health.",
                "Review AHA DASH resources and pick 1–2 changes to implement first.",
                "Evidence-based tools reduce guesswork and help adherence.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "Will I have high blood pressure forever?",
        behavioral_core="PC",
        default_conditions=["HT"],
        links=["BP"],
        answers={
            "Listener": _mk_answer(
                "That’s a common fear—but there’s hope.",
                "Ask your doctor if your pattern is reversible or controllable and what would make the biggest difference.",
                "It opens the door for shared planning.",
            ),
            "Motivator": _mk_answer(
                "You can improve your numbers—many people do!",
                "Celebrate any drop in BP, even a few points.",
                "Every step helps your heart.",
            ),
            "Director": _mk_answer(
                "BP may not go away completely, but it can often be controlled.",
                "Stick with your plan for 3 months, then reassess with your clinician.",
                "Change takes time to show results.",
            ),
            "Expert": _mk_answer(
                "Long-term control often comes from the right combination of lifestyle, monitoring, and medication when needed.",
                "Use a tracker to follow trends and bring them to visits.",
                "Trend-based care supports safer, more precise adjustments.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "How can I track my blood pressure at home?",
        behavioral_core="SY",
        default_conditions=["HT"],
        links=["BP_CHART"],
        answers={
            "Listener": _mk_answer(
                "It can be overwhelming at first, but you’re not alone.",
                "Write down your readings in a simple notebook or note app.",
                "It helps you notice patterns over time.",
            ),
            "Motivator": _mk_answer(
                "Tracking gives you control over your progress.",
                "Celebrate streaks of consistent tracking.",
                "Momentum builds motivation.",
            ),
            "Director": _mk_answer(
                "Take readings morning and evening, seated and rested (unless your clinician advises otherwise).",
                "Set calendar alerts for your BP checks.",
                "Routine readings give more reliable data.",
            ),
            "Expert": _mk_answer(
                "Technique matters: correct cuff size, arm supported at heart level, avoid caffeine/exercise right before measuring.",
                "Review AHA guidance on correct BP technique and confirm your cuff accuracy at a visit.",
                "Accurate technique = trustworthy numbers for decisions.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "Can stress really affect my blood pressure?",
        behavioral_core="PC",
        default_conditions=["HT"],
        links=["STRESS"],
        answers={
            "Listener": _mk_answer(
                "Yes, and life can be stressful—we get it.",
                "Identify one stressor you can reduce this week.",
                "Small wins reduce overall tension.",
            ),
            "Motivator": _mk_answer(
                "Taking care of your mind supports your heart.",
                "Try a 5-minute guided breathing session daily for a week.",
                "It can lower arousal and support healthier BP routines.",
            ),
            "Director": _mk_answer(
                "Chronic stress can push BP higher and also affects sleep, diet, and activity.",
                "Create a wind-down routine before bed.",
                "Better sleep supports better BP control.",
            ),
            "Expert": _mk_answer(
                "Mind-body strategies (like mindfulness and relaxation training) can support BP control for some people.",
                "Build stress reduction into weekly goals alongside diet and activity.",
                "Long-term, it supports lower overall cardiovascular risk.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "What’s a dangerous blood pressure level?",
        behavioral_core="HL",
        default_conditions=["HT"],
        links=["BP_CHART"],
        answers={
            "Listener": _mk_answer(
                "It’s scary not knowing what’s too high.",
                "Learn your BP zones using a chart and keep it handy.",
                "It helps you recognize when to seek help.",
            ),
            "Motivator": _mk_answer(
                "Knowing your numbers gives you power—not fear.",
                "Practice reading and interpreting your monitor with your chart.",
                "You can respond quickly and calmly.",
            ),
            "Director": _mk_answer(
                "A very high reading (like 180/120 or higher), especially with symptoms, can be an emergency.",
                "Program emergency contact numbers in your phone and ask your clinician what to do for your situation.",
                "Preparation helps you act fast if needed.",
            ),
            "Expert": _mk_answer(
                "Hypertension stages and crisis guidance are based on ranges and symptoms; individualized plans matter.",
                "Review your BP history with your clinician to define your red-flag plan.",
                "Knowing trends informs safe treatment decisions.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "Is low blood pressure a problem too?",
        behavioral_core="SY",
        default_conditions=["HT"],
        links=["BP_CHART"],
        answers={
            "Listener": _mk_answer(
                "Yes—it can make you feel dizzy, tired, or weak.",
                "Note symptoms whenever you take readings.",
                "It helps your care team adjust treatment safely.",
            ),
            "Motivator": _mk_answer(
                "It’s okay to ask questions if something doesn’t feel right.",
                "Bring your questions and symptom notes to your next visit.",
                "Shared decisions lead to better care.",
            ),
            "Director": _mk_answer(
                "If BP is too low—especially on meds—your clinician may adjust timing or dose.",
                "Log symptom timing and medication timing for 1–2 weeks.",
                "Timing patterns can reveal the fix.",
            ),
            "Expert": _mk_answer(
                "Low BP can be normal for some but concerning if it causes symptoms, falls, or fainting.",
                "Track hydration and review meds with your clinician if symptoms persist.",
                "Safety comes first—especially when standing/dizziness is present.",
            ),
        },
    ),
    _mk_question(
        "HTN",
        "How do I talk to my family about my high blood pressure?",
        behavioral_core="PC",
        default_conditions=["HT"],
        links=["BP", "LIFES_ESSENTIAL_8"],
        answers={
            "Listener": _mk_answer(
                "Talking about your health takes courage.",
                "Start with one trusted family member.",
                "Support makes healthy changes easier.",
            ),
            "Motivator": _mk_answer(
                "You might inspire them to check their BP too!",
                "Invite a loved one to join you in cooking or walking.",
                "Shared habits stick better.",
            ),
            "Director": _mk_answer(
                "Use simple language: “I’m working on my BP so I can stay healthy.”",
                "Share one goal like reducing salt together.",
                "Shared goals create buy-in.",
            ),
            "Expert": _mk_answer(
                "Family patterns matter—risk factors often run in families.",
                "Encourage them to learn BP basics and check their numbers.",
                "Prevention can start with one conversation.",
            ),
        },
    ),
]

HTN_QUESTIONS = assign_ids(HTN_QUESTIONS, category="HTN", prefix="HTN", start=1)


# -----------------------------
# Future placeholders (safe imports even if empty)
# -----------------------------
HF_QUESTIONS: List[Dict[str, Any]] = []
CAD_QUESTIONS: List[Dict[str, Any]] = []
AFIB_QUESTIONS: List[Dict[str, Any]] = []
STROKE_QUESTIONS: List[Dict[str, Any]] = []
DIABETES_QUESTIONS: List[Dict[str, Any]] = []


QUESTION_BANK: List[Dict[str, Any]] = (
    CKM_QUESTIONS
    + HTN_QUESTIONS
    + HF_QUESTIONS
    + CAD_QUESTIONS
    + AFIB_QUESTIONS
    + STROKE_QUESTIONS
    + DIABETES_QUESTIONS
)


# -----------------------------
# Public API (used by signatures_engine.py)
# -----------------------------
def list_categories() -> List[str]:
    return sorted({(q.get("category") or "UNKNOWN").upper() for q in QUESTION_BANK})


def list_question_summaries(category: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Returns: [(id, category, question), ...]
    If category is provided, filters case-insensitively.
    """
    cat = category.strip().upper() if category else None
    items: List[Tuple[str, str, str]] = []
    for q in QUESTION_BANK:
        qcat = (q.get("category") or "").upper()
        if cat and qcat != cat:
            continue
        items.append((q.get("id", ""), q.get("category", ""), q.get("question", "")))
    return items


def filter_questions_by_category(category: str) -> List[Dict[str, Any]]:
    cat = (category or "").strip().upper()
    return [q for q in QUESTION_BANK if (q.get("category") or "").upper() == cat]


def get_question(question_id: str) -> Optional[Dict[str, Any]]:
    qid = (question_id or "").strip().upper()
    for q in QUESTION_BANK:
        if (q.get("id") or "").upper() == qid:
            return q
    return None


def validate_question_bank(raise_on_error: bool = False) -> List[str]:
    issues: List[str] = []
    seen = set()

    for i, q in enumerate(QUESTION_BANK):
        qid = q.get("id", "")
        if not qid:
            issues.append(f"[{i}] Missing id")
        elif qid in seen:
            issues.append(f"Duplicate id: {qid}")
        else:
            seen.add(qid)

        if not q.get("category"):
            issues.append(f"{qid}: Missing category")
        if not q.get("question"):
            issues.append(f"{qid}: Missing question")

        answers = q.get("answers", {})
        for persona in PERSONAS:
            if persona not in answers:
                issues.append(f"{qid}: Missing persona answer: {persona}")

    if raise_on_error and issues:
        raise ValueError("Question bank validation failed:\n" + "\n".join(issues))
    return issues



