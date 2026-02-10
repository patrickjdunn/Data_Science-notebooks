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

    #next pack

    #end of next pack
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

