import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database import db
from app.services.rubric import RUBRIC_SAMPLES, grade_answer


class RubricPracticeTest(unittest.TestCase):
    def test_pilot_scores_and_saves_partial_credit(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            db, "DB_PATH", Path(directory) / "test.db"
        ):
            db.initialize_database()
            db.create_user("learner", "Test Learner", "learner@example.com", "Password123!")
            pilot = [
                q for q in db.get_published_questions(subject="Physics", rubric_only=True)
                if q["topic_title"] == "Vector components"
            ]
            self.assertEqual(len(pilot), 2)
            short = next(q for q in pilot if q["question_type"] == "Short question")
            long = next(q for q in pilot if q["question_type"] == "Long question")
            review_id = db.add_exam_question(
                None, "A written prompt without a sample", "Short question", "", "",
                "", "Teacher-created practice",
            )
            review = next(q for q in db.get_published_questions(qtype="Short question") if q["id"] == review_id)
            answers = {
                short["id"]: "It has size and direction and splits into components at right angles.",
                long["id"]: "The x-component is 8.66 N. The y-component is 5 N. You cannot just add magnitudes.",
                review["id"]: "My own answer.",
            }
            result = db.save_quiz_attempt(1, "All subjects", "Rubric practice", [short, long, review], answers)
            self.assertEqual((result["earned"], result["possible"]), (5, 6))
            self.assertEqual(result["grades"][short["id"]]["earned"], 2)
            self.assertEqual(result["grades"][review["id"]]["possible"], 0)
            self.assertEqual(db.get_quiz_history(1)[0]["score_percent"], 83.3)
            with db.get_connection() as conn:
                stored = conn.execute("SELECT is_correct FROM question_attempts WHERE question_id=?", (review["id"],)).fetchone()
                self.assertIsNone(stored["is_correct"])
            contradicted = db.save_quiz_attempt(
                1, "Physics", "Rubric practice", [short],
                {short["id"]: "It does not have magnitude and direction."},
            )
            self.assertEqual(contradicted["earned"], 0)

            english = db.get_published_questions(subject="English", rubric_only=True)
            self.assertEqual(len(english), 12)
            question = next(q for q in english if q["question"] == "Explain imagery and metaphor in your own words.")
            result = db.save_quiz_attempt(
                1, "English", "Rubric practice", [question],
                {question["id"]: "Imagery appeals to the senses. A metaphor says one thing is another."},
            )
            self.assertEqual((result["earned"], result["possible"]), (2, 3))
            written = db.get_published_questions(rubric_only=True, limit=200)
            self.assertEqual(len(written), 130)
            self.assertEqual(len({item["subject"] for item in written}), 10)
            for item in written:
                with self.subTest(question=item["question"]):
                    sample = RUBRIC_SAMPLES.get(item["question"], item["answer"])
                    grade = grade_answer(item, sample)
                    self.assertGreater(grade["possible"], 0)
                    self.assertEqual(grade["earned"], grade["possible"])
                    self.assertEqual(grade_answer(item, "")["earned"], 0)

            science = next(q for q in written if q["question"] == "Explain enzymes in your own words.")
            grade = grade_answer(science, "Enzymes are biological catalysts that lower activation energy.")
            self.assertEqual((grade["earned"], grade["possible"]), (1, 3))
