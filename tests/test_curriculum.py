import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from app.database import db
from app.database.curriculum import PACK, SUBJECTS


class CurriculumTest(unittest.TestCase):
    def test_install_is_additive_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(db, "DB_PATH", Path(directory) / "test.db"):
                db.initialize_database()
                pack = json.loads(PACK.read_text(encoding="utf-8"))
                with db.get_connection() as conn:
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0], len(pack["topics"]))
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM practice_questions").fetchone()[0], 195)
                    self.assertEqual(conn.execute("SELECT COUNT(DISTINCT subject) FROM chapters").fetchone()[0], len(SUBJECTS))
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM practice_questions WHERE verified=1").fetchone()[0], 0)
                    self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
                    conn.execute("UPDATE lessons SET introduction='Teacher edited' WHERE topic_id=1")
                db.initialize_database()
                with db.get_connection() as conn:
                    self.assertEqual(conn.execute("SELECT introduction FROM lessons WHERE topic_id=1").fetchone()[0], "Teacher edited")
                    self.assertEqual(conn.execute("SELECT COUNT(*) FROM practice_questions").fetchone()[0], 195)
                for entry in pack["topics"]:
                    mcq = entry["questions"][0]
                    self.assertEqual(len(set(mcq["options"])), 4)
                    self.assertIn(mcq["answer"], mcq["options"])
                    if entry["formula"]:
                        self.assertEqual(len(entry["formula"]), 3)
                from PyQt5.QtWidgets import QApplication
                from app.ui.main_window import MainWindow
                app = QApplication.instance() or QApplication([])
                for role, count in [("student", 5), ("teacher", 5), ("admin", 6)]:
                    window = MainWindow({"id": 1, "full_name": "Test Learner", "role": role})
                    window.show()
                    app.processEvents()
                    self.assertEqual(window.tabs.count(), count)
                    self.assertTrue(window.tabs.tabBar().isHidden())
                    self.assertFalse(any("AI Tutor" in b.text() for b in window.nav_group.buttons()))
                    self.assertFalse(any("Smart Learning" in b.text() for b in window.nav_group.buttons()))
                    self.assertFalse(any("Content Studio" in b.text() for b in window.nav_group.buttons()))
                    for index in range(count):
                        window.nav_group.button(index).click()
                        self.assertEqual(window.tabs.currentIndex(), index)
                    window.tabs.setCurrentIndex(1)
                    for subject in SUBJECTS:
                        window.subject_filter.setCurrentText(subject)
                        self.assertGreater(window.topic_filter.count(), 0)
                        self.assertIn("Content status", window.lesson_view.toPlainText())
                    window.close()


if __name__ == "__main__":
    unittest.main()
