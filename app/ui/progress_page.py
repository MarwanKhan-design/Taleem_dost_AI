"""Student Progress dashboard and printable progress summary."""
from html import escape

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QProgressBar,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout, QWidget,
)

from app.services.progress_analytics import load_progress, percent
from app.ui.page_components import CompletionRing, configure_tabs, page_layout, section_card


class ProgressDashboard(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user_id = user['id']
        self.student_name = user['full_name']
        layout = page_layout(self)
        title = QLabel('📊 My Progress')
        title.setObjectName('page_title')
        layout.addWidget(title)
        self.tabs = QTabWidget()
        configure_tabs(self.tabs)
        layout.addWidget(self.tabs)

        overview = self.add_section('Overview')
        summary_row = QHBoxLayout()
        self.completion_ring = CompletionRing()
        summary_row.addWidget(self.completion_ring)
        summary_column = QVBoxLayout()
        heading = self.add_label(summary_column, "Overall learning completion")
        heading.setObjectName("card_title")
        self.summary = self.add_label(summary_column)
        self.summary.setObjectName("muted")
        self.completion = QProgressBar()
        self.completion.setTextVisible(False)
        self.completion.setAccessibleName("Overall learning completion")
        summary_column.addWidget(self.completion)
        summary_row.addLayout(summary_column, 1)
        overview.addLayout(summary_row)
        self.subjects = self.add_table(
            overview, ['Subject', 'Completed', 'Learning', 'Needs revision', 'Not started', 'Completion']
        )

        syllabus = self.add_section('Syllabus')
        self.chapters = self.add_table(syllabus, ['Subject', 'Chapter', 'Completed', 'Total', 'Completion'])

        quiz = self.add_section('Quiz Performance')
        self.quiz_summary = self.add_label(quiz)
        self.quiz_history = self.add_table(quiz, ['Quiz', 'Subject', 'Type', 'Score', 'Full credit'])
        self.subject_accuracy = self.add_table(quiz, ['Subject', 'Full credit', 'Answered', 'Accuracy'])

        achievements = self.add_section('Achievements')
        self.level = self.add_label(achievements)
        self.badges = self.add_table(achievements, ['Achievement', 'Progress', 'Status', 'XP reward'])

        insights = self.add_section('Learning Insights')
        self.add_label(insights, 'Review topics marked for revision and topics with quiz accuracy below 60%.')
        self.revision = self.add_table(insights, ['Subject', 'Topic to revise', 'Quiz accuracy', 'Learn status'])
        self.next_topics = self.add_table(insights, ['Subject', 'Suggested next topic', 'Chapter'])

        reports = self.add_section('Reports')
        self.report = QTextBrowser()
        reports.addWidget(self.report)
        download = QPushButton('Export Progress Report as PDF')
        download.setObjectName('primary')
        download.clicked.connect(self.export_report)
        reports.addWidget(download)
        self.refresh()

    def add_section(self, title):
        page = QWidget()
        self.tabs.addTab(page, title)
        outer = QVBoxLayout(page)
        card, body = section_card()
        outer.addWidget(card)
        return body

    @staticmethod
    def add_label(layout, text=''):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        layout.addWidget(label)
        return label

    @staticmethod
    def add_table(layout, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)
        return table

    @staticmethod
    def fill(table, rows):
        table.setRowCount(0)
        for index, row in enumerate(rows):
            table.insertRow(index)
            for column, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                table.setItem(index, column, item)

    def refresh(self):
        data = load_progress(self.user_id)
        completed, total = data['completed'], data['total']
        completion = percent(completed, total)
        chapters_complete = sum(done == count for _, _, done, count in data['chapters'])
        self.summary.setText(
            f'{completed} of {total} topics complete • {chapters_complete} of {len(data["chapters"])} chapters complete'
            f' • {data["courses"]} of {len(data["subjects"])} subjects complete'
        )
        self.completion_ring.set_value(completion)
        self.completion.setValue(round(completion))
        self.completion.setFormat(f'{completion:g}% complete')
        self.fill(self.subjects, (
            (subject, *counts.values(), f'{percent(counts["Completed"], sum(counts.values())):g}%')
            for subject, counts in data['subjects'].items()
        ))
        self.fill(self.chapters, (
            (subject, chapter, done, count, f'{percent(done, count):g}%')
            for subject, chapter, done, count in data['chapters']
        ))

        quizzes = data['quizzes']
        scores = [q['score_percent'] for q in quizzes]
        if quizzes:
            summary = f'{len(quizzes)} graded quizzes • Average {data["average"]:g}% • Best {max(scores):g}%'
            if data['change'] is not None:
                summary += f' • Latest {data["sample"]} vs previous {data["sample"]}: {data["change"]:+g} percentage points'
            self.quiz_summary.setText(summary)
        else:
            self.quiz_summary.setText('Complete a graded quiz to see your results here.')
        self.fill(self.quiz_history, (
            (number, q['subject'], q['quiz_type'], f'{q["score_percent"]:g}%',
             f'{q["correct_answers"]}/{q["total_questions"]}')
            for number, q in reversed(list(enumerate(quizzes, 1)))
        ))
        self.fill(self.subject_accuracy, (
            (subject, correct, answered, f'{score:g}%')
            for subject, correct, answered, score in data['accuracy']
        ))

        xp, level, remaining, badges = data['achievements']
        self.level.setText(f'Level {level} • {xp} XP • {remaining} XP to next level')
        self.fill(self.badges, (
            (name, f'{min(value, target):g}/{target}', 'Unlocked' if value >= target else 'Locked', reward)
            for name, value, target, reward in badges
        ))
        self.fill(self.revision, (
            (topic['subject'], topic['title'], '—' if score is None else f'{score:g}%', topic['status'])
            for topic, score in data['revision']
        ))
        self.fill(self.next_topics, (
            (topic['subject'], topic['title'], topic['chapter']) for topic in data['next_topics']
        ))
        self.report.setHtml(self.report_html())

    def report_html(self):
        rows = ''.join(
            '<tr>' + ''.join(f'<td>{escape(self.subjects.item(row, col).text())}</td>'
                             for col in (0, 1, 3, 5)) + '</tr>'
            for row in range(self.subjects.rowCount())
        )
        return (
            f'<h1>Learning Progress Report</h1><p>{escape(self.student_name)}</p>'
            f'<p>{escape(self.summary.text())}</p><p>{escape(self.quiz_summary.text())}</p>'
            f'<p>{escape(self.level.text())}</p>'
            '<h2>Subject progress</h2><table border="1" cellspacing="0" cellpadding="6">'
            '<thead><tr><th>Subject</th><th>Completed</th><th>Needs revision</th><th>Completion</th></tr></thead>'
            f'{rows}</table>'
        )

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save Progress Report', 'progress-report.pdf', 'PDF (*.pdf)')
        if not path:
            return
        if not path.lower().endswith('.pdf'):
            path += '.pdf'
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        document = QTextDocument()
        document.setHtml(self.report_html())
        document.print_(printer)
        if printer.printerState() in (QPrinter.Error, QPrinter.Aborted):
            QMessageBox.warning(self, 'Export failed', 'The report could not be written to that file.')
