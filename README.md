# hi5304-notebooks
Data science module on GitHub

Running signatures_engine.py (Signatures Engine)

The Signatures Engine is a Python script that integrates behavioral context (Signatures), clinical calculators (e.g., MyLifeCheck, PREVENT), and structured messaging. It is designed to be run from the terminal, not by clicking the file.

Prerequisites

A working GitHub Codespace (or local environment with Python 3)

The following files located in the learning/ folder:

signatures_engine.py

combined_calculator.py

Step-by-Step Instructions (GitHub Codespaces)
1. Open a Terminal

In Codespaces:

Use the menu: Terminal → New Terminal

Or press <kbd>Ctrl</kbd> + <kbd>`</kbd>

You should see a prompt similar to:

vscode ➜ /workspaces/hi5304-notebooks $

2. Change to the learning Folder

The Signatures engine lives in the learning directory. Navigate there:

cd learning


Confirm you’re in the correct folder:

ls


You should see:

signatures_engine.py
combined_calculator.py

3. Run the Signatures Engine

Run the engine using Python:

python signatures_engine.py


(If needed in your environment, you may use python3 instead.)

4. Follow the Interactive Prompts

The program will prompt you to enter:

A question (e.g., “How do I start an exercise program?”)

A behavioral core (e.g., PA, BP, NUT)

Any relevant condition modifiers (e.g., CD, HT, CKD)

Engagement drivers with values (-1, 0, or 1)

Clinical values (e.g., blood pressure, labs, activity) are automatically reused from combined_calculator.py when available and do not need to be re-entered.

5. Review the Output

At the end, the engine will print a structured JSON payload that includes:

Behavioral core messaging

Condition modifier messages

Engagement driver framing

Security rules

Action plans

Measurement outputs (MyLifeCheck, PREVENT, etc.)

Links to American Heart Association content

This output is designed to be LLM-ready and can be used for downstream applications, APIs, or research workflows.

