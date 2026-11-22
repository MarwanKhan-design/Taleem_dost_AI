import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app.database import db


class StudyStreakTest(unittest.TestCase):
    def test_completions_and_quizzes_share_one_day_per_account(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "test.db"
        ), patch.object(db, "date") as clock:
            db.initialize_database()
            self.assertTrue(db.create_user("one", "Learner One", "one@example.com", "Password123!")[0])
            self.assertTrue(db.create_user("two", "Learner Two", "two@example.com", "Password123!")[0])
            questions = db.get_published_questions(limit=1)
            question = questions[0]
            answers = {question["id"]: question["answer"]}

            clock.today.return_value = date(2026, 11, 20)
            db.mark_topic(1, 1, "Learning")
            db.save_quiz_attempt(1, "All subjects", "All types", questions, {})
            self.assertEqual(db.get_study_streak(1), 0)
            db.mark_topic(1, 1, "Completed")
            db.save_quiz_attempt(1, "All subjects", "All types", questions, answers)
            self.assertEqual(db.get_study_streak(1), 1)
            self.assertEqual(db.get_study_streak(2), 0)

            clock.today.return_value = date(2026, 11, 21)
            db.mark_topic(1, 1, "Completed")
            self.assertEqual(db.get_study_streak(1), 1)
            db.save_quiz_attempt(1, "All subjects", "All types", questions, answers)
            self.assertEqual(db.get_study_streak(1), 2)
            db.initialize_database()
            self.assertEqual(db.get_study_streak(1), 2)

            clock.today.return_value = date(2026, 11, 23)
            self.assertEqual(db.get_study_streak(1), 0)
            db.mark_topic(1, 2, "Completed")
            self.assertEqual(db.get_study_streak(1), 1)
            db.mark_topic(1, 2, "Needs revision")
            db.mark_topic(1, 2, "Completed")
            db.mark_topic(1, 3, "Completed")
            _, streaks, counts = db.get_monthly_study_activity(1)
            self.assertEqual(streaks[-4:], [1, 2, 0, 1])
            self.assertEqual(counts[-4:], [1, 0, 0, 2])
            self.assertEqual(sum(db.get_monthly_study_activity(2)[2]), 0)

            clock.today.return_value = date(2026, 11, 30)
            db.save_quiz_attempt(1, "All subjects", "All types", questions, answers)
            clock.today.return_value = date(2026, 12, 1)
            db.mark_topic(1, 4, "Completed")
            _, streaks, counts = db.get_monthly_study_activity(1)
            self.assertEqual(streaks, [2])
            self.assertEqual(counts, [1])
