# questions.py
"""
Signatures Question Bank (LLM-friendly)

Design goals
- Human-editable question packs (copy/paste safe)
- Auto-generated stable IDs per pack (e.g., SLEEP-01)
- Clean -1/0/+1 engagement driver scheme
- Tighter validation + auto-fix hints (non-fatal by default)
- “LLM-friendly” structure: each question is a compact, self-contained object
  with explicit tags + persona responses + safety + next steps + trusted sources.

AHA sources used heavily (preferred).
Key AHA hubs referenced:
- Sleep hub: https://www.heart.org/en/healthy-living/healthy-lifestyle/sleep
- Sleep & heart health: https://www.heart.org/en/health-topics/sleep-disorders/sleep-and-heart-health
- Sleep apnea & heart disease/stroke: https://www.heart.org/en/health-topics/sleep-disorders/sleep-apnea-and-heart-disease-stroke
- Life’s Essential 8: https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8
- Cardiac rehab: https://www.heart.org/en/health-topics/cardiac-rehab
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Types / constants
# -----------------------------

PERSONAS: Tuple[str, ...] = ("listener", "motivator", "director", "expert")

# Engagement drivers support -1/0/+1 cleanly
# -1 = not present, 0 = unknown, +1 = present
EngagementDrivers = Dict[str, int]

# Signatures tags (keep this stable + compact for LLM routing)
SignatureTags = Dict[str, Any]

Question = Dict[str, Any]
QuestionBank = Dict[str, Question]


# -----------------------------
# Helper utilities
# -----------------------------

def clamp_driver(v: Any) -> int:
    """Coerce engagement driver values into {-1,0,1}."""
    try:
        iv = int(v)
    except Exception:
        return 0
    if iv < -1:
        return -1
    if iv > 1:
        return 1
    return iv


def normalize_engagement_drivers(drivers: Any) -> EngagementDrivers:
    """Ensure engagement_drivers is a dict[str,int] with values -1/0/1."""
    if not isinstance(drivers, dict):
        return {}
    out: EngagementDrivers = {}
    for k, v in drivers.items():
        if not isinstance(k, str) or not k.strip():
            continue
        out[k.strip().upper()] = clamp_driver(v)
    return out


def ensure_persona_responses(responses: Any) -> Dict[str, str]:
    """Ensure all 4 personas exist; auto-fill missing with safe generic placeholders."""
    safe_default = "I’m here with you. Share what matters most, and we’ll take one step at a time."
    if not isinstance(responses, dict):
        responses = {}

    out: Dict[str, str] = {}
    for p in PERSONAS:
        text = responses.get(p, "")
        if not isinstance(text, str) or not text.strip():
            # Auto-fill
            if p == "director":
                text = "Here’s a simple next step: pick one small action you can do today, and track it for a week."
            elif p == "expert":
                text = "Here’s the evidence-based view: consistent small improvements in sleep, activity, and risk factors reduce cardiovascular risk over time."
            else:
                text = safe_default
        out[p] = text.strip()
    return out


def ensure_list(x: Any) -> List[str]:
    """Convert to list[str] safely."""
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str) and x.strip():
        return [x.strip()]
    return []


def slug_upper(s: str) -> str:
    return "".join(ch for ch in s.upper() if ch.isalnum() or ch in ("_", "-")).strip("-_")


def build_id(pack_code: str, idx_1based: int) -> str:
    return f"{pack_code}-{idx_1based:02d}"


def all_categories(question_bank: QuestionBank) -> List[str]:
    return sorted({q.get("category", "").strip() for q in question_bank.values() if q.get("category", "").strip()})


def list_categories(question_bank: QuestionBank) -> List[str]:
    """Alias kept for backwards-compat with signatures_engine imports."""
    return all_categories(question_bank)


def list_question_summaries(
    question_bank: QuestionBank,
    category: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, str]]:
    cat = category.strip().upper() if isinstance(category, str) and category.strip() else None
    items: List[Dict[str, str]] = []
    for qid, q in sorted(question_bank.items(), key=lambda kv: kv[0]):
        if cat and q.get("category", "").strip().upper() != cat:
            continue
        items.append(
            {
                "id": qid,
                "category": q.get("category", ""),
                "question": q.get("question", ""),
                "title": q.get("title", q.get("question", "")),
            }
        )
        if limit and len(items) >= limit:
            break
    return items


def get_question_by_id(question_bank: QuestionBank, qid: str) -> Optional[Question]:
    if not isinstance(qid, str) or not qid.strip():
        return None
    return question_bank.get(qid.strip().upper())


def search_questions(
    question_bank: QuestionBank,
    query: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, str]]:
    """Simple search (question/title/tags)."""
    if not isinstance(query, str) or not query.strip():
        return []
    q = query.strip().lower()
    cat = category.strip().upper() if isinstance(category, str) and category.strip() else None

    hits: List[Tuple[int, str, Question]] = []
    for qid, item in question_bank.items():
        if cat and item.get("category", "").strip().upper() != cat:
            continue

        hay = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("question", "")),
                " ".join(item.get("keywords", []) or []),
                " ".join((item.get("signatures", {}) or {}).get("behavioral_core", []) or []),
                " ".join((item.get("signatures", {}) or {}).get("condition_modifiers", []) or []),
                " ".join(list(((item.get("signatures", {}) or {}).get("engagement_drivers", {}) or {}).keys())),
            ]
        ).lower()

        if q in hay:
            # naive score: shorter distance / more occurrences
            score = hay.count(q)
            hits.append((score, qid, item))

    hits.sort(key=lambda t: (-t[0], t[1]))
    out: List[Dict[str, str]] = []
    for _, qid, item in hits[: max(1, int(limit))]:
        out.append({"id": qid, "category": item.get("category", ""), "question": item.get("question", "")})
    return out


# -----------------------------
# Validation (tighter + helpful)
# -----------------------------

@dataclass
class BankIssue:
    level: str  # "warn" | "error"
    qid: str
    message: str
    hint: str = ""


def validate_question_bank(
    question_bank: QuestionBank,
    raise_on_error: bool = False,
) -> List[BankIssue]:
    issues: List[BankIssue] = []

    for qid, q in question_bank.items():
        # Required fields
        if not q.get("question"):
            issues.append(
                BankIssue(
                    level="error",
                    qid=qid,
                    message="missing 'question' text",
                    hint="Set q['question'] to a non-empty string.",
                )
            )

        # Persona responses
        resp = q.get("responses", {})
        missing = [p for p in PERSONAS if not isinstance(resp, dict) or not resp.get(p)]
        if missing:
            issues.append(
                BankIssue(
                    level="warn",
                    qid=qid,
                    message=f"missing persona responses: {', '.join(missing)}",
                    hint="Provide responses['listener'|'motivator'|'director'|'expert'] or rely on auto-fill.",
                )
            )

        # Signatures tags sanity
        sig = q.get("signatures", {})
        if not isinstance(sig, dict):
            issues.append(
                BankIssue(
                    level="warn",
                    qid=qid,
                    message="signatures is not a dict",
                    hint="Set q['signatures'] = {'behavioral_core': [...], 'condition_modifiers': [...], 'engagement_drivers': {...}}",
                )
            )
        else:
            ed = sig.get("engagement_drivers", {})
            if isinstance(ed, dict):
                bad_vals = [k for k, v in ed.items() if clamp_driver(v) != int(v) if isinstance(v, int)]
                # (We mostly clamp; just hint if outside range.)
                out_of_range = [k for k, v in ed.items() if isinstance(v, int) and v not in (-1, 0, 1)]
                if out_of_range:
                    issues.append(
                        BankIssue(
                            level="warn",
                            qid=qid,
                            message=f"engagement_drivers values not in -1/0/1 for: {', '.join(out_of_range)}",
                            hint="Use -1 (not present), 0 (unknown), +1 (present). Values will be clamped automatically.",
                        )
                    )

        # Safety blocks should exist (even if empty lists)
        if "security_rules" not in q:
            issues.append(
                BankIssue(
                    level="warn",
                    qid=qid,
                    message="missing security_rules",
                    hint="Add q['security_rules'] = [...] (even if empty).",
                )
            )
        if "action_plans" not in q:
            issues.append(
                BankIssue(
                    level="warn",
                    qid=qid,
                    message="missing action_plans",
                    hint="Add q['action_plans'] = [...] (even if empty).",
                )
            )

    if raise_on_error:
        errs = [i for i in issues if i.level == "error"]
        if errs:
            msg = "\n".join(f"{i.qid}: {i.message} | {i.hint}" for i in errs[:25])
            raise ValueError(f"Question bank validation failed:\n{msg}")

    return issues


# -----------------------------
# PACKS: edit these safely
# (No IDs here. IDs are generated.)
# -----------------------------

def _aha_source(title: str, url: str) -> Dict[str, str]:
    return {"publisher": "American Heart Association", "title": title, "url": url}


PACKS: Dict[str, Dict[str, Any]] = {
    # -------------------------
    # SLEEP PACK (10)
    # -------------------------
    "SLEEP": {
        "category": "SLEEP",
        "title": "Sleep & Heart/Brain Health",
        "source_defaults": [
            _aha_source("Sleep (Healthy Living)", "https://www.heart.org/en/healthy-living/healthy-lifestyle/sleep"),
            _aha_source("Sleep Disorders and Heart Health", "https://www.heart.org/en/health-topics/sleep-disorders/sleep-and-heart-health"),
            _aha_source("Sleep Apnea and Heart Disease/Stroke", "https://www.heart.org/en/health-topics/sleep-disorders/sleep-apnea-and-heart-disease-stroke"),
            _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
        ],
        "questions": [
            {
                "question": "How much sleep do I actually need for heart and brain health?",
                "keywords": ["sleep duration", "7-9 hours", "fatigue"],
                "signatures": {
                    "behavioral_core": ["SLEEP"],
                    "condition_modifiers": ["CV", "BR"],
                    "engagement_drivers": {"HL": 1, "GO": 0, "PR": 0, "SE": 0},
                },
                "responses": {
                    "listener": "Sleep questions can feel surprisingly personal. Tell me what a “good night” looks like for you right now.",
                    "motivator": "You don’t have to be perfect—small shifts can make a real difference. Let’s aim for one doable improvement this week.",
                    "director": "Most adults do best with 7–9 hours nightly. Pick a consistent wake-up time, then move bedtime earlier by 15 minutes for 1 week.",
                    "expert": "Sleep is part of cardiovascular health (Life’s Essential 8). Short sleep is linked to higher blood pressure and worse cardiometabolic risk.",
                },
                "security_rules": [
                    "If excessive daytime sleepiness is severe (falling asleep while driving) or you have breathing pauses/gasping at night, contact your healthcare professional promptly.",
                ],
                "action_plans": [
                    "Set a consistent wake time for 7 days and track total sleep time.",
                    "Use a simple sleep log: bedtime, wake time, awakenings, caffeine/alcohol timing.",
                ],
            },
            {
                "question": "Why does poor sleep raise blood pressure and heart risk?",
                "keywords": ["blood pressure", "stress hormones", "cardiovascular risk"],
                "signatures": {
                    "behavioral_core": ["SLEEP"],
                    "condition_modifiers": ["HTN", "CKM"],
                    "engagement_drivers": {"HL": 1, "EX": 1, "TR": 0},
                },
                "responses": {
                    "listener": "It makes sense to want the “why,” especially when you’re trying hard.",
                    "motivator": "This isn’t about blame—it's about leverage. Improving sleep is one of the highest-impact changes you can make.",
                    "director": "Start by protecting a 7–9 hour sleep window and reducing late caffeine/alcohol. Recheck home BP after 2–3 weeks.",
                    "expert": "Poor sleep affects autonomic balance, inflammation, appetite hormones, and behaviors that influence BP, weight, and glucose.",
                },
                "security_rules": [
                    "If you have very high BP readings or symptoms (chest pain, severe headache, shortness of breath), seek urgent care per your clinician’s plan.",
                ],
                "action_plans": [
                    "Pair sleep improvement with home BP tracking (same time daily).",
                    "Build a 30–60 minute wind-down routine (dim lights, screens off, calming activity).",
                ],
            },
            {
                "question": "How do I build a bedtime routine I can stick with?",
                "keywords": ["routine", "habits", "wind-down"],
                "signatures": {
                    "behavioral_core": ["HB"],  # habit-building
                    "condition_modifiers": ["SLEEP"],
                    "engagement_drivers": {"PR": 1, "GO": 1, "SE": 1, "HL": 0},
                },
                "responses": {
                    "listener": "If your days are packed, routines can feel impossible. What usually gets in the way—time, stress, screens, or something else?",
                    "motivator": "You’re not starting from zero—you’re building a pattern. Even a 10-minute routine counts.",
                    "director": "Pick 3 steps: (1) same wake time, (2) screens off 30 minutes before bed, (3) relaxing cue like reading or stretching. Do it 5 nights.",
                    "expert": "Behavior change works best when cues are consistent. A short, repeatable routine is more effective than a complicated plan.",
                },
                "security_rules": [
                    "Avoid sedatives, sleep meds, or supplements without discussing them with your healthcare professional—especially if you have heart or breathing conditions.",
                ],
                "action_plans": [
                    "Create a “minimum viable” routine (10 minutes) and a “full” routine (30 minutes).",
                    "Use phone settings: scheduled Do Not Disturb + bedtime reminder.",
                ],
            },
            {
                "question": "Is napping good or bad for my heart health?",
                "keywords": ["naps", "daytime sleepiness"],
                "signatures": {
                    "behavioral_core": ["SLEEP"],
                    "condition_modifiers": ["CV"],
                    "engagement_drivers": {"HL": 1, "GO": 0, "PR": 0},
                },
                "responses": {
                    "listener": "Napping can feel like a relief—or it can mess with your night sleep. What happens for you after a nap?",
                    "motivator": "If a nap helps you function, we can make it work—without derailing nighttime sleep.",
                    "director": "Try a short nap (10–20 minutes) earlier in the day. Avoid late-afternoon naps that push bedtime later.",
                    "expert": "Short naps may improve alertness. Long/late naps can reduce sleep drive and worsen insomnia patterns.",
                },
                "security_rules": [
                    "If you need frequent long naps due to exhaustion, consider evaluation for sleep apnea, anemia, medication effects, depression, or thyroid issues.",
                ],
                "action_plans": [
                    "Test a 2-week nap experiment: note nap length/time and nighttime sleep quality.",
                    "If napping is daily and >45–60 minutes, ask your clinician about screening for sleep disorders.",
                ],
            },
            {
                "question": "Could I have sleep apnea—and why does it matter?",
                "keywords": ["sleep apnea", "snoring", "breathing pauses"],
                "signatures": {
                    "behavioral_core": ["SLEEP"],
                    "condition_modifiers": ["OSA", "HTN", "AF", "STROKE"],
                    "engagement_drivers": {"HL": 1, "PR": 1, "TR": 0},
                },
                "responses": {
                    "listener": "If you’re worried about apnea, you’re not overreacting. What symptoms do you notice—snoring, gasping, morning headaches, daytime sleepiness?",
                    "motivator": "If apnea is present, treating it can be a game-changer for energy and risk reduction.",
                    "director": "If you snore loudly, have pauses in breathing, or feel very sleepy during the day, ask for a sleep evaluation (home test or lab study).",
                    "expert": "Sleep apnea is linked to higher rates of high blood pressure, stroke, and coronary artery disease; evaluation and treatment can improve outcomes.",
                },
                "security_rules": [
                    "If you have severe daytime sleepiness (e.g., falling asleep while driving) or nighttime choking/gasping with breathlessness, seek prompt medical evaluation.",
                ],
                "action_plans": [
                    "Screen yourself: note snoring, witnessed apneas, morning headaches, daytime sleepiness.",
                    "Ask your clinician about sleep apnea testing and treatment options (e.g., CPAP) if indicated.",
                ],
            },
            {
                "question": "What should I do if I can’t fall asleep (insomnia)?",
                "keywords": ["insomnia", "sleep onset", "racing thoughts"],
                "signatures": {
                    "behavioral_core": ["SLEEP"],
                    "condition_modifiers": ["ANX", "DEP"],
                    "engagement_drivers": {"SE": 1, "HL": 1, "PR": 0},
                },
                "responses": {
                    "listener": "Lying awake can be frustrating. When does it happen most—work nights, weekends, or every night?",
                    "motivator": "You can train your sleep again. It’s a skill, not a character flaw.",
                    "director": "Keep the bed for sleep. If you’re awake >20 minutes, get up and do a quiet activity, then return when sleepy. Keep wake time consistent.",
                    "expert": "Behavioral approaches (like CBT-I principles) often outperform quick fixes and avoid medication side effects.",
                },
                "security_rules": [
                    "If insomnia is severe, persistent, or linked to depression/anxiety symptoms or substance use, contact a healthcare professional.",
                ],
                "action_plans": [
                    "Start a 2-week sleep diary and identify patterns (caffeine, screens, stress).",
                    "Try stimulus control + consistent wake time before adding supplements/medications.",
                ],
            },
            {
                "question": "Does caffeine or alcohol affect my sleep and heart health?",
                "keywords": ["caffeine", "alcohol", "sleep quality"],
                "signatures": {
                    "behavioral_core": ["NUT", "SLEEP"],
                    "condition_modifiers": ["HTN", "AF"],
                    "engagement_drivers": {"HL": 1, "PR": 1, "GO": 0},
                },
                "responses": {
                    "listener": "A lot of people use caffeine to cope with fatigue—totally understandable. What’s your usual timing?",
                    "motivator": "A small timing tweak can pay off fast—this is a “high return” change.",
                    "director": "Stop caffeine 6–8 hours before bed. Avoid alcohol near bedtime; it can fragment sleep. Track sleep quality for 2 weeks.",
                    "expert": "Both caffeine and alcohol can change sleep architecture and worsen awakenings; for some people they also trigger arrhythmias.",
                },
                "security_rules": [
                    "If you have palpitations, dizziness, or chest discomfort after caffeine/alcohol, discuss this with your healthcare professional.",
                ],
                "action_plans": [
                    "Create a personal cut-off time for caffeine (e.g., 1–2 pm).",
                    "If you drink alcohol, keep it modest and earlier; watch how it changes sleep and next-day BP.",
                ],
            },
            {
                "question": "How does stress and mental health affect sleep—and what can I do tonight?",
                "keywords": ["stress", "anxiety", "relaxation"],
                "signatures": {
                    "behavioral_core": ["ST", "SLEEP"],
                    "condition_modifiers": ["ANX", "DEP"],
                    "engagement_drivers": {"SE": 1, "PR": 1, "HL": 0},
                },
                "responses": {
                    "listener": "If your mind won’t shut off, you’re not alone. What time do you usually feel the stress spike—right at bedtime or earlier?",
                    "motivator": "You can’t delete stress, but you *can* lower the volume—one small practice at a time.",
                    "director": "Try a 5-minute breathing exercise, then a short body scan. Keep lights low and avoid news/social media before bed.",
                    "expert": "Downshifting the nervous system (breathing, mindfulness) can improve sleep latency and reduce nighttime arousal.",
                },
                "security_rules": [
                    "If you’re experiencing panic, severe depression, or thoughts of self-harm, seek urgent help from local emergency services or a crisis line.",
                ],
                "action_plans": [
                    "Use a “brain dump” note: write worries + one next action, then close the notebook.",
                    "Practice the same calming technique nightly for 1–2 weeks to build a conditioned response.",
                ],
            },
            {
                "question": "How do I track sleep in a simple way (without overthinking it)?",
                "keywords": ["tracking", "sleep diary", "wearables"],
                "signatures": {
                    "behavioral_core": ["SY"],  # self-tracking
                    "condition_modifiers": ["SLEEP"],
                    "engagement_drivers": {"GO": 1, "HL": 1, "PR": 0},
                },
                "responses": {
                    "listener": "Tracking can help—or it can add pressure. Which one has it been for you?",
                    "motivator": "Think of tracking as a flashlight, not a grade. We’re looking for patterns, not perfection.",
                    "director": "Track only 3 things for 2 weeks: bedtime, wake time, and how rested you feel (0–10). Add caffeine/alcohol timing if needed.",
                    "expert": "Simple metrics are often enough to guide behavior change and identify when clinical evaluation is needed.",
                },
                "security_rules": [
                    "If trackers increase anxiety or worsen sleep (“orthosomnia”), simplify or stop tracking and focus on routine instead.",
                ],
                "action_plans": [
                    "Use a 2-week micro-log: total sleep time + energy rating.",
                    "If using a wearable, focus on trends (weekly averages) not nightly fluctuations.",
                ],
            },
            {
                "question": "When should I talk to my doctor about sleep problems?",
                "keywords": ["when to seek help", "sleep disorder"],
                "signatures": {
                    "behavioral_core": ["PC"],  # preventive care / escalation
                    "condition_modifiers": ["SLEEP", "CV", "BR"],
                    "engagement_drivers": {"PR": 1, "HL": 1, "TR": 0},
                },
                "responses": {
                    "listener": "It’s okay to ask for help—sleep problems are common and treatable.",
                    "motivator": "Getting support sooner can save months of struggle. You deserve relief and better energy.",
                    "director": "Talk to your clinician if sleep issues last >3 months, impair daytime function, or include loud snoring, apneas, or morning headaches.",
                    "expert": "Persistent insomnia and sleep disorders are linked to cardiometabolic risk; evaluation can identify treatable causes like apnea.",
                },
                "security_rules": [
                    "Seek prompt evaluation for dangerous sleepiness (falling asleep while driving), breathing pauses, or severe symptoms affecting safety.",
                ],
                "action_plans": [
                    "Bring a 2-week sleep log to your appointment.",
                    "Ask about screening for sleep apnea, insomnia treatment options, and medication review.",
                ],
            },
        ],
    },

    # -------------------------
    # REHAB PACK (10) - Cardiac Rehabilitation
    # -------------------------
    "REHAB": {
        "category": "REHAB",
        "title": "Cardiac Rehab & Recovery",
        "source_defaults": [
            _aha_source("Cardiac Rehab", "https://www.heart.org/en/health-topics/cardiac-rehab"),
            _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
        ],
        "questions": [
            {
                "question": "What is cardiac rehabilitation and who is it for?",
                "keywords": ["cardiac rehab", "supervised program", "recovery"],
                "signatures": {
                    "behavioral_core": ["PA", "PC"],
                    "condition_modifiers": ["CAD", "HF", "POST_MI", "POST_PCI", "POST_CABG"],
                    "engagement_drivers": {"HL": 1, "TR": 0, "SE": 0},
                },
                "responses": {
                    "listener": "A new program can feel like a lot. What’s your biggest question—safety, time, cost, or what to expect?",
                    "motivator": "Rehab is one of the strongest “comeback” tools—structured support helps you rebuild confidence and stamina.",
                    "director": "Cardiac rehab is a medically supervised program (exercise + education + risk-factor coaching). Ask your cardiologist for a referral.",
                    "expert": "AHA describes cardiac rehab as designed to improve cardiovascular health after events like heart attack, heart failure, angioplasty, or surgery.",
                },
                "security_rules": [
                    "If you develop chest pain, severe shortness of breath, fainting, or new neurologic symptoms during activity, stop and seek urgent medical care.",
                ],
                "action_plans": [
                    "Ask: “Am I eligible for cardiac rehab?” and “Can you place the referral today?”",
                    "If travel is hard, ask about home-based or hybrid rehab options (if available).",
                ],
            },
            {
                "question": "How do I enroll in cardiac rehab and what happens at the first visit?",
                "keywords": ["enroll", "referral", "intake"],
                "signatures": {
                    "behavioral_core": ["PC", "HB"],
                    "condition_modifiers": ["CAD", "HF"],
                    "engagement_drivers": {"PR": 1, "SE": 1, "HL": 0},
                },
                "responses": {
                    "listener": "Starting something new can be stressful. What would make the first visit feel easier?",
                    "motivator": "You’re taking a powerful step—showing up is the hardest part, and you’re already doing it.",
                    "director": "Call the rehab program after referral. Bring your med list, discharge summary, and questions. Expect baseline vitals + activity assessment.",
                    "expert": "Programs typically assess risk, set goals, and tailor exercise prescriptions based on your condition and symptoms.",
                },
                "security_rules": [
                    "Bring a current medication list; do not change heart meds for rehab without clinician guidance.",
                ],
                "action_plans": [
                    "Prepare a one-page summary: diagnosis/procedure, meds, symptoms, goals.",
                    "Write 3 questions (e.g., target HR, safe intensity, warning signs).",
                ],
            },
            {
                "question": "Is exercise safe for me after a heart event—and how hard should I push?",
                "keywords": ["safe exercise", "intensity", "heart rate"],
                "signatures": {
                    "behavioral_core": ["PA"],
                    "condition_modifiers": ["CAD", "HF", "AF"],
                    "engagement_drivers": {"SE": 1, "PR": 1, "HL": 0},
                },
                "responses": {
                    "listener": "That fear is real—many people worry about overdoing it after a scare.",
                    "motivator": "You can rebuild safely. The goal isn’t to push hard—it’s to progress steadily.",
                    "director": "Start low and go slow. Use the “talk test” (you can talk but not sing). Follow rehab targets for HR/BP and symptoms.",
                    "expert": "Supervised rehab individualizes intensity and improves functional capacity while monitoring safety markers.",
                },
                "security_rules": [
                    "Stop immediately for chest pain/pressure, severe shortness of breath, dizziness, or fainting; contact your healthcare professional or emergency services as appropriate.",
                ],
                "action_plans": [
                    "Ask rehab staff for your personal intensity zone and symptom action plan.",
                    "Track exertion (RPE 0–10) and symptoms during/after sessions.",
                ],
            },
            {
                "question": "What if I’m too tired, depressed, or anxious to do rehab?",
                "keywords": ["fatigue", "depression", "anxiety", "motivation"],
                "signatures": {
                    "behavioral_core": ["ST", "PC"],
                    "condition_modifiers": ["HF", "POST_EVENT"],
                    "engagement_drivers": {"TR": 1, "SE": 1, "HL": 0},
                },
                "responses": {
                    "listener": "That’s not weakness—it’s a common recovery experience. What’s the hardest part right now: mood, energy, or fear?",
                    "motivator": "You don’t need to feel “ready” to start. Rehab can help you *become* ready.",
                    "director": "Tell the rehab team how you’re feeling. Start with shorter sessions and add support (counseling, social work, group).",
                    "expert": "Cardiac rehab includes education and psychosocial support; mood and fatigue are expected targets, not barriers.",
                },
                "security_rules": [
                    "If you have severe depression or thoughts of self-harm, seek urgent help from local emergency services or a crisis line.",
                ],
                "action_plans": [
                    "Set a “minimum attendance” goal (e.g., 1 session this week) and reassess.",
                    "Ask about behavioral health support integrated into rehab (if available).",
                ],
            },
            {
                "question": "How long does cardiac rehab last and what results should I expect?",
                "keywords": ["duration", "outcomes", "progress"],
                "signatures": {
                    "behavioral_core": ["GO", "PA"],
                    "condition_modifiers": ["CAD", "HF"],
                    "engagement_drivers": {"GO": 1, "HL": 1, "SE": 0},
                },
                "responses": {
                    "listener": "It helps to know what the road looks like. What outcome matters most to you—energy, confidence, fewer symptoms, or risk reduction?",
                    "motivator": "Progress shows up faster than you think—especially in stamina and confidence.",
                    "director": "Many programs run for weeks to months with multiple sessions per week. Track simple wins: minutes walked, symptoms, BP response.",
                    "expert": "Rehab aims to improve cardiovascular fitness, risk-factor control, and self-management skills after cardiac events or procedures.",
                },
                "security_rules": [
                    "If symptoms worsen during the program (new swelling, rapid weight gain, increasing breathlessness), contact your clinician promptly.",
                ],
                "action_plans": [
                    "Pick 2 outcomes to track (e.g., 6-minute walk distance or weekly minutes active, plus BP).",
                    "Ask for a mid-program recheck and a discharge home plan.",
                ],
            },
            {
                "question": "Can I do cardiac rehab at home (home-based or hybrid rehab)?",
                "keywords": ["home-based rehab", "hybrid", "telehealth"],
                "signatures": {
                    "behavioral_core": ["PA", "SY"],
                    "condition_modifiers": ["ACCESS"],
                    "engagement_drivers": {"ID": 1, "SE": 1, "PR": 0},
                },
                "responses": {
                    "listener": "If getting to a clinic is hard, you’re not alone. What’s the barrier—time, transportation, cost, or caregiving?",
                    "motivator": "You can still make progress at home with the right structure and support.",
                    "director": "Ask your clinician or rehab center about home-based or hybrid options. Use a simple plan: warm-up, walk, cool-down, symptom check.",
                    "expert": "Programs can adapt delivery while keeping the same core goals: safe exercise progression + education + risk-factor management.",
                },
                "security_rules": [
                    "Home exercise should follow your clinician/rehab guidance; stop for chest pain, severe shortness of breath, or dizziness and seek care.",
                ],
                "action_plans": [
                    "Request a written home exercise prescription (frequency, intensity, time, type).",
                    "Use a BP cuff or wearable as advised and log sessions.",
                ],
            },
            {
                "question": "What should I eat during recovery to support my heart?",
                "keywords": ["diet", "nutrition", "recovery"],
                "signatures": {
                    "behavioral_core": ["NUT"],
                    "condition_modifiers": ["CAD", "HF", "HTN", "CKM"],
                    "engagement_drivers": {"HL": 1, "FI": 0, "GO": 0},
                },
                "responses": {
                    "listener": "Food advice can feel overwhelming. What foods do you actually enjoy and have access to?",
                    "motivator": "You don’t need perfection—one better choice per day adds up quickly.",
                    "director": "Aim for a heart-healthy pattern: more fruits/veg, whole grains, lean proteins; limit sodium and ultra-processed foods. Start with one swap.",
                    "expert": "Heart-healthy patterns support BP, cholesterol, and glucose control—core drivers of cardiovascular risk.",
                },
                "security_rules": [
                    "If you have heart failure or kidney disease, follow your clinician’s guidance on sodium and fluids.",
                ],
                "action_plans": [
                    "Pick one nutrition target for 2 weeks (e.g., reduce sodium, add vegetables).",
                    "Use a simple grocery list and check labels for sodium when relevant.",
                ],
            },
            {
                "question": "What warning signs should make me stop exercising and call for help?",
                "keywords": ["warning signs", "chest pain", "shortness of breath"],
                "signatures": {
                    "behavioral_core": ["PC"],
                    "condition_modifiers": ["CAD", "HF", "AF"],
                    "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0},
                },
                "responses": {
                    "listener": "It’s smart to ask—having a plan reduces fear.",
                    "motivator": "Knowing your red flags is empowering. It helps you act quickly and confidently.",
                    "director": "Stop exercise for chest pain/pressure, severe shortness of breath, dizziness/fainting, or new neurologic symptoms. Follow your emergency plan.",
                    "expert": "Safety plans reduce adverse events by ensuring symptoms prompt early evaluation and appropriate escalation.",
                },
                "security_rules": [
                    "Chest pain during exercise: stop immediately and contact your healthcare professional (or emergency services if severe/persistent).",
                ],
                "action_plans": [
                    "Post a “When to Stop” checklist near your exercise area.",
                    "Keep emergency contacts and medications (e.g., nitroglycerin if prescribed) accessible.",
                ],
            },
            {
                "question": "How does cardiac rehab connect with Life’s Essential 8 and prevention long-term?",
                "keywords": ["Life's Essential 8", "prevention", "habits"],
                "signatures": {
                    "behavioral_core": ["PC"],
                    "condition_modifiers": ["CV"],
                    "engagement_drivers": {"GO": 1, "HL": 1, "PR": 1},
                },
                "responses": {
                    "listener": "It’s great you’re thinking long-term. What’s the one habit you want to keep after rehab ends?",
                    "motivator": "Rehab is a launchpad. The goal is to leave with routines you can actually maintain.",
                    "director": "Use rehab to build a weekly plan across Life’s Essential 8: movement, sleep, nutrition, tobacco-free, weight, BP, cholesterol, glucose.",
                    "expert": "Life’s Essential 8 is AHA’s framework for improving and maintaining cardiovascular health across behaviors + clinical factors.",
                },
                "security_rules": [
                    "If you have multiple chronic conditions, coordinate changes (exercise, diet, meds) with your healthcare professionals to avoid conflicting plans.",
                ],
                "action_plans": [
                    "Pick 2 Life’s Essential 8 areas to improve over the next 30 days and track them weekly.",
                    "Ask rehab staff for a post-discharge maintenance plan and follow-up schedule.",
                ],
            },
            {
                "question": "What if I can’t afford rehab or my schedule makes it hard?",
                "keywords": ["cost", "schedule", "barriers"],
                "signatures": {
                    "behavioral_core": ["ACCESS", "PC"],
                    "condition_modifiers": ["SOC"],
                    "engagement_drivers": {"FI": 1, "ID": 0, "TR": 0},
                },
                "responses": {
                    "listener": "That’s a real barrier—and it’s not your fault. What’s the biggest constraint: cost, time, transportation, or work?",
                    "motivator": "If full rehab isn’t possible, we can still build a safe recovery plan—something is always better than nothing.",
                    "director": "Ask about financial assistance, sliding scale, fewer visits, or home-based options. Build a structured walking plan with check-ins.",
                    "expert": "Access barriers are common; alternative delivery models can preserve core rehab benefits when supervised programs aren’t feasible.",
                },
                "security_rules": [
                    "Avoid unsupervised “hard training” after a cardiac event without medical clearance; keep activity gradual and symptom-guided.",
                ],
                "action_plans": [
                    "Request a written home plan + follow-up call schedule if you can’t attend in person.",
                    "Use community options (safe walking spaces, support groups) and track symptoms + vitals as advised.",
                ],
            },
        ],
    },

    "CAD": {
    "category": "CAD",
    "source_defaults": [
        {
            "name": "American Heart Association",
            "label": "AHA",
            "url": "https://www.heart.org/en/health-topics/heart-attack",
        }
    ],
    "questions": [
        {
            "title": "What caused my coronary artery disease?",
            "question": "What caused my coronary artery disease?",
            "keywords": ["cad", "coronary", "atherosclerosis", "risk factors"],
            "responses": {
                "Listener": "It’s natural to wonder ‘why me?’ Many people ask this.",
                "Motivator": "Knowing your history can help you rewrite your future.",
                "Director": "CAD often results from a mix of cholesterol, high blood pressure, diabetes, smoking, and genes.",
                "Expert": "AHA science shows that atherosclerosis can build silently over decades.",
            },
            "signatures": {
                "behavioral_core": ["HL"],  # Health Literacy (example tag)
                "condition_modifiers": ["CAD"],
                "engagement_drivers": {"TR": 1, "HL": 1, "SE": 0},  # -1/0/+1
            },
            "security_rules": [
                "Seek emergency care for chest pain/pressure, shortness of breath, fainting, or stroke symptoms."
            ],
            "action_plans": [
                "Ask your provider to review your personal CAD risk factors and your last lipid panel.",
                "Pick one risk factor to target this month (LDL, BP, tobacco, activity, nutrition)."
            ],
            # optional; if omitted, source_defaults is used
            # "sources": [...]
        },

                {
        "question": "What should I eat now that I have CAD?",
        "keywords": ["cad", "diet", "eat", "food", "sodium", "mediterranean", "dash"],
        "signatures": {
            "behavioral_core": "NUT",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"HL": 1, "FI": 0, "TR": 0},
            "signature_tags": ["CAD", "Nutrition", "DASH", "Mediterranean", "Sodium"],
        },
        "responses": {
            "Listener": (
                "There’s a lot of confusing advice out there. You’re not alone. If you tell me what you usually eat, "
                "we can find a few heart-healthy swaps that still feel realistic."
            ),
            "Motivator": (
                "You can still enjoy food—just smarter. A few upgrades (more fiber, healthier fats, less sodium) can make a real difference."
            ),
            "Director": (
                "Aim for a Mediterranean- or DASH-style pattern: vegetables, fruits, whole grains, beans, nuts, fish/lean proteins. "
                "Limit sodium, added sugar, and ultra-processed foods. Start by swapping one salty item per day."
            ),
            "Expert": (
                "For CAD, evidence-based eating patterns (Mediterranean/DASH) improve blood pressure and lipids and support secondary prevention. "
                "Reducing saturated fat and excess sodium is particularly helpful for risk reduction."
            ),
        },
        "security_rules": [
            "If you have kidney disease, heart failure, or are on fluid/salt restrictions, confirm your targets with your clinician or dietitian."
        ],
        "action_plans": [
            "Keep a simple 3-day food log to identify your highest-sodium foods.",
            "Replace one processed snack with fruit/vegetables + unsalted nuts.",
            "Ask for a referral to a cardiac dietitian if you want a personalized plan."
        ],
        "sources": [
            {"name": "AHA — Healthy eating", "url": "https://www.heart.org/en/healthy-living/healthy-eating"},
            {"name": "AHA — Coronary artery disease (diet/lifestyle prevention context)", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/coronary-artery-disease"},
       
        ],
    
        },
       
    {
        "question": "Can I exercise safely with CAD?",
        "keywords": ["cad", "exercise", "activity", "safe", "walking", "cardiac rehab", "stress test"],
        "signatures": {
            "behavioral_core": "PA",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"SE": 1, "PR": 1, "TR": 0},
            "signature_tags": ["CAD", "PhysicalActivity", "Safety", "CardiacRehab"],
        },
        "responses": {
            "Listener": (
                "It’s good you’re asking—many people worry about overdoing it. We can start with something gentle and build confidence safely."
            ),
            "Motivator": (
                "Movement is medicine—even 10 minutes counts. Consistency matters more than intensity at first."
            ),
            "Director": (
                "Start with low-to-moderate activity (like walking). Increase gradually. If you’ve had a recent event or procedure, "
                "ask about cardiac rehab or whether you need testing before you start."
            ),
            "Expert": (
                "Regular physical activity improves functional capacity, vascular function, and risk-factor control in CAD. "
                "Cardiac rehab is strongly supported for eligible patients after events/procedures and improves outcomes."
            ),
        },
        "security_rules": [
            "Stop exercise and seek urgent care if you develop chest pain/pressure, severe shortness of breath, fainting, or new neurologic symptoms.",
            "If you have nitroglycerin prescribed, follow your clinician’s instructions and call 911 if symptoms do not resolve promptly."
        ],
        "action_plans": [
            "Start with 5–10 minutes of walking, 5 days/week; add 1–2 minutes every few sessions as tolerated.",
            "Ask your clinician about a cardiac rehab referral (clinic-based or home-based options).",
            "Use a simple exertion scale (easy/moderate/hard) and aim for ‘moderate’ most days."
        ],
        "sources": [
            {"name": "AHA — Fitness and exercise", "url": "https://www.heart.org/en/healthy-living/fitness"},
            {"name": "AHA — Cardiac rehabilitation", "url": "https://www.heart.org/en/health-topics/cardiac-rehab"},
        ],
    },
       
    {
        "question": "What are my chances of having another heart event?",
        "keywords": ["cad", "another heart attack", "risk", "recurrence", "secondary prevention", "statin"],
        "signatures": {
            "behavioral_core": "PC",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"GO": 1, "TR": 1, "PR": 1},
            "signature_tags": ["CAD", "SecondaryPrevention", "Risk", "L8", "PREVENT"],
        },
        "responses": {
            "Listener": (
                "It’s totally normal to feel anxious about recurrence. If you want, we can focus on what you can control and "
                "build a plan that lowers your risk step by step."
            ),
            "Motivator": (
                "Every day you take action, you lower your risk. Your efforts matter—even small changes add up."
            ),
            "Director": (
                "Your risk depends on your heart function, symptoms, blood pressure, cholesterol, diabetes status, smoking, and lifestyle. "
                "Ask your care team for your targets and a checklist to track progress."
            ),
            "Expert": (
                "Secondary prevention is the evidence-based approach: optimize LDL lowering, BP control, diabetes management if present, "
                "tobacco cessation, physical activity, and adherence to guideline-directed therapy."
            ),
        },
        "security_rules": [
            "If you develop new/worsening chest pain, shortness of breath, fainting, or symptoms of a heart attack, call 911."
        ],
        "action_plans": [
            "Ask: ‘What are my target LDL and BP goals, and what’s my plan to reach them?’",
            "Use MyLifeCheck (Life’s Essential 8) as a monthly scorecard and track improvement over time.",
            "Bring your medication list to visits and confirm you’re on appropriate secondary prevention therapy."
        ],
        "sources": [
            {"name": "AHA — Coronary artery disease", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/coronary-artery-disease"},
            {"name": "AHA — Life’s Essential 8 / My Life Check", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"},
        ],
    },
        
    {
        "question": "How do I manage stress without hurting my heart?",
        "keywords": ["cad", "stress", "anxiety", "mindfulness", "sleep", "relaxation"],
        "signatures": {
            "behavioral_core": "ST",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"SE": 1, "HL": 1, "TR": 0},
            "signature_tags": ["CAD", "Stress", "Sleep", "MindBody"],
        },
        "responses": {
            "Listener": (
                "Heart issues can feel overwhelming. You’re not alone. We can start by identifying what stresses you most and one small step "
                "that makes your days feel more manageable."
            ),
            "Motivator": (
                "Stress can shrink when you take control. A few minutes of calming practice daily can build momentum fast."
            ),
            "Director": (
                "Pick one technique: 5 minutes of slow breathing, a short walk, journaling, or a tech-free wind-down before bed. "
                "Schedule it like an appointment."
            ),
            "Expert": (
                "Stress affects the body and can influence blood pressure, sleep, and health behaviors. The AHA recommends practical stress-management strategies; "
                "consistent routines and social support are protective."
            ),
        },
        "security_rules": [
            "If stress is causing panic symptoms, chest pain, or thoughts of self-harm, seek urgent help (911/988 in the U.S.)."
        ],
        "action_plans": [
            "Try a 5-minute breathing session daily for 7 days; track how you feel before/after.",
            "Build a 15-minute tech-free wind-down routine to support sleep quality.",
            "Ask your clinician about counseling, cardiac support groups, or behavior coaching if stress feels unmanageable."
        ],
        "sources": [
            {"name": "AHA — Stress Management", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management"},
            {"name": "AHA — Stress and Heart Health", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management/stress-and-heart-health"},
        ],
    },
       
    {
        "question": "What should I do if I have chest pain again?",
        "keywords": ["cad", "chest pain", "angina", "911", "nitroglycerin", "emergency"],
        "signatures": {
            "behavioral_core": "SY",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"TR": 1, "PR": 1, "HL": 1},
            "signature_tags": ["CAD", "Angina", "Emergency", "Safety"],
        },
        "responses": {
            "Listener": (
                "Chest pain can be scary. You’re not alone in this. The most important thing is having a clear plan so you don’t have to guess in the moment."
            ),
            "Motivator": (
                "Taking action right away can protect your heart. A written plan can give you confidence and help your family support you."
            ),
            "Director": (
                "If chest pain lasts more than a few minutes, is severe, or comes with shortness of breath, sweating, nausea, or fainting—call 911. "
                "If you have nitroglycerin, use it exactly as prescribed and do not delay emergency care."
            ),
            "Expert": (
                "Recurrent chest pain (angina) can reflect reduced blood flow to heart muscle and needs urgent evaluation if persistent or worsening. "
                "Rapid response reduces the risk of complications."
            ),
        },
        "security_rules": [
            "Call 911 for chest pain/pressure that is severe, persistent, or accompanied by concerning symptoms (shortness of breath, sweating, fainting, weakness).",
            "Do not drive yourself to the ER if you suspect a heart attack."
        ],
        "action_plans": [
            "Create a written ‘Chest Pain Plan’ with your clinician (when to rest, when to use nitro, when to call 911).",
            "Keep emergency numbers saved and posted; tell family what to do.",
            "Schedule follow-up if you have new or changing angina patterns, even if symptoms stop."
        ],
        "sources": [
            {"name": "AHA — Stable angina", "url": "https://www.heart.org/en/health-topics/heart-attack/angina-chest-pain/stable-angina"},
            {"name": "AHA — Ischemic heart disease (CAD/CHD)", "url": "https://www.heart.org/en/health-topics/heart-attack/about-heart-attacks/silent-ischemia-and-ischemic-heart-disease"},
        ],
    },
      
    {
        "question": "Should I get a stent or surgery again?",
        "keywords": ["cad", "stent", "bypass", "surgery", "angiogram", "revascularization"],
        "signatures": {
            "behavioral_core": "DS",  # decision-making / shared decisions
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"TR": 1, "DS": 1, "HL": 1},
            "signature_tags": ["CAD", "SharedDecisionMaking", "Procedures", "Imaging"],
        },
        "responses": {
            "Listener": (
                "It’s okay to feel uncertain about procedures. If you share your biggest concerns, we can organize questions for your cardiologist so you feel heard."
            ),
            "Motivator": (
                "You’ve been through this before—you know your body. Asking good questions helps you choose the path that fits your goals."
            ),
            "Director": (
                "Repeat procedures depend on symptoms, stress test/imaging, and how your heart is functioning now. "
                "Ask what the tests show and what the non-procedure options are."
            ),
            "Expert": (
                "Revascularization decisions are guided by symptoms, ischemia burden, anatomy, and response to medical therapy. "
                "Your cardiologist can explain whether the benefit is symptom relief, risk reduction, or both."
            ),
        },
        "security_rules": [
            "Seek urgent care for unstable symptoms (new/worsening chest pain at rest, fainting, severe shortness of breath)."
        ],
        "action_plans": [
            "Bring your questions list: benefits, risks, alternatives, and expected recovery.",
            "Ask to review your most recent imaging/stress testing results in plain language.",
            "Confirm you’re optimized on guideline-based medications before deciding on repeat procedures (if appropriate)."
        ],
        "sources": [
            {"name": "AHA — Coronary artery disease", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/coronary-artery-disease"},
        ],
    },
        
    {
        "question": "Can I travel or fly with CAD?",
        "keywords": ["cad", "travel", "fly", "vacation", "airport", "plane", "compression socks"],
        "signatures": {
            "behavioral_core": "PC",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"PR": 1, "SE": 1, "HL": 1},
            "signature_tags": ["CAD", "Travel", "Planning", "Safety"],
        },
        "responses": {
            "Listener": (
                "Wanting to live fully is a good sign. Let’s make travel feel safer by planning around your meds, energy, and symptoms."
            ),
            "Motivator": (
                "Yes—you can still enjoy life with a heart condition. Preparation turns anxiety into confidence."
            ),
            "Director": (
                "If your symptoms are stable, travel is often fine. Pack medications, keep them in your carry-on, plan stretch breaks, "
                "stay hydrated, and know where you’d go for care if needed."
            ),
            "Expert": (
                "Most stable CAD patients can travel safely, but risk varies based on recent events, symptoms, and overall fitness. "
                "Discuss timing if you’ve had a recent hospitalization or procedure."
            ),
        },
        "security_rules": [
            "Avoid travel soon after a major cardiac event/procedure unless your cardiologist explicitly clears you.",
            "Seek emergency care for chest pain, severe shortness of breath, fainting, or stroke symptoms while traveling."
        ],
        "action_plans": [
            "Ask your clinician: ‘Am I cleared for travel? Any restrictions?’",
            "Carry a medication list + diagnoses summary; keep emergency contacts handy.",
            "Set a plan to move every 1–2 hours during long trips."
        ],
        "sources": [
            {"name": "AHA News — Heart-healthy travel hacks", "url": "https://newsroom.heart.org/local-news/heart-healthy-travel-hacks"},
            {"name": "AHA Support Network — Traveling and flying", "url": "https://www.supportnetwork.heart.org/s/question/0D5Hr00006fwkGaKAI/traveling-and-flying"},
        ],
    },
       
    {
        "question": "What’s the role of cholesterol and statins?",
        "keywords": ["cad", "cholesterol", "statins", "ldl", "medication", "side effects"],
        "signatures": {
            "behavioral_core": "MA",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"TR": 1, "DS": 1, "HL": 1},
            "signature_tags": ["CAD", "Cholesterol", "Statins", "MedicationAdherence"],
        },
        "responses": {
            "Listener": (
                "Many people wonder about statins and side effects. If you tell me what you’ve heard or what worries you, "
                "we can sort it out and build questions for your clinician."
            ),
            "Motivator": (
                "Lowering cholesterol protects your arteries—keep going. Each refill and each dose is an investment in fewer future scares."
            ),
            "Director": (
                "Statins help lower LDL and stabilize plaque. Take them consistently. Ask your clinician what your LDL goal is and "
                "when you should recheck labs (often every 3–12 months depending on your situation)."
            ),
            "Expert": (
                "In CAD, LDL-lowering therapy is central to secondary prevention. Statins reduce events by lowering LDL and stabilizing plaques; "
                "non-statin options may be added if goals aren’t met or if side effects limit dosing."
            ),
        },
        "security_rules": [
            "Do not stop cholesterol medication without discussing it with your prescribing clinician.",
            "Report severe muscle pain/weakness, dark urine, or signs of allergic reaction promptly."
        ],
        "action_plans": [
            "Ask: ‘What is my LDL goal and what is my current LDL?’",
            "Recheck lipids on the schedule your clinician recommends.",
            "If side effects occur, ask about dose adjustment, alternate dosing, or non-statin therapies."
        ],
        "sources": [
            {"name": "AHA — Cholesterol-lowering medications (Answers by Heart PDF)", "url": "https://www.heart.org/-/media/Files/Health-Topics/Answers-by-Heart/Cholesterol-Lowering-Meds.pdf?rev=e3a2fa7e02654542bed939fd49397e22"},
            {"name": "AHA — High blood cholesterol pocket guide (PDF)", "url": "https://www.heart.org/en/-/media/Files/Professional/Quality-Improvement/Check-Change-Control-Cholesterol/AHA20PrimaryPocketGuideFinal.pdf"},
        ],
    },
        
    {
        "question": "How do I stay motivated with heart-healthy habits?",
        "keywords": ["cad", "motivation", "habits", "goals", "accountability", "tracking"],
        "signatures": {
            "behavioral_core": "GO",
            "condition_modifiers": {"CAD": 1},
            "engagement_drivers": {"SE": 1, "GO": 1, "PR": 1},
            "signature_tags": ["CAD", "BehaviorChange", "Goals", "Tracking", "L8"],
        },
        "responses": {
            "Listener": (
                "Staying motivated is hard—we all need encouragement. What’s the hardest part for you right now: getting started, "
                "staying consistent, or bouncing back after a slip?"
            ),
            "Motivator": (
                "Every small win matters. Keep moving forward. Momentum builds when you celebrate progress, not perfection."
            ),
            "Director": (
                "Pick 1 SMART goal for this month. Track it daily or weekly. Share it with someone who can support you, "
                "and schedule a quick weekly check-in."
            ),
            "Expert": (
                "Long-term change is strongest with tracking, feedback loops, and support (coaching, rehab, community, care teams). "
                "Using Life’s Essential 8 as a scorecard can help you focus on the highest-impact behaviors."
            ),
        },
        "security_rules": [
            "If you feel unwell during activity (chest pain, severe shortness of breath, fainting), stop and seek urgent care."
        ],
        "action_plans": [
            "Choose one habit: walking after one meal daily, sodium reduction, medication consistency, or sleep routine.",
            "Track your habit + one metric (BP, steps, or minutes) for 14 days.",
            "Ask about cardiac rehab or a prevention program if you want structured support."
        ],
        "sources": [
            {"name": "AHA — Life’s Essential 8", "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"},
            {"name": "AHA — Cardiac rehabilitation", "url": "https://www.heart.org/en/health-topics/cardiac-rehab"},
        ],
    },
  
    ],

    },

 
# -------------------------
# CKMH PACK (10) - Heart, Kidney, Metabolic Health (CKM/CKMH)
# -------------------------
     

    "CKMH": {
    "category": "CKMH",
    "title": "Heart, Kidney, and Metabolic Health (CKM)",
    "source_defaults": [
        _aha_source("CKM Syndrome (Overview)", "https://www.heart.org/en/health-topics/cardiometabolic-health/cardiovascular-kidney-metabolic-syndrome"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
        _aha_source("High Blood Pressure", "https://www.heart.org/en/health-topics/high-blood-pressure"),
        _aha_source("Diabetes & Heart Health", "https://www.heart.org/en/health-topics/diabetes"),
        _aha_source("Kidney Disease & Heart Health", "https://www.heart.org/en/health-topics/consumer-healthcare/kidney-disease-and-heart-health"),
    ],
    "questions": [
        {
            "question": "What does my diagnosis mean for my future?",
            "keywords": ["diagnosis", "prognosis", "future", "ckm"],
            "signatures": {
                "behavioral_core": ["HL", "GO"],
                "condition_modifiers": ["CKM"],
                "engagement_drivers": {"HL": 1, "SE": 0, "GO": 1, "TR": 0},
                "signature_tags": ["CKMH", "CKM", "LifeEssential8", "PREVENT", "SharedDecisionMaking"],
            },
            "responses": {
                "listener": "That sounds overwhelming. What are you most worried about?",
                "motivator": "You can live a full life with support—one step at a time.",
                "director": "Let’s monitor your labs and key scores regularly (often every ~3 months early on). Schedule your next lab visit and follow-up now.",
                "expert": "Early action guided by risk scoring and Life’s Essential 8 can change your trajectory by targeting the highest-impact risks.",
            },
            "security_rules": [
                "If you have chest pain, trouble breathing, fainting, stroke symptoms, or very high blood pressure with symptoms, seek urgent/emergency care.",
            ],
            "action_plans": [
                "Write down your top 3 concerns and bring them to your next visit (it helps your care team focus on what matters most).",
                "Ask for your PREVENT (or similar) risk estimate and a simple plan for what to improve next (personalized targets guide care decisions).",
            ],
        },
        {
            "question": "What can I eat—and what should I avoid?",
            "keywords": ["diet", "nutrition", "dash", "mediterranean", "sodium"],
            "signatures": {
                "behavioral_core": ["NUT"],
                "condition_modifiers": ["CKM", "HTN", "DM", "CKD"],
                "engagement_drivers": {"HL": 1, "SE": 0, "GO": 0, "FI": 0},
                "signature_tags": ["CKMH", "Nutrition", "DASH", "Mediterranean", "LifeEssential8"],
            },
            "responses": {
                "listener": "What foods do you enjoy? Let’s start there.",
                "motivator": "Healthy food can taste great—and small swaps add up fast.",
                "director": "Use a DASH or Mediterranean-style pattern: more fruits/veg, beans, whole grains; lean proteins; lower sodium and added sugars. Start with one swap today.",
                "expert": "These patterns are strongly linked to lower cardiovascular risk and better blood pressure and metabolic control over time.",
            },
            "security_rules": [
                "If you have kidney disease or heart failure, follow clinician guidance on sodium, potassium, and fluids—needs can differ by stage and meds.",
            ],
            "action_plans": [
                "Track meals for 3 days (it reveals strengths and the easiest next change).",
                "Replace one salty snack with fruit/vegetables or unsalted nuts this week (small swaps can lower blood pressure and improve metabolic health).",
            ],
        },
        {
            "question": "Why am I on so many medications?",
            "keywords": ["medications", "polypharmacy", "side effects", "adherence"],
            "signatures": {
                "behavioral_core": ["HL", "SE"],
                "condition_modifiers": ["CKM", "HTN", "DM", "CKD", "CAD"],
                "engagement_drivers": {"HL": 1, "SE": 1, "TR": 0, "GO": 0},
                "signature_tags": ["CKMH", "Medications", "Adherence", "Safety"],
            },
            "responses": {
                "listener": "Do any of them cause side effects or feel confusing?",
                "motivator": "Each medication is usually doing a specific job—protecting your heart, kidneys, and metabolism together.",
                "director": "Bring all meds (or a photo/list) to your next visit. Ask what each one is for and when to take it. Use a pillbox or reminders.",
                "expert": "When used correctly, guideline-based medications reduce complications and ER visits; your clinician can simplify or adjust when needed.",
            },
            "security_rules": [
                "Do not stop or change prescription medicines without clinician guidance—especially blood pressure meds, blood thinners, insulin, or diuretics.",
            ],
            "action_plans": [
                "Bring all meds/supplements to your next appointment (helps avoid duplication and interactions).",
                "Report missed doses and side effects early (your clinician can adjust safely).",
            ],
        },
        {
            "question": "How do I know if my condition is getting better or worse?",
            "keywords": ["monitoring", "labs", "symptoms", "progress"],
            "signatures": {
                "behavioral_core": ["SY", "HL"],
                "condition_modifiers": ["CKM"],
                "engagement_drivers": {"HL": 1, "GO": 1, "SE": 0, "TR": 0},
                "signature_tags": ["CKMH", "Tracking", "Labs", "LifeEssential8"],
            },
            "responses": {
                "listener": "Have you noticed any changes in how you feel day to day?",
                "motivator": "Monitoring gives you control—data helps you act early.",
                "director": "Use a simple weekly log (BP, weight, symptoms, activity). Ask your provider to explain lab trends and what’s “good progress” for you.",
                "expert": "Scores and trends (blood pressure, glucose/A1c, cholesterol, kidney labs) help track real progress across systems.",
            },
            "security_rules": [
                "Seek urgent care for chest pain, severe shortness of breath, fainting, new confusion/weakness, or rapid swelling/weight gain with breathing trouble.",
            ],
            "action_plans": [
                "Keep a weekly symptom + vitals log (it spots change early).",
                "At visits, ask: “Is my risk improving? What’s the next target?” (trend-based decisions are more effective than one-off values).",
            ],
        },
        {
            "question": "Will I need dialysis or heart surgery?",
            "keywords": ["dialysis", "surgery", "fear", "risk"],
            "signatures": {
                "behavioral_core": ["PR", "HL"],
                "condition_modifiers": ["CKD", "CAD", "HF", "CKM"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "TR": 0},
                "signature_tags": ["CKMH", "RiskReduction", "Planning", "SpecialistCare"],
            },
            "responses": {
                "listener": "That’s a scary thought. What worries you most about it?",
                "motivator": "You can take meaningful steps that lower risk—your actions matter.",
                "director": "Stay current on labs and imaging, and keep BP and glucose targets. Ask if you should see cardiology/nephrology for a tailored plan.",
                "expert": "Controlling blood pressure and glucose and following guideline therapy can substantially reduce progression and complications over time.",
            },
            "security_rules": [
                "If you have chest pain, worsening shortness of breath, confusion, or severe swelling, seek urgent evaluation.",
            ],
            "action_plans": [
                "Write down questions for your clinician (reduces fear and supports planning).",
                "Ask whether a specialist visit is appropriate and what your key “watch” markers are (early detection enables early action).",
            ],
        },
        {
            "question": "Can I still exercise?",
            "keywords": ["exercise", "activity", "safety", "ckm"],
            "signatures": {
                "behavioral_core": ["PA"],
                "condition_modifiers": ["CKM", "CAD", "HTN", "DM", "CKD"],
                "engagement_drivers": {"SE": 1, "GO": 1, "HL": 0, "PR": 1},
                "signature_tags": ["CKMH", "PhysicalActivity", "CardiacRehab", "LifeEssential8"],
            },
            "responses": {
                "listener": "What kind of movement do you enjoy—or feel willing to try?",
                "motivator": "Movement is medicine. Even 10 minutes counts.",
                "director": "Aim toward ~150 minutes/week moderate activity, but start small. Try a 10-minute walk after a meal and build from there. Ask about cardiac rehab if needed.",
                "expert": "Regular activity improves blood pressure, insulin sensitivity, lipids, and fitness—key drivers across CKM health.",
            },
            "security_rules": [
                "Stop and seek urgent care for chest pain/pressure, severe shortness of breath, fainting, or new neurologic symptoms during activity.",
            ],
            "action_plans": [
                "Do a 10-minute walk after one meal daily for 7 days (light activity improves glucose and BP).",
                "If you’ve had a recent event/procedure, ask about supervised rehab (structured programs improve safety and confidence).",
            ],
        },
        {
            "question": "What’s a healthy blood pressure for me?",
            "keywords": ["blood pressure", "targets", "monitoring"],
            "signatures": {
                "behavioral_core": ["SY", "HL"],
                "condition_modifiers": ["HTN", "CKM"],
                "engagement_drivers": {"HL": 1, "GO": 1, "SE": 0, "PR": 0},
                "signature_tags": ["CKMH", "BloodPressure", "Targets", "HomeMonitoring"],
            },
            "responses": {
                "listener": "Do you remember your last reading—and how it was taken (home vs clinic)?",
                "motivator": "Lower BP supports your brain, heart, and kidneys. You’re building protection with each step.",
                "director": "Targets are individualized, but many people aim <130/80. Take readings consistently and bring your cuff/log to visits for accuracy checks.",
                "expert": "Good control lowers risk of stroke and kidney disease progression; technique and consistent measurement matter.",
            },
            "security_rules": [
                "If BP is ≥180/120 especially with symptoms (chest pain, severe headache, shortness of breath, neurologic symptoms), seek urgent/emergency care.",
            ],
            "action_plans": [
                "Take BP at the same time on 3 days this week and record results (consistent technique reduces noise).",
                "Bring your BP cuff to your next visit to verify accuracy (bad devices mislead decisions).",
            ],
        },
        {
            "question": "How can I manage this and still live my life?",
            "keywords": ["routine", "balance", "quality of life", "stress"],
            "signatures": {
                "behavioral_core": ["HB", "ST"],
                "condition_modifiers": ["CKM"],
                "engagement_drivers": {"SE": 1, "GO": 1, "PR": 1, "HL": 0},
                "signature_tags": ["CKMH", "Routines", "BehaviorChange", "Support"],
            },
            "responses": {
                "listener": "What’s been hardest lately—time, stress, food, meds, or motivation?",
                "motivator": "You’re not alone—and you’re stronger than you think. One habit at a time works.",
                "director": "Pick a weekly planning day. Build your plan into your real routine (med timing, grocery habits, walks). Use reminders and small defaults.",
                "expert": "Digital tools and structured routines improve adherence and reduce decision fatigue across chronic conditions.",
            },
            "security_rules": [
                "If stress or mood symptoms feel severe or unsafe, seek urgent help or talk to a healthcare professional promptly.",
            ],
            "action_plans": [
                "Write your top 3 barriers and one workaround for each (barrier awareness improves follow-through).",
                "Choose a “health buddy” or accountability check-in this week (support increases consistency).",
            ],
        },
        {
            "question": "Are my heart, kidneys, and diabetes connected?",
            "keywords": ["ckm", "connected", "kidney", "diabetes", "heart"],
            "signatures": {
                "behavioral_core": ["HL"],
                "condition_modifiers": ["CKM", "DM", "CKD", "CAD", "HF"],
                "engagement_drivers": {"HL": 1, "TR": 0, "SE": 0, "GO": 0},
                "signature_tags": ["CKMH", "CKM", "SystemsThinking", "Education"],
            },
            "responses": {
                "listener": "Have you heard of CKM syndrome before, or is it new?",
                "motivator": "The good news: one healthy habit can help all three systems at once.",
                "director": "Ask for coordinated care (primary + cardiology + nephrology/endocrine as needed). Use one daily habit (like a short walk after dinner) to support multiple systems.",
                "expert": "The AHA treats CKM as a connected health issue; shared drivers include BP, glucose, weight, and inflammation—addressing them improves outcomes broadly.",
            },
            "security_rules": [
                "If you have sudden worsening symptoms (breathing trouble, chest pain, confusion, severe swelling), seek urgent evaluation.",
            ],
            "action_plans": [
                "Ask your provider to explain how your conditions connect and what your top 2 targets are (understanding helps earlier action).",
                "Walk 10–15 minutes after dinner for 7 days (one action can improve BP and glucose).",
            ],
        },
        {
            "question": "How do I avoid going back to the hospital?",
            "keywords": ["readmission", "prevention", "early warning signs", "remote monitoring"],
            "signatures": {
                "behavioral_core": ["PC", "SY"],
                "condition_modifiers": ["CKM", "HF", "CAD", "CKD"],
                "engagement_drivers": {"PR": 1, "SE": 1, "HL": 1, "TR": 0},
                "signature_tags": ["CKMH", "Readmissions", "EarlyAction", "RemoteMonitoring"],
            },
            "responses": {
                "listener": "What happened the last time you were hospitalized—what were the early signs?",
                "motivator": "Every healthy choice counts. You’re building stability one day at a time.",
                "director": "Create an early-warning plan: symptoms to watch, who to call, and what to do first. Ask about telehealth or remote monitoring if available.",
                "expert": "Early recognition and rapid adjustment of care reduces crises; connected monitoring and coaching can reduce readmissions in many programs.",
            },
            "security_rules": [
                "Chest pain, severe shortness of breath, fainting, stroke symptoms, or rapidly worsening swelling/weight gain with breathing difficulty requires urgent evaluation.",
            ],
            "action_plans": [
                "Keep a simple journal of early symptoms and triggers (patterns help prevent emergencies).",
                "Ask your care team about remote monitoring/telehealth options and escalation thresholds (early care reduces ER visits).",
            ],
        },
    ],
},



# -------------------------
# HTN PACK (10) - High Blood Pressure
# -------------------------
"HTN": {
"category": "HTN",
"title": "High Blood Pressure (Hypertension)",
    "source_defaults": [
        _aha_source("High Blood Pressure", "https://www.heart.org/en/health-topics/high-blood-pressure"),
        _aha_source("Understanding Blood Pressure Readings", "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings"),
        _aha_source("DASH Eating Plan", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/dash-diet"),
        _aha_source("How to Measure Blood Pressure at Home", "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings/monitoring-your-blood-pressure-at-home"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
    ],
    "questions": [
        {
            "question": "What should my blood pressure goal be?",
            "keywords": ["goal", "target", "130/80", "bp"],
            "signatures": {
                "behavioral_core": ["HL", "SY"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"HL": 1, "GO": 1, "SE": 0, "TR": 0},
                "signature_tags": ["HTN", "Targets", "HomeMonitoring", "LifeEssential8"],
            },
            "responses": {
                "listener": "It’s normal to feel unsure—many people don’t know their number.",
                "motivator": "Knowing your goal puts you in control!",
                "director": "For many people, a common target is below 130/80, but confirm your personal goal with your clinician. Track BP and compare to your target weekly.",
                "expert": "Lower blood pressure is linked to lower risk of heart attack, stroke, and kidney disease; targets are safer when individualized.",
            },
            "security_rules": [
                "If BP is ≥180/120 with symptoms (chest pain, severe headache, shortness of breath, weakness, confusion), seek urgent/emergency care.",
            ],
            "action_plans": [
                "Ask your doctor: “What’s my target BP?” (clear targets guide decisions).",
                "Write your goal somewhere visible (visibility improves follow-through).",
            ],
        },
        {
            "question": "Do I really need medication?",
            "keywords": ["medication", "antihypertensive", "lifestyle vs meds"],
            "signatures": {
                "behavioral_core": ["HL", "SE"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"HL": 1, "SE": 1, "TR": 0, "PR": 0},
                "signature_tags": ["HTN", "Medications", "Adherence", "SharedDecisionMaking"],
            },
            "responses": {
                "listener": "It’s okay to feel unsure. Many people ask this.",
                "motivator": "Medication is one tool to protect your heart—just like food and movement.",
                "director": "Ask how meds fit your overall plan. If starting meds, link them to a daily habit (like brushing teeth) and recheck BP with your clinician’s timeline.",
                "expert": "For many people, the best results come from combining medication with healthy habits—especially when BP is persistently elevated or risk is higher.",
            },
            "security_rules": [
                "Do not stop blood pressure medicines abruptly without clinician guidance.",
            ],
            "action_plans": [
                "Ask: “What problem is this medication solving?” (clarity improves adherence).",
                "Pair your dose with a daily routine cue (habit pairing increases consistency).",
            ],
        },
        {
            "question": "What can I do besides taking medication?",
            "keywords": ["lifestyle", "salt", "exercise", "sleep", "stress"],
            "signatures": {
                "behavioral_core": ["NUT", "PA", "SLEEP", "ST"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"GO": 1, "SE": 1, "HL": 1, "PR": 0},
                "signature_tags": ["HTN", "Lifestyle", "DASH", "LifeEssential8"],
            },
            "responses": {
                "listener": "It’s great that you want to take action!",
                "motivator": "Your body responds quickly to healthy habits—small steps work.",
                "director": "Choose one focus area this week: food, movement, sleep, or stress. Try tracking sodium for 3 days and add a daily 10-minute walk.",
                "expert": "Lifestyle changes can lower systolic BP meaningfully; stacking a few changes often beats any single change alone.",
            },
            "security_rules": [
                "If you’re starting an exercise plan and have chest pain, fainting, or severe shortness of breath history, get medical clearance first.",
            ],
            "action_plans": [
                "Pick one area (food/movement/sleep/stress) and do one change for 7 days (small starts are sustainable).",
                "Track sodium intake for 3 days (awareness drives improvement).",
            ],
        },
        {
            "question": "What kind of diet should I follow?",
            "keywords": ["dash", "diet", "sodium", "nutrition"],
            "signatures": {
                "behavioral_core": ["NUT"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"HL": 1, "SE": 0, "GO": 0, "FI": 0},
                "signature_tags": ["HTN", "Nutrition", "DASH", "Mediterranean"],
            },
            "responses": {
                "listener": "Choosing what to eat can feel confusing. You’re not alone.",
                "motivator": "Small food swaps can lead to big results.",
                "director": "Try a DASH-style pattern: fruits/veg, whole grains, low-fat dairy, beans, nuts; limit sodium and ultra-processed foods. Add one fruit/veg to each meal.",
                "expert": "Clinical trials show DASH lowers BP and improves heart health; consistency matters more than perfection.",
            },
            "security_rules": [
                "If you have kidney disease, discuss potassium/salt substitutes with your clinician—some can be unsafe with certain meds.",
            ],
            "action_plans": [
                "Keep a simple food journal for 3 days (reflection builds insight).",
                "Add one fruit or vegetable to each meal for a week (gradual changes stick).",
            ],
        },
        {
            "question": "Will I have high blood pressure forever?",
            "keywords": ["forever", "reversible", "control", "hypertension"],
            "signatures": {
                "behavioral_core": ["GO", "SE"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"SE": 1, "GO": 1, "HL": 0, "PR": 0},
                "signature_tags": ["HTN", "LongTerm", "Hope", "Maintenance"],
            },
            "responses": {
                "listener": "That’s a common fear—but there’s hope.",
                "motivator": "You can improve your numbers—many people do!",
                "director": "Even if it doesn’t go away completely, it can often be controlled. Stick with a plan for 3 months, then reassess with your clinician.",
                "expert": "Long-term control comes from lifestyle plus medications when needed; the goal is sustained risk reduction, not perfection.",
            },
            "security_rules": [
                "Do not stop medications just because readings improve—confirm a taper plan with your clinician.",
            ],
            "action_plans": [
                "Ask if your HTN is potentially reversible and what would make the biggest difference (shared planning reduces uncertainty).",
                "Celebrate small BP drops (positive feedback supports persistence).",
            ],
        },
        {
            "question": "How can I track my blood pressure at home?",
            "keywords": ["home monitoring", "bp cuff", "technique"],
            "signatures": {
                "behavioral_core": ["SY"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"HL": 1, "SE": 1, "GO": 0, "PR": 0},
                "signature_tags": ["HTN", "HomeMonitoring", "Technique", "Tracking"],
            },
            "responses": {
                "listener": "It can be overwhelming at first, but you’re not alone.",
                "motivator": "Tracking gives you control over your progress.",
                "director": "Take readings morning and evening, seated and rested. Use reminders and log readings with date/time and symptoms.",
                "expert": "Technique matters: correct cuff size, arm at heart level, avoid caffeine/exercise 30 minutes before, and rest 5 minutes first.",
            },
            "security_rules": [
                "If you get repeated very high readings (especially ≥180/120) or symptoms, seek urgent guidance per your clinician’s plan.",
            ],
            "action_plans": [
                "Set a calendar alert for BP checks 3 days/week (routine improves reliability).",
                "Bring your cuff to a visit to confirm accuracy (trustworthy data improves decisions).",
            ],
        },
        {
            "question": "Can stress really affect my blood pressure?",
            "keywords": ["stress", "bp", "mindfulness", "sleep"],
            "signatures": {
                "behavioral_core": ["ST", "SLEEP"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"SE": 1, "PR": 1, "HL": 0, "GO": 0},
                "signature_tags": ["HTN", "Stress", "Sleep", "MindBody"],
            },
            "responses": {
                "listener": "Yes—and life can be stressful. We get it.",
                "motivator": "Taking care of your mind supports your heart.",
                "director": "Create a wind-down routine and try 5 minutes of guided breathing daily. Also watch the stress behaviors (sleep, salty food, alcohol).",
                "expert": "Stress can raise BP and drive behaviors that raise BP; mind-body strategies can support better control over time.",
            },
            "security_rules": [
                "If anxiety or panic symptoms feel severe or unsafe, seek urgent help or contact a healthcare professional.",
            ],
            "action_plans": [
                "Identify one stressor you can reduce this week (small wins reduce tension).",
                "Try 5 minutes of paced breathing daily for 7 days (quick nervous-system downshift).",
            ],
        },
        {
            "question": "What’s a dangerous blood pressure level?",
            "keywords": ["dangerous", "hypertensive crisis", "180/120"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "GO": 0},
                "signature_tags": ["HTN", "Safety", "Escalation", "EmergencyPlan"],
            },
            "responses": {
                "listener": "It’s scary not knowing what’s too high.",
                "motivator": "Knowing your numbers gives you power—not fear.",
                "director": "A hypertensive crisis is often defined around 180/120, especially if symptoms are present. Know your plan: recheck, call, or seek urgent care depending on symptoms.",
                "expert": "Risk rises as BP rises, and symptoms matter. Your clinician can help you set thresholds based on your history and meds.",
            },
            "security_rules": [
                "If BP is ≥180/120 with chest pain, shortness of breath, weakness, vision changes, confusion, or severe headache, seek emergency care.",
            ],
            "action_plans": [
                "Learn BP zones using a chart (recognition supports timely action).",
                "Program urgent contacts and keep your plan accessible (preparedness reduces delay).",
            ],
        },
        {
            "question": "Is low blood pressure a problem too?",
            "keywords": ["low bp", "90/60", "dizzy", "hypotension"],
            "signatures": {
                "behavioral_core": ["SY", "HL"],
                "condition_modifiers": ["HTN", "MEDS"],
                "engagement_drivers": {"HL": 1, "SE": 1, "PR": 0, "GO": 0},
                "signature_tags": ["HTN", "Safety", "Symptoms", "MedicationReview"],
            },
            "responses": {
                "listener": "Yes—low BP can make you feel dizzy, tired, or weak.",
                "motivator": "It’s okay to ask questions if something doesn’t feel right.",
                "director": "If BP feels too low—especially on meds—log symptoms and timing of doses, and share with your clinician to adjust safely.",
                "expert": "BP under ~90/60 can be normal for some, but concerning if it causes symptoms; dehydration and meds can contribute.",
            },
            "security_rules": [
                "Seek urgent care if low BP is accompanied by fainting, chest pain, severe shortness of breath, or confusion.",
            ],
            "action_plans": [
                "Note symptoms whenever you take readings (symptom-linked data guides adjustments).",
                "Track hydration and med timing for a week and review with your clinician (timing often explains patterns).",
            ],
        },
        {
            "question": "How do I talk to my family about my high blood pressure?",
            "keywords": ["family", "support", "communication", "history"],
            "signatures": {
                "behavioral_core": ["TR", "SE"],
                "condition_modifiers": ["HTN"],
                "engagement_drivers": {"TR": 1, "SE": 1, "HL": 0, "GO": 0},
                "signature_tags": ["HTN", "FamilySupport", "Prevention", "Communication"],
            },
            "responses": {
                "listener": "Talking about your health takes courage.",
                "motivator": "You might inspire them to check their BP too!",
                "director": "Use simple language: “I’m working on my BP so I can stay healthy.” Share one goal and invite support.",
                "expert": "Family history matters—sharing encourages prevention and earlier detection for loved ones too.",
            },
            "security_rules": [
                "If family conversations increase stress significantly, consider bringing a trusted support person to a clinic visit instead.",
            ],
            "action_plans": [
                "Start with one trusted family member (support makes change easier).",
                "Invite a loved one to join a walk or cooking swap (shared habits improve follow-through).",
            ],
        },
    ],
},

# -------------------------
# AF PACK (10) - Atrial Fibrillation
# -------------------------
"HTN": {
"category": "HTN",
    "title": "Atrial Fibrillation (AFib)",
    "source_defaults": [
        _aha_source("Atrial Fibrillation (AFib)", "https://www.heart.org/en/health-topics/atrial-fibrillation"),
        _aha_source("Stroke Warning Signs (FAST)", "https://www.heart.org/en/health-topics/stroke/warning-signs-of-stroke"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
        _aha_source("Sleep Apnea and Heart Disease/Stroke", "https://www.heart.org/en/health-topics/sleep-disorders/sleep-apnea-and-heart-disease-stroke"),
    ],
    "questions": [
        {
            "question": "What exactly is atrial fibrillation?",
            "keywords": ["afib", "irregular heartbeat", "atria", "ecg"],
            "signatures": {
                "behavioral_core": ["HL"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"HL": 1, "SE": 0, "TR": 0, "PR": 0},
                "signature_tags": ["AF", "Education", "Diagnosis", "ECG"],
            },
            "responses": {
                "listener": "You’re not alone—this diagnosis can feel overwhelming.",
                "motivator": "You’ve taken an important first step by asking.",
                "director": "AFib is an irregular rhythm that can raise stroke and heart failure risk. Ask for a clear explanation of your type and your plan.",
                "expert": "AFib involves disorganized electrical activity in the atria; confirmation and classification help guide treatment.",
            },
            "security_rules": [
                "Seek urgent care for chest pain, fainting, severe shortness of breath, or signs of stroke (face droop, arm weakness, speech difficulty).",
            ],
            "action_plans": [
                "Ask your clinician to explain AFib in plain language (understanding reduces fear and improves adherence).",
                "Ask what AFib type you have (paroxysmal/persistent/permanent) and what it changes in your plan (type guides strategy).",
            ],
        },
        {
            "question": "What are my treatment options?",
            "keywords": ["rate control", "rhythm control", "ablation", "cardioversion"],
            "signatures": {
                "behavioral_core": ["HL", "GO"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"HL": 1, "GO": 1, "TR": 0, "SE": 0},
                "signature_tags": ["AF", "TreatmentOptions", "SharedDecisionMaking"],
            },
            "responses": {
                "listener": "It’s okay to feel unsure—there are several options.",
                "motivator": "You deserve a plan that fits your life.",
                "director": "Options include meds (rate/rhythm), cardioversion, ablation, and risk-factor control. Schedule a dedicated planning visit to decide goals.",
                "expert": "Therapy depends on symptoms, duration, comorbidities, and AFib type—tailoring improves outcomes.",
            },
            "security_rules": [
                "Do not change heart rhythm/heart rate medications without clinician guidance.",
            ],
            "action_plans": [
                "Write your top goals: symptom relief, stroke prevention, or both (goals guide decisions).",
                "Ask about rhythm vs rate strategy and why it fits you (clarity improves confidence).",
            ],
        },
        {
            "question": "Do I need a blood thinner?",
            "keywords": ["anticoagulation", "blood thinner", "stroke risk", "CHA2DS2-VASc"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["AF", "STROKE_RISK"],
                "engagement_drivers": {"HL": 1, "PR": 1, "TR": 0, "SE": 0},
                "signature_tags": ["AF", "Anticoagulation", "StrokePrevention", "Safety"],
            },
            "responses": {
                "listener": "It’s common to be nervous about bleeding risk.",
                "motivator": "Blood thinners can be powerful protection against stroke.",
                "director": "Ask for your stroke risk score and how it compares to bleeding risk. Learn what to do if you miss a dose and what interactions to avoid.",
                "expert": "Guidelines commonly use risk scoring (like CHA₂DS₂-VASc) to decide anticoagulation; the goal is matching therapy to risk.",
            },
            "security_rules": [
                "If you have signs of serious bleeding (vomiting blood, black/tarry stools, severe unexplained bruising) or stroke symptoms, seek emergency care.",
            ],
            "action_plans": [
                "Ask for your stroke risk score and what it means (informed decisions are safer).",
                "Ask for a “missed dose + bleeding precautions” handout (clear rules reduce errors).",
            ],
        },
        {
            "question": "Can AFib go away?",
            "keywords": ["remission", "paroxysmal", "ablation", "risk factor control"],
            "signatures": {
                "behavioral_core": ["GO", "HB"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"GO": 1, "SE": 1, "HL": 0, "TR": 0},
                "signature_tags": ["AF", "Remission", "RiskFactorControl", "SleepApnea"],
            },
            "responses": {
                "listener": "That’s a hopeful question—and a fair one.",
                "motivator": "Some people do return to normal rhythm with treatment and risk-factor changes.",
                "director": "Track episodes and triggers. Keep follow-ups for rhythm checks and discuss whether ablation or specific risk-factor plans are appropriate.",
                "expert": "In some cases, treating drivers like sleep apnea, weight, alcohol exposure, and BP can reduce burden; some achieve remission, especially earlier on.",
            },
            "security_rules": [
                "If AFib symptoms are severe (fainting, chest pain, severe breathlessness), seek urgent evaluation.",
            ],
            "action_plans": [
                "Track episodes/triggers for 2–4 weeks (patterns guide the plan).",
                "Ask if sleep apnea screening or a weight-risk plan is appropriate (driver control can reduce AFib burden).",
            ],
        },
        {
            "question": "How does AFib affect my risk of stroke?",
            "keywords": ["stroke", "risk", "FAST", "prevention"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["AF", "STROKE_RISK"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "TR": 0},
                "signature_tags": ["AF", "StrokeRisk", "FAST", "Anticoagulation"],
            },
            "responses": {
                "listener": "That fear is valid—stroke risk is real, but manageable.",
                "motivator": "You’re taking charge by focusing on prevention.",
                "director": "Learn FAST signs of stroke and follow your anticoagulation plan if prescribed. Keep BP, diabetes, and sleep in check too.",
                "expert": "AFib increases stroke risk; anticoagulation can reduce risk substantially when indicated, and comorbidity control supports prevention.",
            },
            "security_rules": [
                "If you notice FAST symptoms, call emergency services immediately—time matters.",
            ],
            "action_plans": [
                "Learn FAST and teach one family member (recognition saves lives).",
                "Review your stroke prevention plan at each visit (staying aligned reduces risk).",
            ],
        },
        {
            "question": "What should I avoid with AFib?",
            "keywords": ["triggers", "alcohol", "caffeine", "cold medicine", "stress"],
            "signatures": {
                "behavioral_core": ["ST", "SLEEP", "NUT"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"SE": 1, "HL": 1, "PR": 0, "GO": 0},
                "signature_tags": ["AF", "Triggers", "Lifestyle", "Prevention"],
            },
            "responses": {
                "listener": "You’re not alone in wondering what can make it worse.",
                "motivator": "Small changes can make a big difference.",
                "director": "Identify triggers (alcohol, too much caffeine, poor sleep, stress, stimulants). Make a list and test one reduction for 2 weeks.",
                "expert": "Common triggers include alcohol and stimulants; risk-factor control is a core part of AFib management and symptom reduction.",
            },
            "security_rules": [
                "Avoid stimulant-containing cold medications unless your clinician says they’re safe for you; ask a pharmacist if unsure.",
            ],
            "action_plans": [
                "Create a trigger list and track symptoms for 2 weeks (data makes triggers obvious).",
                "Choose one trigger to reduce this week (small experiments improve control).",
            ],
        },
        {
            "question": "Can I still exercise?",
            "keywords": ["exercise", "safe activity", "rehab", "symptoms"],
            "signatures": {
                "behavioral_core": ["PA"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"SE": 1, "GO": 1, "PR": 1, "HL": 0},
                "signature_tags": ["AF", "PhysicalActivity", "CardiacRehab", "Safety"],
            },
            "responses": {
                "listener": "It’s smart to ask—many people worry about this.",
                "motivator": "Yes—moving your body is part of healing.",
                "director": "Start with walking or light movement and increase gradually. Ask about cardiac rehab if you want structured monitoring early on.",
                "expert": "Moderate exercise can improve AFib symptoms and overall cardiovascular health when done safely and progressively.",
            },
            "security_rules": [
                "Stop exercise and seek urgent evaluation for chest pain, fainting, severe shortness of breath, or new neurologic symptoms.",
            ],
            "action_plans": [
                "Tell your clinician what exercise you enjoy (plans stick when they fit you).",
                "Start with a 10–15 minute walk 3–5 days/week and build (steady progression improves tolerance).",
            ],
        },
        {
            "question": "Will AFib get worse over time?",
            "keywords": ["progression", "paroxysmal", "persistent", "risk factors"],
            "signatures": {
                "behavioral_core": ["GO", "HL"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"GO": 1, "HL": 1, "SE": 0, "PR": 0},
                "signature_tags": ["AF", "Progression", "RiskFactorControl", "Monitoring"],
            },
            "responses": {
                "listener": "It’s okay to worry—uncertainty is hard.",
                "motivator": "Staying proactive makes a big difference.",
                "director": "Ask which AFib type you have and what would signal progression. Track symptoms and keep follow-ups for rhythm checks.",
                "expert": "Progression risk is influenced by drivers like age, weight, sleep apnea, hypertension, and diabetes—controlling them can slow worsening.",
            },
            "security_rules": [
                "If episodes become much more frequent or symptoms worsen significantly, contact your clinician promptly.",
            ],
            "action_plans": [
                "Ask for your AFib type and what it predicts (classification guides planning).",
                "Choose one risk-factor target this month (BP, sleep, weight, alcohol) (driver control can slow progression).",
            ],
        },
        {
            "question": "Can I travel or fly with AFib?",
            "keywords": ["travel", "flying", "dehydration", "clots"],
            "signatures": {
                "behavioral_core": ["PR", "HB"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"PR": 1, "SE": 1, "HL": 0, "GO": 0},
                "signature_tags": ["AF", "Travel", "Planning", "Safety"],
            },
            "responses": {
                "listener": "This is a common concern—and you’re wise to ask.",
                "motivator": "AFib doesn’t have to ground your life.",
                "director": "Travel is often fine if stable. Pack meds, hydrate, and walk during long trips. Know what symptoms mean you should seek care.",
                "expert": "Dehydration and long immobility can worsen symptoms and clot risk; movement and hydration help reduce triggers.",
            },
            "security_rules": [
                "If you develop chest pain, severe shortness of breath, fainting, or stroke symptoms while traveling, seek emergency care immediately.",
            ],
            "action_plans": [
                "Talk to your clinician before long trips (pre-planning reduces risk).",
                "During flights: hydrate and walk/stand regularly (reduces triggers and clot risk).",
            ],
        },
        {
            "question": "Will I have to live with AFib forever?",
            "keywords": ["chronic", "long-term", "remission", "management"],
            "signatures": {
                "behavioral_core": ["SE", "GO"],
                "condition_modifiers": ["AF"],
                "engagement_drivers": {"SE": 1, "GO": 1, "HL": 0, "TR": 0},
                "signature_tags": ["AF", "LongTerm", "Hope", "Maintenance"],
            },
            "responses": {
                "listener": "It’s okay to wonder—many people do.",
                "motivator": "You can live well with AFib.",
                "director": "Some people reach remission, many manage it long-term. The best plan is consistent meds (if prescribed) plus driver control and regular check-ins.",
                "expert": "AFib is often chronic but can be controlled; early stages may respond strongly to interventions like ablation and risk-factor management in appropriate patients.",
            },
            "security_rules": [
                "If you feel unsafe, faint, or have stroke symptoms, seek emergency care immediately.",
            ],
            "action_plans": [
                "Ask: “What does success look like for me?” (clear expectations reduce anxiety).",
                "Pick one habit change this month (sleep, alcohol, BP, activity) (small changes can reduce AFib burden).",
            ],
        },
    ],
},

# -------------------------
# HF PACK (10) - Heart Failure
# -------------------------
"HF": {
    "category": "HF",
    "title": "Heart Failure",
    "source_defaults": [
        _aha_source("Heart Failure", "https://www.heart.org/en/health-topics/heart-failure"),
        _aha_source("Warning Signs of Heart Failure", "https://www.heart.org/en/health-topics/heart-failure/warning-signs-of-heart-failure"),
        _aha_source("Cardiac Rehab", "https://www.heart.org/en/health-topics/cardiac-rehab"),
        _aha_source("Low-Sodium Eating", "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/sodium"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
    ],
    "questions": [
        {
            "question": "What is heart failure and can it be managed?",
            "keywords": ["heart failure", "managed", "pumping", "diagnosis"],
            "signatures": {
                "behavioral_core": ["HL", "SE"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"HL": 1, "SE": 1, "TR": 0, "PR": 0},
                "signature_tags": ["HF", "Education", "CarePlan", "Hope"],
            },
            "responses": {
                "listener": "It’s okay to feel nervous. You’re not alone in this.",
                "motivator": "Many people with heart failure live full, active lives.",
                "director": "Heart failure means your heart isn’t pumping as well—but treatment helps. Build a care plan with your team and track symptoms.",
                "expert": "Guidelines support medicines, lifestyle changes, and symptom tracking; early recognition of changes helps prevent hospitalizations.",
            },
            "security_rules": [
                "Seek urgent care for chest pain, severe shortness of breath at rest, fainting, confusion, or blue lips/face.",
            ],
            "action_plans": [
                "Ask your clinician to explain your HF in simple terms (understanding reduces fear).",
                "Start a simple symptom log (tracking helps detect problems early).",
            ],
        },
        {
            "question": "How do I know if my heart failure is getting worse?",
            "keywords": ["worsening", "weight gain", "swelling", "breathing"],
            "signatures": {
                "behavioral_core": ["SY", "PR"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"PR": 1, "SE": 1, "HL": 1, "GO": 0},
                "signature_tags": ["HF", "EarlyWarning", "Weight", "Readmissions"],
            },
            "responses": {
                "listener": "It’s okay to check in with how your body feels.",
                "motivator": "You’re learning your body’s signals—that’s powerful.",
                "director": "Track weight daily and watch swelling/breathing. Report sudden gain (often ~2+ lbs overnight or ~5+ in a week) or worsening symptoms per your plan.",
                "expert": "Daily monitoring (weight, symptoms) helps catch fluid buildup early and reduce hospital visits.",
            },
            "security_rules": [
                "If breathing becomes severely difficult, you cannot lie flat, or you have chest pain, seek emergency care.",
            ],
            "action_plans": [
                "Weigh yourself every morning after the bathroom, before breakfast (consistent timing improves accuracy).",
                "Use a simple checklist: weight, swelling, breathlessness, fatigue (patterns matter more than single days).",
            ],
        },
        {
            "question": "What can I eat with heart failure?",
            "keywords": ["sodium", "diet", "fluids", "labels"],
            "signatures": {
                "behavioral_core": ["NUT"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"HL": 1, "SE": 0, "GO": 0, "FI": 0},
                "signature_tags": ["HF", "Nutrition", "Sodium", "DASH"],
            },
            "responses": {
                "listener": "Eating can feel tricky when you’re told to ‘cut back.’",
                "motivator": "Your meals can still be flavorful and fulfilling!",
                "director": "Limit sodium (often ~1,500–2,000 mg/day depending on your plan). Read labels and reduce processed foods. Follow fluid guidance if your clinician gave it.",
                "expert": "Lower sodium helps reduce fluid retention and symptoms; heart-healthy patterns support long-term outcomes.",
            },
            "security_rules": [
                "If you have kidney disease or are on diuretics, follow clinician guidance on sodium, fluids, and potassium—avoid salt substitutes unless approved.",
            ],
            "action_plans": [
                "Check one label per day for sodium (small steps add up).",
                "Try one new low-sodium recipe this week (variety supports adherence).",
            ],
        },
        {
            "question": "How much activity is safe for me?",
            "keywords": ["activity", "exercise", "safe", "rehab"],
            "signatures": {
                "behavioral_core": ["PA", "PR"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"SE": 1, "PR": 1, "GO": 1, "HL": 0},
                "signature_tags": ["HF", "PhysicalActivity", "Rehab", "Safety"],
            },
            "responses": {
                "listener": "It’s natural to feel cautious.",
                "motivator": "Even a few steps count—movement is medicine.",
                "director": "Ask for safe goals and start with short walks (like 5 minutes after meals). Consider cardiac rehab for tailored guidance.",
                "expert": "Supervised rehab improves quality of life and outcomes; gradual progression helps build stamina safely.",
            },
            "security_rules": [
                "Stop and seek urgent care for chest pain, fainting, severe shortness of breath, or new neurologic symptoms during activity.",
            ],
            "action_plans": [
                "Ask for a referral to rehab or a written walking plan (structure improves safety).",
                "Use the talk test and symptom checks (prevents overexertion).",
            ],
        },
        {
            "question": "Will I always feel tired or short of breath?",
            "keywords": ["fatigue", "shortness of breath", "symptoms", "treatment"],
            "signatures": {
                "behavioral_core": ["SE", "SY"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"SE": 1, "HL": 1, "GO": 0, "PR": 0},
                "signature_tags": ["HF", "Symptoms", "Optimization", "FollowUp"],
            },
            "responses": {
                "listener": "It’s frustrating when energy is low—but you’re doing your best.",
                "motivator": "Good days will come—keep going.",
                "director": "Stick to meds, meals, and movement plan. Track fatigue and breathing so your clinician can adjust therapy.",
                "expert": "Symptoms can improve when therapy is optimized; regular review helps fine-tune your plan.",
            },
            "security_rules": [
                "If you have rapidly worsening breathlessness, chest pain, or fainting, seek urgent evaluation.",
            ],
            "action_plans": [
                "Keep a fatigue + symptom journal for 2 weeks (patterns help clinicians adjust therapy).",
                "Ask about medication optimization if symptoms persist (guideline-directed therapy changes over time).",
            ],
        },
        {
            "question": "What medications will I need, and what do they do?",
            "keywords": ["medications", "beta-blocker", "ACE", "ARNI", "SGLT2", "MRA"],
            "signatures": {
                "behavioral_core": ["HL", "SE"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"HL": 1, "SE": 1, "TR": 0, "GO": 0},
                "signature_tags": ["HF", "Medications", "GDMT", "Adherence"],
            },
            "responses": {
                "listener": "It’s okay to ask what each pill is for. That’s smart.",
                "motivator": "Learning your meds is part of owning your care.",
                "director": "Make a simple med chart: name, time, purpose, and side effects to watch. Review it with your clinician every 3–6 months.",
                "expert": "Guidelines support key medication classes for many patients; therapy is tailored and may change as your body responds.",
            },
            "security_rules": [
                "Do not stop HF medications without clinician guidance; seek help for severe side effects (fainting, severe dizziness, swelling of face/lips, allergic reactions).",
            ],
            "action_plans": [
                "Bring all meds to your next visit and ask what each one does (clarity improves adherence).",
                "Review your list every 3–6 months (med needs change with kidney function, BP, and symptoms).",
            ],
        },
        {
            "question": "Can I travel or go on vacation with heart failure?",
            "keywords": ["travel", "vacation", "planning", "stability"],
            "signatures": {
                "behavioral_core": ["PR", "HB"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"PR": 1, "SE": 1, "HL": 0, "GO": 0},
                "signature_tags": ["HF", "Travel", "Planning", "Safety"],
            },
            "responses": {
                "listener": "It’s totally okay to want some normalcy.",
                "motivator": "You can still explore and enjoy—just with preparation.",
                "director": "Travel is usually safer when symptoms are stable. Pack meds, a weight plan, and emergency contacts. Confirm travel clearance with your clinician.",
                "expert": "Guidance is individualized based on symptoms and recent labs; extremes (altitude/heat) can strain the heart.",
            },
            "security_rules": [
                "If you develop severe breathing trouble, chest pain, fainting, or confusion while traveling, seek emergency care immediately.",
            ],
            "action_plans": [
                "Talk to your provider about travel plans ahead of time (planning reduces risk).",
                "Pack meds + a brief health summary and keep them with you (preparedness prevents missed doses).",
            ],
        },
        {
            "question": "Will I need a device like a defibrillator or pacemaker?",
            "keywords": ["ICD", "CRT", "device", "ejection fraction"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "TR": 0},
                "signature_tags": ["HF", "Devices", "EF", "Reassessment"],
            },
            "responses": {
                "listener": "It’s okay to be nervous about devices. Ask away.",
                "motivator": "Many people feel safer with a device protecting them.",
                "director": "Eligibility depends on heart function (often ejection fraction) and symptoms. Ask if you need an updated echo and when reassessment should happen.",
                "expert": "Guidelines support device therapy for select patients after medical therapy optimization; reassessment is often recommended after months of treatment.",
            },
            "security_rules": [
                "If you have fainting, near-fainting, or suspected arrhythmia symptoms, contact your clinician promptly or seek urgent care.",
            ],
            "action_plans": [
                "Ask if your ejection fraction qualifies you and when it will be rechecked (data drives decisions).",
                "Discuss pros/cons and recovery expectations (shared decisions reduce anxiety).",
            ],
        },
        {
            "question": "What should I do during a flare or worsening episode?",
            "keywords": ["flare", "decompensation", "plan", "when to call"],
            "signatures": {
                "behavioral_core": ["PR", "SY"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"PR": 1, "SE": 1, "HL": 1, "GO": 0},
                "signature_tags": ["HF", "EmergencyPlan", "EarlyAction", "Readmissions"],
            },
            "responses": {
                "listener": "You’re not alone. Flares happen even when you’re doing everything right.",
                "motivator": "Having a plan makes you powerful—you can respond early.",
                "director": "Use a “When to Call” checklist: weight gain, swelling, breathlessness, reduced urine, new fatigue. Keep your care team number posted and in your phone.",
                "expert": "Guidelines emphasize early contact and adjustment of therapy to prevent hospitalization during acute worsening.",
            },
            "security_rules": [
                "Seek emergency care for severe breathlessness at rest, chest pain, fainting, confusion, or blue lips/face.",
            ],
            "action_plans": [
                "Write a ‘When to Call’ checklist and post it at home (removes guesswork).",
                "Review your emergency plan every 3–6 months (keeps plans current as meds change).",
            ],
        },
        {
            "question": "How long can I live with heart failure?",
            "keywords": ["prognosis", "life expectancy", "markers", "follow-up"],
            "signatures": {
                "behavioral_core": ["TR", "GO"],
                "condition_modifiers": ["HF"],
                "engagement_drivers": {"TR": 1, "GO": 1, "HL": 0, "SE": 0},
                "signature_tags": ["HF", "Prognosis", "Goals", "Monitoring"],
            },
            "responses": {
                "listener": "It’s okay to think about the future—it means you care.",
                "motivator": "Many people live for years—what matters is your path and your support.",
                "director": "Ask your team to track objective markers (echo results, symptoms, exercise tolerance, labs as ordered) and adjust therapy over time.",
                "expert": "Outcomes improve with adherence to guideline-directed therapy and timely follow-ups; prognosis varies widely by individual factors.",
            },
            "security_rules": [
                "If you notice a sudden, major symptom change (breathing at rest, chest pain, fainting), seek urgent evaluation.",
            ],
            "action_plans": [
                "Set one meaningful long-term goal (purpose supports resilience).",
                "Schedule regular check-ins to optimize therapy (timely updates keep care effective).",
            ],
        },
    ],
},

   
"Stroke": {
    "category": "Stroke",
    "title": "Stroke Recovery & Prevention",
    "source_defaults": [
        _aha_source("Stroke", "https://www.heart.org/en/health-topics/stroke"),
        _aha_source("Warning Signs of Stroke (FAST)", "https://www.heart.org/en/health-topics/stroke/warning-signs-of-stroke"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
    ],
    "questions": [
        {
            "question": "What caused my stroke?",
            "keywords": ["cause", "ischemic", "hemorrhagic", "etiology"],
            "signatures": {
                "behavioral_core": ["HL"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"HL": 1, "TR": 0, "SE": 0, "PR": 0, "GO": 0},
                "signature_tags": ["Stroke", "Etiology", "Education"],
            },
            "responses": {
                "listener": "You’re not alone in wondering why this happened.",
                "motivator": "Learning the cause helps you regain control.",
                "director": "Ask your provider to explain what likely caused your stroke and review your imaging and test results together.",
                "expert": "Most strokes are ischemic (clot-related) and some are hemorrhagic (bleeding). The cause guides prevention and treatment choices.",
            },
            "security_rules": [
                "Any new weakness, facial droop, speech trouble, vision loss, or confusion requires emergency care immediately.",
            ],
            "action_plans": [
                "Request a clear explanation of stroke type and cause in plain language.",
                "Ask for a copy of your discharge summary/stroke report for your records.",
            ],
        },
        {
            "question": "Am I at risk of having another stroke?",
            "keywords": ["recurrence", "risk", "secondary prevention"],
            "signatures": {
                "behavioral_core": ["PR"],
                "condition_modifiers": ["STROKE", "HTN", "AF", "DM"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "TR": 0, "GO": 0},
                "signature_tags": ["Stroke", "SecondaryPrevention", "Risk"],
            },
            "responses": {
                "listener": "It’s natural to worry—it means you care about your future.",
                "motivator": "You’ve already taken the first step—asking the question.",
                "director": "Follow your prevention plan: take meds as prescribed, track BP, and keep follow-ups for labs and monitoring.",
                "expert": "Secondary prevention (BP control, cholesterol treatment, AFib management, and medication adherence) is the strongest path to lowering recurrence risk.",
            },
            "security_rules": [
                "Do not stop antiplatelet/anticoagulant medicines without clinician guidance—stopping can raise stroke risk.",
            ],
            "action_plans": [
                "Schedule your next follow-up appointment before you leave the clinic/hospital.",
                "Track BP and medication adherence for 2 weeks and bring logs to visits.",
            ],
        },
        {
            "question": "Will I fully recover?",
            "keywords": ["recovery", "rehab", "neuroplasticity"],
            "signatures": {
                "behavioral_core": ["SE", "GO"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"SE": 1, "GO": 1, "HL": 0, "TR": 0, "PR": 0},
                "signature_tags": ["Stroke", "Recovery", "Rehab"],
            },
            "responses": {
                "listener": "Recovery looks different for everyone—and that’s okay.",
                "motivator": "With support and effort, many people make amazing recoveries.",
                "director": "Ask for PT/OT/speech therapy referrals and set one weekly functional goal you can practice daily.",
                "expert": "Neuroplasticity allows the brain to rewire over time. Repetition + meaningful practice drives improvements.",
            },
            "security_rules": [
                "Sudden worsening weakness, new severe headache, or confusion needs emergency evaluation.",
            ],
            "action_plans": [
                "Pick one daily practice (walking, hand exercises, speech drills) and track minutes.",
                "Celebrate one small win each week (builds momentum).",
            ],
        },
        {
            "question": "Can I drive again?",
            "keywords": ["driving", "independence", "safety evaluation"],
            "signatures": {
                "behavioral_core": ["PR", "ACCESS"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"PR": 1, "SE": 0, "HL": 0, "TR": 0, "GO": 0},
                "signature_tags": ["Stroke", "Driving", "Safety"],
            },
            "responses": {
                "listener": "Wanting to regain independence is totally normal.",
                "motivator": "Getting back behind the wheel is a goal worth working toward.",
                "director": "Ask your provider about readiness and request a formal driving assessment if recommended.",
                "expert": "Driving depends on vision, reaction time, cognition, and motor control. Many places require medical clearance or testing.",
            },
            "security_rules": [
                "Do not drive until you’ve been cleared—unsafe driving can harm you and others.",
            ],
            "action_plans": [
                "Ask: “Am I medically cleared to drive?” and “Do I need a driving evaluation?”",
                "Work with rehab on the specific skills driving requires (vision scanning, coordination, endurance).",
            ],
        },
        {
            "question": "Will I ever feel normal again?",
            "keywords": ["identity", "adjustment", "emotions", "fatigue"],
            "signatures": {
                "behavioral_core": ["ST", "SE"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"SE": 1, "TR": 1, "HL": 0, "GO": 0, "PR": 0},
                "signature_tags": ["Stroke", "EmotionalHealth", "Adjustment"],
            },
            "responses": {
                "listener": "This is one of the most honest and common questions.",
                "motivator": "You are adapting and growing—even now.",
                "director": "Talk about emotions and fatigue with your team. Set one personal goal that matters to you and revisit it monthly.",
                "expert": "Mood changes and fatigue are common after stroke. Support groups, counseling, and rehab can improve quality of life.",
            },
            "security_rules": [
                "If you have thoughts of self-harm or feel unsafe, seek urgent help from emergency services or a crisis line.",
            ],
            "action_plans": [
                "Choose one meaningful goal (family, purpose, hobby) and break it into weekly steps.",
                "Ask about counseling or a stroke support group (social support improves recovery).",
            ],
        },
        {
            "question": "How will this affect my memory or thinking?",
            "keywords": ["cognition", "memory", "attention", "neuropsychology"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Stroke", "Cognition", "BrainHealth"],
            },
            "responses": {
                "listener": "It’s okay to notice changes and feel concerned.",
                "motivator": "Your brain can rebuild new connections.",
                "director": "Tell your provider what you’re noticing and ask about a neuropsychological assessment if problems persist.",
                "expert": "Cognitive effects vary by stroke location/severity. Strategies like routines, reminders, and targeted therapy can help.",
            },
            "security_rules": [
                "New sudden confusion, severe headache, or weakness is an emergency—seek care immediately.",
            ],
            "action_plans": [
                "Use a daily routine + reminders (calendar, alarms, checklists).",
                "Ask for cognitive rehab or neuropsych testing if thinking changes interfere with life.",
            ],
        },
        {
            "question": "What kind of rehabilitation do I need?",
            "keywords": ["rehab", "PT", "OT", "speech therapy"],
            "signatures": {
                "behavioral_core": ["ACCESS", "GO"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"GO": 1, "SE": 1, "HL": 0, "TR": 0, "PR": 0},
                "signature_tags": ["Stroke", "Rehab", "Plan"],
            },
            "responses": {
                "listener": "Rehab can feel overwhelming—we’ll take it step by step.",
                "motivator": "You’re investing in your recovery with every rehab session.",
                "director": "Ask for a personalized rehab plan (PT/OT/speech) and agree on 2–3 goals that matter to you.",
                "expert": "Stroke rehab should start once medically stable. Early, consistent therapy improves long-term function.",
            },
            "security_rules": [
                "Report new falls, sudden weakness, or severe headaches promptly.",
            ],
            "action_plans": [
                "Before discharge, ask: “What therapy do I need and how often?”",
                "Track rehab attendance and home exercises weekly (consistency drives gains).",
            ],
        },
        {
            "question": "What lifestyle changes should I make?",
            "keywords": ["lifestyle", "blood pressure", "cholesterol", "exercise", "nutrition"],
            "signatures": {
                "behavioral_core": ["HB"],
                "condition_modifiers": ["STROKE", "HTN", "DM", "CAD"],
                "engagement_drivers": {"GO": 1, "HL": 1, "SE": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Stroke", "Prevention", "LifeEssential8"],
            },
            "responses": {
                "listener": "Changing habits is hard—but you’re not alone.",
                "motivator": "You’re strong enough to make changes that protect your brain and heart.",
                "director": "Focus on the big levers: BP control, cholesterol, diabetes care, movement, and tobacco avoidance.",
                "expert": "Life’s Essential 8 targets (sleep, diet, activity, weight, BP, cholesterol, glucose, tobacco) are evidence-based drivers of risk reduction.",
            },
            "security_rules": [
                "Any exercise plan after stroke should be cleared by your healthcare team if you have balance issues or heart symptoms.",
            ],
            "action_plans": [
                "Pick ONE change this week (10-min walk, salt reduction, pill routine).",
                "Use a simple weekly checklist for BP, activity, meds, and sleep.",
            ],
        },
        {
            "question": "What medications will I need long-term?",
            "keywords": ["medications", "antiplatelet", "statin", "anticoagulant"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["STROKE", "AF", "HTN"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Stroke", "Meds", "Adherence"],
            },
            "responses": {
                "listener": "It’s okay to have questions about new medications.",
                "motivator": "Taking your medications is an act of self-care.",
                "director": "Keep a current med list and ask what each medication does and when to take it.",
                "expert": "Common post-stroke meds include antiplatelets, statins, BP meds, and anticoagulants if AFib is present—tailored to your cause/risk.",
            },
            "security_rules": [
                "Do not stop blood thinners or antiplatelets without medical guidance.",
            ],
            "action_plans": [
                "Make a simple med chart: name, dose, time, purpose.",
                "Set reminders and bring your list to every appointment.",
            ],
        },
        {
            "question": "How can my family help me?",
            "keywords": ["caregiver", "support", "family"],
            "signatures": {
                "behavioral_core": ["TR", "ACCESS"],
                "condition_modifiers": ["STROKE"],
                "engagement_drivers": {"TR": 1, "SE": 1, "HL": 0, "GO": 0, "PR": 0},
                "signature_tags": ["Stroke", "Caregiver", "Support"],
            },
            "responses": {
                "listener": "Asking for help shows strength, not weakness.",
                "motivator": "Your recovery is stronger when it’s a team effort.",
                "director": "Invite a family member to a visit and create a simple shared plan for meds, transportation, and rehab support.",
                "expert": "Caregiver education and support can improve recovery and reduce readmissions by improving adherence and early symptom recognition.",
            },
            "security_rules": [
                "Caregivers should know FAST stroke warning signs and emergency steps.",
            ],
            "action_plans": [
                "Create a shared calendar for appointments/therapy and a medication checklist.",
                "Ask your care team for caregiver resources and training materials.",
            ],
        },
    ],
},
    
    "DIABETES": {
    "category": "DIABETES",
    "title": "Diabetes Management & Prevention",
    "source_defaults": [
        _aha_source("Diabetes", "https://www.heart.org/en/health-topics/diabetes"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
    ],
    "questions": [
        {
            "question": "What should my blood sugar levels be?",
            "keywords": ["targets", "glucose", "fasting", "post-meal"],
            "signatures": {
                "behavioral_core": ["HL", "SY"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"HL": 1, "SE": 1, "GO": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Targets", "Monitoring"],
            },
            "responses": {
                "listener": "It’s normal to feel confused about numbers at first.",
                "motivator": "Knowing your numbers is a key to taking control.",
                "director": "Typical targets: fasting 80–130 mg/dL, after meals <180 mg/dL. Ask your team for your personalized range.",
                "expert": "Targets vary by age, medications, hypoglycemia risk, and comorbidities—individualized goals are safest.",
            },
            "security_rules": [
                "Repeated readings <70 mg/dL or very high readings (e.g., >300 mg/dL) should be reviewed promptly with a clinician.",
            ],
            "action_plans": [
                "Ask for your personal glucose targets and when to check.",
                "Track readings for 7 days and note meals/activity to find patterns.",
            ],
        },
        {
            "question": "What foods should I avoid or eat more of?",
            "keywords": ["diet", "carbs", "fiber", "plate method"],
            "signatures": {
                "behavioral_core": ["NUT"],
                "condition_modifiers": ["DM", "CKM", "CAD"],
                "engagement_drivers": {"HL": 1, "GO": 0, "SE": 0, "PR": 0, "FI": 0},
                "signature_tags": ["Diabetes", "Nutrition", "Carbs"],
            },
            "responses": {
                "listener": "You don’t have to give up all your favorite foods.",
                "motivator": "Every healthy meal is a step toward better control.",
                "director": "Try the plate method: half non-starchy veggies, quarter protein, quarter carbs. Choose fiber-rich carbs and limit sugary drinks.",
                "expert": "Fiber-rich patterns (Mediterranean/DASH-style) support glucose and heart health; refined carbs and added sugars increase spikes.",
            },
            "security_rules": [
                "If you use insulin or sulfonylureas, don’t skip meals without guidance—hypoglycemia risk can rise.",
            ],
            "action_plans": [
                "Make one swap this week: sugary drink → water or unsweetened tea.",
                "Add one fiber target daily (beans, oats, veggies, whole grains).",
            ],
        },
        {
            "question": "Do I need to check my blood sugar every day?",
            "keywords": ["monitoring", "frequency", "CGM", "meter"],
            "signatures": {
                "behavioral_core": ["HL", "SY"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"HL": 1, "SE": 0, "PR": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Monitoring", "Plan"],
            },
            "responses": {
                "listener": "Testing can feel like a hassle—it’s okay to feel that way.",
                "motivator": "Each check gives you insight into what works.",
                "director": "Ask your provider what schedule fits your meds and goals. Some people need daily checks; others need less frequent monitoring.",
                "expert": "Frequency depends on treatment (especially insulin), hypoglycemia risk, and A1c control—match monitoring to clinical need.",
            },
            "security_rules": [
                "If you have frequent lows/highs, contact your clinician—medications may need adjustment.",
            ],
            "action_plans": [
                "Agree on a monitoring schedule with your care team.",
                "When you test, note context (meal, exercise, stress, sleep).",
            ],
        },
        {
            "question": "Can I still exercise safely with diabetes?",
            "keywords": ["exercise", "activity", "safety", "insulin"],
            "signatures": {
                "behavioral_core": ["PA", "PR"],
                "condition_modifiers": ["DM", "CAD", "HTN"],
                "engagement_drivers": {"SE": 1, "PR": 1, "GO": 0, "HL": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Exercise", "Safety"],
            },
            "responses": {
                "listener": "Exercise can be intimidating at first—especially if you’ve had a scare.",
                "motivator": "Moving your body is one of the best things you can do.",
                "director": "Start with walks after meals. If on insulin, check glucose before/after and carry fast carbs.",
                "expert": "About 150 minutes/week of moderate activity improves glucose, BP, and weight; combining aerobic + resistance is especially effective.",
            },
            "security_rules": [
                "If you have chest pain, severe shortness of breath, dizziness, or signs of low glucose during exercise, stop and seek help.",
            ],
            "action_plans": [
                "Walk 10 minutes after one meal daily this week.",
                "Keep a small hypoglycemia kit (glucose tabs/juice) available when active.",
            ],
        },
        {
            "question": "How often should I get my A1c checked?",
            "keywords": ["A1c", "labs", "frequency"],
            "signatures": {
                "behavioral_core": ["PC", "HL"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"HL": 1, "GO": 1, "SE": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Diabetes", "A1c", "Monitoring"],
            },
            "responses": {
                "listener": "Blood work can be stressful—I get it.",
                "motivator": "Knowing your A1c helps you see how far you’ve come.",
                "director": "Many people check every 3–6 months depending on control. Ask your provider to set a schedule.",
                "expert": "A1c reflects average glucose over ~2–3 months and helps guide therapy adjustments over time.",
            },
            "security_rules": [
                "If you have frequent hypoglycemia or rapid symptom changes, discuss earlier follow-up with your clinician.",
            ],
            "action_plans": [
                "Put your next A1c date on your calendar today.",
                "Track your A1c results in a simple log to see trends.",
            ],
        },
        {
            "question": "What is A1c and why is it important?",
            "keywords": ["A1c", "average glucose", "complications"],
            "signatures": {
                "behavioral_core": ["HL"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"HL": 1, "SE": 0, "GO": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Diabetes", "A1c", "Education"],
            },
            "responses": {
                "listener": "It’s okay if the term sounds new—it trips up a lot of people at first.",
                "motivator": "Knowing your A1c gives you power to improve it.",
                "director": "A1c is your average blood sugar over a few months. Ask what your target is and how to move it safely.",
                "expert": "A1c is a key marker tied to complication risk; it complements daily checks by showing longer-term control.",
            },
            "security_rules": [
                "Do not change medications solely based on one number—review results with your clinician.",
            ],
            "action_plans": [
                "Ask: “What’s my A1c target and why?”",
                "Pick one behavior linked to your A1c trend (sleep, movement, nutrition, meds).",
            ],
        },
        {
            "question": "What should I do if I feel shaky or sweaty?",
            "keywords": ["hypoglycemia", "low blood sugar", "15-15 rule"],
            "signatures": {
                "behavioral_core": ["PR"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Hypoglycemia", "Safety"],
            },
            "responses": {
                "listener": "That can feel scary—lots of people experience it.",
                "motivator": "Learning your body’s signals makes you stronger.",
                "director": "Check glucose if you can. Treat with 15g fast carbs, recheck in 15 minutes, and repeat if still low.",
                "expert": "Hypoglycemia is typically <70 mg/dL and needs fast correction; frequent lows mean your plan may need adjustment.",
            },
            "security_rules": [
                "If you pass out, have a seizure, or can’t safely swallow, call emergency services immediately.",
            ],
            "action_plans": [
                "Keep glucose tablets or juice nearby at home/work.",
                "If lows happen more than occasionally, ask your clinician to review meds and timing.",
            ],
        },
        {
            "question": "What long-term complications should I watch for?",
            "keywords": ["complications", "kidney", "eyes", "feet", "heart"],
            "signatures": {
                "behavioral_core": ["PC"],
                "condition_modifiers": ["DM", "CKM", "CAD"],
                "engagement_drivers": {"PR": 1, "HL": 1, "GO": 0, "SE": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Complications", "Screening"],
            },
            "responses": {
                "listener": "It’s tough to hear about complications—but you’re asking the right question.",
                "motivator": "You’re doing the brave work of prevention.",
                "director": "Schedule yearly eye, foot, and kidney checks, and report new symptoms early.",
                "expert": "Diabetes increases risks for heart disease, stroke, kidney disease, and nerve damage—screening and multi-factor control reduce harm.",
            },
            "security_rules": [
                "Seek urgent care for chest pain, stroke symptoms, or infected foot wounds.",
            ],
            "action_plans": [
                "Book annual eye and foot exams; confirm kidney labs schedule.",
                "Use a simple symptom checklist and bring it to visits.",
            ],
        },
        {
            "question": "Will I always have to take medication?",
            "keywords": ["medications", "long-term plan", "remission"],
            "signatures": {
                "behavioral_core": ["HL", "GO"],
                "condition_modifiers": ["DM"],
                "engagement_drivers": {"HL": 1, "GO": 1, "SE": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Meds", "SharedDecisionMaking"],
            },
            "responses": {
                "listener": "Many people wonder the same thing—it’s a valid concern.",
                "motivator": "In some cases, people do reduce meds through lifestyle changes—step by step.",
                "director": "Never stop meds without guidance. Ask what milestones could allow dose reduction and how you’ll monitor safely.",
                "expert": "Medication needs depend on diabetes type, duration, genetics, and risks. Reassess periodically with your clinician.",
            },
            "security_rules": [
                "Do not stop insulin or prescribed medications abruptly without medical supervision.",
            ],
            "action_plans": [
                "Ask: “What would success look like in 3–6 months?”",
                "Reevaluate your regimen every 6–12 months (or sooner if lows/highs occur).",
            ],
        },
        {
            "question": "How can I prevent serious complications?",
            "keywords": ["prevention", "ABCs", "A1c", "blood pressure", "cholesterol"],
            "signatures": {
                "behavioral_core": ["PR"],
                "condition_modifiers": ["DM", "CAD", "HTN", "CKM"],
                "engagement_drivers": {"PR": 1, "GO": 1, "HL": 1, "SE": 0, "TR": 0},
                "signature_tags": ["Diabetes", "Prevention", "ABCs"],
            },
            "responses": {
                "listener": "It’s okay to feel overwhelmed—but you’re not powerless.",
                "motivator": "You have the power to change your story—one habit at a time.",
                "director": "Focus on ABCs: A1c, blood pressure, and cholesterol. Add movement, sleep, and tobacco-free living.",
                "expert": "Multi-factor control can substantially reduce complications. Consistency across behaviors + meds matters most.",
            },
            "security_rules": [
                "If you have severe symptoms (confusion, chest pain, stroke signs, or repeated severe lows), seek urgent care.",
            ],
            "action_plans": [
                "Build a simple tracker for A1c, BP, LDL with dates and targets.",
                "Choose one habit to stick to this week and review results weekly.",
            ],
        },
    ],
},
    
"WELLNESS": {
    "category": "WELLNESS",
    "title": "Whole-Person Wellness & Prevention",
    "source_defaults": [
        _aha_source("Healthy Living", "https://www.heart.org/en/healthy-living"),
        _aha_source("Life’s Essential 8", "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8"),
    ],
    "questions": [
        {
            "question": "How much water should I drink each day?",
            "keywords": ["hydration", "water", "fluids"],
            "signatures": {
                "behavioral_core": ["HB"],
                "condition_modifiers": ["WELLNESS"],
                "engagement_drivers": {"SE": 1, "HL": 1, "GO": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Wellness", "Hydration"],
            },
            "responses": {
                "listener": "How do you feel when you’re hydrated? Your body often gives clues.",
                "motivator": "Staying hydrated is one of the easiest ways to boost energy and focus.",
                "director": "Aim for a simple baseline like 6–8 cups/day unless your clinician recommends otherwise, and adjust for heat/exercise.",
                "expert": "Hydration needs vary by body size, activity, and environment; total intake includes water from foods.",
            },
            "security_rules": [
                "If you have heart failure or kidney disease, follow your clinician’s fluid guidance (do not increase fluids automatically).",
            ],
            "action_plans": [
                "Keep a refillable water bottle nearby and refill it twice daily.",
                "Use a simple goal (cups/day) for 7 days and note energy/headaches.",
            ],
        },
        {
            "question": "How much sleep do I need?",
            "keywords": ["sleep", "rest", "7-9 hours"],
            "signatures": {
                "behavioral_core": ["SLEEP"],
                "condition_modifiers": ["WELLNESS"],
                "engagement_drivers": {"HL": 1, "SE": 1, "GO": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Wellness", "Sleep"],
            },
            "responses": {
                "listener": "Think about when you feel your best—sleep is often the difference-maker.",
                "motivator": "Sleep is your superpower. Small improvements add up fast.",
                "director": "Most adults do best with 7–9 hours. Set a consistent wake time and protect a wind-down routine.",
                "expert": "Short sleep is linked with higher cardiometabolic risk; sleep is one of AHA’s Life’s Essential 8 metrics.",
            },
            "security_rules": [
                "If you have severe daytime sleepiness, loud snoring, or breathing pauses, ask about sleep apnea evaluation.",
            ],
            "action_plans": [
                "Set a consistent wake time for 7 days.",
                "Reduce screens 30 minutes before bed and track sleep quality (0–10).",
            ],
        },
        {
            "question": "What is a normal blood pressure?",
            "keywords": ["blood pressure", "normal", "120/80"],
            "signatures": {
                "behavioral_core": ["HL", "PC"],
                "condition_modifiers": ["WELLNESS", "HTN"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Wellness", "BloodPressure", "Basics"],
            },
            "responses": {
                "listener": "Knowing your numbers is an act of self-care.",
                "motivator": "Every healthy choice moves you closer to your goal.",
                "director": "A common target is <120/80. If you’re consistently ≥130/80, discuss next steps with your clinician.",
                "expert": "Higher BP increases risk for heart attack, stroke, and kidney disease; trends over time matter more than a single reading.",
            },
            "security_rules": [
                "If BP is extremely high (e.g., ~180/120) with symptoms like chest pain or severe headache, seek urgent care.",
            ],
            "action_plans": [
                "Check BP twice weekly at the same time and log results.",
                "Bring readings to your next appointment for trend review.",
            ],
        },
        {
            "question": "How can I lose weight in a healthy way?",
            "keywords": ["weight loss", "calorie deficit", "habits"],
            "signatures": {
                "behavioral_core": ["HB", "GO"],
                "condition_modifiers": ["WELLNESS", "CKM"],
                "engagement_drivers": {"GO": 1, "SE": 1, "HL": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Wellness", "Weight", "Habits"],
            },
            "responses": {
                "listener": "What’s worked for you in the past? You’re not alone in this.",
                "motivator": "Small, consistent changes lead to lasting results—progress over perfection.",
                "director": "Aim for a modest calorie deficit, balanced meals, and ≥150 minutes/week of activity. Track and adjust weekly.",
                "expert": "Evidence supports multi-component approaches: nutrition + activity + behavior strategies; resistance training helps preserve lean mass.",
            },
            "security_rules": [
                "Avoid extreme diets or rapid weight-loss products; discuss safe targets if you have chronic conditions.",
            ],
            "action_plans": [
                "Choose one lever this week: reduce sugary drinks or add 10 minutes walking daily.",
                "Track weight weekly (not daily) and focus on trend lines.",
            ],
        },
        {
            "question": "What are the symptoms of a heart attack?",
            "keywords": ["heart attack", "chest pain", "warning signs"],
            "signatures": {
                "behavioral_core": ["PR"],
                "condition_modifiers": ["WELLNESS", "CAD"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Wellness", "HeartAttack", "Emergency"],
            },
            "responses": {
                "listener": "If something doesn’t feel right, it’s okay to seek help right away.",
                "motivator": "Recognizing signs early could save your life—share what you learn with others too.",
                "director": "Call 911 for chest pressure/pain, shortness of breath, sweating, nausea, or jaw/back pain—don’t drive yourself.",
                "expert": "Heart attacks can present with typical or atypical symptoms; immediate emergency evaluation improves outcomes.",
            },
            "security_rules": [
                "Do not wait for symptoms to pass—call emergency services for suspected heart attack symptoms.",
            ],
            "action_plans": [
                "Save emergency numbers and share a plan with family.",
                "Learn the warning signs and review them twice a year.",
            ],
        },
        {
            "question": "How can I lower my cholesterol naturally?",
            "keywords": ["cholesterol", "LDL", "fiber", "diet", "exercise"],
            "signatures": {
                "behavioral_core": ["NUT", "PA"],
                "condition_modifiers": ["WELLNESS", "CAD"],
                "engagement_drivers": {"GO": 0, "HL": 1, "SE": 0, "PR": 0, "TR": 0},
                "signature_tags": ["Wellness", "Cholesterol", "LDL"],
            },
            "responses": {
                "listener": "It’s great you’re asking—small shifts can make a big difference.",
                "motivator": "Every healthy bite and step helps—keep going.",
                "director": "Increase soluble fiber, reduce saturated fat, avoid trans fats, and build regular aerobic activity. Recheck labs in 3–6 months.",
                "expert": "LDL reduction correlates with lower CVD risk; dietary patterns and exercise help, and medications may still be needed for high-risk patients.",
            },
            "security_rules": [
                "Do not stop statins or prescribed meds without clinician guidance.",
            ],
            "action_plans": [
                "Add one fiber-rich food daily (oats, beans, fruit, veggies).",
                "Schedule a lipid panel follow-up date and track progress.",
            ],
        },
        {
            "question": "When should I get screened for cancer?",
            "keywords": ["screening", "cancer", "prevention"],
            "signatures": {
                "behavioral_core": ["PC"],
                "condition_modifiers": ["WELLNESS"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Wellness", "Screening", "Prevention"],
            },
            "responses": {
                "listener": "Screenings are about peace of mind—you’re doing the right thing by asking.",
                "motivator": "Prevention is powerful. Catching things early changes outcomes.",
                "director": "Ask your clinician which screenings you need based on age, sex, and family history, and schedule the next one.",
                "expert": "Screening intervals vary by risk; shared decisions based on guidelines help avoid missed prevention opportunities.",
            },
            "security_rules": [
                "New alarming symptoms (unexplained bleeding, rapid weight loss) should be evaluated promptly—don’t wait for routine screening.",
            ],
            "action_plans": [
                "Ask: “Which screenings am I due for this year?”",
                "Create a preventive care checklist with dates (annual review).",
            ],
        },
        {
            "question": "How do I prevent type 2 diabetes?",
            "keywords": ["prediabetes", "prevention", "lifestyle"],
            "signatures": {
                "behavioral_core": ["PR", "HB"],
                "condition_modifiers": ["WELLNESS", "DM"],
                "engagement_drivers": {"GO": 1, "SE": 1, "HL": 1, "PR": 1, "TR": 0},
                "signature_tags": ["Wellness", "DiabetesPrevention"],
            },
            "responses": {
                "listener": "It’s smart to ask early—prevention works best before problems build.",
                "motivator": "You’re in control. Small daily choices can prevent or delay diabetes.",
                "director": "Aim for 150 minutes/week activity, reduce sugary drinks, and consider a 5–7% weight loss goal if advised.",
                "expert": "Lifestyle intervention is strongly supported; screening with A1c or fasting glucose is appropriate if risk factors are present.",
            },
            "security_rules": [
                "If you already have symptoms of high glucose (excess thirst/urination, blurry vision), seek clinical evaluation.",
            ],
            "action_plans": [
                "Walk 10 minutes after dinner 5 days this week.",
                "Swap sugary drinks for water or unsweetened beverages.",
            ],
        },
        {
            "question": "Is it safe to take vitamins or supplements?",
            "keywords": ["supplements", "vitamins", "safety", "interactions"],
            "signatures": {
                "behavioral_core": ["HL", "PR"],
                "condition_modifiers": ["WELLNESS"],
                "engagement_drivers": {"HL": 1, "PR": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Wellness", "Supplements", "Safety"],
            },
            "responses": {
                "listener": "It’s good you’re asking—wanting clarity is smart.",
                "motivator": "Being informed is a powerful health habit.",
                "director": "Only take supplements if medically indicated; choose reputable brands and tell your clinician what you take.",
                "expert": "Evidence varies widely; supplements can interact with medications (especially blood thinners). Testing for deficiency is often better than guessing.",
            },
            "security_rules": [
                "Avoid mega-doses and avoid starting supplements if you’re on anticoagulants without clinician review (interaction risk).",
            ],
            "action_plans": [
                "Make a list of all supplements/OTC meds and bring it to your next visit.",
                "Ask if lab testing for deficiency is appropriate before supplementing.",
            ],
        },
        {
            "question": "How often should I get a physical check-up?",
            "keywords": ["checkup", "annual visit", "prevention"],
            "signatures": {
                "behavioral_core": ["PC"],
                "condition_modifiers": ["WELLNESS"],
                "engagement_drivers": {"PR": 1, "HL": 1, "SE": 0, "GO": 0, "TR": 0},
                "signature_tags": ["Wellness", "PrimaryCare", "Prevention"],
            },
            "responses": {
                "listener": "Your annual visit is a chance to check in—body and mind.",
                "motivator": "Staying ahead of issues is a form of self-respect and strength.",
                "director": "Schedule at least yearly if you have chronic conditions; otherwise follow your clinician’s recommended interval.",
                "expert": "Routine care typically includes BP, lipids, glucose screening, immunizations, and preventive counseling tailored to age and risk.",
            },
            "security_rules": [
                "Do not delay evaluation for urgent symptoms—acute issues should be addressed immediately, not at the next routine physical.",
            ],
            "action_plans": [
                "Schedule your next check-up now (or set a reminder 11 months out).",
                "Bring a short agenda: top concerns, meds, vitals logs, screenings due.",
            ],
        },
    ],
}

    
}


# -----------------------------
# Build QUESTION_BANK from PACKS
# -----------------------------

def build_question_bank(packs: Dict[str, Dict[str, Any]]) -> QuestionBank:
    bank: QuestionBank = {}

    for pack_code_raw, pack in packs.items():
        pack_code = slug_upper(pack_code_raw) or "PACK"
        category = pack.get("category", pack_code)
        source_defaults = pack.get("source_defaults", [])

        questions = pack.get("questions", [])
        if not isinstance(questions, list):
            continue

        for i, q in enumerate(questions, start=1):
            qid = build_id(pack_code, i)

            question_text = str(q.get("question", "")).strip()
            title = str(q.get("title", question_text)).strip() or question_text

            # Normalize
            responses = ensure_persona_responses(q.get("responses"))
            signatures = q.get("signatures", {})
            if not isinstance(signatures, dict):
                signatures = {}

            # Normalize tags
            behavioral_core = [str(x).strip().upper() for x in (signatures.get("behavioral_core") or []) if str(x).strip()]
            condition_modifiers = [str(x).strip().upper() for x in (signatures.get("condition_modifiers") or []) if str(x).strip()]
            engagement_drivers = normalize_engagement_drivers(signatures.get("engagement_drivers") or {})

            # Attach
            item: Question = {
                "id": qid,
                "category": str(category).strip().upper() if str(category).strip() else pack_code,
                "title": title,
                "question": question_text,
                "keywords": [str(x).strip().lower() for x in (q.get("keywords") or []) if str(x).strip()],
                "responses": responses,
                "signatures": {
                    "behavioral_core": behavioral_core,
                    "condition_modifiers": condition_modifiers,
                    "engagement_drivers": engagement_drivers,  # -1/0/+1
                },
                "security_rules": ensure_list(q.get("security_rules")),
                "action_plans": ensure_list(q.get("action_plans")),
                "sources": q.get("sources", source_defaults) or source_defaults,
            }

            bank[qid] = item

    return bank


QUESTION_BANK: QuestionBank = build_question_bank(PACKS)


# -----------------------------
# Optional: auto-fix pass (safe)
# -----------------------------

def autofix_question_bank(question_bank: QuestionBank) -> List[BankIssue]:
    """
    Non-destructive fixes:
    - ensure persona responses exist (auto-fill)
    - ensure security_rules/action_plans exist as lists
    - normalize engagement driver values to -1/0/+1
    """
    fixes: List[BankIssue] = []

    for qid, q in question_bank.items():
        # Responses
        q["responses"] = ensure_persona_responses(q.get("responses"))
        # Lists
        if "security_rules" not in q or not isinstance(q.get("security_rules"), list):
            q["security_rules"] = ensure_list(q.get("security_rules"))
            fixes.append(BankIssue("warn", qid, "auto-fixed security_rules to list[str]"))
        if "action_plans" not in q or not isinstance(q.get("action_plans"), list):
            q["action_plans"] = ensure_list(q.get("action_plans"))
            fixes.append(BankIssue("warn", qid, "auto-fixed action_plans to list[str]"))
        # Drivers
        sig = q.get("signatures", {})
        if isinstance(sig, dict):
            sig["engagement_drivers"] = normalize_engagement_drivers(sig.get("engagement_drivers"))
            q["signatures"] = sig

    return fixes


# Run a small validation on import (non-fatal)
_issues = validate_question_bank(QUESTION_BANK, raise_on_error=False)
# You can inspect _issues from signatures_engine if you want.


# -----------------------------
# Convenience exports for signatures_engine.py imports
# -----------------------------
__all__ = [
    "PERSONAS",
    "QUESTION_BANK",
    "BankIssue",
    "all_categories",
    "list_categories",
    "list_question_summaries",
    "get_question_by_id",
    "search_questions",
    "validate_question_bank",
    "autofix_question_bank",
]

