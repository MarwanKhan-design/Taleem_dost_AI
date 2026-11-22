import json
from html import escape

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from app.database import db
from app.ui.page_components import configure_tabs, page_layout, section_card
from app.services.rubric import RUBRIC_PROMPTS, RUBRIC_SAMPLES, grade_answer


class SmartLearningPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        root = page_layout(self)
        title = QLabel("Study Insights")
        title.setObjectName("page_title")
        root.addWidget(title)
        tabs = QTabWidget()
        configure_tabs(tabs)
        root.addWidget(tabs, 1)
        tabs.addTab(self.weakness_tab(), "My Weak Topics")
        tabs.addTab(self.flashcard_tab(), "Flashcards")
        tabs.addTab(self.board_tab(), "Board Trends")
        tabs.currentChanged.connect(self.refresh_flashcards)

    def weakness_tab(self):
        w=QWidget(); outer=QVBoxLayout(w); surface,v=section_card(); outer.addWidget(surface)
        description = QLabel("Topics are ranked by your saved answers. Practise more questions to get a clearer picture.")
        description.setWordWrap(True)
        description.setObjectName("muted")
        v.addWidget(description)
        b=QPushButton("Refresh my learning insights"); b.clicked.connect(self.refresh_weakness); v.addWidget(b)
        self.weak_table=QTableWidget(0,5); self.weak_table.setHorizontalHeaderLabels(["Subject","Topic","Attempts","Correct","Accuracy"]); self.weak_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); v.addWidget(self.weak_table,1)
        self.weak_note=QLabel("No performance data yet."); self.weak_note.setObjectName("notice"); self.weak_note.setWordWrap(True); v.addWidget(self.weak_note)
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
        w=QWidget(); outer=QVBoxLayout(w); surface,v=section_card(); outer.addWidget(surface)
        self.flash_status=QLabel(); self.flash_status.setObjectName("muted"); v.addWidget(self.flash_status)
        self.card_front=QLabel(); self.card_front.setWordWrap(True); self.card_front.setMinimumHeight(110); self.card_front.setAlignment(Qt.AlignCenter); self.card_front.setTextFormat(Qt.PlainText); self.card_front.setObjectName("flashcard_prompt"); v.addWidget(self.card_front)
        self.card_response = QPlainTextEdit()
        self.card_response.setPlaceholderText("Type your answer, then select Show answer for feedback.")
        self.card_response.setMaximumHeight(110)
        v.addWidget(self.card_response)
        self.card_back=QTextBrowser(); v.addWidget(self.card_back, 1)
        controls=QHBoxLayout()
        self.show_answer=QPushButton("Show answer"); self.show_answer.setObjectName("primary"); self.show_answer.clicked.connect(self.reveal_card)
        self.ratings = []
        for label,quality in [("Again",0),("Hard",1),("Good",2),("Easy",3)]:
            btn=QPushButton(label); btn.clicked.connect(lambda _,q=quality:self.rate_card(q)); controls.addWidget(btn)
            self.ratings.append(btn)
        controls.insertWidget(0,self.show_answer); v.addLayout(controls)
        self.due_cards=[]; self.load_due_cards()
        return w

    def refresh_flashcards(self, index):
        if index == 1:
            db.sync_flashcards(self.user["id"])
            self.load_due_cards()

    def load_due_cards(self):
        self.due_cards=list(db.get_due_flashcards(self.user["id"]))
        self.flash_status.setText(f"{len(self.due_cards)} cards due today.")
        self.show_current_card()
    def show_current_card(self):
        self.card_back.clear()
        self.card_response.clear()
        self.card_response.setEnabled(bool(self.due_cards))
        self.card_response.setReadOnly(False)
        for button in self.ratings:
            button.setEnabled(False)
        if not self.due_cards:
            self.card_front.setText("No cards are due today.")
            self.show_answer.setEnabled(False); return
        self.show_answer.setEnabled(True)
        card=self.due_cards[0]
        prompt = RUBRIC_PROMPTS.get(card["front"], card["front"])
        if card["question_type"] == "MCQ" and card["options"]:
            prompt += "\n" + "  ·  ".join(card["options"].splitlines())
        self.card_front.setText(prompt)

    def reveal_card(self):
        if self.due_cards:
            self.card_response.setReadOnly(True)
            card = self.due_cards[0]
            question = {
                "question": card["front"],
                "question_type": card["question_type"],
                "answer": card["back"],
            }
            response = self.card_response.toPlainText()
            sample = RUBRIC_SAMPLES.get(card["front"], card["back"])
            feedback = ["Sample answer", sample]
            if card["question_type"] and response.strip():
                grade = grade_answer(question, response)
                if grade["possible"]:
                    feedback.extend(("", f"{grade['earned']} / {grade['possible']} marks"))
                for point, earned in grade["points"]:
                    status = "Earned (+1)" if earned else "Needs review (+0)"
                    feedback.append(f"{status} · {point}")
            self.card_back.setPlainText("\n".join(feedback))
            for button in self.ratings:
                button.setEnabled(True)
    def rate_card(self,q):
        if not self.due_cards: return
        card=self.due_cards[0]
        db.review_flashcard(card["id"],self.user["id"],q)
        self.load_due_cards()
        self.flash_status.setText("Review saved. The next due date has been scheduled.")

    def board_tab(self):
        tabs = QTabWidget()
        configure_tabs(tabs)
        tabs.addTab(self.grade_xii_tab(), "Grade XII past papers")
        tabs.addTab(self.local_board_tab(), "Local verified records")
        return tabs

    def grade_xii_tab(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        surface, layout = section_card()
        outer.addWidget(surface)
        description = QLabel("Selected Grade XII past-paper questions, paraphrased for practice. Counts apply to this collection.")
        description.setWordWrap(True)
        layout.addWidget(description)
        path = db.DATA_DIR / "kpk_grade_xii_past_papers.json"
        self.past_papers = json.loads(path.read_text(encoding="utf-8"))
        self.paper_picker = QComboBox()
        for paper in self.past_papers:
            self.paper_picker.addItem(f"{paper['subject']} · {paper['board']} · {paper['year']} · {paper['session']}")
        layout.addWidget(self.paper_picker)
        self.paper_topics = QLabel()
        self.paper_topics.setWordWrap(True)
        layout.addWidget(self.paper_topics)
        self.paper_questions = QTextBrowser()
        layout.addWidget(self.paper_questions, 1)
        self.paper_source = QLabel()
        self.paper_source.setOpenExternalLinks(True)
        layout.addWidget(self.paper_source)
        self.paper_picker.currentIndexChanged.connect(self.show_past_paper)
        self.show_past_paper(0)
        return page

    def show_past_paper(self, index):
        paper = self.past_papers[index]
        questions = paper["questions"]
        counts = {}
        rows = []
        for reference, topic, question in questions:
            counts[topic] = counts.get(topic, 0) + 1
            rows.append(f"<p><b>{escape(reference)} · {escape(topic)}</b><br>{escape(question)}</p>")
        details = " · ".join(f"{topic} ({count})" for topic, count in counts.items())
        self.paper_topics.setText(f"{len(questions)} questions · {details}")
        self.paper_questions.setHtml("".join(rows))
        self.paper_source.setText(f'<a href="{escape(paper["source"])}">Open source paper transcription</a>')

    def local_board_tab(self):
        w=QWidget(); outer=QVBoxLayout(w); surface,v=section_card(); outer.addWidget(surface)
        description = QLabel("Verified past-paper questions with a board, year, and source reference.")
        description.setObjectName("muted")
        description.setWordWrap(True)
        v.addWidget(description)
        b=QPushButton("Refresh verified-paper summary"); b.clicked.connect(self.refresh_board); v.addWidget(b)
        self.board_table=QTableWidget(0,6); self.board_table.setHorizontalHeaderLabels(["Subject","Topic","Board","Year","Session","Recorded Qs"]); self.board_table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch); v.addWidget(self.board_table,1)
        self.board_note=QLabel("No verified, source-referenced past-paper questions are recorded yet."); self.board_note.setObjectName("notice"); self.board_note.setWordWrap(True); v.addWidget(self.board_note)
        self.refresh_board(); return w

    def refresh_board(self):
        rows=db.get_board_intelligence(); self.board_table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x["subject"],x["topic"],x["board"],x["exam_year"],x["session"],x["question_count"]]
            for c,val in enumerate(vals): self.board_table.setItem(r,c,QTableWidgetItem(str(val)))
        self.board_note.setText(f"{len(rows)} subject/topic/year records found. Frequency counts reflect only records entered and marked verified by your content team; incomplete archives can distort trends.")
