from backend.ai_engine import ask_ai

def create_plan(text):

    prompt=f"""
Create a study plan based on topics.

Notes:
{text}
"""

    return ask_ai(prompt)