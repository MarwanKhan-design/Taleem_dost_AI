"""Phase 7 AI and adaptive-learning services for Taleem Dost AI."""
import os, json, base64
from pathlib import Path

# Explicit project-root .env loading (independent of PyCharm working directory).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_FILE, override=False)
except ImportError:
    pass

def _client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OpenAI API key is missing. Add it to your .env file and restart the app.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI package is missing. Run: python -m pip install -r requirements.txt") from exc
    return OpenAI(api_key=key)

def _model():
    return os.getenv("OPENAI_MODEL", "gpt-5.5").strip() or "gpt-5.5"

def solve_photo(path, subject="General", language="English"):
    p = Path(path)
    if not p.exists():
        raise RuntimeError("The selected image could not be found.")
    if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise RuntimeError("Choose a PNG, JPG, JPEG or WEBP image.")
    if p.stat().st_size > 12 * 1024 * 1024:
        raise RuntimeError("Image is too large. Please choose an image smaller than 12 MB.")
    mime = {".png":"image/png", ".jpg":"image/jpeg", ".jpeg":"image/jpeg", ".webp":"image/webp"}[p.suffix.lower()]
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    response = _client().responses.create(
        model=_model(),
        instructions=("You are Taleem Dost AI, a careful tutor for Pakistani secondary and higher-secondary students. "
                      "Read the question in the image carefully. If any text is unclear, say exactly what is unclear; "
                      "do not guess missing values. Explain step by step at the student's level. For numericals list "
                      "given values, required quantity, formula, substitution, calculation and units. "
                      "Never claim a question is from a past paper unless the student provides a verifiable source. "
                      f"Subject: {subject}. Response language: {language}."),
        input=[{"role":"user","content":[
            {"type":"input_text","text":"Please read and solve the question in this image. Explain the method."},
            {"type":"input_image","image_url":f"data:{mime};base64,{encoded}"}
        ]}],
        store=False, max_output_tokens=2200
    )
    answer=(response.output_text or "").strip()
    if not answer:
        raise RuntimeError("The AI returned an empty answer.")
    return answer

def generate_quiz(topic, subject, count=5, language="English"):
    response = _client().responses.create(
        model=_model(),
        instructions=("Create original educational practice questions for a Pakistani Grade XI student. "
                      "Return ONLY valid JSON: {\"questions\":[{\"question\":\"...\",\"options\":[\"A) ...\","
                      "\"B) ...\",\"C) ...\",\"D) ...\"],\"answer\":\"exactly one option including its letter\","
                      "\"explanation\":\"...\"}]}. Every question must have exactly four options and one unambiguous "
                      "correct answer. Do not claim these are historical board questions. Do not invent syllabus "
                      "or textbook references. Use the requested language."),
        input=f"Subject: {subject}\nTopic: {topic}\nNumber of questions: {max(3,min(int(count),15))}\nLanguage: {language}",
        store=False, max_output_tokens=3500
    )
    raw=(response.output_text or "").strip()
    if raw.startswith("```"):
        raw=raw.strip("`")
        if raw.lower().startswith("json"): raw=raw[4:].strip()
    try:
        data=json.loads(raw)
        questions=data["questions"]
        if not isinstance(questions,list) or not questions:
            raise ValueError()
        clean=[]
        for q in questions[:15]:
            opts=q.get("options",[])
            if not q.get("question") or len(opts)!=4 or not q.get("answer"):
                continue
            clean.append({"question":str(q["question"]), "options":"\n".join(map(str,opts)),
                          "answer":str(q["answer"]), "explanation":str(q.get("explanation",""))})
        if not clean: raise ValueError()
        return clean
    except Exception as exc:
        raise RuntimeError("The AI response was not valid quiz data. Please try generating the quiz again.") from exc

def generate_flashcards(topic, subject, lesson_text, count=8):
    response = _client().responses.create(
        model=_model(),
        instructions=("Create concise revision flashcards for a Grade XI student. Return ONLY JSON "
                      "{\"cards\":[{\"front\":\"question or term\",\"back\":\"clear concise answer\"}]}. "
                      "Use only the supplied lesson content; do not invent facts. Use distinct cards."),
        input=f"Subject: {subject}\nTopic: {topic}\nLesson:\n{lesson_text[:10000]}\nCreate {max(3,min(int(count),15))} cards.",
        store=False, max_output_tokens=2200
    )
    raw=(response.output_text or "").strip()
    if raw.startswith("```"):
        raw=raw.strip("`")
        if raw.lower().startswith("json"): raw=raw[4:].strip()
    try:
        cards=json.loads(raw)["cards"]
        return [{"front":str(x["front"]), "back":str(x["back"])} for x in cards if x.get("front") and x.get("back")][:15]
    except Exception as exc:
        raise RuntimeError("The AI response was not valid flashcard data. Please try again.") from exc
