from backend.ai_engine import ask_ai

def generate_flashcards(text):

    prompt=f"""
Create flashcards.
Format:

Q:
A:

Notes:
{text}
"""

    return ask_ai(prompt)