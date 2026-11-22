from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from app.database import db
from app.services.smart_learning import solve_photo, generate_quiz, generate_flashcards
from app.services.ai_tutor import is_configured

from app.database.curriculum import SUBJECTS

class WorkThread(QThread):
    done=pyqtSignal(object)
    failed=pyqtSignal(str)
    def __init__(self, fn, *args):
        super().__init__(); self.fn=fn; self.args=args
    def run(self):
        try: self.done.emit(self.fn(*self.args))
        except Exception as e: self.failed.emit(str(e))

class SmartLearningPage(QWidget):
    def __init__(self,user,parent_window=None):
        super().__init__(); self.user=user; self.parent_window=parent_window
        root=QVBoxLayout(self)
        title=QLabel("🚀 Smart AI Learning & Exam Intelligence"); title.setObjectName("page_title"); root.addWidget(title)
        intro=QLabel("Photo solving, AI-generated practice, personal weakness insights, flashcards and evidence-based board-paper trends.")
        intro.setWordWrap(True); intro.setObjectName("muted"); root.addWidget(intro)
        self.tabs=QTabWidget(); root.addWidget(self.tabs,1)
        self.tabs.addTab(self.photo_tab(),"📷 Photo Solver")
        self.tabs.addTab(self.quiz_tab(),"✨ AI Quiz")
        self.tabs.addTab(self.weakness_tab(),"🎯 My Weak Topics")
        self.tabs.addTab(self.flashcard_tab(),"🗂 Flashcards")
        self.tabs.addTab(self.board_tab(),"📈 Board Trends")
        self.worker=None

    def photo_tab(self):
        w=QWidget(); v=QVBoxLayout(w)
        v.addWidget(QLabel("Upload a clear photo of a textbook or practice question. The image is sent to the AI provider to answer your request; it is not saved in this app's database."))
        row=QHBoxLayout(); self.photo_path=QLineEdit(); self.photo_path.setReadOnly(True)
        choose=QPushButton("Choose image"); choose.clicked.connect(self.choose_photo)
        self.photo_subject=QComboBox(); self.photo_subject.addItems(SUBJECTS)
        self.photo_language=QComboBox(); self.photo_language.addItems(["English","Urdu","Pashto","English + Urdu"])
        solve=QPushButton("Solve question"); solve.setObjectName("primary"); solve.clicked.connect(self.run_photo)
        row.addWidget(self.photo_path,3); row.addWidget(choose); v.addLayout(row)
        opts=QHBoxLayout(); opts.addWidget(QLabel("Subject")); opts.addWidget(self.photo_subject); opts.addWidget(QLabel("Language")); opts.addWidget(self.photo_language); opts.addWidget(solve); v.addLayout(opts)
        self.photo_status=QLabel("Supported formats: PNG, JPG, JPEG, WEBP. Maximum size: 12 MB."); self.photo_status.setObjectName("notice"); v.addWidget(self.photo_status)
        self.photo_result=QTextBrowser(); v.addWidget(self.photo_result,1)
        return w

    def choose_photo(self):
        p,_=QFileDialog.getOpenFileName(self,"Choose question photo","","Images (*.png *.jpg *.jpeg *.webp)")
        if p: self.photo_path.setText(p)

    def run_photo(self):
        p=self.photo_path.text().strip()
        if not p: QMessageBox.information(self,"Choose an image","Please choose a question photo first."); return
        if not is_configured(): QMessageBox.warning(self,"AI not configured","Add your OpenAI API key to .env and restart the app."); return
        self.photo_status.setText("Reading and solving the question...")
        self._start(solve_photo,p,self.photo_subject.currentText(),self.photo_language.currentText(),target="photo")

    def quiz_tab(self):
        w=QWidget(); v=QVBoxLayout(w)
        v.addWidget(QLabel("Generate original AI practice MCQs from a topic in your learning library. These are not historical board questions."))
        self.quiz_topic=QComboBox()
        self.quiz_topic.addItem("Select a topic",None)
        for t in db.get_topics(): self.quiz_topic.addItem(f"{t['subject']} • {t['title']}",t["id"])
        row=QHBoxLayout(); row.addWidget(QLabel("Topic")); row.addWidget(self.quiz_topic,3)
        self.quiz_count=QSpinBox(); self.quiz_count.setRange(3,15); self.quiz_count.setValue(5)
        self.quiz_lang=QComboBox(); self.quiz_lang.addItems(["English","Urdu","English + Urdu"])
        row.addWidget(QLabel("Questions")); row.addWidget(self.quiz_count); row.addWidget(self.quiz_lang); v.addLayout(row)
        b=QPushButton("Generate AI quiz"); b.setObjectName("primary"); b.clicked.connect(self.run_quiz); v.addWidget(b)
        self.quiz_status=QLabel("Generated questions are saved as AI-generated practice and can be used in Exam Preparation."); self.quiz_status.setObjectName("notice"); self.quiz_status.setWordWrap(True); v.addWidget(self.quiz_status)
        self.quiz_output=QTextBrowser(); v.addWidget(self.quiz_output,1)
        return w

    def run_quiz(self):
        tid=self.quiz_topic.currentData()
        if not tid: QMessageBox.information(self,"Select topic","Choose a topic first."); return
        if not is_configured(): QMessageBox.warning(self,"AI not configured","Add your OpenAI API key to .env and restart the app."); return
        topic=db.get_topic_context(tid)
        self.quiz_status.setText("Generating original questions...")
        self._start(generate_quiz,topic["topic_title"],topic["subject"],self.quiz_count.value(),self.quiz_lang.currentText(),target=("quiz",tid,topic["subject"]))

    def weakness_tab(self):
        w=QWidget(); v=QVBoxLayout(w)
        v.addWidget(QLabel("Topics are ranked using your saved answers to questions linked to a topic. A topic needs more practice data for a reliable picture."))
        b=QPushButton("Refresh my learning insights"); b.clicked.connect(self.refresh_weakness); v.addWidget(b)
        self.weak_table=QTableWidget(0,5); self.weak_table.setHorizontalHeaderLabels(["Subject","Topic","Attempts","Correct","Accuracy"]); self.weak_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); v.addWidget(self.weak_table,1)
        self.weak_note=QLabel("No performance data yet."); self.weak_note.setObjectName("notice"); v.addWidget(self.weak_note)
        self.refresh_weakness(); return w

    def refresh_weakness(self):
        rows=db.get_weak_topics(self.user["id"]); self.weak_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x["subject"],x["topic"],x["attempts"],x["correct"],f"{x['accuracy']}%"]
            for c,val in enumerate(vals): self.weak_table.setItem(r,c,QTableWidgetItem(str(val)))
        if rows:
            weakest=rows[0]
            self.weak_note.setText(f"Suggested priority: revise {weakest['topic']} ({weakest['accuracy']}% accuracy from {weakest['attempts']} recorded answers).")
        else:
            self.weak_note.setText("No topic-linked quiz attempts yet. Practise published questions that are connected to a topic to build your personal insights.")

    def flashcard_tab(self):
        w=QWidget(); v=QVBoxLayout(w)
        v.addWidget(QLabel("Create flashcards from a saved lesson, then review due cards. Scheduling is a simple spaced-repetition aid, not a medical or scientific guarantee."))
        self.flash_topic=QComboBox(); self.flash_topic.addItem("Select a topic",None)
        for t in db.get_topics(): self.flash_topic.addItem(f"{t['subject']} • {t['title']}",t["id"])
        row=QHBoxLayout(); row.addWidget(self.flash_topic,3)
        self.flash_count=QSpinBox(); self.flash_count.setRange(3,15); self.flash_count.setValue(8)
        row.addWidget(QLabel("Cards")); row.addWidget(self.flash_count)
        gen=QPushButton("Generate from lesson"); gen.setObjectName("primary"); gen.clicked.connect(self.run_flashcards); row.addWidget(gen); v.addLayout(row)
        self.flash_status=QLabel("Flashcards are private to your local account."); self.flash_status.setObjectName("notice"); v.addWidget(self.flash_status)
        self.card_front=QLabel("Choose a due card and press Show answer."); self.card_front.setWordWrap(True); self.card_front.setMinimumHeight(80); self.card_front.setAlignment(Qt.AlignCenter); self.card_front.setObjectName("hero_title"); v.addWidget(self.card_front)
        self.card_back=QTextBrowser(); self.card_back.setMaximumHeight(130); v.addWidget(self.card_back)
        controls=QHBoxLayout()
        self.show_answer=QPushButton("Show answer"); self.show_answer.clicked.connect(self.reveal_card)
        for label,quality in [("Again",0),("Hard",1),("Good",2),("Easy",3)]:
            btn=QPushButton(label); btn.clicked.connect(lambda _,q=quality:self.rate_card(q)); controls.addWidget(btn)
        controls.insertWidget(0,self.show_answer); v.addLayout(controls)
        self.flash_index=0; self.due_cards=[]; self.load_due_cards()
        return w

    def run_flashcards(self):
        tid=self.flash_topic.currentData()
        if not tid: QMessageBox.information(self,"Select topic","Choose a topic first."); return
        if not is_configured(): QMessageBox.warning(self,"AI not configured","Add your OpenAI API key to .env and restart the app."); return
        topic=db.get_topic_context(tid)
        if not topic or not topic["topic_title"]: return
        lesson=topic["beginner_explanation"] or ""
        lesson += "\n"+(topic["detailed_explanation"] or "")+"\n"+(topic["definitions"] or "")+"\n"+(topic["revision_notes"] or "")
        if len(lesson.strip())<40:
            QMessageBox.information(self,"Lesson needed","Add lesson content in Content Studio before generating flashcards."); return
        self.flash_status.setText("Creating flashcards from the saved lesson...")
        self._start(generate_flashcards,topic["topic_title"],topic["subject"],lesson,self.flash_count.value(),target=("flash",tid,topic["subject"]))

    def load_due_cards(self):
        self.due_cards=list(db.get_due_flashcards(self.user["id"])); self.flash_index=0
        self.show_current_card()
    def show_current_card(self):
        self.card_back.clear()
        if not self.due_cards:
            self.card_front.setText("No cards due today. Generate cards from a lesson or come back later.")
            self.show_answer.setEnabled(False); return
        self.show_answer.setEnabled(True)
        card=self.due_cards[self.flash_index % len(self.due_cards)]
        self.card_front.setText(card["front"])
    def reveal_card(self):
        if self.due_cards: self.card_back.setText(self.due_cards[self.flash_index % len(self.due_cards)]["back"])
    def rate_card(self,q):
        if not self.due_cards: return
        card=self.due_cards[self.flash_index % len(self.due_cards)]
        db.review_flashcard(card["id"],self.user["id"],q)
        self.load_due_cards()
        self.flash_status.setText("Review saved. The next due date has been scheduled.")

    def board_tab(self):
        w=QWidget(); v=QVBoxLayout(w)
        v.addWidget(QLabel("This report includes only questions explicitly marked as verified past-paper questions with a board, year and source reference. It is a record summary, not a prediction."))
        b=QPushButton("Refresh verified-paper summary"); b.clicked.connect(self.refresh_board); v.addWidget(b)
        self.board_table=QTableWidget(0,6); self.board_table.setHorizontalHeaderLabels(["Subject","Topic","Board","Year","Session","Recorded Qs"]); self.board_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); v.addWidget(self.board_table,1)
        self.board_note=QLabel("No verified, source-referenced past-paper questions are recorded yet."); self.board_note.setObjectName("notice"); v.addWidget(self.board_note)
        self.refresh_board(); return w

    def refresh_board(self):
        rows=db.get_board_intelligence(); self.board_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x["subject"],x["topic"],x["board"],x["exam_year"],x["session"],x["question_count"]]
            for c,val in enumerate(vals): self.board_table.setItem(r,c,QTableWidgetItem(str(val)))
        self.board_note.setText(f"{len(rows)} subject/topic/year records found. Frequency counts reflect only records entered and marked verified by your content team; incomplete archives can distort trends.")

    def _start(self,fn,*args,target):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self,"Please wait","Another AI task is already running."); return
        self._target=target; self.worker=WorkThread(fn,*args)
        self.worker.done.connect(self._finished); self.worker.failed.connect(self._failed); self.worker.start()

    def _finished(self,result):
        target=self._target
        if target=="photo":
            self.photo_result.setPlainText(result); self.photo_status.setText("Answer ready. Verify important facts against your textbook.")
        elif isinstance(target,tuple) and target[0]=="quiz":
            _,tid,subject=target; saved=0; lines=[]
            for i,q in enumerate(result,1):
                qid=db.add_exam_question(tid,q["question"],"MCQ",q["options"],q["answer"],q["explanation"],
                    "AI-generated practice",created_by=self.user["id"])
                saved+=1; lines.append(f"Q{i}. {q['question']}\n{q['options']}\nCorrect: {q['answer']}\nExplanation: {q['explanation']}")
            self.quiz_output.setPlainText("\n\n".join(lines))
            self.quiz_status.setText(f"Created and saved {saved} original AI practice questions. Open Exam Preparation to attempt them.")
        elif isinstance(target,tuple) and target[0]=="flash":
            _,tid,subject=target; db.add_flashcards(self.user["id"],tid,subject,result)
            self.flash_status.setText(f"Saved {len(result)} flashcards to your account.")
            self.load_due_cards()
        if self.parent_window and hasattr(self.parent_window,"load_quiz_history"):
            self.parent_window.load_quiz_history()

    def _failed(self,message):
        for label in ("photo_status","quiz_status","flash_status"):
            w=getattr(self,label,None)
            if w: w.setText("Task failed: "+message)
