"""Original supplementary learning pack. Never represents historical board papers."""
import json
from pathlib import Path

SUBJECTS = ["Physics", "Mathematics", "Computer Science", "Chemistry", "Biology",
            "English", "Urdu", "Pakistan Studies", "Mutala-e-Quran Hakeem", "Islamiat"]
PACK = Path(__file__).resolve().parents[2] / "data" / "kpk_grade_xi.json"


def seed_curriculum(conn):
    """Add a versioned pack once, preserving teacher content and student records."""
    pack = json.loads(PACK.read_text(encoding="utf-8"))
    conn.execute("CREATE TABLE IF NOT EXISTS content_packs (pack_id TEXT PRIMARY KEY, installed_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    if conn.execute("SELECT 1 FROM content_packs WHERE pack_id=?", (pack["id"],)).fetchone():
        return
    source = pack["source_note"]
    for order, entry in enumerate(pack["topics"], 1):
        subject, chapter, title = entry["subject"], entry["chapter"], entry["title"]
        conn.execute("INSERT OR IGNORE INTO chapters(subject,grade,title,sort_order) VALUES(?,?,?,?)",
                     (subject, "Grade XI", chapter, order))
        cid = conn.execute("SELECT id FROM chapters WHERE subject=? AND grade=? AND title=?",
                           (subject, "Grade XI", chapter)).fetchone()[0]
        conn.execute("INSERT OR IGNORE INTO topics(chapter_id,title,sort_order,objectives,prerequisites) VALUES(?,?,?,?,?)",
                     (cid, title, order, entry["objectives"], entry["prerequisites"]))
        tid = conn.execute("SELECT id FROM topics WHERE chapter_id=? AND title=?", (cid, title)).fetchone()[0]
        # Never overwrite a lesson a teacher has already written.
        fields = {"introduction": entry["introduction"], "beginner_explanation": entry["concept"],
                  "detailed_explanation": entry["detail"], "definitions": entry["definition"],
                  "examples": entry["example"], "common_mistakes": entry["mistake"],
                  "revision_notes": entry["revision"], "topper_notes": entry["exam_tip"],
                  "summary": entry["concept"], "source_reference": source}
        keys = list(fields)
        conn.execute("INSERT OR IGNORE INTO lessons(topic_id," + ",".join(keys) + ",status) VALUES(" +
                     ",".join("?" for _ in range(len(keys)+2)) + ")", [tid, *fields.values(), "published"])
        for question in entry["questions"]:
            # Allows safe recovery and avoids duplicating an existing identical question.
            if conn.execute("SELECT 1 FROM practice_questions WHERE topic_id=? AND question=?", (tid, question["prompt"])).fetchone():
                continue
            conn.execute("""INSERT INTO practice_questions
                (topic_id,question,question_type,options,answer,explanation,provenance,board,source_reference,verified,status)
                VALUES(?,?,?,?,?,?,?,?,?,0,'published')""",
                (tid, question["prompt"], question["type"], "\n".join(question.get("options", [])),
                 question["answer"], question["explanation"], "Original curriculum practice",
                 "Khyber Pakhtunkhwa study support", source))
        if entry.get("formula"):
            f = entry["formula"]
            if not conn.execute("SELECT 1 FROM formulas WHERE topic_id=? AND name=?", (tid, title)).fetchone():
                conn.execute("INSERT INTO formulas(topic_id,name,expression,symbols,si_units,explanation) VALUES(?,?,?,?,?,?)",
                             (tid, title, f[0], f[1], f[2], entry["concept"]))
    conn.execute("INSERT INTO content_packs(pack_id) VALUES(?)", (pack["id"],))
