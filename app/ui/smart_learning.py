from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from app.database import db


class SmartLearningPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        root = QVBoxLayout(self)
        title = QLabel("Study Insights")
        title.setObjectName("page_title")
        root.addWidget(title)
        tabs = QTabWidget()
        root.addWidget(tabs, 1)
        tabs.addTab(self.weakness_tab(), "My Weak Topics")
        tabs.addTab(self.flashcard_tab(), "Flashcards")
        tabs.addTab(self.board_tab(), "Board Trends")

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
        self.flash_status=QLabel("Flashcards are private to your local account."); self.flash_status.setObjectName("notice"); v.addWidget(self.flash_status)
        self.card_front=QLabel("Press Show answer to review the current card."); self.card_front.setWordWrap(True); self.card_front.setMinimumHeight(80); self.card_front.setAlignment(Qt.AlignCenter); self.card_front.setObjectName("hero_title"); v.addWidget(self.card_front)
        self.card_back=QTextBrowser(); self.card_back.setMaximumHeight(130); v.addWidget(self.card_back)
        controls=QHBoxLayout()
        self.show_answer=QPushButton("Show answer"); self.show_answer.clicked.connect(self.reveal_card)
        for label,quality in [("Again",0),("Hard",1),("Good",2),("Easy",3)]:
            btn=QPushButton(label); btn.clicked.connect(lambda _,q=quality:self.rate_card(q)); controls.addWidget(btn)
        controls.insertWidget(0,self.show_answer); v.addLayout(controls)
        self.flash_index=0; self.due_cards=[]; self.load_due_cards()
        return w

    def load_due_cards(self):
        self.due_cards=list(db.get_due_flashcards(self.user["id"])); self.flash_index=0
        self.show_current_card()
    def show_current_card(self):
        self.card_back.clear()
        if not self.due_cards:
            self.card_front.setText("No flashcards are due today.")
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
