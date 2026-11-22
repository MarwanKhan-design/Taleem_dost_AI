"""OpenAI-powered academic tutor service. API keys are read only from environment variables."""
import os
from pathlib import Path

# Load .env from the project folder, not the current working directory.
# This makes the app work when launched through PyCharm or a desktop shortcut.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_FILE, override=False)
except ImportError:
    pass

TUTOR_INSTRUCTIONS = """
You are Taleem Dost AI, a patient and careful tutor for Pakistani secondary and higher-secondary students.
Teach at the student's level. Start with a simple explanation, then build understanding step by step.
For Physics/Mathematics numericals: list given values, identify the required quantity, choose the formula,
substitute values with units, calculate carefully, and state the final answer with units.
Explain important terms. Use clear headings and examples. Respond in the requested language.
If asked for Urdu, use readable Urdu script. If asked for Pashto, use simple Pashto where possible.
Never invent BISE Peshawar past-paper sources, years, question numbers, syllabus claims, textbook page references,
or exam predictions. If a fact depends on a particular textbook or board syllabus and no source is supplied,
say it needs verification. Clearly distinguish a generated practice question from a historical exam question.
Do not claim to be an official board authority. Encourage learning rather than merely copying answers.
Keep responses age-appropriate, respectful, and focused on education.
"""

def is_configured():
    return bool(os.getenv("OPENAI_API_KEY", "").strip())

def ask_tutor(messages, subject="General", language="English", lesson_context=""):
    api_key=os.getenv("OPENAI_API_KEY","").strip()
    if not api_key:
        raise RuntimeError("OpenAI API key is not configured. Set OPENAI_API_KEY in Windows environment variables and restart the app.")
    model=os.getenv("OPENAI_MODEL","gpt-5.5").strip() or "gpt-5.5"
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI package is missing. Run: python -m pip install -r requirements.txt") from exc
    client=OpenAI(api_key=api_key)
    context=f"Student selected subject: {subject}. Preferred response language: {language}."
    if lesson_context:
        context += "\nVerified lesson context supplied by the app (treat as user-provided reference, not guaranteed official):\n"+lesson_context[:12000]
    response=client.responses.create(
        model=model,
        instructions=TUTOR_INSTRUCTIONS+"\n\nCurrent learning context:\n"+context,
        input=messages[-12:],
        store=False,
        max_output_tokens=1800,
    )
    answer=(response.output_text or "").strip()
    if not answer:
        raise RuntimeError("The AI service returned an empty answer. Please try again.")
    return answer
