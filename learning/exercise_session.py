
# ------------------------
# Exercise Session
# ------------------------

def pre_exercise_check(
    symptoms_since_last_session,
    medications_taken_as_prescribed,
    mental_health,
    resting_heart_rate,
    systolic_blood_pressure,
    diastolic_blood_pressure,
    glucose,
    pulse_ox,
    ecg
):
    # Symptom and medication checks
    if symptoms_since_last_session.lower() == "yes":
        return "Follow up with healthcare professional before exercise"
    if medications_taken_as_prescribed.lower() == "no":
        return "Take medications before exercise"
    if mental_health.lower() != "good":
        return "Address mental health prior to exercise"

    # Biometric checks
    if resting_heart_rate < 60 or resting_heart_rate > 100:
        return "Follow up with healthcare professional before exercise"
    if systolic_blood_pressure > 180:
        return "Follow up with healthcare professional before exercise"
    if diastolic_blood_pressure > 100:
        return "Follow up with healthcare professional before exercise"
    if glucose > 240:
        return "Follow up with healthcare professional before exercise"
    if pulse_ox < 90:
        return "Follow up with healthcare professional before exercise"
    if ecg.lower() != "normal":
        return "Follow up with healthcare professional before exercise"

    # All checks passed
    return "Proceed to exercise phase"


# Example usage:
pre_status = pre_exercise_check(
    symptoms_since_last_session="no",
    medications_taken_as_prescribed="yes",
    mental_health="good",
    resting_heart_rate=72,
    systolic_blood_pressure=130,
    diastolic_blood_pressure=85,
    glucose=110,
    pulse_ox=96,
    ecg="normal"
)
print("\n=== Exercise Session ===")
print("Pre-Exercise Status:", pre_status)



# -------------------- Logic Functions --------------------

def check_progression(exercise_heart_rate, target_heart_rate, perceived_exertion, symptoms):
    if any(symptom.lower() != "no" for symptom in symptoms):
        return "❗ Stop exercise and check in with healthcare professional"

    hr_diff = exercise_heart_rate - target_heart_rate

    if -5 <= hr_diff <= 5 and 3 <= perceived_exertion <= 4:
        return "✅ Proceed to next stage"
    elif hr_diff < -5 and perceived_exertion < 3:
        return "➡️ Advance to the next level"
    elif hr_diff > 5 and perceived_exertion > 4:
        return "⬅️ Return to previous level"
    else:
        return "⏸️ Maintain current stage and monitor"

def post_exercise_check(
    post_exercise_heart_rate,
    resting_heart_rate,
    post_exercise_systolic_bp,
    post_exercise_diastolic_bp,
    post_exercise_glucose,
    symptoms
):
    if any(symptom.lower() != "no" for symptom in symptoms):
        return "⚠️ Continue monitoring"

    hr_recovered = post_exercise_heart_rate < 100 or abs(post_exercise_heart_rate - resting_heart_rate) <= 10
    bp_ok = post_exercise_systolic_bp < 180 and post_exercise_diastolic_bp < 100

    if hr_recovered and bp_ok:
        return "✅ You can end the session"
    else:
        return "⚠️ Continue monitoring"


# -------------------- Prescription Input --------------------

def input_exercise_stage(stage_number):
    print(f"\n--- Input for Stage {stage_number} ---")
    stage_name = input("Enter stage name (warm-up, cardio, resistance, cool-down): ").strip().lower()
    modality = input("Enter modality (walking, cycling, swimming, dancing, jogging, resistance band): ").strip().lower()
    intensity = input("Enter intensity (e.g., 3 mph, level 5, moderate): ").strip()
    duration = int(input("Enter duration (in minutes): ").strip())

    stage = {
        "stage_name": stage_name,
        "modality": modality,
        "duration": duration,
        "intensity": intensity,
        "exercise_heart_rate": 0,        # Placeholder
        "perceived_exertion": 0,         # Placeholder
        "symptoms": ["no"]               # Placeholder
    }
    return stage

def prescribe_exercise_program(filename="exercise_program.json"):
    stages = []
    stage_number = 1
    print("=== 📝 Exercise Prescription Input ===")

    while True:
        stage = input_exercise_stage(stage_number)
        stages.append(stage)
        stage_number += 1

        add_more = input("Add another stage? (yes/no): ").strip().lower()
        if add_more != "yes":
            break

    with open(filename, 'w') as f:
        json.dump(stages, f, indent=2)
    print(f"\n✅ Program saved to '{filename}'")

def load_preprogrammed_session(program_name, filename="preprogrammed_sessions.json"):
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return None

    with open(filename, 'r') as f:
        all_programs = json.load(f)

    if program_name not in all_programs:
        print(f"❌ Program '{program_name}' not found in '{filename}'")
        return None

    print(f"\n✅ Loaded '{program_name}' program from {filename}")
    return all_programs[program_name]


# -------------------- Session Execution --------------------

def run_exercise_session(filename="exercise_program.json", target_heart_rate=110):
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return

    with open(filename, 'r') as f:
        stages = json.load(f)

    print("\n=== 🏃 Running Exercise Session ===")
    resting_heart_rate = int(input("Enter resting heart rate (bpm): ").strip())

    for i, stage in enumerate(stages, 1):
        print(f"\n--- Stage {i}: {stage['stage_name'].capitalize()} ({stage['modality']}) ---")
        print(f"Prescribed: {stage['duration']} minutes at {stage['intensity']}")

        hr = int(input("Enter actual exercise heart rate: ").strip())
        exertion = int(input("Enter perceived exertion (Borg scale 1–10): ").strip())
        symptoms_input = input("Any symptoms? (comma-separated, or 'no'): ").strip().lower()
        symptoms = [s.strip() for s in symptoms_input.split(",")]

        stage["exercise_heart_rate"] = hr
        stage["perceived_exertion"] = exertion
        stage["symptoms"] = symptoms

        result = check_progression(hr, target_heart_rate, exertion, symptoms)
        print(f"🩺 Recommendation: {result}")

    # Post-exercise check
    print("\n=== 🧘 Post-Exercise Check ===")
    post_hr = int(input("Post-exercise heart rate: "))
    post_sys = int(input("Post-exercise systolic BP: "))
    post_dia = int(input("Post-exercise diastolic BP: "))
    post_glucose = int(input("Post-exercise glucose: "))
    post_symptoms = input("Any symptoms post-exercise? (comma-separated, or 'no'): ").strip().lower()
    post_symptoms_list = [s.strip() for s in post_symptoms.split(",")]

    post_result = post_exercise_check(
        post_hr, resting_heart_rate, post_sys, post_dia, post_glucose, post_symptoms_list
    )

    print(f"\n🩺 Final Recommendation: {post_result}")

    with open("exercise_session_log.json", 'w') as f:
        json.dump(stages, f, indent=2)

    print("\n✅ Session log saved to 'exercise_session_log.json'")


# -------------------- Main Runner --------------------

if __name__ == "__main__":
            print("\n📋 Welcome to the Monitored Exercise Session Tool")
            print("1. Prescribe a new program")
            print("2. Run a saved session")
            print("3. Run a preprogrammed session\n")

            choice = input("Select an option (1, 2, or 3): ").strip()

            if choice == "1":
                prescribe_exercise_program()

            elif choice == "2":
                target_hr = int(input("Enter target heart rate for session: "))
                run_exercise_session(target_heart_rate=target_hr)

            elif choice == "3":
                print("\nAvailable Programs: beginner_program, advanced_program")
                program_name = input("Enter the name of the preprogrammed session: ").strip()
                target_hr = int(input("Enter target heart rate for session: "))
                session_stages = load_preprogrammed_session(program_name)
                if session_stages:
                    # Save to temp file and run it
                    with open("exercise_program.json", "w") as f:
                        json.dump(session_stages, f, indent=2)
                    run_exercise_session(target_heart_rate=target_hr)
            else:
                print("Invalid choice. Please restart the program.")
