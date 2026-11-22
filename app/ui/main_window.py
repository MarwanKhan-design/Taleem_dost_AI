
from calendar import monthrange
from datetime import date
from html import escape
from pathlib import Path
import shutil, re
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from app.database import db
from app.services.rubric import RUBRIC_PROMPTS, RUBRIC_SAMPLES, WRITTEN_TYPES, written_mark_count
from app.ui.styles import APP_STYLE
from app.ui.smart_learning import SmartLearningPage
from app.ui.study_chart import StudyChart

from app.database.curriculum import SUBJECTS
def heading(title,sub=""):
    box=QVBoxLayout(); a=QLabel(title); a.setObjectName("page_title"); box.addWidget(a)
    if sub:
        b=QLabel(sub); b.setObjectName("muted"); b.setWordWrap(True); box.addWidget(b)
    return box
def card(text):
    w=QLabel(text); w.setObjectName("notice"); w.setWordWrap(True); w.setMinimumHeight(55); return w

class MainWindow(QMainWindow):
    def __init__(self,user):
        super().__init__(); self.user=user; self.current_topic=None
        self.setWindowTitle("Taleem Dost AI — Smart Learning Platform"); self.resize(1360,900); self.setMinimumSize(1050,700); self.setStyleSheet(APP_STYLE)
        central=QWidget(); central.setObjectName("central"); self.setCentralWidget(central)
        root=QHBoxLayout(central); root.setContentsMargins(0,0,0,0)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220); sv=QVBoxLayout(side)
        brand=QLabel("🎓 Taleem Dost AI"); brand.setObjectName("brand"); sv.addWidget(brand)
        identity=QLabel(f"{user['full_name']}  •  {user['role'].upper()}")
        identity.setObjectName("brand_sub"); identity.setWordWrap(True); sv.addWidget(identity)
        self.tabs=QTabWidget(); self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.dashboard(),"🏠 Dashboard")
        self.tabs.addTab(self.learning(),"📚 Learn")
        self.tabs.addTab(self.revision(),"🧠 Revision & Practice")
        self.tabs.addTab(SmartLearningPage(user),"Study Insights")
        self.tabs.addTab(self.planner(),"📅 Study Planner")
        self.tabs.addTab(self.progress(),"📊 Progress")
        if user["role"]=="admin": self.tabs.addTab(self.admin_users(),"🛡 Users")
        self.tabs.tabBar().hide()
        self.nav_group=QButtonGroup(self); self.nav_group.setExclusive(True)
        for index in range(self.tabs.count()):
            button=QPushButton(self.tabs.tabText(index)); button.setObjectName("nav"); button.setCheckable(True)
            self.nav_group.addButton(button,index); sv.addWidget(button)
            button.clicked.connect(lambda checked,i=index:self.tabs.setCurrentIndex(i))
        self.tabs.currentChanged.connect(lambda i:self.nav_group.button(i).setChecked(True))
        self.tabs.currentChanged.connect(self.refresh_dashboard)
        self.nav_group.button(0).setChecked(True)
        sv.addStretch(); root.addWidget(side); root.addWidget(self.tabs,1)

    def dashboard(self):
        page = QWidget()
        page.setObjectName("dashboard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("page_title")
        header.addWidget(title, 1)
        self.dashboard_date = QLabel()
        self.dashboard_date.setObjectName("dashboard_date")
        header.addWidget(self.dashboard_date)
        layout.addLayout(header)

        hero = QFrame()
        hero.setObjectName("dashboard_hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        welcome = QVBoxLayout()
        welcome.setSpacing(4)
        name = self.user["full_name"].strip().split()
        greeting = QLabel(f"Welcome, {name[0]}" if name else "Welcome")
        greeting.setTextFormat(Qt.PlainText)
        greeting.setObjectName("hero_title")
        welcome.addWidget(greeting)
        subtitle = QLabel("Grade XI study library and exam practice")
        subtitle.setObjectName("hero_sub")
        welcome.addWidget(subtitle)
        hero_layout.addLayout(welcome, 1)
        practice = QPushButton("Start practice")
        practice.setObjectName("dashboard_outline")
        practice.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        library = QPushButton("Open library")
        library.setObjectName("dashboard_action")
        library.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        hero_layout.addWidget(practice)
        hero_layout.addWidget(library)
        layout.addWidget(hero)

        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.streak_value = QLabel()
        self.streak_detail = QLabel()
        self.completion_value = QLabel()
        self.completion_detail = QLabel()
        self.active_days_value = QLabel()
        self.active_days_detail = QLabel()
        for label, value, detail in (
            ("Current streak", self.streak_value, self.streak_detail),
            ("Topics completed", self.completion_value, self.completion_detail),
            ("Study days this month", self.active_days_value, self.active_days_detail),
        ):
            panel = QFrame()
            panel.setObjectName("dashboard_panel")
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(17, 12, 17, 12)
            panel_layout.setSpacing(3)
            caption = QLabel(label)
            caption.setObjectName("card_title")
            value.setObjectName("dashboard_value")
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            panel_layout.addWidget(caption)
            panel_layout.addWidget(value)
            panel_layout.addWidget(detail)
            panel_layout.addStretch()
            stats.addWidget(panel, 1)
        layout.addLayout(stats)

        activity = QHBoxLayout()
        activity_title = QLabel("Study activity")
        activity_title.setObjectName("page_title")
        activity.addWidget(activity_title, 1)
        self.study_month = QLabel()
        self.study_month.setObjectName("dashboard_date")
        activity.addWidget(self.study_month)
        layout.addLayout(activity)

        charts = QHBoxLayout()
        charts.setSpacing(14)
        self.monthly_streak = StudyChart(heatmap=True)
        self.daily_topics = StudyChart()
        for title, chart in (
            ("Streak calendar", self.monthly_streak),
            ("Topics completed per day", self.daily_topics),
        ):
            panel = QFrame()
            panel.setObjectName("dashboard_panel")
            column = QVBoxLayout(panel)
            column.setContentsMargins(12, 12, 12, 6)
            label = QLabel(title)
            label.setObjectName("card_title")
            column.addWidget(label)
            column.addWidget(chart)
            charts.addWidget(panel, 1)
        layout.addLayout(charts)
        layout.addStretch()
        self.refresh_dashboard()
        return self.scroll(page)

    def refresh_dashboard(self, index=0):
        if index != 0:
            return
        user_id = self.user["id"]
        streak = db.get_study_streak(user_id)
        today, streaks, topic_counts = db.get_monthly_study_activity(user_id)
        first_weekday, days_in_month = monthrange(today.year, today.month)
        self.dashboard_date.setText(f"{today:%A, %B} {today.day}")
        self.study_month.setText(today.strftime("%B %Y"))
        self.monthly_streak.set_data(streaks, days_in_month, first_weekday)
        self.daily_topics.set_data(topic_counts, days_in_month)

        unit = "day" if streak == 1 else "days"
        self.streak_value.setText(f"{streak} {unit}")
        self.streak_detail.setText(
            "You earned today's streak." if streaks[-1]
            else "Complete a topic or submit an answered quiz."
        )
        progress = db.get_progress(user_id)
        total = progress["total"] or 0
        done = progress["done"] or 0
        percent = round(done / total * 100) if total else 0
        self.completion_value.setText(f"{done} / {total}")
        self.completion_detail.setText(f"{percent}% of the learning library")
        self.active_days_value.setText(str(sum(value > 0 for value in streaks)))
        topics = sum(topic_counts)
        topic_label = "topic" if topics == 1 else "topics"
        self.active_days_detail.setText(f"{topics} {topic_label} completed this month")

    def learning(self):
        p=QWidget(); outer=QVBoxLayout(p); outer.addLayout(heading("📚 Learning Library","Select a subject, chapter and topic to explore the learning library."))
        filters=QHBoxLayout(); self.subject_filter=QComboBox(); self.subject_filter.addItems(SUBJECTS)
        self.chapter_filter=QComboBox(); self.topic_filter=QComboBox()
        for label,w in [("Subject",self.subject_filter),("Chapter",self.chapter_filter),("Topic",self.topic_filter)]:
            col=QVBoxLayout(); col.addWidget(QLabel(label)); col.addWidget(w); filters.addLayout(col,1)
        outer.addLayout(filters)
        self.subject_filter.currentTextChanged.connect(self.refresh_chapters)
        self.chapter_filter.currentIndexChanged.connect(self.refresh_topics)
        self.topic_filter.currentIndexChanged.connect(self.show_lesson)
        self.lesson_view=QTextBrowser(); self.lesson_view.setOpenExternalLinks(True); outer.addWidget(self.lesson_view,3)
        row=QHBoxLayout()
        self.status_box=QComboBox(); self.status_box.addItems(["Not started","Learning","Needs revision","Completed"])
        save_status=QPushButton("Save learning status"); save_status.clicked.connect(self.save_status)
        self.bookmark_btn=QPushButton("☆ Bookmark"); self.bookmark_btn.clicked.connect(self.bookmark)
        row.addWidget(self.status_box); row.addWidget(save_status); row.addWidget(self.bookmark_btn); outer.addLayout(row)
        outer.addWidget(QLabel("My private notes")); self.note_edit=QTextEdit(); self.note_edit.setMaximumHeight(110); outer.addWidget(self.note_edit)
        nb=QPushButton("Save my notes"); nb.clicked.connect(self.save_notes); outer.addWidget(nb)
        self.refresh_chapters(); return p

    def refresh_chapters(self,*_):
        subject=self.subject_filter.currentText(); self.chapter_filter.blockSignals(True); self.chapter_filter.clear()
        self.chapters=[x for x in db.get_chapters() if x["subject"]==subject]
        for ch in self.chapters: self.chapter_filter.addItem(f"{ch['chapter_number']}  {ch['title']}",ch["id"])
        self.chapter_filter.blockSignals(False); self.refresh_topics()
    def refresh_topics(self,*_):
        self.topic_filter.blockSignals(True); self.topic_filter.clear()
        cid=self.chapter_filter.currentData()
        self.topics=db.get_topics(cid) if cid else []
        for t in self.topics: self.topic_filter.addItem(t["title"],t["id"])
        self.topic_filter.blockSignals(False); self.show_lesson()
    def show_lesson(self,*_):
        tid=self.topic_filter.currentData(); self.current_topic=tid
        if not tid: self.lesson_view.setHtml("<h3>No topics in this chapter yet.</h3>"); self.note_edit.clear(); return
        topic=next((t for t in self.topics if t["id"]==tid),None); lesson=db.get_lesson(tid)
        if not lesson:
            self.lesson_view.setHtml("<h2>"+topic["title"]+"</h2><p>This lesson is not available yet. Please choose another topic.</p>")
        else:
            labels=[("Introduction","introduction"),("Learning objectives","objectives"),("Prerequisites","prerequisites"),("Beginner explanation","beginner_explanation"),("Detailed explanation","detailed_explanation"),("Definitions","definitions"),("Vocabulary (English / Urdu / Pashto)","vocabulary"),("Examples and solved work","examples"),("Common mistakes","common_mistakes"),("Revision notes","revision_notes"),("Topper notes","topper_notes"),("Summary","summary"),("Source reference","source_reference")]
            html=f"<h1>{topic['title']}</h1><p><b>Content status:</b> {lesson['status']}</p>"
            for label,key in labels:
                value=topic[key] if key in ("objectives","prerequisites") else lesson[key]
                if value: html+=f"<h2>{label}</h2><p>{value.replace(chr(10),'<br>')}</p>"
            forms=db.get_formulas(tid)
            if forms:
                html+="<h2>Formula library</h2>"
                for f in forms: html+=f"<p><b>{f['name']}</b>: {f['expression']}<br>{f['symbols']}<br>SI units: {f['si_units']}<br>{f['explanation']}</p>"
            self.lesson_view.setHtml(html)
        self.status_box.setCurrentText(db.get_topic_status(self.user["id"], tid))
        self.note_edit.setPlainText(db.get_note(self.user["id"],tid)); self.bookmark_btn.setText("★ Bookmarked" if db.is_bookmarked(self.user["id"],tid) else "☆ Bookmark")
    def save_status(self):
        if self.current_topic:
            db.mark_topic(self.user["id"],self.current_topic,self.status_box.currentText()); QMessageBox.information(self,"Saved","Learning status updated.")
    def bookmark(self):
        if self.current_topic:
            state=db.toggle_bookmark(self.user["id"],self.current_topic); self.bookmark_btn.setText("★ Bookmarked" if state else "☆ Bookmark")
    def save_notes(self):
        if self.current_topic: db.save_note(self.user["id"],self.current_topic,self.note_edit.toPlainText()); QMessageBox.information(self,"Saved","Your private note has been saved.")

    def revision(self):
        p=QWidget(); v=QVBoxLayout(p)
        v.addLayout(heading("📝 Exam Preparation & Mock Tests","Practise questions published by your teacher/admin. Scores are saved to your account."))
        filters=QHBoxLayout()
        self.exam_subject=QComboBox(); self.exam_subject.addItems(["All subjects"]+SUBJECTS)
        self.exam_type=QComboBox(); self.exam_type.addItems(["All types","MCQ","Short question","Long question","Numerical","Rubric practice"])
        self.exam_count=QSpinBox(); self.exam_count.setRange(1,50); self.exam_count.setValue(10)
        for label,w in [("Subject",self.exam_subject),("Question type",self.exam_type),("Questions",self.exam_count)]:
            col=QVBoxLayout(); col.addWidget(QLabel(label)); col.addWidget(w); filters.addLayout(col)
        v.addLayout(filters)
        self.exam_info=QLabel("Choose filters, then start a practice session. Only published questions are included.")
        self.exam_info.setObjectName("notice"); self.exam_info.setWordWrap(True); v.addWidget(self.exam_info)
        self.quiz_area=QScrollArea(); self.quiz_area.setWidgetResizable(True)
        self.quiz_inner=QWidget(); self.quiz_layout=QVBoxLayout(self.quiz_inner); self.quiz_area.setWidget(self.quiz_inner); v.addWidget(self.quiz_area,1)
        row=QHBoxLayout()
        start=QPushButton("Start Practice"); start.setObjectName("primary"); start.clicked.connect(self.start_quiz)
        submit=QPushButton("Submit Answers"); submit.clicked.connect(self.submit_quiz)
        self.submit_quiz_btn=submit; self.submit_quiz_btn.setEnabled(False)
        row.addWidget(start); row.addWidget(submit); v.addLayout(row)
        self.quiz_questions=[]; self.quiz_controls={}
        self.history_table=QTableWidget(0,5); self.history_table.setHorizontalHeaderLabels(["Date","Subject","Type","Score","Full credit"])
        self.history_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        v.addWidget(QLabel("Recent attempts")); v.addWidget(self.history_table); self.load_quiz_history()
        return p

    def start_quiz(self):
        subject=self.exam_subject.currentText(); qtype=self.exam_type.currentText()
        rubric_only = qtype == "Rubric practice"
        rows=db.get_published_questions(subject,None if rubric_only else qtype,
                                        limit=self.exam_count.value(),rubric_only=rubric_only)
        if not rows:
            QMessageBox.information(self,"No published questions","There are no published questions matching these filters yet. Try another subject or question type.")
            return
        self.quiz_questions=list(rows); self.quiz_controls={}
        while self.quiz_layout.count():
            item=self.quiz_layout.takeAt(0); widget=item.widget()
            if widget: widget.deleteLater()
        for i,q in enumerate(self.quiz_questions,1):
            box=QGroupBox(f"Question {i} — {q['question_type']}")
            layout=QVBoxLayout(box)
            prompt=QLabel(RUBRIC_PROMPTS.get(q["question"], q["question"]))
            prompt.setTextFormat(Qt.PlainText)
            prompt.setWordWrap(True)
            layout.addWidget(prompt)
            options=[x.strip() for x in q["options"].splitlines() if x.strip()]
            if q["question_type"]=="MCQ" and options:
                group=QButtonGroup(box)
                for opt in options:
                    rb=QRadioButton(opt); group.addButton(rb); layout.addWidget(rb)
                self.quiz_controls[q["id"]]=("mcq",group)
            else:
                if q["question_type"] in WRITTEN_TYPES:
                    marks = written_mark_count(q)
                    unit = "mark" if marks == 1 else "marks"
                    label = f"{marks} {unit} · Answer in your own words" if marks else "Self-review · Compare with the sample after submitting"
                    layout.addWidget(QLabel(label))
                edit=QPlainTextEdit(); edit.setPlaceholderText("Write your answer here..."); edit.setMaximumHeight(85)
                layout.addWidget(edit); self.quiz_controls[q["id"]]=("text",edit)
            self.quiz_layout.addWidget(box)
        self.quiz_layout.addStretch()
        self.exam_info.setText(f"Practice session ready: {len(rows)} question(s). Your answers are not saved until you submit.")
        self.submit_quiz_btn.setEnabled(True)

    def submit_quiz(self):
        if not self.quiz_questions: return
        answers={}
        for q in self.quiz_questions:
            kind,control=self.quiz_controls[q["id"]]
            if kind=="mcq":
                checked=control.checkedButton()
                answers[q["id"]]=checked.text() if checked else ""
            else: answers[q["id"]]=control.toPlainText().strip()
        result=db.save_quiz_attempt(self.user["id"],self.exam_subject.currentText(),
                                    self.exam_type.currentText(),self.quiz_questions,answers)
        self.submit_quiz_btn.setEnabled(False)
        if result["possible"]:
            report = (f"<h2>Practice result: {result['score']}%</h2>"
                      f"<p>{result['earned']} / {result['possible']} marks on scored questions.</p>")
        else:
            report = "<h2>Practice review</h2><p>Compare your answers with the sample responses below.</p>"
        for i,q in enumerate(self.quiz_questions,1):
            selected = escape(answers.get(q["id"], "") or "Not answered").replace("\n", "<br>")
            sample = escape(RUBRIC_SAMPLES.get(q["question"], q["answer"])).replace("\n", "<br>")
            prompt = escape(RUBRIC_PROMPTS.get(q["question"], q["question"]))
            grade = result["grades"][q["id"]]
            report += f"<hr><b>Q{i}. {prompt}</b><p>Your answer: {selected}</p><p>Sample answer: {sample}</p>"
            if grade["points"]:
                report += f"<p><b>{grade['earned']} / {grade['possible']} marks</b></p><ul>"
                for point, earned in grade["points"]:
                    feedback = "Earned (+1)" if earned else "Needs review (+0)"
                    report += f"<li>{feedback} · {escape(point)}</li>"
                report += "</ul>"
            elif not grade["possible"]:
                report += "<p>Self-review only. This answer is excluded from the score.</p>"
            else:
                status = "Correct" if grade["earned"] else "Review this answer"
                report += f"<p>{status}. {escape(q['explanation'])}</p>"
        while self.quiz_layout.count():
            item=self.quiz_layout.takeAt(0); widget=item.widget()
            if widget: widget.deleteLater()
        result_view=QTextBrowser(); result_view.setHtml(report); self.quiz_layout.addWidget(result_view)
        self.exam_info.setText("Your attempt has been saved in your private quiz history.")
        self.quiz_questions=[]; self.load_quiz_history()

    def load_quiz_history(self):
        if not hasattr(self,"history_table"): return
        rows=db.get_quiz_history(self.user["id"]); self.history_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            score = f"{x['score_percent']}%" if x["total_questions"] else "Self-review"
            full_credit = f"{x['correct_answers']}/{x['total_questions']}" if x["total_questions"] else "—"
            vals=[x["completed_at"] or x["started_at"],x["subject"],x["quiz_type"],score,full_credit]
            for c,val in enumerate(vals): self.history_table.setItem(r,c,QTableWidgetItem(str(val)))

    def planner(self):
        p=QWidget(); v=QVBoxLayout(p); v.addLayout(heading("📅 Study Planner","Plan study sessions for this local account."))
        self.plan_subject=QComboBox(); self.plan_subject.addItems(SUBJECTS)
        self.plan_date=QDateEdit(); self.plan_date.setCalendarPopup(True); self.plan_date.setDate(date.today())
        self.plan_task=QLineEdit(); self.plan_task.setPlaceholderText("e.g. Revise vectors and solve 5 numericals")
        self.plan_minutes=QSpinBox(); self.plan_minutes.setRange(10,300); self.plan_minutes.setValue(40)
        for label,w in [("Subject",self.plan_subject),("Date",self.plan_date),("Task",self.plan_task),("Minutes",self.plan_minutes)]: v.addWidget(QLabel(label)); v.addWidget(w)
        b=QPushButton("Save task"); b.setObjectName("primary"); b.clicked.connect(self.save_task); v.addWidget(b)
        self.task_table=QTableWidget(0,4); self.task_table.setHorizontalHeaderLabels(["Date","Subject","Task","Minutes"]); self.task_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch); v.addWidget(self.task_table); self.load_tasks(); return self.scroll(p)
    def save_task(self):
        task=self.plan_task.text().strip()
        if not task: QMessageBox.warning(self,"Task missing","Enter a task."); return
        db.add_task(self.user["id"],self.plan_subject.currentText(),task,self.plan_date.date().toString("yyyy-MM-dd"),self.plan_minutes.value()); self.plan_task.clear(); self.load_tasks()
    def load_tasks(self):
        rows=db.get_tasks(self.user["id"]); self.task_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,val in enumerate([x["study_date"],x["subject"],x["task"],x["duration_minutes"]]): self.task_table.setItem(r,c,QTableWidgetItem(str(val)))
    def progress(self):
        p=QWidget(); v=QVBoxLayout(p); v.addLayout(heading("📊 My Progress","Your personal topic completion summary."))
        pr=db.get_progress(self.user["id"]); total=pr["total"] or 0; done=pr["done"] or 0
        v.addWidget(card(f"Total topics: {total}     Completed: {done}     Completion: {round(done/total*100) if total else 0}%"))
        v.addWidget(card("Use the Learn tab to mark topics as Learning, Needs revision or Completed. Progress is stored locally in this desktop version.")); v.addStretch(); return p

    def content_admin(self):
        p=QWidget(); v=QVBoxLayout(p); v.addLayout(heading("🛠 Content Studio","For admins and teachers. Upload source PDFs, organize topics, and publish lesson content."))
        tabs=QTabWidget(); v.addWidget(tabs)
        source=QWidget(); sv=QVBoxLayout(source); self.src_title=QLineEdit(); self.src_title.setPlaceholderText("Textbook / source title")
        self.src_subject=QComboBox(); self.src_subject.addItems(SUBJECTS); self.src_edition=QLineEdit(); self.src_edition.setPlaceholderText("Edition / year (if known)")
        self.src_path=QLineEdit(); self.src_path.setReadOnly(True); choose=QPushButton("Choose PDF"); choose.clicked.connect(self.choose_pdf)
        upload=QPushButton("Import source PDF"); upload.setObjectName("primary"); upload.clicked.connect(self.import_pdf)
        for label,w in [("Title",self.src_title),("Subject",self.src_subject),("Edition",self.src_edition),("Selected file",self.src_path)]: sv.addWidget(QLabel(label)); sv.addWidget(w)
        sv.addWidget(choose); sv.addWidget(upload); sv.addWidget(card("PDFs are copied into this project's data/sources folder. Text extraction requires PyMuPDF. Scanned PDFs need OCR; this version does not run OCR automatically.")); tabs.addTab(source,"Source Library")
        org=QWidget(); ov=QVBoxLayout(org); self.new_ch_subject=QComboBox(); self.new_ch_subject.addItems(SUBJECTS); self.new_ch_num=QLineEdit(); self.new_ch_title=QLineEdit()
        for label,w in [("Subject",self.new_ch_subject),("Chapter number",self.new_ch_num),("Chapter title (verify with textbook)",self.new_ch_title)]: ov.addWidget(QLabel(label)); ov.addWidget(w)
        cb=QPushButton("Add chapter"); cb.clicked.connect(self.create_chapter); ov.addWidget(cb)
        self.chapter_admin=QComboBox(); self.new_topic_title=QLineEdit(); ov.addWidget(QLabel("Select chapter")); ov.addWidget(self.chapter_admin); ov.addWidget(QLabel("New topic title")); ov.addWidget(self.new_topic_title)
        tb=QPushButton("Add topic"); tb.clicked.connect(self.create_topic); ov.addWidget(tb); tabs.addTab(org,"Chapters & Topics")
        lesson=QWidget(); lv=QVBoxLayout(lesson); self.lesson_topic=QComboBox()
        lv.addWidget(QLabel("Topic")); lv.addWidget(self.lesson_topic)
        self.lesson_fields={}
        field_defs=[("Introduction","introduction"),("Learning objectives","objectives"),("Prerequisites","prerequisites"),("Beginner explanation","beginner_explanation"),("Detailed explanation","detailed_explanation"),("Definitions","definitions"),("Vocabulary: English / Urdu / Pashto","vocabulary"),("Examples and solved work","examples"),("Common mistakes","common_mistakes"),("Revision notes","revision_notes"),("Topper notes","topper_notes"),("Summary","summary"),("Source reference (book, page, section)","source_reference")]
        area=QScrollArea(); area.setWidgetResizable(True); fw=QWidget(); fl=QVBoxLayout(fw)
        for label,key in field_defs:
            fl.addWidget(QLabel(label)); e=QPlainTextEdit(); e.setPlaceholderText(label); e.setMinimumHeight(65); self.lesson_fields[key]=e; fl.addWidget(e)
        area.setWidget(fw); lv.addWidget(area,1)
        self.lesson_status=QComboBox(); self.lesson_status.addItems(["draft","published"]); lv.addWidget(QLabel("Publication status")); lv.addWidget(self.lesson_status)
        self.lesson_topic.currentIndexChanged.connect(self.load_lesson_editor)
        save=QPushButton("Save lesson"); save.setObjectName("primary"); save.clicked.connect(self.save_lesson_editor); lv.addWidget(save); tabs.addTab(lesson,"Lesson Editor")
        formula=QWidget(); fv=QVBoxLayout(formula); self.formula_topic=QComboBox(); self.formula_name=QLineEdit(); self.formula_expr=QLineEdit(); self.formula_symbols=QLineEdit(); self.formula_units=QLineEdit(); self.formula_explain=QTextEdit()
        for label,w in [("Topic",self.formula_topic),("Formula name",self.formula_name),("Expression",self.formula_expr),("Symbols explained",self.formula_symbols),("SI units",self.formula_units),("Explanation",self.formula_explain)]: fv.addWidget(QLabel(label)); fv.addWidget(w)
        fb=QPushButton("Add formula"); fb.clicked.connect(self.save_formula); fv.addWidget(fb); tabs.addTab(formula,"Formula Library")

        qbank=QWidget(); qv=QVBoxLayout(qbank)
        qv.addWidget(QLabel("Create questions for student practice. For MCQs, write one option per line and set the correct option exactly as written."))
        self.q_topic=QComboBox(); self.q_topic.addItem("General / unassigned",None)
        self.qtype=QComboBox(); self.qtype.addItems(["MCQ","Short question","Long question","Numerical"])
        self.q_prompt=QPlainTextEdit(); self.q_prompt.setPlaceholderText("Question text")
        self.q_options=QPlainTextEdit(); self.q_options.setPlaceholderText("A) First option\\nB) Second option\\nC) Third option\\nD) Fourth option")
        self.q_answer=QLineEdit(); self.q_answer.setPlaceholderText("Correct option text or model answer")
        self.q_explanation=QPlainTextEdit(); self.q_explanation.setPlaceholderText("Explanation / worked solution")
        self.q_provenance=QComboBox(); self.q_provenance.addItems(["Teacher-created practice","AI-generated practice","Verified past-paper question"])
        self.q_board=QLineEdit("BISE Peshawar"); self.q_year=QLineEdit(); self.q_session=QLineEdit(); self.q_source=QLineEdit()
        for label,w in [("Topic",self.q_topic),("Question type",self.qtype),("Question",self.q_prompt),("MCQ options (one per line)",self.q_options),("Correct answer",self.q_answer),("Explanation",self.q_explanation),("Question source",self.q_provenance),("Board",self.q_board),("Year",self.q_year),("Session",self.q_session),("Source / page / question number",self.q_source)]:
            qv.addWidget(QLabel(label)); qv.addWidget(w)
        qsave=QPushButton("Publish question"); qsave.setObjectName("primary"); qsave.clicked.connect(self.publish_question); qv.addWidget(qsave)
        self.qbank_table=QTableWidget(0,5); self.qbank_table.setHorizontalHeaderLabels(["ID","Question","Type","Source","Status"]); self.qbank_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); qv.addWidget(self.qbank_table)
        tabs.addTab(qbank,"Question Bank")
        self.refresh_admin_lists()
        self.load_question_bank()
        return p
    def choose_pdf(self):
        path,_=QFileDialog.getOpenFileName(self,"Select textbook PDF","","PDF files (*.pdf)")
        if path: self.src_path.setText(path)
    def import_pdf(self):
        src=self.src_path.text()
        if not src or not Path(src).exists(): QMessageBox.warning(self,"Select a PDF","Choose a PDF first."); return
        title=self.src_title.text().strip() or Path(src).stem
        destdir=Path(__file__).resolve().parents[2]/"data"/"sources"; destdir.mkdir(parents=True,exist_ok=True)
        dest=destdir/(re.sub(r"[^A-Za-z0-9._-]+","_",Path(src).name))
        if Path(src).resolve()!=dest.resolve(): shutil.copy2(src,dest)
        extracted=""
        try:
            import fitz
            doc=fitz.open(str(dest)); pages=[]
            for i,page in enumerate(doc): pages.append(f"\\n\\n--- PAGE {i+1} ---\\n"+page.get_text())
            extracted="".join(pages)
            (destdir/(dest.stem+".txt")).write_text(extracted,encoding="utf-8")
        except ImportError: extracted="PyMuPDF not installed. Run: pip install PyMuPDF"
        except Exception as exc: extracted=f"Extraction issue: {exc}"
        from app.database.db import get_connection
        with get_connection() as c:
            c.execute("INSERT INTO source_documents(title,file_path,subject,edition,uploaded_by) VALUES(?,?,?,?,?)",(title,str(dest),self.src_subject.currentText(),self.src_edition.text(),self.user["id"]))
        QMessageBox.information(self,"Source imported",f"PDF copied successfully.\\n\\nExtraction result: {len(extracted)} characters.\\nText file, when extracted, is saved beside the PDF. Please verify page references manually.")
    def refresh_admin_lists(self):
        chapters=db.get_chapters(); self.chapter_admin.clear()
        for c in chapters: self.chapter_admin.addItem(f"{c['subject']} • {c['chapter_number']} {c['title']}",c["id"])
        self.lesson_topic.clear(); self.formula_topic.clear()
        if hasattr(self,"q_topic"):
            self.q_topic.clear(); self.q_topic.addItem("General / unassigned",None)
        for t in db.get_topics():
            label=f"{t['subject']} • {t['chapter_title']} • {t['title']}"
            self.lesson_topic.addItem(label,t["id"]); self.formula_topic.addItem(label,t["id"])
            if hasattr(self,"q_topic"): self.q_topic.addItem(label,t["id"])
        self.load_lesson_editor()
    def create_chapter(self):
        title=self.new_ch_title.text().strip()
        if not title: return
        db.add_chapter(self.new_ch_subject.currentText(),title,self.new_ch_num.text().strip())
        self.new_ch_title.clear(); self.refresh_admin_lists()
    def create_topic(self):
        cid=self.chapter_admin.currentData(); title=self.new_topic_title.text().strip()
        if cid and title: db.add_topic(cid,title); self.new_topic_title.clear(); self.refresh_admin_lists()
    def load_lesson_editor(self,*_):
        tid=self.lesson_topic.currentData()
        if not tid: return
        topic=next((x for x in db.get_topics() if x["id"]==tid),None); lesson=db.get_lesson(tid)
        for key,e in self.lesson_fields.items():
            value=(topic[key] if topic and key in ("objectives","prerequisites") else lesson[key] if lesson and key in lesson.keys() else "")
            e.setPlainText(value or "")
        if lesson: self.lesson_status.setCurrentText(lesson["status"])
    def save_lesson_editor(self):
        tid=self.lesson_topic.currentData()
        if not tid: return
        fields={k:e.toPlainText() for k,e in self.lesson_fields.items()}
        db.save_lesson(tid,fields,self.lesson_status.currentText())
        from app.database.db import get_connection
        with get_connection() as c: c.execute("UPDATE topics SET objectives=?,prerequisites=? WHERE id=?",(fields["objectives"],fields["prerequisites"],tid))
        QMessageBox.information(self,"Saved","Lesson content saved.")
    def save_formula(self):
        tid=self.formula_topic.currentData()
        if tid and self.formula_name.text().strip() and self.formula_expr.text().strip():
            db.add_formula(tid,self.formula_name.text(),self.formula_expr.text(),self.formula_symbols.text(),self.formula_units.text(),self.formula_explain.toPlainText())
            QMessageBox.information(self,"Saved","Formula added.")
    def publish_question(self):
        prompt=self.q_prompt.toPlainText().strip(); answer=self.q_answer.text().strip()
        if not prompt or not answer:
            QMessageBox.warning(self,"Missing details","Enter both the question and its correct answer."); return
        qtype=self.qtype.currentText(); options=self.q_options.toPlainText().strip()
        if qtype=="MCQ":
            option_lines=[x.strip() for x in options.splitlines() if x.strip()]
            if len(option_lines)<2 or answer not in option_lines:
                QMessageBox.warning(self,"MCQ options","Add at least two options and make the correct answer exactly match one option line."); return
        provenance=self.q_provenance.currentText()
        if provenance=="Verified past-paper question" and (not self.q_year.text().strip() or not self.q_source.text().strip()):
            QMessageBox.warning(self,"Source required","A past-paper question needs its year and source/page/question number."); return
        db.add_exam_question(self.q_topic.currentData(),prompt,qtype,options,answer,self.q_explanation.toPlainText(),
                             provenance,self.q_board.text(),self.q_year.text(),self.q_session.text(),self.q_source.text(),self.user["id"])
        self.q_prompt.clear(); self.q_options.clear(); self.q_answer.clear(); self.q_explanation.clear()
        self.load_question_bank()
        QMessageBox.information(self,"Published","Question published to student practice.")
    def load_question_bank(self):
        if not hasattr(self,"qbank_table"): return
        rows=db.get_question_bank_admin(); self.qbank_table.setRowCount(len(rows))
        for r,q in enumerate(rows):
            vals=[q["id"],q["question"][:100],q["question_type"],q["provenance"],q["status"]]
            for c,val in enumerate(vals): self.qbank_table.setItem(r,c,QTableWidgetItem(str(val)))

    def admin_users(self):
        p=QWidget(); v=QVBoxLayout(p); v.addLayout(heading("🛡️ Account Management","Local desktop user administration. Not a production cloud security console."))
        self.user_table=QTableWidget(0,6); self.user_table.setHorizontalHeaderLabels(["ID","Username","Name","Email","Role","Active"]); self.user_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch); v.addWidget(self.user_table)
        refresh=QPushButton("Refresh"); refresh.clicked.connect(self.load_users); v.addWidget(refresh)
        self.target_user=QSpinBox(); self.target_user.setRange(1,9999999); v.addWidget(QLabel("User ID")); v.addWidget(self.target_user)
        row=QHBoxLayout()
        for label,active in [("Enable",True),("Disable",False)]:
            b=QPushButton(label); b.clicked.connect(lambda _,a=active:self.change_user(a)); row.addWidget(b)
        v.addLayout(row); self.load_users(); return p
    def load_users(self):
        rows=db.list_users(); self.user_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,val in enumerate([x["id"],x["username"],x["full_name"],x["email"],x["role"],"Yes" if x["is_active"] else "No"]): self.user_table.setItem(r,c,QTableWidgetItem(str(val)))
    def change_user(self,active):
        ok,msg=db.set_user_active(self.target_user.value(),active,self.user["id"]); QMessageBox.information(self,"Account",msg); self.load_users()
    def scroll(self,w):
        s=QScrollArea(); s.setWidgetResizable(True); s.setFrameShape(QFrame.NoFrame); s.setWidget(w); return s
