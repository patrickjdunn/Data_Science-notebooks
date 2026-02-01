"""
questions.py

Question bank for the Signatures Engine.

Features
- Stores questions by category (CKM, HTN, HF, CAD, AFIB, STROKE, DM).
- Auto-generates stable IDs like "CKM-01", "HTN-10", etc.
- Provides helpers to list, filter, get by id, and search.

Data model for each question:
{
  "id": "CKM-01",
  "category": "CKM",
  "question": "...",
  "persona": {
      "Listener": {"message": "...", "action_step": "...", "why": "..."},
      "Motivator": {...},
      "Director": {...},
      "Expert": {...},
  },
  # Optional extra metadata you can extend later:
  "tags": ["exercise", "diet"],
  "notes": "...",
}

If you add new categories later, just add them to RAW_QUESTION_SETS,
and IDs will be regenerated automatically.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import re


# ----------------------------
# Helpers / normalization
# ----------------------------

PERSONAS = ("Listener", "Motivator", "Director", "Expert")

def _clean_text(s: str) -> str:
    return " ".join((s or "").strip().split())

def _ensure_persona_block(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures all 4 personas exist. Missing personas are filled with safe placeholders.
    """
    out = {}
    for persona in PERSONAS:
        block = p.get(persona, {}) if isinstance(p.get(persona, {}), dict) else {}
        out[persona] = {
            "message": _clean_text(block.get("message", "")) or "(Message pending.)",
            "action_step": _clean_text(block.get("action_step", "")) or "(Action step pending.)",
            "why": _clean_text(block.get("why", "")) or "(Rationale pending.)",
        }
    return out


# ----------------------------
# RAW question sets (NO IDs here)
# ----------------------------

RAW_QUESTION_SETS: Dict[str, List[Dict[str, Any]]] = {

    # ========= CKM (Cardio-Kidney-Metabolic) =========
    "CKM": [
        {
            "question": "What does my diagnosis mean for my future?",
            "persona": {
                "Listener": {
                    "message": "That sounds overwhelming. What are you most worried about?",
                    "action_step": "Write down your top 3 concerns.",
                    "why": "Sharing helps your care team focus on what matters to you.",
                },
                "Motivator": {
                    "message": "You can live a full life with support.",
                    "action_step": "Set one small health goal, like a daily walk.",
                    "why": "Goals help build confidence and momentum.",
                },
                "Director": {
                    "message": "Let’s monitor labs and scores every 3 months.",
                    "action_step": "Schedule your next lab appointment.",
                    "why": "Staying on track helps catch changes early.",
                },
                "Expert": {
                    "message": "Early action guided by PREVENT and Life’s Essential 8 makes a difference.",
                    "action_step": "Ask for your PREVENT score.",
                    "why": "Personalized scores help guide care decisions.",
                },
            },
            "tags": ["prognosis", "planning", "risk"],
        },
        {
            "question": "What can I eat—and what should I avoid?",
            "persona": {
                "Listener": {
                    "message": "What foods do you enjoy? Let’s start there.",
                    "action_step": "Track meals for 3 days.",
                    "why": "Helps identify strengths and needed changes.",
                },
                "Motivator": {
                    "message": "Healthy food can taste great.",
                    "action_step": "Try one new heart-healthy recipe.",
                    "why": "Enjoyment builds lasting habits.",
                },
                "Director": {
                    "message": "Follow DASH or Mediterranean-style eating.",
                    "action_step": "Replace one salty snack with fruit or veggies.",
                    "why": "Small swaps lower blood pressure.",
                },
                "Expert": {
                    "message": "These diets reduce stroke and heart risk by 20–30%.",
                    "action_step": "Use a food-tracking app.",
                    "why": "Tools support consistency.",
                },
            },
            "tags": ["diet", "nutrition", "dash", "mediterranean"],
        },
        {
            "question": "Why am I on so many medications?",
            "persona": {
                "Listener": {
                    "message": "Do any cause side effects or confusion?",
                    "action_step": "Bring all meds to your next visit.",
                    "why": "Helps avoid duplication and interactions.",
                },
                "Motivator": {
                    "message": "Each one helps protect your organs.",
                    "action_step": "Use a pillbox or phone reminders.",
                    "why": "Improves medication adherence.",
                },
                "Director": {
                    "message": "Your meds follow evidence-based guidelines.",
                    "action_step": "Ask what each one does.",
                    "why": "Understanding builds trust.",
                },
                "Expert": {
                    "message": "Proper medication use reduces ER visits and complications.",
                    "action_step": "Report missed doses or side effects.",
                    "why": "Your doctor can adjust your regimen.",
                },
            },
            "tags": ["meds", "adherence"],
        },
        {
            "question": "How do I know if my condition is getting better or worse?",
            "persona": {
                "Listener": {
                    "message": "Notice any changes in how you feel?",
                    "action_step": "Keep a weekly symptom log.",
                    "why": "Tracking helps spot changes early.",
                },
                "Motivator": {
                    "message": "Monitoring gives you control.",
                    "action_step": "Check BP twice weekly.",
                    "why": "Prevents silent worsening.",
                },
                "Director": {
                    "message": "We’ll review your data and labs regularly.",
                    "action_step": "Ask your provider to explain recent results.",
                    "why": "Helps guide next steps.",
                },
                "Expert": {
                    "message": "Scores like Life’s Essential 8 track real progress.",
                    "action_step": "Ask how your score is trending.",
                    "why": "It reflects your health across multiple systems.",
                },
            },
            "tags": ["monitoring", "labs", "tracking"],
        },
        {
            "question": "Will I need dialysis or heart surgery?",
            "persona": {
                "Listener": {
                    "message": "That’s a scary thought. What worries you most?",
                    "action_step": "Write down questions to ask your doctor.",
                    "why": "Reduces fear and supports planning.",
                },
                "Motivator": {
                    "message": "You can take steps to lower that risk.",
                    "action_step": "Stick to your BP and A1c goals.",
                    "why": "These are major protective factors.",
                },
                "Director": {
                    "message": "We’ll monitor kidney and heart function closely.",
                    "action_step": "Stay up to date on labs.",
                    "why": "Early detection means early action.",
                },
                "Expert": {
                    "message": "Managing BP and A1c cuts surgery/dialysis risk in half.",
                    "action_step": "Consider seeing a specialist.",
                    "why": "Experts can tailor your plan.",
                },
            },
            "tags": ["kidney", "dialysis", "procedures"],
        },
        {
            "question": "Can I still exercise?",
            "persona": {
                "Listener": {
                    "message": "What kind of movement do you enjoy?",
                    "action_step": "Try a 10-minute walk after a meal.",
                    "why": "Even light activity helps control glucose.",
                },
                "Motivator": {
                    "message": "Movement is medicine!",
                    "action_step": "Set a weekly activity goal.",
                    "why": "Goals support consistency.",
                },
                "Director": {
                    "message": "Aim for 150 minutes/week.",
                    "action_step": "Ask about cardiac rehab.",
                    "why": "Rehab offers safe, tailored exercise.",
                },
                "Expert": {
                    "message": "Exercise improves BP, cholesterol, and kidney function.",
                    "action_step": "Use a fitness tracker.",
                    "why": "Builds motivation and routine.",
                },
            },
            "tags": ["exercise", "activity", "rehab"],
        },
        {
            "question": "What’s a healthy blood pressure for me?",
            "persona": {
                "Listener": {
                    "message": "Do you remember your last reading?",
                    "action_step": "Take a photo of your BP log.",
                    "why": "Visuals help share your progress.",
                },
                "Motivator": {
                    "message": "Lower BP = better brain, heart, kidney health.",
                    "action_step": "Reduce one salty item.",
                    "why": "Sodium affects your pressure.",
                },
                "Director": {
                    "message": "Target is usually <130/80.",
                    "action_step": "Take BP at the same time daily.",
                    "why": "Reduces variability in readings.",
                },
                "Expert": {
                    "message": "Control lowers stroke and kidney failure risk.",
                    "action_step": "Bring cuff to your visit.",
                    "why": "We can check its accuracy.",
                },
            },
            "tags": ["bp", "targets"],
        },
        {
            "question": "How can I manage this and still live my life?",
            "persona": {
                "Listener": {
                    "message": "What’s been hardest lately?",
                    "action_step": "Write down your top 3 challenges.",
                    "why": "Knowing barriers helps us support you.",
                },
                "Motivator": {
                    "message": "You’re not alone—and you’re stronger than you think.",
                    "action_step": "Find a health buddy.",
                    "why": "Accountability makes it easier.",
                },
                "Director": {
                    "message": "Let’s build your plan into your daily routine.",
                    "action_step": "Pick a weekly planning day.",
                    "why": "Structure creates consistency.",
                },
                "Expert": {
                    "message": "Digital tools can help you stay organized and connected.",
                    "action_step": "Ask about a care app.",
                    "why": "Apps simplify routines and tracking.",
                },
            },
            "tags": ["self-management", "routine"],
        },
        {
            "question": "Are my heart, kidneys, and diabetes connected?",
            "persona": {
                "Listener": {
                    "message": "Have you heard of CKM syndrome?",
                    "action_step": "Ask your provider to explain how these are linked.",
                    "why": "Understanding helps you act sooner.",
                },
                "Motivator": {
                    "message": "One healthy habit helps all 3!",
                    "action_step": "Walk 10–15 minutes after dinner.",
                    "why": "A single action can improve multiple systems.",
                },
                "Director": {
                    "message": "We manage this as a connected syndrome now.",
                    "action_step": "Ask for coordinated care options.",
                    "why": "Team-based care is more effective.",
                },
                "Expert": {
                    "message": "The AHA now treats CKM as a unified health issue.",
                    "action_step": "Review your PREVENT score with your doctor.",
                    "why": "It reflects your full-body risk.",
                },
            },
            "tags": ["ckm", "connections"],
        },
        {
            "question": "How do I avoid going back to the hospital?",
            "persona": {
                "Listener": {
                    "message": "What happened the last time you were hospitalized?",
                    "action_step": "Keep a journal of early symptoms.",
                    "why": "Spotting patterns helps avoid emergencies.",
                },
                "Motivator": {
                    "message": "Every healthy choice counts.",
                    "action_step": "Pick one habit to stick with this week.",
                    "why": "Small steps add up.",
                },
                "Director": {
                    "message": "We’ll act early—before a crisis.",
                    "action_step": "Ask about telehealth or remote monitoring.",
                    "why": "Early care reduces ER visits.",
                },
                "Expert": {
                    "message": "Remote support programs reduce readmissions by 30%.",
                    "action_step": "Ask if you qualify for a digital health tool.",
                    "why": "Keeps your care team connected.",
                },
            },
            "tags": ["hospital", "prevention", "remote monitoring"],
        },
    ],

    # ========= HTN (High Blood Pressure) =========
    "HTN": [
        {
            "question": "What should my blood pressure goal be?",
            "persona": {
                "Listener": {
                    "message": "It’s normal to feel unsure—many people don’t know their number.",
                    "action_step": "Ask your doctor, “What’s my target BP?”",
                    "why": "Clear targets help you stay on track.",
                },
                "Motivator": {
                    "message": "Knowing your goal puts you in control!",
                    "action_step": "Write your BP goal on your fridge or phone.",
                    "why": "Visible goals keep you focused.",
                },
                "Director": {
                    "message": "For most people, the AHA recommends a goal below 130/80.",
                    "action_step": "Track your BP regularly and compare it to your goal.",
                    "why": "Regular feedback supports better decisions.",
                },
                "Expert": {
                    "message": "AHA guidance: lower BP lowers risk of heart attack, stroke, and kidney disease.",
                    "action_step": "Review the AHA blood pressure chart on heart.org.",
                    "why": "Evidence-based goals are safer and more effective.",
                },
            },
            "tags": ["bp goal", "targets"],
        },
        {
            "question": "Do I really need medication?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to feel unsure. Many people ask this.",
                    "action_step": "Talk to your doctor about how meds fit your overall plan.",
                    "why": "Personalized plans reduce confusion.",
                },
                "Motivator": {
                    "message": "Taking medication is one way to protect your heart—just like walking or eating well.",
                    "action_step": "Pair taking your med with a daily habit (e.g., brushing teeth).",
                    "why": "It builds consistency.",
                },
                "Director": {
                    "message": "Medications are usually started if lifestyle changes alone don’t lower BP enough.",
                    "action_step": "Follow up in 4 weeks to evaluate your progress.",
                    "why": "Your needs can change over time.",
                },
                "Expert": {
                    "message": "For many people, medication + healthy habits works best.",
                    "action_step": "Review potential side effects with your provider.",
                    "why": "Informed patients are more successful with treatment.",
                },
            },
            "tags": ["meds", "hypertension"],
        },
        {
            "question": "What can I do besides taking medication?",
            "persona": {
                "Listener": {
                    "message": "It’s great that you want to take action!",
                    "action_step": "Choose one area: food, movement, sleep, or stress.",
                    "why": "Starting small makes change more manageable.",
                },
                "Motivator": {
                    "message": "Your body responds quickly to healthy habits.",
                    "action_step": "Walk 10 minutes after lunch each day this week.",
                    "why": "Consistency builds confidence.",
                },
                "Director": {
                    "message": "Try the DASH diet, reduce sodium, increase activity, lose weight if needed.",
                    "action_step": "Track salt intake for 3 days.",
                    "why": "Awareness is the first step to improvement.",
                },
                "Expert": {
                    "message": "Lifestyle changes can lower systolic BP by ~4–11 mmHg for many people.",
                    "action_step": "Explore AHA’s Life’s Essential 8 tool.",
                    "why": "It connects behaviors with long-term outcomes.",
                },
            },
            "tags": ["lifestyle", "dash", "exercise"],
        },
        {
            "question": "What kind of diet should I follow?",
            "persona": {
                "Listener": {
                    "message": "Choosing what to eat can feel confusing. You’re not alone.",
                    "action_step": "Keep a simple food journal for 3 days.",
                    "why": "Reflection builds insight.",
                },
                "Motivator": {
                    "message": "Small food swaps can lead to big results.",
                    "action_step": "Choose one low-salt snack to try this week.",
                    "why": "Starting with snacks is manageable.",
                },
                "Director": {
                    "message": "The DASH diet emphasizes fruits, vegetables, whole grains, and low-fat dairy.",
                    "action_step": "Add one fruit or veggie to each meal.",
                    "why": "Gradual changes lead to lasting habits.",
                },
                "Expert": {
                    "message": "Clinical trials show DASH lowers BP and supports heart health.",
                    "action_step": "Review AHA’s DASH resources.",
                    "why": "Evidence-based tools support success.",
                },
            },
            "tags": ["diet", "dash"],
        },
        {
            "question": "Will I have high blood pressure forever?",
            "persona": {
                "Listener": {
                    "message": "That’s a common fear—but there’s hope.",
                    "action_step": "Ask your doctor if your condition is reversible.",
                    "why": "Opens the door for shared planning.",
                },
                "Motivator": {
                    "message": "You can improve your numbers—many people do!",
                    "action_step": "Celebrate any drop in BP, even a few points.",
                    "why": "Every step helps your heart.",
                },
                "Director": {
                    "message": "High BP may not go away completely, but it can often be controlled.",
                    "action_step": "Stick with your plan for 3 months, then reassess.",
                    "why": "Change takes time to show results.",
                },
                "Expert": {
                    "message": "Lifestyle + medication can keep BP controlled long-term for many people.",
                    "action_step": "Use an AHA BP tracker/logbook approach.",
                    "why": "Tracking supports engagement and safer decisions.",
                },
            },
            "tags": ["long-term", "control"],
        },
        {
            "question": "How can I track my blood pressure at home?",
            "persona": {
                "Listener": {
                    "message": "It can be overwhelming at first, but you’re not alone.",
                    "action_step": "Write down readings in a simple notebook or notes app.",
                    "why": "It helps you notice patterns over time.",
                },
                "Motivator": {
                    "message": "Tracking gives you control over your progress.",
                    "action_step": "Celebrate streaks of consistent tracking.",
                    "why": "Motivation builds with momentum.",
                },
                "Director": {
                    "message": "Take readings morning and evening, seated and rested.",
                    "action_step": "Set calendar alerts to build a habit.",
                    "why": "Routine readings give reliable data.",
                },
                "Expert": {
                    "message": "Technique matters: arm supported at heart level; avoid caffeine/exercise right before.",
                    "action_step": "Use an AHA measurement guide/video for technique.",
                    "why": "Accurate technique = trustworthy numbers.",
                },
            },
            "tags": ["monitoring", "home bp"],
        },
        {
            "question": "Can stress really affect my blood pressure?",
            "persona": {
                "Listener": {
                    "message": "Yes—and life can be stressful. You’re not alone.",
                    "action_step": "Identify one stressor you can reduce this week.",
                    "why": "Small wins reduce overall tension.",
                },
                "Motivator": {
                    "message": "Taking care of your mind supports your heart.",
                    "action_step": "Try a 5-minute guided breathing session.",
                    "why": "Can lower stress response and support BP control.",
                },
                "Director": {
                    "message": "Chronic stress can drive behaviors that raise BP (sleep, diet, alcohol).",
                    "action_step": "Create a wind-down routine before bed.",
                    "why": "Better sleep supports better BP control.",
                },
                "Expert": {
                    "message": "Mindfulness, yoga, and relaxation techniques have evidence for modest BP benefits in some people.",
                    "action_step": "Add stress reduction to your weekly goals.",
                    "why": "Long-term stress management supports cardiovascular risk reduction.",
                },
            },
            "tags": ["stress", "sleep"],
        },
        {
            "question": "What’s a dangerous blood pressure level?",
            "persona": {
                "Listener": {
                    "message": "It’s scary not knowing what’s too high.",
                    "action_step": "Learn your BP zones with a color-coded chart.",
                    "why": "Helps you recognize when to seek help.",
                },
                "Motivator": {
                    "message": "Knowing your numbers gives you power—not fear.",
                    "action_step": "Practice reading and interpreting your monitor.",
                    "why": "You can respond quickly and calmly.",
                },
                "Director": {
                    "message": "180/120 or higher is a hypertensive crisis—especially with symptoms.",
                    "action_step": "Program emergency contacts in your phone and know when to seek urgent care.",
                    "why": "Being prepared helps you act fast if needed.",
                },
                "Expert": {
                    "message": "Stage 2 hypertension begins at 140/90; crisis thresholds require rapid response.",
                    "action_step": "Review your BP history and symptoms plan with your clinician.",
                    "why": "Trends + symptoms guide safer treatment.",
                },
            },
            "tags": ["crisis", "emergency"],
        },
        {
            "question": "Is low blood pressure a problem too?",
            "persona": {
                "Listener": {
                    "message": "Yes—it can make you feel dizzy, tired, or weak.",
                    "action_step": "Note symptoms when you take readings.",
                    "why": "Helps your care team adjust treatment.",
                },
                "Motivator": {
                    "message": "It’s okay to ask questions if something doesn’t feel right.",
                    "action_step": "Bring those questions to your next visit.",
                    "why": "Supports shared decision-making.",
                },
                "Director": {
                    "message": "If BP is too low—especially on meds—we may need to adjust dose or timing.",
                    "action_step": "Log symptoms and medication timing.",
                    "why": "Timing affects BP levels.",
                },
                "Expert": {
                    "message": "Under ~90/60 can be normal for some, but concerning if it causes symptoms/falls.",
                    "action_step": "Track hydration and symptoms alongside BP.",
                    "why": "Dehydration can worsen low BP.",
                },
            },
            "tags": ["hypotension", "side effects"],
        },
        {
            "question": "How do I talk to my family about my high blood pressure?",
            "persona": {
                "Listener": {
                    "message": "Talking about your health takes courage.",
                    "action_step": "Start with one trusted family member.",
                    "why": "Support makes healthy changes easier.",
                },
                "Motivator": {
                    "message": "You might inspire them to check their BP too!",
                    "action_step": "Invite a loved one to join you in cooking or walking.",
                    "why": "Shared habits are easier to keep.",
                },
                "Director": {
                    "message": "Use simple language: “I’m working on my BP so I can stay healthy.”",
                    "action_step": "Share one concrete goal, like reducing salt together.",
                    "why": "Shared goals create buy-in.",
                },
                "Expert": {
                    "message": "Family history matters—encouraging screening supports prevention.",
                    "action_step": "Ask family members to check BP and review guidance.",
                    "why": "Prevention can start with one conversation.",
                },
            },
            "tags": ["family", "support"],
        },
    ],

    # ========= HF (Heart Failure) =========
    "HF": [
        {
            "question": "What is heart failure and can it be managed?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to feel nervous. You’re not alone in this.",
                    "action_step": "Ask your doctor to explain your heart’s condition in simple terms.",
                    "why": "Understanding helps reduce fear.",
                },
                "Motivator": {
                    "message": "Many people with heart failure live full, active lives.",
                    "action_step": "Write down one strength you want to keep using each day.",
                    "why": "Keeps your identity strong.",
                },
                "Director": {
                    "message": "Heart failure means your heart isn’t pumping as well—but treatment helps.",
                    "action_step": "Create a care plan with your team.",
                    "why": "Clarity boosts confidence.",
                },
                "Expert": {
                    "message": "Guidelines support medicines, lifestyle changes, and symptom tracking.",
                    "action_step": "Start a daily symptom/weight log.",
                    "why": "Tracking helps detect problems early.",
                },
            },
            "tags": ["hf", "basics"],
        },
        {
            "question": "How do I know if my heart failure is getting worse?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to check in with how your body feels.",
                    "action_step": "Keep a log of weight, swelling, and breathing daily.",
                    "why": "Early signs help prevent hospital visits.",
                },
                "Motivator": {
                    "message": "You’re learning your body’s signals—that’s powerful.",
                    "action_step": "Set a reminder to weigh yourself each morning.",
                    "why": "Sudden gain may mean fluid buildup.",
                },
                "Director": {
                    "message": "Watch for weight gain, shortness of breath, swelling, or fatigue.",
                    "action_step": "Report changes of 2+ pounds overnight or 5+ in a week.",
                    "why": "Quick action prevents worsening.",
                },
                "Expert": {
                    "message": "Daily weight and symptom monitoring is standard HF self-care guidance.",
                    "action_step": "Use a simple symptom checklist.",
                    "why": "Patterns matter more than single events.",
                },
            },
            "tags": ["hf", "monitoring"],
        },
        {
            "question": "What can I eat with heart failure?",
            "persona": {
                "Listener": {
                    "message": "Eating can feel tricky when you’re told to ‘cut back.’",
                    "action_step": "Write down your favorite heart-healthy foods.",
                    "why": "Focus on what you can enjoy.",
                },
                "Motivator": {
                    "message": "Your meals can still be flavorful and fulfilling!",
                    "action_step": "Try one new low-sodium recipe this week.",
                    "why": "Keeps meals exciting.",
                },
                "Director": {
                    "message": "Limit sodium (often ~1,500–2,000 mg/day) and follow fluid guidance if prescribed.",
                    "action_step": "Check one food label daily for sodium.",
                    "why": "Small steps add up.",
                },
                "Expert": {
                    "message": "Lower sodium and healthy dietary patterns support BP, fluid balance, and symptoms.",
                    "action_step": "Make a grocery list centered on minimally processed foods.",
                    "why": "Shopping decisions drive daily intake.",
                },
            },
            "tags": ["hf", "diet", "sodium"],
        },
        {
            "question": "How much activity is safe for me?",
            "persona": {
                "Listener": {
                    "message": "It’s natural to feel cautious.",
                    "action_step": "Ask your provider about safe movement goals.",
                    "why": "Avoids fear-based inactivity.",
                },
                "Motivator": {
                    "message": "Even a few steps count. Movement is medicine.",
                    "action_step": "Walk for 5 minutes after each meal.",
                    "why": "Builds stamina without stress.",
                },
                "Director": {
                    "message": "Most people can do light-to-moderate activity depending on symptoms and plan.",
                    "action_step": "Ask about cardiac rehab or a structured walking plan.",
                    "why": "Structured programs offer guidance.",
                },
                "Expert": {
                    "message": "Supervised rehab and progressive activity improve function and quality of life for many.",
                    "action_step": "Request a rehab referral if eligible.",
                    "why": "Rehab improves safety and confidence.",
                },
            },
            "tags": ["hf", "exercise", "rehab"],
        },
        {
            "question": "Will I always feel tired or short of breath?",
            "persona": {
                "Listener": {
                    "message": "It’s frustrating when energy is low—but you’re doing your best.",
                    "action_step": "Keep a fatigue and symptom journal.",
                    "why": "Patterns help your team help you.",
                },
                "Motivator": {
                    "message": "Good days will come—keep going.",
                    "action_step": "Celebrate energy wins, no matter how small.",
                    "why": "Momentum matters.",
                },
                "Director": {
                    "message": "Symptoms may improve as your treatment plan is optimized.",
                    "action_step": "Stick to meds, meals, and movement plan, then reassess.",
                    "why": "Structure supports improvement.",
                },
                "Expert": {
                    "message": "Guideline-directed therapy often improves symptoms over time, but it can require adjustments.",
                    "action_step": "Ask about med optimization if symptoms persist.",
                    "why": "Regular review improves outcomes.",
                },
            },
            "tags": ["hf", "symptoms"],
        },
        {
            "question": "What medications will I need, and what do they do?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to ask what each pill is for. That’s smart.",
                    "action_step": "Bring all meds to your next visit and ask questions.",
                    "why": "Builds confidence in your treatment.",
                },
                "Motivator": {
                    "message": "Learning about your meds is part of owning your care.",
                    "action_step": "Make a simple chart: what, when, why.",
                    "why": "Keeps it manageable.",
                },
                "Director": {
                    "message": "There are several core HF medication classes; each plays a specific role.",
                    "action_step": "Ask if you’re on the recommended therapies for your type of HF.",
                    "why": "Maximizes benefit and safety.",
                },
                "Expert": {
                    "message": "Medication selection depends on EF, symptoms, kidney function, BP, and tolerance.",
                    "action_step": "Review your med list every 3–6 months.",
                    "why": "Regimens evolve as your body changes.",
                },
            },
            "tags": ["hf", "meds"],
        },
        {
            "question": "Can I travel or go on vacation with heart failure?",
            "persona": {
                "Listener": {
                    "message": "It’s totally okay to want some normalcy.",
                    "action_step": "Talk to your provider about your plans in advance.",
                    "why": "Better to plan than guess.",
                },
                "Motivator": {
                    "message": "You can still explore and enjoy—just with preparation.",
                    "action_step": "Pack meds and a brief health summary.",
                    "why": "Preparedness reduces anxiety.",
                },
                "Director": {
                    "message": "Travel can be safe if symptoms are stable and you plan for rest and medications.",
                    "action_step": "Get clearance and emergency contacts before you go.",
                    "why": "Reduces travel stress.",
                },
                "Expert": {
                    "message": "Individual guidance depends on recent symptoms, labs, and stability.",
                    "action_step": "Avoid extremes (heat, altitude) if advised.",
                    "why": "Extreme conditions can strain the heart.",
                },
            },
            "tags": ["hf", "travel"],
        },
        {
            "question": "Will I need a device like a defibrillator or pacemaker?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to be nervous about devices. Ask away.",
                    "action_step": "Ask whether your ejection fraction and symptoms meet criteria.",
                    "why": "Eligibility depends on heart strength and rhythm risk.",
                },
                "Motivator": {
                    "message": "Many people feel safer with a device protecting them.",
                    "action_step": "Talk to someone who has one if that helps.",
                    "why": "Real stories can ease anxiety.",
                },
                "Director": {
                    "message": "Devices are considered based on EF, symptoms, ECG pattern, and response to meds.",
                    "action_step": "Make sure imaging (echo) is up to date.",
                    "why": "Decisions should be based on current data.",
                },
                "Expert": {
                    "message": "Timing often includes a period of optimized meds before final device decisions.",
                    "action_step": "Reassess after therapy optimization.",
                    "why": "Some people improve and avoid devices.",
                },
            },
            "tags": ["hf", "devices"],
        },
        {
            "question": "What should I do during a flare or worsening episode?",
            "persona": {
                "Listener": {
                    "message": "You’re not alone. Flares happen even when you’re doing everything right.",
                    "action_step": "Write down a “When to Call” symptom checklist.",
                    "why": "Removes guesswork.",
                },
                "Motivator": {
                    "message": "You can bounce back. Having a plan makes you powerful.",
                    "action_step": "Pack a small “go bag” with meds and notes just in case.",
                    "why": "Prepares you for emergencies.",
                },
                "Director": {
                    "message": "Call if symptoms worsen quickly: weight gain, swelling, breathlessness, chest pain.",
                    "action_step": "Keep your care team’s number posted and saved.",
                    "why": "Early contact = fewer hospital stays.",
                },
                "Expert": {
                    "message": "Early treatment changes can prevent acute decompensation from escalating.",
                    "action_step": "Review your action plan every 3–6 months.",
                    "why": "Plans drift; refresh keeps you ready.",
                },
            },
            "tags": ["hf", "flare", "emergency"],
        },
        {
            "question": "How long can I live with heart failure?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to think about the future—it means you care.",
                    "action_step": "Focus on today’s goals and routines.",
                    "why": "Peace comes from progress, not prediction.",
                },
                "Motivator": {
                    "message": "Many people live for years—what matters is your path.",
                    "action_step": "Set a meaningful long-term goal.",
                    "why": "Purpose fuels resilience.",
                },
                "Director": {
                    "message": "Outlook varies by age, EF, comorbidities, and response to treatment.",
                    "action_step": "Ask your team to track key markers over time.",
                    "why": "Objective data shows trends.",
                },
                "Expert": {
                    "message": "Prognosis improves with adherence to optimized, guideline-directed care.",
                    "action_step": "Schedule regular check-ins to adjust treatment.",
                    "why": "Timely updates keep care effective.",
                },
            },
            "tags": ["hf", "prognosis"],
        },
    ],

    # ========= CAD (Coronary Artery Disease) =========
    "CAD": [
        {
            "question": "What caused my coronary artery disease?",
            "persona": {
                "Listener": {
                    "message": "It’s natural to wonder ‘why me?’ Many people ask this.",
                    "action_step": "Ask your provider to walk through your risk factors.",
                    "why": "Understanding helps reduce blame and clarify prevention.",
                },
                "Motivator": {
                    "message": "Knowing your history can help you rewrite your future.",
                    "action_step": "Write down your top 3 risks and 1 way to tackle each.",
                    "why": "Personal action builds momentum.",
                },
                "Director": {
                    "message": "CAD often results from cholesterol, BP, diabetes, smoking, and genetics.",
                    "action_step": "Request a printout of your latest labs and risk profile.",
                    "why": "You can’t manage what you don’t see.",
                },
                "Expert": {
                    "message": "Atherosclerosis develops over time; risk factor control slows progression.",
                    "action_step": "Use Life’s Essential 8 as a prevention checklist.",
                    "why": "Targets the major drivers of CAD.",
                },
            },
            "tags": ["cad", "causes"],
        },
        {
            "question": "What should I eat now that I have CAD?",
            "persona": {
                "Listener": {
                    "message": "There’s a lot of confusing advice out there. You’re not alone.",
                    "action_step": "Bring a food log to your next visit.",
                    "why": "It helps personalize advice.",
                },
                "Motivator": {
                    "message": "You can still enjoy food—just smarter.",
                    "action_step": "Try a new heart-healthy recipe this week.",
                    "why": "Small changes spark habits.",
                },
                "Director": {
                    "message": "Emphasize plants, whole grains, nuts, lean proteins; limit sodium and added sugars.",
                    "action_step": "Reduce sodium toward <1500 mg/day if advised.",
                    "why": "Supports BP and vascular health.",
                },
                "Expert": {
                    "message": "Mediterranean and DASH patterns are widely recommended for secondary prevention.",
                    "action_step": "Use a structured meal plan template.",
                    "why": "Reduces guesswork and improves adherence.",
                },
            },
            "tags": ["cad", "diet"],
        },
        {
            "question": "Can I exercise safely with CAD?",
            "persona": {
                "Listener": {
                    "message": "It’s good you’re asking. Many people worry about overdoing it.",
                    "action_step": "Ask about cardiac rehab or a safe home walking plan.",
                    "why": "Support builds confidence.",
                },
                "Motivator": {
                    "message": "Movement is medicine—even 10 minutes counts.",
                    "action_step": "Walk after one meal each day this week.",
                    "why": "Easy routines are powerful.",
                },
                "Director": {
                    "message": "Most people benefit from moderate activity unless symptoms worsen.",
                    "action_step": "Track steps or minutes daily.",
                    "why": "You learn your limits and progress.",
                },
                "Expert": {
                    "message": "Exercise improves vascular function and lowers future risk when done safely.",
                    "action_step": "Ask whether stress testing or a 6-minute walk test is appropriate.",
                    "why": "Baseline testing helps tailor intensity.",
                },
            },
            "tags": ["cad", "exercise", "rehab"],
        },
        {
            "question": "What are my chances of having another heart event?",
            "persona": {
                "Listener": {
                    "message": "It’s totally normal to feel anxious about recurrence.",
                    "action_step": "Ask what lowers your risk the most right now.",
                    "why": "Turns fear into a plan.",
                },
                "Motivator": {
                    "message": "Every day you take action, you lower your risk.",
                    "action_step": "Commit to 1 healthy habit for the next 30 days.",
                    "why": "Consistency compounds benefits.",
                },
                "Director": {
                    "message": "Risk depends on BP/lipids control, heart function, symptoms, and lifestyle.",
                    "action_step": "Keep a shared checklist with your care team.",
                    "why": "Organized care is safer care.",
                },
                "Expert": {
                    "message": "Secondary prevention relies on evidence-based meds + lifestyle and monitoring.",
                    "action_step": "Confirm you’re on optimized preventive therapy.",
                    "why": "Right therapy reduces recurrence risk.",
                },
            },
            "tags": ["cad", "risk"],
        },
        {
            "question": "How do I manage stress without hurting my heart?",
            "persona": {
                "Listener": {
                    "message": "Heart issues can feel overwhelming. You’re not alone.",
                    "action_step": "Write down 3 things that bring you calm.",
                    "why": "Awareness helps you choose coping tools.",
                },
                "Motivator": {
                    "message": "Stress can shrink when you take control.",
                    "action_step": "Try deep breathing or stretching once a day.",
                    "why": "Quick tools build confidence.",
                },
                "Director": {
                    "message": "Sleep, connection, and relaxation all support better outcomes.",
                    "action_step": "Set a 15-minute tech-free wind-down before bed.",
                    "why": "Sleep and stress affect heart risk.",
                },
                "Expert": {
                    "message": "Psychosocial stress is a recognized risk factor; behavior support can help.",
                    "action_step": "Ask about support groups or counseling.",
                    "why": "Support improves self-management and quality of life.",
                },
            },
            "tags": ["cad", "stress", "sleep"],
        },
        {
            "question": "What should I do if I have chest pain again?",
            "persona": {
                "Listener": {
                    "message": "Chest pain can be scary. You’re not alone in this.",
                    "action_step": "Write down what it feels like, when it happens, and how long it lasts.",
                    "why": "Details help your team make safer decisions.",
                },
                "Motivator": {
                    "message": "Taking action right away can protect your heart.",
                    "action_step": "Make a plan with loved ones for when to call emergency services.",
                    "why": "Preparation reduces hesitation.",
                },
                "Director": {
                    "message": "If chest pain lasts >5 minutes or doesn’t improve with rest/meds, call emergency services.",
                    "action_step": "Keep prescribed nitroglycerin available if you have it.",
                    "why": "Fast response saves heart muscle.",
                },
                "Expert": {
                    "message": "Recurrent angina can signal reduced blood flow and needs evaluation.",
                    "action_step": "Schedule urgent follow-up if pain recurs even if it resolves.",
                    "why": "Prevents complications.",
                },
            },
            "tags": ["cad", "chest pain", "emergency"],
        },
        {
            "question": "Should I get a stent or surgery again?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to feel uncertain about procedures.",
                    "action_step": "List your pros, cons, and concerns before your visit.",
                    "why": "Helps you feel heard and involved.",
                },
                "Motivator": {
                    "message": "You’ve been through this before. You know your body.",
                    "action_step": "Ask about non-surgical alternatives too.",
                    "why": "Shared decisions build trust.",
                },
                "Director": {
                    "message": "Repeat procedures depend on symptoms, tests, and current heart function.",
                    "action_step": "Request updated imaging or stress testing.",
                    "why": "Decisions should use current data.",
                },
                "Expert": {
                    "message": "Revascularization decisions depend on anatomy, ischemia burden, and symptom severity.",
                    "action_step": "Review your prior cath/angiogram report with your cardiologist.",
                    "why": "Context informs next steps.",
                },
            },
            "tags": ["cad", "procedures"],
        },
        {
            "question": "Can I travel or fly with CAD?",
            "persona": {
                "Listener": {
                    "message": "Wanting to live fully is a good sign. Let’s talk about it.",
                    "action_step": "Discuss travel plans with your care team.",
                    "why": "They can help you plan safely.",
                },
                "Motivator": {
                    "message": "Yes—you can still enjoy life with a heart condition!",
                    "action_step": "Pack medications and emergency contacts.",
                    "why": "Preparedness reduces anxiety.",
                },
                "Director": {
                    "message": "Move regularly during travel, stay hydrated, avoid long uninterrupted sitting.",
                    "action_step": "Plan stretch breaks every 2 hours.",
                    "why": "Supports circulation and comfort.",
                },
                "Expert": {
                    "message": "Travel is usually safe when stable, but timing after recent events matters.",
                    "action_step": "Ask if you need clearance based on recent symptoms/events.",
                    "why": "Risk varies person-to-person.",
                },
            },
            "tags": ["cad", "travel"],
        },
        {
            "question": "What’s the role of cholesterol and statins?",
            "persona": {
                "Listener": {
                    "message": "Many people wonder about statins and side effects.",
                    "action_step": "Ask about your LDL goal and how your statin is helping.",
                    "why": "Knowing the ‘why’ builds trust.",
                },
                "Motivator": {
                    "message": "Lowering cholesterol protects your arteries—keep going!",
                    "action_step": "Get your lipid panel rechecked as advised.",
                    "why": "Tracks progress and guides adjustments.",
                },
                "Director": {
                    "message": "Statins reduce risk by lowering LDL and stabilizing plaque.",
                    "action_step": "Take your statin consistently at the same time daily.",
                    "why": "Consistency improves effectiveness.",
                },
                "Expert": {
                    "message": "Therapy intensity depends on risk and history; non-statin options exist if needed.",
                    "action_step": "Review options with your clinician if side effects occur.",
                    "why": "There are alternatives and dose strategies.",
                },
            },
            "tags": ["cad", "cholesterol", "statins"],
        },
        {
            "question": "How do I stay motivated with heart-healthy habits?",
            "persona": {
                "Listener": {
                    "message": "Staying motivated is hard—we all need encouragement.",
                    "action_step": "Share your ‘why’ with a friend or coach.",
                    "why": "Accountability builds momentum.",
                },
                "Motivator": {
                    "message": "Every small win matters. Keep moving forward!",
                    "action_step": "Celebrate weekly wins: steps, meals, sodium reductions.",
                    "why": "Positivity sustains progress.",
                },
                "Director": {
                    "message": "Use SMART goals: specific, measurable, achievable, relevant, time-bound.",
                    "action_step": "Pick 1 SMART goal for this month.",
                    "why": "Clarity improves follow-through.",
                },
                "Expert": {
                    "message": "Long-term change is supported by tracking tools, care teams, and community.",
                    "action_step": "Use a logbook/app and review progress monthly.",
                    "why": "Feedback loops improve adherence.",
                },
            },
            "tags": ["cad", "motivation", "habits"],
        },
    ],

    # ========= AFIB (Atrial Fibrillation) =========
    "AFIB": [
        {
            "question": "What exactly is atrial fibrillation?",
            "persona": {
                "Listener": {
                    "message": "You’re not alone—this diagnosis can feel overwhelming.",
                    "action_step": "Ask your provider to explain AFib in plain language.",
                    "why": "Understanding helps you manage it.",
                },
                "Motivator": {
                    "message": "You’ve taken the first step just by asking this question.",
                    "action_step": "Watch a short explainer video/animation.",
                    "why": "Visual tools build clarity and confidence.",
                },
                "Director": {
                    "message": "AFib is an irregular heartbeat that increases stroke and heart failure risk.",
                    "action_step": "Learn your symptoms and triggers.",
                    "why": "Monitoring supports earlier intervention.",
                },
                "Expert": {
                    "message": "AFib involves disorganized electrical activity in the atria; type matters for treatment.",
                    "action_step": "Ask about ECG confirmation and AFib classification.",
                    "why": "Classification guides therapy selection.",
                },
            },
            "tags": ["afib", "basics"],
        },
        {
            "question": "What are my treatment options?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to feel unsure—there are several options.",
                    "action_step": "Write down your top goals (symptoms, stroke prevention, both).",
                    "why": "Guides shared decisions.",
                },
                "Motivator": {
                    "message": "You deserve a plan that fits your life.",
                    "action_step": "Ask about rhythm control vs rate control.",
                    "why": "Both can work depending on your needs.",
                },
                "Director": {
                    "message": "Options include medications, cardioversion, ablation, or devices in some cases.",
                    "action_step": "Schedule a treatment planning visit.",
                    "why": "Dedicated time improves clarity.",
                },
                "Expert": {
                    "message": "Therapy depends on duration, symptoms, comorbidities, and AFib type.",
                    "action_step": "Bring a full medical history and med list to your visit.",
                    "why": "Informs safest choices.",
                },
            },
            "tags": ["afib", "treatment"],
        },
        {
            "question": "Do I need a blood thinner?",
            "persona": {
                "Listener": {
                    "message": "It’s common to be nervous about bleeding risk.",
                    "action_step": "Ask your doctor to explain your stroke risk score.",
                    "why": "Helps you weigh benefits and risks.",
                },
                "Motivator": {
                    "message": "Blood thinners help prevent strokes—they protect you.",
                    "action_step": "Ask about options (warfarin vs DOACs).",
                    "why": "You have choices.",
                },
                "Director": {
                    "message": "Many AFib patients need anticoagulation unless stroke risk is very low.",
                    "action_step": "Discuss bleeding precautions and fall risk.",
                    "why": "Safety matters.",
                },
                "Expert": {
                    "message": "Guidelines use CHA₂DS₂-VASc to guide anticoagulation decisions.",
                    "action_step": "Calculate and review your CHA₂DS₂-VASc in clinic.",
                    "why": "Matches treatment intensity to risk.",
                },
            },
            "tags": ["afib", "anticoagulation", "chadsvasc"],
        },
        {
            "question": "Can AFib go away?",
            "persona": {
                "Listener": {
                    "message": "That’s a hopeful question—and a fair one.",
                    "action_step": "Track episodes and triggers in a journal.",
                    "why": "Some cases are intermittent.",
                },
                "Motivator": {
                    "message": "Some people do return to normal rhythm with treatment.",
                    "action_step": "Follow your plan and stay active as advised.",
                    "why": "Risk factor control helps.",
                },
                "Director": {
                    "message": "AFib may become less frequent or recur; monitoring helps guide next steps.",
                    "action_step": "Schedule regular rhythm checks.",
                    "why": "Detects changes early.",
                },
                "Expert": {
                    "message": "Risk factor management (weight, sleep apnea, BP) can reduce AFib burden in some people.",
                    "action_step": "Discuss sleep study or weight management if advised.",
                    "why": "Targets upstream drivers.",
                },
            },
            "tags": ["afib", "remission"],
        },
        {
            "question": "How does AFib affect my risk of stroke?",
            "persona": {
                "Listener": {
                    "message": "That fear is valid—stroke risk is real, but manageable.",
                    "action_step": "Learn FAST stroke warning signs.",
                    "why": "Recognition saves lives.",
                },
                "Motivator": {
                    "message": "You’re taking charge by asking about prevention.",
                    "action_step": "Review stroke risk factors with your team.",
                    "why": "Many are modifiable.",
                },
                "Director": {
                    "message": "AFib increases stroke risk; anticoagulation can substantially reduce risk.",
                    "action_step": "Follow your medication plan consistently.",
                    "why": "Consistency protects.",
                },
                "Expert": {
                    "message": "CHA₂DS₂-VASc and bleeding risk tools guide anticoagulation decisions.",
                    "action_step": "Ask for your calculated risk scores.",
                    "why": "Improves shared decision-making.",
                },
            },
            "tags": ["afib", "stroke prevention"],
        },
        {
            "question": "What should I avoid with AFib?",
            "persona": {
                "Listener": {
                    "message": "You’re not alone in wondering what can make it worse.",
                    "action_step": "Ask about alcohol, caffeine, stress, and cold meds.",
                    "why": "These can be triggers for some people.",
                },
                "Motivator": {
                    "message": "Small changes can make a big difference.",
                    "action_step": "Try cutting back on one trigger this week.",
                    "why": "Experimenting helps you learn your pattern.",
                },
                "Director": {
                    "message": "Avoid known triggers and manage risk factors as part of treatment.",
                    "action_step": "Make a personal trigger list.",
                    "why": "Helps tailor guidance.",
                },
                "Expert": {
                    "message": "Common triggers include alcohol, excess stimulants, dehydration, poor sleep, and stress.",
                    "action_step": "Review lifestyle patterns with your clinician.",
                    "why": "Reduces episode frequency for some.",
                },
            },
            "tags": ["afib", "triggers"],
        },
        {
            "question": "Can I still exercise?",
            "persona": {
                "Listener": {
                    "message": "It’s smart to ask—many people worry about this.",
                    "action_step": "Tell your doctor what activities you enjoy.",
                    "why": "Exercise can often be adapted.",
                },
                "Motivator": {
                    "message": "Yes! Moving your body is part of healing.",
                    "action_step": "Start with walking or light movement.",
                    "why": "Builds endurance safely.",
                },
                "Director": {
                    "message": "Exercise is encouraged, but start gradually and consider supervision early on.",
                    "action_step": "Ask about cardiac rehab if appropriate.",
                    "why": "Guided exercise improves safety.",
                },
                "Expert": {
                    "message": "Moderate exercise can improve symptoms and overall cardiovascular health.",
                    "action_step": "Create a condition-tailored activity plan.",
                    "why": "Optimizes benefits and reduces risk.",
                },
            },
            "tags": ["afib", "exercise"],
        },
        {
            "question": "Will AFib get worse over time?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to worry—uncertainty can be hard.",
                    "action_step": "Ask what type of AFib you have.",
                    "why": "Type gives clues about progression.",
                },
                "Motivator": {
                    "message": "Staying proactive makes a big difference.",
                    "action_step": "Stick to your plan and healthy habits.",
                    "why": "Good control can slow progression.",
                },
                "Director": {
                    "message": "AFib can become more frequent without management.",
                    "action_step": "Track symptoms and report changes.",
                    "why": "Enables timely adjustments.",
                },
                "Expert": {
                    "message": "Progression risk is influenced by age, weight, sleep apnea, BP, and diabetes.",
                    "action_step": "Control comorbidities with your care team.",
                    "why": "Reduces progression drivers.",
                },
            },
            "tags": ["afib", "progression"],
        },
        {
            "question": "Can I travel or fly with AFib?",
            "persona": {
                "Listener": {
                    "message": "This is a common concern—and you're wise to ask.",
                    "action_step": "Talk to your doctor before long trips.",
                    "why": "May need plan adjustments.",
                },
                "Motivator": {
                    "message": "AFib doesn’t have to ground your life.",
                    "action_step": "Pack meds and a hydration plan.",
                    "why": "Planning boosts confidence.",
                },
                "Director": {
                    "message": "Travel is often fine if AFib is stable.",
                    "action_step": "Know when to seek care if symptoms occur.",
                    "why": "Prepares you for surprises.",
                },
                "Expert": {
                    "message": "Dehydration and immobility can increase symptoms and clot risk in some people.",
                    "action_step": "Move regularly during flights and stay hydrated.",
                    "why": "Reduces common triggers.",
                },
            },
            "tags": ["afib", "travel"],
        },
        {
            "question": "Will I have to live with AFib forever?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to wonder—many people do.",
                    "action_step": "Ask what success looks like for you.",
                    "why": "Defines realistic expectations.",
                },
                "Motivator": {
                    "message": "You can live well with AFib.",
                    "action_step": "Focus on one habit change at a time.",
                    "why": "Builds confidence.",
                },
                "Director": {
                    "message": "Some people achieve remission; many manage AFib long-term with a plan.",
                    "action_step": "Follow your care plan consistently.",
                    "why": "Long-term consistency improves outcomes.",
                },
                "Expert": {
                    "message": "Early-stage AFib burden can decrease with risk factor control and/or ablation for some patients.",
                    "action_step": "Ask if you’re eligible for rhythm strategies.",
                    "why": "May reduce episodes.",
                },
            },
            "tags": ["afib", "long-term"],
        },
    ],

    # ========= STROKE =========
    "STROKE": [
        {
            "question": "What caused my stroke?",
            "persona": {
                "Listener": {
                    "message": "You’re not alone in wondering why this happened.",
                    "action_step": "Ask your provider to explain the likely cause of your stroke.",
                    "why": "Understanding helps guide prevention.",
                },
                "Motivator": {
                    "message": "Learning the cause helps you regain control.",
                    "action_step": "Keep asking questions until it makes sense.",
                    "why": "Clarity supports recovery.",
                },
                "Director": {
                    "message": "Strokes can be from a clot, bleeding, or blocked blood flow.",
                    "action_step": "Review imaging and tests with your team.",
                    "why": "Type guides care.",
                },
                "Expert": {
                    "message": "Ischemic vs hemorrhagic stroke have different causes and prevention strategies.",
                    "action_step": "Request your discharge summary and stroke type documentation.",
                    "why": "Supports continuity of care.",
                },
            },
            "tags": ["stroke", "cause"],
        },
        {
            "question": "Am I at risk of having another stroke?",
            "persona": {
                "Listener": {
                    "message": "It’s natural to worry—it means you care about your future.",
                    "action_step": "Share your concerns with your provider.",
                    "why": "Opens the door for a prevention plan.",
                },
                "Motivator": {
                    "message": "You’ve already taken the first step—asking the question.",
                    "action_step": "Start a daily routine that supports brain and heart health.",
                    "why": "Habits reduce future risk.",
                },
                "Director": {
                    "message": "Yes, but your risk can be lowered with the right care.",
                    "action_step": "Take medications as prescribed and attend follow-ups.",
                    "why": "Adherence lowers recurrence risk.",
                },
                "Expert": {
                    "message": "Secondary prevention targets BP, cholesterol, diabetes, and AFib when present.",
                    "action_step": "Schedule regular follow-ups for risk factor monitoring.",
                    "why": "Early adjustments improve outcomes.",
                },
            },
            "tags": ["stroke", "recurrence"],
        },
        {
            "question": "Will I fully recover?",
            "persona": {
                "Listener": {
                    "message": "Recovery looks different for everyone—and that’s okay.",
                    "action_step": "Be patient with your progress.",
                    "why": "Healing takes time.",
                },
                "Motivator": {
                    "message": "With support and effort, many people make amazing recoveries.",
                    "action_step": "Celebrate small wins—every step counts.",
                    "why": "Reinforcement builds momentum.",
                },
                "Director": {
                    "message": "Some functions may return; others may need rehab and adaptation.",
                    "action_step": "Ask for PT/OT/speech therapy referrals.",
                    "why": "Rehab maximizes recovery.",
                },
                "Expert": {
                    "message": "Neuroplasticity supports recovery over time when therapy is consistent.",
                    "action_step": "Do prescribed cognitive and physical exercises daily.",
                    "why": "Practice drives improvement.",
                },
            },
            "tags": ["stroke", "recovery"],
        },
        {
            "question": "Can I drive again?",
            "persona": {
                "Listener": {
                    "message": "Wanting to regain independence is totally normal.",
                    "action_step": "Talk to your provider about safety evaluations.",
                    "why": "Driving must be assessed individually.",
                },
                "Motivator": {
                    "message": "Getting back behind the wheel is a goal worth working toward.",
                    "action_step": "Work with rehab on strength and coordination.",
                    "why": "Prepares for evaluation.",
                },
                "Director": {
                    "message": "Driving clearance depends on vision, reaction time, and cognition.",
                    "action_step": "Request a formal driving assessment if available.",
                    "why": "Ensures safety.",
                },
                "Expert": {
                    "message": "Rules vary by state and may require medical clearance.",
                    "action_step": "Check your state DMV requirements with your care team.",
                    "why": "Avoids legal/insurance issues.",
                },
            },
            "tags": ["stroke", "driving"],
        },
        {
            "question": "Will I ever feel normal again?",
            "persona": {
                "Listener": {
                    "message": "This is one of the most honest and common questions.",
                    "action_step": "Talk about emotions as well as physical recovery.",
                    "why": "Stroke affects body and mind.",
                },
                "Motivator": {
                    "message": "You are adapting and growing—even now.",
                    "action_step": "Focus on what you can do, not only what changed.",
                    "why": "Shifts mindset toward progress.",
                },
                "Director": {
                    "message": "Many stroke survivors live meaningful lives with adjustments.",
                    "action_step": "Set a personal goal to work toward this month.",
                    "why": "Goals give structure and hope.",
                },
                "Expert": {
                    "message": "Fatigue and mood changes are common; support groups and counseling help.",
                    "action_step": "Ask about counseling or stroke support resources.",
                    "why": "Mental health supports recovery.",
                },
            },
            "tags": ["stroke", "adjustment", "mental health"],
        },
        {
            "question": "How will this affect my memory or thinking?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to notice changes and feel concerned.",
                    "action_step": "Share cognitive changes with your doctor or loved ones.",
                    "why": "Early support helps.",
                },
                "Motivator": {
                    "message": "Your brain can rebuild new connections.",
                    "action_step": "Do one brain-challenging activity daily.",
                    "why": "Mental activity supports recovery.",
                },
                "Director": {
                    "message": "Cognition can be affected; support is available.",
                    "action_step": "Ask about neuropsychological evaluation if needed.",
                    "why": "Identifies strengths and supports.",
                },
                "Expert": {
                    "message": "Effects depend on stroke location and severity.",
                    "action_step": "Use routines/reminders and rehab strategies.",
                    "why": "Compensation reduces frustration.",
                },
            },
            "tags": ["stroke", "cognition"],
        },
        {
            "question": "What kind of rehabilitation do I need?",
            "persona": {
                "Listener": {
                    "message": "Rehab can feel overwhelming—we’ll take it step by step.",
                    "action_step": "Talk openly about what matters most to you.",
                    "why": "Goals guide rehab priorities.",
                },
                "Motivator": {
                    "message": "You’re investing in recovery with every session.",
                    "action_step": "Stick with the plan and celebrate small gains.",
                    "why": "Consistency matters.",
                },
                "Director": {
                    "message": "Rehab may include PT, OT, and speech therapy.",
                    "action_step": "Ask for a personalized rehab referral before discharge (or ASAP).",
                    "why": "Early rehab improves outcomes.",
                },
                "Expert": {
                    "message": "Rehab should begin as soon as medically stable and continue as needed.",
                    "action_step": "Track progress with your care team.",
                    "why": "Feedback keeps therapy targeted.",
                },
            },
            "tags": ["stroke", "rehab"],
        },
        {
            "question": "What lifestyle changes should I make?",
            "persona": {
                "Listener": {
                    "message": "Changing habits is hard—but you’re not alone.",
                    "action_step": "Pick one small change to start with (e.g., 10-minute walk).",
                    "why": "Small wins build momentum.",
                },
                "Motivator": {
                    "message": "You’re strong enough to make changes that support your health.",
                    "action_step": "Set one weekly goal for nutrition, sleep, or activity.",
                    "why": "Measurable goals help.",
                },
                "Director": {
                    "message": "Focus on BP, cholesterol, diabetes control, and safe exercise.",
                    "action_step": "Use a checklist to track habits and meds.",
                    "why": "Tracking improves follow-through.",
                },
                "Expert": {
                    "message": "Life’s Essential 8 provides evidence-based targets for cardiovascular health.",
                    "action_step": "Use trusted tools to guide your plan.",
                    "why": "Reliable sources reduce misinformation.",
                },
            },
            "tags": ["stroke", "lifestyle"],
        },
        {
            "question": "What medications will I need long-term?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to have questions about new medications.",
                    "action_step": "Keep a list of meds and bring it to appointments.",
                    "why": "Improves safety and accuracy.",
                },
                "Motivator": {
                    "message": "Taking medications is an act of self-care.",
                    "action_step": "Use reminders to take meds consistently.",
                    "why": "Routines prevent missed doses.",
                },
                "Director": {
                    "message": "You may need meds for clots, BP, and cholesterol depending on stroke type.",
                    "action_step": "Ask how each medication helps your prevention plan.",
                    "why": "Understanding improves adherence.",
                },
                "Expert": {
                    "message": "Typical meds include antiplatelets/statins/antihypertensives; anticoagulants if AFib present.",
                    "action_step": "Review side effects and interactions regularly.",
                    "why": "Prevents complications.",
                },
            },
            "tags": ["stroke", "meds"],
        },
        {
            "question": "How can my family help me?",
            "persona": {
                "Listener": {
                    "message": "Asking for help shows strength, not weakness.",
                    "action_step": "Tell loved ones what support you want most.",
                    "why": "Builds a shared recovery journey.",
                },
                "Motivator": {
                    "message": "Recovery is stronger when it’s a team effort.",
                    "action_step": "Invite a loved one to a visit or rehab session.",
                    "why": "Keeps them informed and involved.",
                },
                "Director": {
                    "message": "Family can help with daily tasks, transportation, and emotional support.",
                    "action_step": "Create a shared calendar or plan.",
                    "why": "Reduces stress and confusion.",
                },
                "Expert": {
                    "message": "Caregiver support improves recovery and can reduce readmissions.",
                    "action_step": "Explore caregiver education resources.",
                    "why": "Skills improve safety at home.",
                },
            },
            "tags": ["stroke", "family", "caregiving"],
        },
    ],

    # ========= DM (Diabetes) =========
    "DM": [
        {
            "question": "What should my blood sugar levels be?",
            "persona": {
                "Listener": {
                    "message": "It’s normal to feel confused about numbers at first.",
                    "action_step": "Ask your care team for your personal target ranges.",
                    "why": "Targets vary based on health and meds.",
                },
                "Motivator": {
                    "message": "Knowing your numbers is a key to taking control.",
                    "action_step": "Track levels daily using a log or app.",
                    "why": "Tracking reveals patterns and progress.",
                },
                "Director": {
                    "message": "Many targets: fasting 80–130 mg/dL; 2-hr after meals often <180 mg/dL (individualize).",
                    "action_step": "Record readings before meals and 2 hours after.",
                    "why": "Supports medication and diet adjustments.",
                },
                "Expert": {
                    "message": "Targets vary by age, meds, hypoglycemia risk, and comorbidities.",
                    "action_step": "Review your targets each visit.",
                    "why": "Improves safety and personalization.",
                },
            },
            "tags": ["diabetes", "targets"],
        },
        {
            "question": "What foods should I avoid or eat more of?",
            "persona": {
                "Listener": {
                    "message": "You don’t have to give up all your favorite foods.",
                    "action_step": "Start with one meal a day that supports your goals.",
                    "why": "Gradual change is more sustainable.",
                },
                "Motivator": {
                    "message": "Every healthy meal is a step toward better control.",
                    "action_step": "Try the plate method (½ veggies, ¼ protein, ¼ carbs).",
                    "why": "Simple structure builds confidence.",
                },
                "Director": {
                    "message": "Limit added sugars and refined carbs; focus on fiber-rich foods.",
                    "action_step": "Choose whole grains and non-starchy vegetables.",
                    "why": "Helps glucose and heart health.",
                },
                "Expert": {
                    "message": "Mediterranean/DASH patterns are often recommended depending on needs.",
                    "action_step": "Use a plan aligned with clinician guidance.",
                    "why": "Evidence-based patterns reduce complications.",
                },
            },
            "tags": ["diabetes", "diet"],
        },
        {
            "question": "Do I need to check my blood sugar every day?",
            "persona": {
                "Listener": {
                    "message": "Testing can feel like a hassle—it’s okay to feel that way.",
                    "action_step": "Ask what schedule fits your treatment plan.",
                    "why": "It should match your meds and risk.",
                },
                "Motivator": {
                    "message": "Each test gives you insight into what works.",
                    "action_step": "Write down results with food/activity notes.",
                    "why": "Connects behaviors to numbers.",
                },
                "Director": {
                    "message": "Some people benefit from daily checks; CGMs may be appropriate for some.",
                    "action_step": "Follow your clinician’s monitoring plan.",
                    "why": "Prevents highs/lows.",
                },
                "Expert": {
                    "message": "Frequency depends on meds, hypoglycemia risk, and A1c goals.",
                    "action_step": "Align monitoring with meds and symptoms.",
                    "why": "Avoids over- or under-testing.",
                },
            },
            "tags": ["diabetes", "monitoring"],
        },
        {
            "question": "Can I still exercise safely with diabetes?",
            "persona": {
                "Listener": {
                    "message": "Exercise can be intimidating at first, especially after a scare.",
                    "action_step": "Start with short walks after meals.",
                    "why": "Gently lowers glucose.",
                },
                "Motivator": {
                    "message": "Moving your body is one of the best things you can do.",
                    "action_step": "Set a 3-days/week activity goal.",
                    "why": "Builds stamina gradually.",
                },
                "Director": {
                    "message": "If you use insulin, monitor glucose before/after workouts.",
                    "action_step": "Carry fast-acting carbs during activity.",
                    "why": "Prevents dangerous lows.",
                },
                "Expert": {
                    "message": "150 min/week moderate activity improves glucose, weight, and BP for many people.",
                    "action_step": "Combine aerobic and resistance training.",
                    "why": "Improves insulin sensitivity.",
                },
            },
            "tags": ["diabetes", "exercise"],
        },
        {
            "question": "How often should I get my A1c checked?",
            "persona": {
                "Listener": {
                    "message": "Blood work can be stressful—I get it.",
                    "action_step": "Set a calendar reminder before appointments.",
                    "why": "Keeps care on track.",
                },
                "Motivator": {
                    "message": "Knowing your A1c helps you see how far you’ve come.",
                    "action_step": "Celebrate improvements!",
                    "why": "Encouragement fuels success.",
                },
                "Director": {
                    "message": "Often every 3–6 months depending on control and changes.",
                    "action_step": "Ask your provider for your schedule.",
                    "why": "Timely changes improve outcomes.",
                },
                "Expert": {
                    "message": "A1c reflects ~2–3 months average glucose; targets are individualized.",
                    "action_step": "Use A1c to adjust your overall plan, not just daily habits.",
                    "why": "Provides a bigger picture than single readings.",
                },
            },
            "tags": ["diabetes", "a1c"],
        },
        {
            "question": "What is A1c and why is it important?",
            "persona": {
                "Listener": {
                    "message": "It’s okay if the term sounds new—many people feel that way.",
                    "action_step": "Ask your provider to explain your last A1c.",
                    "why": "Clarity reduces fear and confusion.",
                },
                "Motivator": {
                    "message": "Knowing your A1c gives you power to improve it.",
                    "action_step": "Track A1c values over time.",
                    "why": "Seeing progress builds motivation.",
                },
                "Director": {
                    "message": "A1c is a 3-month average of blood sugar; many aim near <7% but personalize.",
                    "action_step": "Check A1c every 3–6 months as advised.",
                    "why": "Supports treatment effectiveness.",
                },
                "Expert": {
                    "message": "A1c helps predict complications risk; targets balance control with hypoglycemia safety.",
                    "action_step": "Pair A1c with symptom/CGM patterns for best decisions.",
                    "why": "Improves precision and safety.",
                },
            },
            "tags": ["diabetes", "a1c"],
        },
        {
            "question": "What should I do if I feel shaky or sweaty?",
            "persona": {
                "Listener": {
                    "message": "That can feel scary—lots of people experience it.",
                    "action_step": "Note symptoms and what happened before (food/activity).",
                    "why": "Helps identify triggers.",
                },
                "Motivator": {
                    "message": "Learning your body’s signals makes you stronger.",
                    "action_step": "Keep glucose tablets or juice nearby.",
                    "why": "Preparedness improves confidence.",
                },
                "Director": {
                    "message": "It may be low blood sugar—check if you can and treat promptly.",
                    "action_step": "Use the 15-15 rule if appropriate (15g carbs, recheck in 15 min).",
                    "why": "Prevents severe hypoglycemia.",
                },
                "Expert": {
                    "message": "Hypoglycemia is often <70 mg/dL and needs quick correction.",
                    "action_step": "Report frequent lows; meds may need adjustment.",
                    "why": "Repeated lows increase risk.",
                },
            },
            "tags": ["diabetes", "hypoglycemia"],
        },
        {
            "question": "What long-term complications should I watch for?",
            "persona": {
                "Listener": {
                    "message": "It’s tough to hear about complications—but you’re asking the right question.",
                    "action_step": "Schedule yearly eye, foot, and kidney checks.",
                    "why": "Early detection prevents major issues.",
                },
                "Motivator": {
                    "message": "You’re doing the brave work of prevention.",
                    "action_step": "Celebrate every screening you complete.",
                    "why": "Momentum matters.",
                },
                "Director": {
                    "message": "Watch for eye changes, numbness, kidney issues, and heart symptoms.",
                    "action_step": "Keep a symptom checklist for visits.",
                    "why": "Improves communication and detection.",
                },
                "Expert": {
                    "message": "Diabetes increases risks for heart disease, stroke, neuropathy, and kidney disease.",
                    "action_step": "Treat BP, lipids, glucose, and weight together.",
                    "why": "Multi-factor control reduces complications.",
                },
            },
            "tags": ["diabetes", "complications"],
        },
        {
            "question": "Will I always have to take medication?",
            "persona": {
                "Listener": {
                    "message": "Many people wonder the same thing—it’s a valid concern.",
                    "action_step": "Talk about long-term goals with your provider.",
                    "why": "Supports shared decisions.",
                },
                "Motivator": {
                    "message": "Some people reduce meds with lifestyle changes—sometimes.",
                    "action_step": "Focus on one habit at a time.",
                    "why": "Small wins can lead to big changes.",
                },
                "Director": {
                    "message": "Some can reduce meds; many still need them depending on diabetes type and duration.",
                    "action_step": "Never stop meds without medical guidance.",
                    "why": "Unsupervised changes can be dangerous.",
                },
                "Expert": {
                    "message": "Medication needs vary by diabetes type, duration, genetics, and risk factors.",
                    "action_step": "Reevaluate regimen every 6–12 months.",
                    "why": "Keeps treatment safe and current.",
                },
            },
            "tags": ["diabetes", "meds"],
        },
        {
            "question": "How can I prevent serious complications?",
            "persona": {
                "Listener": {
                    "message": "It’s okay to feel overwhelmed—but you’re not powerless.",
                    "action_step": "Pick one area (food or movement) to improve this week.",
                    "why": "Action reduces fear.",
                },
                "Motivator": {
                    "message": "You have the power to change your story.",
                    "action_step": "Share your goals with someone you trust.",
                    "why": "Accountability helps.",
                },
                "Director": {
                    "message": "Manage the ABCs: A1c, Blood pressure, Cholesterol. And don’t smoke.",
                    "action_step": "Build a tracker for these 3 values.",
                    "why": "Combined control lowers risk dramatically.",
                },
                "Expert": {
                    "message": "Multi-factorial control can cut complication risk substantially over time.",
                    "action_step": "Work with your team on a personalized prevention plan.",
                    "why": "Comprehensive care protects best.",
                },
            },
            "tags": ["diabetes", "prevention"],
        },
    ],
}


# ----------------------------
# Build final QUESTION_BANK with auto IDs
# ----------------------------

def build_question_bank() -> List[Dict[str, Any]]:
    bank: List[Dict[str, Any]] = []
    for category, items in RAW_QUESTION_SETS.items():
        for idx, item in enumerate(items, start=1):
            qid = f"{category}-{idx:02d}"
            question = _clean_text(item.get("question", ""))
            persona = _ensure_persona_block(item.get("persona", {}))
            tags = item.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            tags = [t.strip().lower() for t in tags if str(t).strip()]
            bank.append(
                {
                    "id": qid,
                    "category": category,
                    "question": question,
                    "persona": persona,
                    "tags": tags,
                    "notes": _clean_text(item.get("notes", "")),
                }
            )
    return bank


QUESTION_BANK: List[Dict[str, Any]] = build_question_bank()


# ----------------------------
# Public API functions
# ----------------------------

def all_categories() -> List[str]:
    return sorted(list({q["category"] for q in QUESTION_BANK}))

def list_questions(category: Optional[str] = None) -> List[Dict[str, Any]]:
    if not category:
        return list(QUESTION_BANK)
    cat = category.strip().upper()
    return [q for q in QUESTION_BANK if q["category"] == cat]

def valid_ids(category: Optional[str] = None) -> List[str]:
    return [q["id"] for q in list_questions(category)]

def get_question_by_id(qid: str) -> Optional[Dict[str, Any]]:
    qid = (qid or "").strip().upper()
    for q in QUESTION_BANK:
        if q["id"].upper() == qid:
            return q
    return None

def search_questions(query: str, category: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Searches across:
    - question text
    - tags
    - persona messages/action_step/why (all personas)
    """
    query = _clean_text(query).lower()
    if not query:
        return []
    pool = list_questions(category)
    hits: List[Tuple[int, Dict[str, Any]]] = []

    # Simple scoring: exact word hits score higher
    qwords = set(re.findall(r"[a-z0-9']+", query))

    for q in pool:
        hay = []
        hay.append(q["question"])
        hay.extend(q.get("tags", []))
        for persona in PERSONAS:
            block = q["persona"][persona]
            hay.append(block.get("message", ""))
            hay.append(block.get("action_step", ""))
            hay.append(block.get("why", ""))

        joined = " ".join([str(x) for x in hay]).lower()
        if query in joined:
            score = 50
        else:
            # word overlap scoring
            score = 0
            joined_words = set(re.findall(r"[a-z0-9']+", joined))
            score += 5 * len(qwords.intersection(joined_words))

        if score > 0:
            hits.append((score, q))

    hits.sort(key=lambda t: t[0], reverse=True)
    return [q for _, q in hits[: max(1, limit)]]




