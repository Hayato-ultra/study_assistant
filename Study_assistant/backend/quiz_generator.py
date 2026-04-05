from backend.ai_engine import ask_ai

def generate_quiz(text):
    prompt=f"""
Create quiz from notes.

Include:
MCQ
True/False
Fill blanks
Short answers

Notes:
{text}
"""
    return ask_ai(prompt)