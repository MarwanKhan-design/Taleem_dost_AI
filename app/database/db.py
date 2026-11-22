
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from app.auth.security import hash_password, verify_password, validate_password
from app.services.rubric import grade_answer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "taleem_dost.db"

class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            full_name TEXT NOT NULL, email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_salt TEXT NOT NULL, password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('admin','teacher','student')),
            is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS student_profiles (
            user_id INTEGER PRIMARY KEY, grade TEXT DEFAULT 'Grade XI', board TEXT DEFAULT 'BISE Peshawar',
            group_name TEXT DEFAULT 'Computer Science', FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS study_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT NOT NULL,
            task TEXT NOT NULL, study_date TEXT NOT NULL, duration_minutes INTEGER NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, actor_user_id INTEGER, action TEXT NOT NULL,
            target_user_id INTEGER, details TEXT DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY(target_user_id) REFERENCES users(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS source_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, file_path TEXT NOT NULL,
            board TEXT DEFAULT 'BISE Peshawar', grade TEXT DEFAULT 'Grade XI',
            subject TEXT DEFAULT 'Physics', edition TEXT DEFAULT '', source_type TEXT DEFAULT 'Textbook',
            uploaded_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, grade TEXT DEFAULT 'Grade XI',
            chapter_number TEXT DEFAULT '', title TEXT NOT NULL, source_document_id INTEGER,
            sort_order INTEGER DEFAULT 0, UNIQUE(subject,grade,title),
            FOREIGN KEY(source_document_id) REFERENCES source_documents(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_id INTEGER NOT NULL, title TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0, objectives TEXT DEFAULT '', prerequisites TEXT DEFAULT '',
            UNIQUE(chapter_id,title), FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS lessons (
            topic_id INTEGER PRIMARY KEY, introduction TEXT DEFAULT '', beginner_explanation TEXT DEFAULT '',
            detailed_explanation TEXT DEFAULT '', definitions TEXT DEFAULT '', vocabulary TEXT DEFAULT '',
            examples TEXT DEFAULT '', common_mistakes TEXT DEFAULT '', revision_notes TEXT DEFAULT '',
            topper_notes TEXT DEFAULT '', summary TEXT DEFAULT '', source_reference TEXT DEFAULT '',
            status TEXT DEFAULT 'draft', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, topic_id INTEGER NOT NULL, name TEXT NOT NULL,
            expression TEXT NOT NULL, symbols TEXT DEFAULT '', si_units TEXT DEFAULT '', explanation TEXT DEFAULT '',
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS student_topic_progress (
            user_id INTEGER NOT NULL, topic_id INTEGER NOT NULL, completed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Not started', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,topic_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS study_activity_days (
            user_id INTEGER NOT NULL,
            activity_date TEXT NOT NULL,
            PRIMARY KEY(user_id, activity_date),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS daily_topic_completions (
            user_id INTEGER NOT NULL,
            activity_date TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, activity_date, topic_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS bookmarks (
            user_id INTEGER NOT NULL, topic_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,topic_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS student_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, topic_id INTEGER NOT NULL,
            note TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id,topic_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS practice_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, topic_id INTEGER, question TEXT NOT NULL,
            question_type TEXT DEFAULT 'Practice', options TEXT DEFAULT '', answer TEXT DEFAULT '',
            explanation TEXT DEFAULT '', provenance TEXT DEFAULT 'AI-generated practice',
            board TEXT DEFAULT '', exam_year TEXT DEFAULT '', session TEXT DEFAULT '',
            source_reference TEXT DEFAULT '', verified INTEGER DEFAULT 0,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, quiz_type TEXT NOT NULL, total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL DEFAULT 0, score_percent REAL NOT NULL DEFAULT 0,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS question_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL, selected_answer TEXT DEFAULT '',
            is_correct INTEGER DEFAULT 0, FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
            FOREIGN KEY(question_id) REFERENCES practice_questions(id) ON DELETE CASCADE);
        """)
        # Additive migrations preserve existing Phase 3/4 databases.
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(practice_questions)")}
        for name, definition in [
            ("status", "TEXT DEFAULT 'draft'"),
            ("created_by", "INTEGER"),
            ("created_at", "TEXT DEFAULT 0")
        ]:
            if name not in columns:
                conn.execute(f"ALTER TABLE practice_questions ADD COLUMN {name} {definition}")
        conn.execute("UPDATE practice_questions SET status='published' WHERE status='draft' AND verified=1")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_status_type ON practice_questions(status, question_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_topic ON practice_questions(topic_id)")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, topic_id INTEGER,
            subject TEXT NOT NULL, front TEXT NOT NULL, back TEXT NOT NULL,
            due_date TEXT NOT NULL DEFAULT (date('now')), interval_days INTEGER NOT NULL DEFAULT 1,
            ease REAL NOT NULL DEFAULT 2.5, review_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE SET NULL);
        CREATE INDEX IF NOT EXISTS idx_flashcards_due ON flashcards(user_id,due_date);
        """)

        from app.database.curriculum import seed_curriculum
        seed_curriculum(conn)

def admin_exists():
    with get_connection() as c: return c.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone() is not None

def create_user(username, full_name, email, password, role="student", actor_id=None):
    username, full_name, email = username.strip(), full_name.strip(), email.strip().lower()
    if not username or not full_name or not email: return False, "Please complete all fields."
    if "@" not in email or "." not in email.split("@")[-1]: return False, "Enter a valid email address."
    if role not in ("admin","teacher","student"): return False, "Invalid account role."
    error=validate_password(password)
    if error: return False,error
    salt,digest=hash_password(password)
    try:
        with get_connection() as c:
            cur=c.execute("INSERT INTO users(username,full_name,email,password_salt,password_hash,role) VALUES(?,?,?,?,?,?)",(username,full_name,email,salt,digest,role))
            uid=cur.lastrowid
            if role=="student": c.execute("INSERT INTO student_profiles(user_id) VALUES(?)",(uid,))
            c.execute("INSERT INTO audit_logs(actor_user_id,action,target_user_id,details) VALUES(?,?,?,?)",(actor_id,"user_created",uid,f"role={role}"))
        return True,"Account created successfully."
    except sqlite3.IntegrityError: return False,"That username or email is already registered."

def authenticate(username_or_email,password):
    with get_connection() as c:
        r=c.execute("SELECT id,username,full_name,email,password_salt,password_hash,role,is_active FROM users WHERE username=? COLLATE NOCASE OR email=? COLLATE NOCASE",(username_or_email.strip(),username_or_email.strip())).fetchone()
    if not r or not r["is_active"] or not verify_password(password,r["password_salt"],r["password_hash"]): return None
    return {"id":r["id"],"username":r["username"],"full_name":r["full_name"],"email":r["email"],"role":r["role"]}

def list_users():
    with get_connection() as c: return c.execute("SELECT id,username,full_name,email,role,is_active,created_at FROM users ORDER BY id").fetchall()
def set_user_active(uid,active,actor_id):
    with get_connection() as c:
        r=c.execute("SELECT role FROM users WHERE id=?",(uid,)).fetchone()
        if not r: return False,"User not found."
        if r["role"]=="admin": return False,"Admin accounts cannot be disabled."
        c.execute("UPDATE users SET is_active=? WHERE id=?",(int(active),uid))
        c.execute("INSERT INTO audit_logs(actor_user_id,action,target_user_id,details) VALUES(?,?,?,?)",(actor_id,"user_status_changed",uid,f"is_active={int(active)}"))
    return True,"User status updated."
def get_user_stats():
    with get_connection() as c:
        return {r["role"]:r["n"] for r in c.execute("SELECT role,COUNT(*) n FROM users GROUP BY role")}
def add_task(uid,subject,task,study_date,duration):
    with get_connection() as c: c.execute("INSERT INTO study_tasks(user_id,subject,task,study_date,duration_minutes) VALUES(?,?,?,?,?)",(uid,subject,task,study_date,duration))
def get_tasks(uid):
    with get_connection() as c: return c.execute("SELECT id,subject,task,study_date,duration_minutes,completed FROM study_tasks WHERE user_id=? ORDER BY study_date,id",(uid,)).fetchall()

def add_chapter(subject, title, number="", grade="Grade XI"):
    with get_connection() as c:
        c.execute("INSERT OR IGNORE INTO chapters(subject,grade,chapter_number,title,sort_order) VALUES(?,?,?,?,(SELECT COALESCE(MAX(sort_order),0)+1 FROM chapters WHERE subject=? AND grade=?))",(subject,grade,number,title,subject,grade))
def get_chapters():
    with get_connection() as c: return c.execute("SELECT * FROM chapters ORDER BY subject,sort_order,id").fetchall()
def add_topic(chapter_id,title):
    with get_connection() as c:
        c.execute("INSERT OR IGNORE INTO topics(chapter_id,title,sort_order) VALUES(?,?,(SELECT COALESCE(MAX(sort_order),0)+1 FROM topics WHERE chapter_id=?))",(chapter_id,title,chapter_id))
        return c.execute("SELECT id FROM topics WHERE chapter_id=? AND title=?",(chapter_id,title)).fetchone()["id"]
def get_topics(chapter_id=None):
    with get_connection() as c:
        if chapter_id: return c.execute("SELECT t.*,c.subject,c.title chapter_title FROM topics t JOIN chapters c ON c.id=t.chapter_id WHERE chapter_id=? ORDER BY t.sort_order,t.id",(chapter_id,)).fetchall()
        return c.execute("SELECT t.*,c.subject,c.title chapter_title FROM topics t JOIN chapters c ON c.id=t.chapter_id ORDER BY c.subject,c.sort_order,t.sort_order").fetchall()
def save_lesson(topic_id, fields, status="published"):
    keys=["introduction","beginner_explanation","detailed_explanation","definitions","vocabulary","examples","common_mistakes","revision_notes","topper_notes","summary","source_reference"]
    vals=[fields.get(k,"") for k in keys]
    with get_connection() as c:
        c.execute("INSERT INTO lessons(topic_id,"+",".join(keys)+",status) VALUES("+",".join("?" for _ in range(len(keys)+2))+") ON CONFLICT(topic_id) DO UPDATE SET "+",".join(k+"=excluded."+k for k in keys)+",status=excluded.status,updated_at=CURRENT_TIMESTAMP",[topic_id]+vals+[status])
def get_lesson(topic_id):
    with get_connection() as c: return c.execute("SELECT * FROM lessons WHERE topic_id=?",(topic_id,)).fetchone()
def save_note(uid,tid,note):
    with get_connection() as c: c.execute("INSERT INTO student_notes(user_id,topic_id,note) VALUES(?,?,?) ON CONFLICT(user_id,topic_id) DO UPDATE SET note=excluded.note,updated_at=CURRENT_TIMESTAMP",(uid,tid,note))
def get_note(uid,tid):
    with get_connection() as c:
        r=c.execute("SELECT note FROM student_notes WHERE user_id=? AND topic_id=?",(uid,tid)).fetchone()
        return r["note"] if r else ""
def toggle_bookmark(uid,tid):
    with get_connection() as c:
        exists=c.execute("SELECT 1 FROM bookmarks WHERE user_id=? AND topic_id=?",(uid,tid)).fetchone()
        if exists: c.execute("DELETE FROM bookmarks WHERE user_id=? AND topic_id=?",(uid,tid)); return False
        c.execute("INSERT INTO bookmarks(user_id,topic_id) VALUES(?,?)",(uid,tid)); return True
def is_bookmarked(uid,tid):
    with get_connection() as c: return c.execute("SELECT 1 FROM bookmarks WHERE user_id=? AND topic_id=?",(uid,tid)).fetchone() is not None
def get_topic_status(uid, tid):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM student_topic_progress WHERE user_id=? AND topic_id=?",
            (uid, tid),
        ).fetchone()
    return (row["status"] or "Not started") if row else "Not started"


def _record_study_day(conn, user_id, activity_date):
    conn.execute(
        """INSERT INTO study_activity_days(user_id, activity_date) VALUES (?, ?)
           ON CONFLICT(user_id, activity_date) DO NOTHING""",
        (user_id, activity_date),
    )


def get_study_streak(user_id):
    today = date.today()
    expected = today
    one_day = timedelta(days=1)
    streak = 0
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT activity_date FROM study_activity_days
               WHERE user_id=? AND activity_date<=?
               ORDER BY activity_date DESC""",
            (user_id, today.isoformat()),
        )
        for row in rows:
            if streak == 0 and row["activity_date"] == (today - one_day).isoformat():
                expected = today - one_day
            if row["activity_date"] != expected.isoformat():
                break
            streak += 1
            expected -= one_day
    return streak


def get_monthly_study_activity(user_id):
    today = date.today()
    first = today.replace(day=1)
    with get_connection() as conn:
        prior_days = [
            row["activity_date"]
            for row in conn.execute(
                """SELECT activity_date FROM study_activity_days
                   WHERE user_id=? AND activity_date<? ORDER BY activity_date DESC""",
                (user_id, first.isoformat()),
            )
        ]
        month_rows = conn.execute(
            """SELECT days.activity_date, COUNT(topics.topic_id) AS completed
               FROM study_activity_days AS days
               LEFT JOIN daily_topic_completions AS topics
                 ON topics.user_id=days.user_id AND topics.activity_date=days.activity_date
               WHERE days.user_id=? AND days.activity_date BETWEEN ? AND ?
               GROUP BY days.activity_date""",
            (user_id, first.isoformat(), today.isoformat()),
        ).fetchall()
    completions = {row["activity_date"]: row["completed"] for row in month_rows}
    streak = 0
    for offset, prior in enumerate(prior_days, 1):
        if prior != (first - timedelta(days=offset)).isoformat():
            break
        streak += 1
    streaks = []
    topic_counts = []
    for day in range(1, today.day + 1):
        key = today.replace(day=day).isoformat()
        streak = streak + 1 if key in completions else 0
        streaks.append(streak)
        topic_counts.append(completions.get(key, 0))
    return today, streaks, topic_counts


def mark_topic(uid, tid, status):
    completed = int(status == "Completed")
    with get_connection() as conn:
        result = conn.execute(
            """INSERT INTO student_topic_progress(user_id,topic_id,status,completed)
               VALUES(?,?,?,?)
               ON CONFLICT(user_id,topic_id) DO UPDATE SET
                   status=excluded.status, completed=excluded.completed,
                   updated_at=CURRENT_TIMESTAMP
               WHERE student_topic_progress.status IS NOT excluded.status
                  OR student_topic_progress.completed IS NOT excluded.completed""",
            (uid, tid, status, completed),
        )
        if completed and result.rowcount:
            activity_date = date.today().isoformat()
            _record_study_day(conn, uid, activity_date)
            conn.execute(
                """INSERT INTO daily_topic_completions(user_id, activity_date, topic_id)
                   VALUES (?, ?, ?) ON CONFLICT(user_id, activity_date, topic_id) DO NOTHING""",
                (uid, activity_date, tid),
            )
def get_progress(uid):
    with get_connection() as c:
        return c.execute("SELECT COUNT(*) total,SUM(CASE WHEN p.completed=1 THEN 1 ELSE 0 END) done FROM topics t LEFT JOIN student_topic_progress p ON p.topic_id=t.id AND p.user_id=?",(uid,)).fetchone()
def add_formula(tid,name,expression,symbols="",units="",explanation=""):
    with get_connection() as c: c.execute("INSERT INTO formulas(topic_id,name,expression,symbols,si_units,explanation) VALUES(?,?,?,?,?,?)",(tid,name,expression,symbols,units,explanation))
def get_formulas(tid):
    with get_connection() as c: return c.execute("SELECT * FROM formulas WHERE topic_id=?",(tid,)).fetchall()
def add_question(tid,question,qtype,answer="",explanation="",provenance="AI-generated practice",board="",year="",session="",source=""):
    with get_connection() as c: c.execute("INSERT INTO practice_questions(topic_id,question,question_type,answer,explanation,provenance,board,exam_year,session,source_reference) VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,question,qtype,answer,explanation,provenance,board,year,session,source))
def get_questions(tid):
    with get_connection() as c: return c.execute("SELECT * FROM practice_questions WHERE topic_id=? ORDER BY id DESC",(tid,)).fetchall()


def add_exam_question(topic_id, question, qtype, options, correct_answer, explanation,
                     provenance, board="", year="", session="", source="", created_by=None):
    with get_connection() as c:
        cur=c.execute("""INSERT INTO practice_questions
            (topic_id,question,question_type,options,answer,explanation,provenance,board,exam_year,session,source_reference,verified,status,created_by)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (topic_id,question,qtype,options,correct_answer,explanation,provenance,board,year,session,source,
             1 if provenance=="Verified past-paper question" else 0,"published",created_by))
        return cur.lastrowid

def get_published_questions(subject=None, qtype=None, topic_id=None, limit=100, rubric_only=False):
    sql="""SELECT q.*,t.title topic_title,c.subject FROM practice_questions q
           LEFT JOIN topics t ON t.id=q.topic_id LEFT JOIN chapters c ON c.id=t.chapter_id
           WHERE q.status='published'"""
    args=[]
    if subject and subject!="All subjects": sql+=" AND c.subject=?"; args.append(subject)
    if qtype and qtype!="All types": sql+=" AND q.question_type=?"; args.append(qtype)
    if topic_id: sql+=" AND q.topic_id=?"; args.append(topic_id)
    if rubric_only:
        sql += " AND q.question_type IN ('Short question','Long question') AND TRIM(q.answer) <> ''"
    sql+=" ORDER BY q.id DESC LIMIT ?"; args.append(limit)
    with get_connection() as c: return c.execute(sql,args).fetchall()

def get_question_bank_admin():
    with get_connection() as c:
        return c.execute("SELECT q.*,t.title topic_title FROM practice_questions q LEFT JOIN topics t ON t.id=q.topic_id ORDER BY q.id DESC").fetchall()

def set_question_status(question_id,status):
    if status not in ("draft","published","archived"): return
    with get_connection() as c: c.execute("UPDATE practice_questions SET status=? WHERE id=?",(status,question_id))

def save_quiz_attempt(user_id,subject,quiz_type,question_rows,answers):
    grades = {q["id"]: grade_answer(q, answers.get(q["id"], "")) for q in question_rows}
    earned = sum(grade["earned"] for grade in grades.values())
    possible = sum(grade["possible"] for grade in grades.values())
    total = sum(grade["possible"] > 0 for grade in grades.values())
    correct = sum(grade["earned"] == grade["possible"] > 0 for grade in grades.values())
    score = round(earned / possible * 100, 1) if possible else 0
    with get_connection() as c:
        cur=c.execute("""INSERT INTO quiz_attempts(user_id,subject,quiz_type,total_questions,correct_answers,score_percent,completed_at)
                         VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)""",(user_id,subject,quiz_type,total,correct,score))
        aid=cur.lastrowid
        for q in question_rows:
            selected=answers.get(q["id"],"")
            grade = grades[q["id"]]
            is_correct = int(grade["earned"] == grade["possible"]) if grade["possible"] else None
            c.execute("INSERT INTO question_attempts(attempt_id,question_id,selected_answer,is_correct) VALUES(?,?,?,?)",
                      (aid,q["id"],selected,is_correct))
        if any(answers.get(q["id"], "").strip() for q in question_rows):
            _record_study_day(c, user_id, date.today().isoformat())
    return {"attempt_id": aid, "total": total, "correct": correct, "score": score,
            "earned": earned, "possible": possible, "grades": grades}

def get_quiz_history(user_id,limit=20):
    with get_connection() as c:
        return c.execute("SELECT * FROM quiz_attempts WHERE user_id=? ORDER BY id DESC LIMIT ?",(user_id,limit)).fetchall()


def get_topic_context(topic_id):
    with get_connection() as c:
        row=c.execute("""SELECT t.title topic_title,c.subject,l.* FROM topics t
            JOIN chapters c ON c.id=t.chapter_id LEFT JOIN lessons l ON l.topic_id=t.id
            WHERE t.id=?""",(topic_id,)).fetchone()
        return row

def sync_flashcards(uid):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO flashcards(user_id, topic_id, subject, front, back)
               SELECT u.id, t.id, c.subject, q.question, q.answer
               FROM practice_questions q
               JOIN topics t ON t.id=q.topic_id
               JOIN chapters c ON c.id=t.chapter_id
               JOIN users u ON u.id=?
               WHERE q.id IN (
                   SELECT MIN(id) FROM practice_questions
                   WHERE status='published' AND TRIM(answer)<>''
                   GROUP BY topic_id, question
               )
               AND NOT EXISTS (
                   SELECT 1 FROM flashcards f
                   WHERE f.user_id=u.id AND f.topic_id=t.id AND f.front=q.question
               )
               ORDER BY q.id""",
            (uid,),
        )

def get_due_flashcards(uid):
    with get_connection() as c:
        return c.execute(
            """SELECT f.*, q.question_type, q.options
               FROM flashcards f
               LEFT JOIN practice_questions q ON q.id=(
                   SELECT id FROM practice_questions
                   WHERE topic_id=f.topic_id AND question=f.front
                     AND status='published' AND TRIM(answer)<>''
                   ORDER BY id LIMIT 1
               )
               WHERE f.user_id=? AND f.due_date<=date('now')
               ORDER BY f.due_date,f.id""",
            (uid,),
        ).fetchall()

def review_flashcard(card_id, uid, quality):
    # Simple SM-2-inspired schedule: Again=0, Hard=1, Good=2, Easy=3.
    with get_connection() as c:
        r=c.execute("SELECT interval_days,ease,review_count FROM flashcards WHERE id=? AND user_id=?",
                    (card_id,uid)).fetchone()
        if not r: return
        interval=int(r["interval_days"]); ease=float(r["ease"]); count=int(r["review_count"])
        if quality == 0:
            interval=1; count=0; ease=max(1.3,ease-0.2)
        else:
            count += 1
            if quality == 1: interval=max(1,round(interval*1.2)); ease=max(1.3,ease-0.15)
            elif quality == 2: interval=1 if count==1 else (6 if count==2 else max(2,round(interval*ease)))
            else: interval=2 if count==1 else max(3,round(interval*ease*1.3)); ease=min(3.0,ease+0.15)
        c.execute("""UPDATE flashcards SET interval_days=?,ease=?,review_count=?,
            due_date=date('now',?) WHERE id=? AND user_id=?""",
            (interval,ease,count,f"+{interval} days",card_id,uid))

def get_weak_topics(uid):
    with get_connection() as c:
        return c.execute("""SELECT t.id topic_id,t.title topic,c.subject,
            COUNT(qa.id) attempts,SUM(CASE WHEN qa.is_correct=1 THEN 1 ELSE 0 END) correct,
            ROUND(100.0*SUM(CASE WHEN qa.is_correct=1 THEN 1 ELSE 0 END)/COUNT(qa.id),1) accuracy
            FROM question_attempts qa JOIN quiz_attempts a ON a.id=qa.attempt_id
            JOIN practice_questions q ON q.id=qa.question_id
            JOIN topics t ON t.id=q.topic_id JOIN chapters c ON c.id=t.chapter_id
            WHERE a.user_id=? AND q.topic_id IS NOT NULL AND qa.is_correct IS NOT NULL
            GROUP BY t.id HAVING COUNT(qa.id)>=1 ORDER BY accuracy ASC,attempts DESC""",(uid,)).fetchall()

def get_board_intelligence():
    with get_connection() as c:
        return c.execute("""SELECT c.subject,t.title topic,q.board,q.exam_year,q.session,
            COUNT(*) question_count,COUNT(DISTINCT q.exam_year) years_seen
            FROM practice_questions q JOIN topics t ON t.id=q.topic_id
            JOIN chapters c ON c.id=t.chapter_id
            WHERE q.verified=1 AND q.provenance='Verified past-paper question'
              AND TRIM(COALESCE(q.exam_year,''))<>'' AND TRIM(COALESCE(q.source_reference,''))<>''
            GROUP BY c.subject,t.id,q.board,q.exam_year,q.session
            ORDER BY c.subject,t.title,q.exam_year DESC""").fetchall()
