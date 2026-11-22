
from calendar import monthrange
from datetime import date
from html import escape
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
        side=QFrame(); side.setObjectName("sidebar"); sv=QVBoxLayout(side)
        sv.setSizeConstraint(QLayout.SetMinimumSize)
        side.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        brand = QLabel("🎓 Taleem Dost AI")
        brand.setObjectName("brand")
        brand.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sv.addWidget(brand)
        sv.addSpacing(4)
        self.tabs=QTabWidget(); self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.dashboard(),"🏠 Dashboard")
        self.tabs.addTab(self.learning(),"📚 Learn")
        self.tabs.addTab(self.revision(),"🧠 Revision & Practice")
        self.tabs.addTab(SmartLearningPage(user),"💡 Study Insights")
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
        sv.addStretch()
        root.addWidget(side); root.addWidget(self.tabs,1)

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
