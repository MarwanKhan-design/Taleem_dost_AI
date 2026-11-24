"""Expanded Study Planner for Taleem Dost AI (PyQt5 + SQLite).
All records are scoped to the signed-in user. Existing project tables are preserved.
"""
from datetime import date
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDoubleSpinBox,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from app.database import db
from app.ui.page_components import configure_tabs, page_layout, section_card
from app.database.curriculum import SUBJECTS


def ensure_planner_schema():
    """Upgrade the planner schema in one transaction."""
    with db.get_connection() as c:
        c.executescript("""
        BEGIN IMMEDIATE;
        CREATE TABLE IF NOT EXISTS planner_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, chapter TEXT DEFAULT '', test_date TEXT NOT NULL,
            duration_minutes INTEGER DEFAULT 0, total_marks REAL NOT NULL,
            obtained_marks REAL NOT NULL, notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS planner_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, target_percent REAL NOT NULL,
            UNIQUE(user_id,subject), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS planner_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            subject TEXT NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '',
            due_date TEXT NOT NULL, priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending', notes TEXT DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_planner_tests_user_date ON planner_tests(user_id,test_date);
        CREATE INDEX IF NOT EXISTS idx_planner_assign_user_due ON planner_assignments(user_id,due_date);
        """)
        cols = {r['name'] for r in c.execute('PRAGMA table_info(study_tasks)')}
        for name, definition in [
            ('priority', "TEXT NOT NULL DEFAULT 'Medium'"),
            ('status', "TEXT NOT NULL DEFAULT 'Pending'"),
            ('notes', "TEXT DEFAULT ''"),
        ]:
            if name not in cols:
                c.execute(f'ALTER TABLE study_tasks ADD COLUMN {name} {definition}')
        if 'status' not in cols:
            c.execute("UPDATE study_tasks SET status='Completed' WHERE completed=1")
        if 'updated_at' not in cols:
            # SQLite requires a constant default when adding a column to a populated table.
            c.execute('ALTER TABLE study_tasks ADD COLUMN updated_at TEXT')
            c.execute('UPDATE study_tasks SET updated_at = created_at')


class StudyPlannerWidget(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.uid = user['id']
        ensure_planner_schema()
        root = page_layout(self)
        title = QLabel('📅 Study Planner')
        title.setObjectName('page_title')
        root.addWidget(title)
        sub = QLabel('Plan tasks, measure performance, and track syllabus progress.')
        sub.setObjectName('muted')
        root.addWidget(sub)
        self.tabs = QTabWidget()
        configure_tabs(self.tabs)
        root.addWidget(self.tabs)
        self.tabs.addTab(self.overview_tab(), 'Overview')
        self.tabs.addTab(self.tasks_tab(), 'Task Management')
        self.tabs.addTab(self.tests_tab(), 'Tests && Targets')
        self.tabs.addTab(self.syllabus_tab(), 'Syllabus')
        self.tabs.addTab(self.assignments_tab(), 'Assignments')
        self.tabs.addTab(self.analytics_tab(), 'Analytics')
        self.tabs.currentChanged.connect(self.refresh_all)
        self.refresh_all()

    def make_table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        return t

    def overview_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        self.overview_text=QLabel()
        self.overview_text.setWordWrap(True)
        self.overview_text.setObjectName('notice')
        v.addWidget(self.overview_text)
        v.addWidget(QLabel('Study tasks'))
        self.overview_tasks_table=self.make_table(['Due date','Subject','Task','Priority','Status'])
        v.addWidget(self.overview_tasks_table)
        v.addWidget(QLabel('Today\'s productivity score'))
        self.score_label=QLabel()
        self.score_label.setWordWrap(True)
        v.addWidget(self.score_label)
        return w

    def tasks_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        form=QGridLayout()
        self.task_subject=QComboBox()
        self.task_subject.addItems(SUBJECTS)
        self.task_text=QLineEdit()
        self.task_text.setPlaceholderText('Task title / study activity')
        self.task_date=QDateEdit()
        self.task_date.setCalendarPopup(True)
        self.task_date.setDate(date.today())
        self.task_minutes=QSpinBox()
        self.task_minutes.setRange(5,600)
        self.task_minutes.setValue(40)
        self.task_priority=QComboBox()
        self.task_priority.addItems(['Medium','High','Low'])
        self.task_status=QComboBox()
        self.task_status.addItems(['Pending','In Progress','Completed'])
        self.task_notes=QLineEdit()
        self.task_notes.setPlaceholderText('Optional notes')
        fields=[('Subject',self.task_subject),('Task',self.task_text),('Due date',self.task_date),('Duration (min)',self.task_minutes),('Priority',self.task_priority),('Status',self.task_status),('Notes',self.task_notes)]
        for i,(label,widget) in enumerate(fields):
            form.addWidget(QLabel(label),i//2,(i%2)*2)
            form.addWidget(widget,i//2,(i%2)*2+1)
        v.addLayout(form)
        row=QHBoxLayout()
        add=QPushButton('Add Task')
        add.setObjectName('primary')
        add.clicked.connect(self.add_task)
        edit=QPushButton('Update Selected')
        edit.clicked.connect(self.update_task)
        delete=QPushButton('Delete Selected')
        delete.clicked.connect(self.delete_task)
        row.addWidget(add)
        row.addWidget(edit)
        row.addWidget(delete)
        v.addLayout(row)
        self.tasks_table=self.make_table(['ID','Due date','Subject','Task','Minutes','Priority','Status','Notes'])
        v.addWidget(self.tasks_table)
        self.tasks_table.itemSelectionChanged.connect(self.select_task)
        return w

    def tests_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        form=QGridLayout()
        self.test_subject=QComboBox()
        self.test_subject.addItems(SUBJECTS)
        self.test_chapter=QComboBox()
        self.chapters = db.get_chapters()
        self.test_subject.currentTextChanged.connect(self.load_test_chapters)
        self.load_test_chapters()
        self.test_date=QDateEdit()
        self.test_date.setCalendarPopup(True)
        self.test_date.setDate(date.today())
        self.test_duration=QSpinBox()
        self.test_duration.setRange(0,600)
        self.test_duration.setValue(30)
        self.total_marks=QDoubleSpinBox()
        self.total_marks.setRange(1,10000)
        self.total_marks.setValue(100)
        self.obtained_marks=QDoubleSpinBox()
        self.obtained_marks.setRange(0,10000)
        self.obtained_marks.setValue(0)
        self.test_notes=QLineEdit()
        self.test_notes.setPlaceholderText('Mistakes / topics to revise')
        for i,(lab,ctrl) in enumerate([('Subject',self.test_subject),('Chapter / topic',self.test_chapter),('Test date',self.test_date),('Duration (min)',self.test_duration),('Total marks',self.total_marks),('Obtained marks',self.obtained_marks),('Notes',self.test_notes)]):
            form.addWidget(QLabel(lab),i//2,(i%2)*2)
            form.addWidget(ctrl,i//2,(i%2)*2+1)
        v.addLayout(form)
        b=QPushButton('Save Test Result')
        b.setObjectName('primary')
        b.clicked.connect(self.save_test)
        v.addWidget(b)
        self.test_table=self.make_table(['Date','Subject','Chapter','Marks','Percentage','Duration','Notes'])
        v.addWidget(self.test_table)
        v.addWidget(QLabel('Target marks planner — set the target percentage for each subject.'))
        targetrow=QHBoxLayout()
        self.target_subject=QComboBox()
        self.target_subject.addItems(SUBJECTS)
        self.target_value=QDoubleSpinBox()
        self.target_value.setRange(1,100)
        self.target_value.setValue(85)
        tb=QPushButton('Save Target')
        tb.clicked.connect(self.save_target)
        targetrow.addWidget(self.target_subject)
        targetrow.addWidget(self.target_value)
        targetrow.addWidget(tb)
        v.addLayout(targetrow)
        self.target_table=self.make_table(['Subject','Target %','Current average %','Gap to target'])
        v.addWidget(self.target_table)
        return w

    def load_test_chapters(self):
        self.test_chapter.clear()
        self.test_chapter.addItem('General / not specified', '')
        for chapter in self.chapters:
            if chapter['subject'] == self.test_subject.currentText():
                self.test_chapter.addItem(chapter['title'], chapter['title'])

    def syllabus_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        v.addWidget(QLabel('Syllabus completion uses the existing Learn library and topic progress records.'))
        self.syllabus_table=self.make_table(['Subject','Chapter','Topic','Status'])
        v.addWidget(self.syllabus_table)
        info=QLabel('To update a topic, open the Learn section, select the topic, and save its learning status.')
        info.setWordWrap(True)
        v.addWidget(info)
        return w

    def assignments_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        form=QGridLayout()
        self.as_subject=QComboBox()
        self.as_subject.addItems(SUBJECTS)
        self.as_title=QLineEdit()
        self.as_title.setPlaceholderText('Homework / assignment title')
        self.as_desc=QLineEdit()
        self.as_desc.setPlaceholderText('Description')
        self.as_due=QDateEdit()
        self.as_due.setCalendarPopup(True)
        self.as_due.setDate(date.today())
        self.as_priority=QComboBox()
        self.as_priority.addItems(['Medium','High','Low'])
        self.as_status=QComboBox()
        self.as_status.addItems(['Pending','In Progress','Submitted','Completed'])
        self.as_notes=QLineEdit()
        self.as_notes.setPlaceholderText('Notes')
        for i,(lab,ctrl) in enumerate([('Subject',self.as_subject),('Title',self.as_title),('Description',self.as_desc),('Due date',self.as_due),('Priority',self.as_priority),('Status',self.as_status),('Notes',self.as_notes)]):
            form.addWidget(QLabel(lab),i//2,(i%2)*2)
            form.addWidget(ctrl,i//2,(i%2)*2+1)
        v.addLayout(form)
        b=QPushButton('Add Assignment')
        b.setObjectName('primary')
        b.clicked.connect(self.add_assignment)
        v.addWidget(b)
        self.assignment_table=self.make_table(['ID','Due date','Subject','Title','Priority','Status','Description','Notes'])
        v.addWidget(self.assignment_table)
        row=QHBoxLayout()
        done=QPushButton('Mark Selected Submitted')
        done.clicked.connect(self.complete_assignment)
        delete=QPushButton('Delete Selected')
        delete.clicked.connect(self.delete_assignment)
        row.addWidget(done)
        row.addWidget(delete)
        v.addLayout(row)
        return w

    def analytics_tab(self):
        w=QWidget()
        outer = QVBoxLayout(w)
        surface, v = section_card()
        outer.addWidget(surface)
        self.analytics_text=QLabel()
        self.analytics_text.setWordWrap(True)
        self.analytics_text.setObjectName('notice')
        v.addWidget(self.analytics_text)
        self.weak_table=self.make_table(['Subject','Test average %','Suggested action'])
        v.addWidget(self.weak_table)
        self.refresh_btn=QPushButton('Refresh Analytics')
        self.refresh_btn.clicked.connect(self.refresh_all)
        v.addWidget(self.refresh_btn)
        return w

    def add_task(self):
        title=self.task_text.text().strip()
        if not title:
            QMessageBox.warning(self,'Missing task','Please enter a task title.')
            return
        with db.get_connection() as c:
            c.execute('INSERT INTO study_tasks(user_id,subject,task,study_date,duration_minutes,priority,status,notes,completed,updated_at) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)',
                (self.uid,self.task_subject.currentText(),title,self.task_date.date().toString('yyyy-MM-dd'),self.task_minutes.value(),self.task_priority.currentText(),self.task_status.currentText(),self.task_notes.text().strip(), int(self.task_status.currentText() == 'Completed')))
        self.task_text.clear()
        self.task_notes.clear()
        self.refresh_all()

    def selected_id(self, table):
        rows=table.selectionModel().selectedRows()
        return int(table.item(rows[0].row(),0).text()) if rows else None

    def select_task(self):
        tid=self.selected_id(self.tasks_table)
        if not tid: return
        with db.get_connection() as c: r=c.execute('SELECT * FROM study_tasks WHERE id=? AND user_id=?',(tid,self.uid)).fetchone()
        if not r: return
        self.task_subject.setCurrentText(r['subject'])
        self.task_text.setText(r['task'])
        self.task_date.setDate(QDate.fromString(r['study_date'],'yyyy-MM-dd'))
        self.task_minutes.setValue(r['duration_minutes'])
        self.task_priority.setCurrentText(r['priority'])
        self.task_status.setCurrentText(r['status'])
        self.task_notes.setText(r['notes'] or '')

    def update_task(self):
        tid=self.selected_id(self.tasks_table)
        if not tid:
            QMessageBox.information(self,'Select task','Select a task first.')
            return
        title = self.task_text.text().strip()
        if not title:
            QMessageBox.warning(self, 'Missing task', 'Please enter a task title.')
            return
        with db.get_connection() as c: c.execute('UPDATE study_tasks SET subject=?,task=?,study_date=?,duration_minutes=?,priority=?,status=?,notes=?,completed=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?',
            (self.task_subject.currentText(),title,self.task_date.date().toString('yyyy-MM-dd'),self.task_minutes.value(),self.task_priority.currentText(),self.task_status.currentText(),self.task_notes.text().strip(),int(self.task_status.currentText() == 'Completed'),tid,self.uid))
        self.refresh_all()

    def delete_task(self):
        tid=self.selected_id(self.tasks_table)
        if tid and QMessageBox.question(self,'Delete task','Delete the selected task?')==QMessageBox.Yes:
            with db.get_connection() as c: c.execute('DELETE FROM study_tasks WHERE id=? AND user_id=?',(tid,self.uid))
            self.refresh_all()

    def save_test(self):
        total=self.total_marks.value()
        got=self.obtained_marks.value()
        if got>total:
            QMessageBox.warning(self,'Invalid marks','Obtained marks cannot exceed total marks.')
            return
        with db.get_connection() as c: c.execute('INSERT INTO planner_tests(user_id,subject,chapter,test_date,duration_minutes,total_marks,obtained_marks,notes) VALUES(?,?,?,?,?,?,?,?)',
            (self.uid,self.test_subject.currentText(),self.test_chapter.currentData() or '',self.test_date.date().toString('yyyy-MM-dd'),self.test_duration.value(),total,got,self.test_notes.text().strip()))
        self.refresh_all()

    def save_target(self):
        with db.get_connection() as c: c.execute('INSERT INTO planner_targets(user_id,subject,target_percent) VALUES(?,?,?) ON CONFLICT(user_id,subject) DO UPDATE SET target_percent=excluded.target_percent',(self.uid,self.target_subject.currentText(),self.target_value.value()))
        self.refresh_all()

    def add_assignment(self):
        title=self.as_title.text().strip()
        if not title:
            QMessageBox.warning(self,'Missing title','Enter an assignment title.')
            return
        with db.get_connection() as c: c.execute('INSERT INTO planner_assignments(user_id,subject,title,description,due_date,priority,status,notes) VALUES(?,?,?,?,?,?,?,?)',
            (self.uid,self.as_subject.currentText(),title,self.as_desc.text().strip(),self.as_due.date().toString('yyyy-MM-dd'),self.as_priority.currentText(),self.as_status.currentText(),self.as_notes.text().strip()))
        self.as_title.clear()
        self.as_desc.clear()
        self.refresh_all()

    def complete_assignment(self):
        aid=self.selected_id(self.assignment_table)
        if aid:
            with db.get_connection() as c: c.execute("UPDATE planner_assignments SET status='Submitted' WHERE id=? AND user_id=?",(aid,self.uid))
            self.refresh_all()

    def delete_assignment(self):
        aid=self.selected_id(self.assignment_table)
        if aid and QMessageBox.question(self,'Delete assignment','Delete selected assignment?')==QMessageBox.Yes:
            with db.get_connection() as c: c.execute('DELETE FROM planner_assignments WHERE id=? AND user_id=?',(aid,self.uid))
            self.refresh_all()

    def fill(self, table, rows, fields):
        table.clearSelection()
        table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,key in enumerate(fields): table.setItem(i,j,QTableWidgetItem(str(r[key] if r[key] is not None else '')))

    def refresh_all(self):
        with db.get_connection() as c:
            tasks=c.execute('SELECT id,study_date,subject,task,duration_minutes,priority,status,notes FROM study_tasks WHERE user_id=? ORDER BY study_date,id',(self.uid,)).fetchall()
            tests=c.execute("SELECT *,printf('%g / %g',obtained_marks,total_marks) marks,ROUND(obtained_marks*100.0/total_marks,1) pct FROM planner_tests WHERE user_id=? ORDER BY test_date DESC,id DESC",(self.uid,)).fetchall()
            targets=c.execute('SELECT * FROM planner_targets WHERE user_id=? ORDER BY subject',(self.uid,)).fetchall()
            assignments=c.execute('SELECT id,due_date,subject,title,priority,status,description,notes FROM planner_assignments WHERE user_id=? ORDER BY due_date',(self.uid,)).fetchall()
            averages=c.execute('SELECT subject,ROUND(AVG(obtained_marks*100.0/total_marks),1) avg FROM planner_tests WHERE user_id=? GROUP BY subject',(self.uid,)).fetchall()
        self.fill(self.tasks_table,tasks,['id','study_date','subject','task','duration_minutes','priority','status','notes'])
        self.fill(self.test_table,tests,['test_date','subject','chapter','marks','pct','duration_minutes','notes'])
        self.fill(self.assignment_table,assignments,['id','due_date','subject','title','priority','status','description','notes'])
        avgmap={r['subject']:float(r['avg'] or 0) for r in averages}
        target_rows=[]
        for t in targets:
            av=avgmap.get(t['subject'])
            target_rows.append({'subject':t['subject'],'target':t['target_percent'],'avg':f'{av:.1f}' if av is not None else 'No tests','gap':f'{max(0,t["target_percent"]-av):.1f}' if av is not None else '—'})
        self.fill(self.target_table,target_rows,['subject','target','avg','gap'])
        self.refresh_syllabus()
        today=date.today().isoformat()
        self.fill(self.overview_tasks_table,tasks,['study_date','subject','task','priority','status'])
        done=sum(1 for r in tasks if r['study_date']==today and r['status']=='Completed')
        planned=sum(1 for r in tasks if r['study_date']==today)
        with db.get_connection() as c:
            completed_topics=c.execute("SELECT COUNT(*) n FROM student_topic_progress WHERE user_id=? AND completed=1",(self.uid,)).fetchone()['n']
            total_topics=c.execute('SELECT COUNT(*) n FROM topics').fetchone()['n']
            due=c.execute("SELECT COUNT(*) n FROM planner_assignments WHERE user_id=? AND due_date<? AND status NOT IN ('Submitted','Completed')",(self.uid,today)).fetchone()['n']
        task_pts=30*done/planned if planned else 0
        syllabus_pts=20*(completed_topics/total_topics) if total_topics else 0
        with db.get_connection() as c:
            today_tests=c.execute('SELECT COUNT(*) n FROM planner_tests WHERE user_id=? AND test_date=?',(self.uid,today)).fetchone()['n']
            today_assign=c.execute("SELECT COUNT(*) n FROM planner_assignments WHERE user_id=? AND due_date=? AND status IN ('Submitted','Completed')",(self.uid,today)).fetchone()['n']
        practice_pts=15 if today_tests or today_assign else 0
        plan_pts=10 if planned else 0
        score=round(task_pts+syllabus_pts+practice_pts+plan_pts)
        self.score_label.setText(f'{score}/75  |  Tasks {task_pts:.0f}/30 • Syllabus {syllabus_pts:.0f}/20 • Tests/assignments {practice_pts}/15 • Daily plan {plan_pts}/10')
        self.overview_text.setText(f"Tasks: {len(tasks)} total • {sum(1 for r in tasks if r['status']=='Completed')} completed\nTests recorded: {len(tests)}\nSyllabus: {completed_topics}/{total_topics} topics complete • Overdue assignments: {due}")
        self.analytics_text.setText('Weak-subject indicator is based on recorded test averages. Subjects with an average below 60% are flagged for extra practice. Add more tests for a more reliable trend.')
        self.weak_table.setRowCount(0)
        for r in averages:
            row=self.weak_table.rowCount()
            self.weak_table.insertRow(row)
            avg=float(r['avg'] or 0)
            vals=[r['subject'],f'{avg:.1f}%', 'Prioritise revision + another practice test' if avg<60 else 'Maintain practice and review mistakes']
            for j,val in enumerate(vals): self.weak_table.setItem(row,j,QTableWidgetItem(val))

    def refresh_syllabus(self):
        with db.get_connection() as c:
            rows=c.execute('SELECT c.subject,c.title chapter,t.title topic,COALESCE(p.status,"Not started") status FROM topics t JOIN chapters c ON c.id=t.chapter_id LEFT JOIN student_topic_progress p ON p.topic_id=t.id AND p.user_id=? ORDER BY c.subject,c.sort_order,t.sort_order',(self.uid,)).fetchall()
        self.fill(self.syllabus_table,rows,['subject','chapter','topic','status'])
