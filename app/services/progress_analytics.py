"""Learning analytics derived from the main app's saved topic and quiz records."""
from statistics import mean

from app.database import db


def percent(part, total):
    return round(100 * part / total, 1) if total else 0


def load_progress(user_id):
    with db.get_connection() as connection:
        topics = connection.execute(
            """SELECT t.id, t.title, c.id chapter_id, c.title chapter, c.subject,
                      COALESCE(p.status, 'Not started') status, COALESCE(p.completed, 0) completed
               FROM topics t JOIN chapters c ON c.id=t.chapter_id
               LEFT JOIN student_topic_progress p ON p.topic_id=t.id AND p.user_id=?
               ORDER BY c.subject, c.sort_order, c.id, t.sort_order, t.id""",
            (user_id,),
        ).fetchall()
        quizzes = connection.execute(
            """SELECT a.id, a.subject, a.quiz_type, a.total_questions,
                      a.correct_answers, a.score_percent,
                      EXISTS (SELECT 1 FROM question_attempts qa WHERE qa.attempt_id=a.id
                              AND TRIM(qa.selected_answer)<>'') answered
               FROM quiz_attempts a
               WHERE a.user_id=? AND a.total_questions>0 AND a.completed_at IS NOT NULL
               ORDER BY a.id""",
            (user_id,),
        ).fetchall()
        answers = connection.execute(
            """SELECT t.id topic_id, COALESCE(c.subject, 'General / mixed') subject,
                      COUNT(*) total, SUM(CASE WHEN qa.is_correct=1 THEN 1 ELSE 0 END) correct
               FROM question_attempts qa JOIN quiz_attempts a ON a.id=qa.attempt_id
               LEFT JOIN practice_questions q ON q.id=qa.question_id
               LEFT JOIN topics t ON t.id=q.topic_id LEFT JOIN chapters c ON c.id=t.chapter_id
               WHERE a.user_id=? AND a.total_questions>0 AND a.completed_at IS NOT NULL
                 AND qa.is_correct IS NOT NULL AND TRIM(qa.selected_answer)<>''
               GROUP BY c.subject, t.id""",
            (user_id,),
        ).fetchall()

    subjects, chapters, accuracy = {}, {}, {}
    for topic in topics:
        status = 'Completed' if topic['completed'] else topic['status']
        subject = subjects.setdefault(topic['subject'], dict.fromkeys(
            ('Completed', 'Learning', 'Needs revision', 'Not started'), 0
        ))
        subject[status if status in subject else 'Not started'] += 1
        chapter = chapters.setdefault(topic['chapter_id'], [topic['subject'], topic['chapter'], 0, 0])
        chapter[2] += topic['completed']
        chapter[3] += 1
    for answer in answers:
        counts = accuracy.setdefault(answer['subject'], [0, 0])
        counts[0] += answer['correct']
        counts[1] += answer['total']
    subject_accuracy = sorted(
        ((subject, correct, total, percent(correct, total)) for subject, (correct, total) in accuracy.items()),
        key=lambda row: (row[3], row[0]),
    )

    topic_accuracy = {
        row['topic_id']: percent(row['correct'], row['total'])
        for row in answers if row['topic_id'] is not None
    }
    revision, next_topics = [], []
    for topic in topics:
        score = topic_accuracy.get(topic['id'])
        if topic['status'] == 'Needs revision' or (score is not None and score < 60):
            revision.append((topic, score))
        elif not topic['completed']:
            next_topics.append(topic)
    revision.sort(key=lambda entry: (
        entry[0]['status'] != 'Needs revision', entry[1] if entry[1] is not None else 101
    ))
    weak_subjects = {row[0] for row in subject_accuracy if row[3] < 60}
    next_topics.sort(key=lambda topic: (topic['subject'] not in weak_subjects, topic['status'] != 'Learning'))

    completed = sum(t['completed'] for t in topics)
    scores = [q['score_percent'] for q in quizzes]
    average = round(mean(scores), 1) if scores else None
    sample = min(5, len(scores) // 2)
    change = round(mean(scores[-sample:]) - mean(scores[-2 * sample:-sample]), 1) if sample else None
    courses = sum(counts['Completed'] == sum(counts.values()) for counts in subjects.values())
    return {
        'completed': completed, 'total': len(topics), 'subjects': subjects, 'chapters': chapters.values(),
        'courses': courses, 'quizzes': quizzes, 'average': average, 'change': change, 'sample': sample,
        'accuracy': subject_accuracy, 'revision': revision[:8], 'next_topics': next_topics[:5],
        'achievements': achievements(completed, quizzes, courses, average),
    }


def achievements(completed, quizzes, courses, average):
    answered = [quiz for quiz in quizzes if quiz['answered']]
    perfect = sum(quiz['score_percent'] >= 100 and quiz['total_questions'] >= 3 for quiz in answered)
    badges = [
        ('First Lesson Completed', completed, 1, 25),
        ('5 Lessons Completed', completed, 5, 40),
        ('10 Lessons Completed', completed, 10, 60),
        ('25 Lessons Completed', completed, 25, 100),
        ('50 Lessons Completed', completed, 50, 150),
        ('First Quiz Taken', len(answered), 1, 20),
        ('Quiz Master', len(answered), 10, 80),
        ('100% Quiz Score', perfect, 1, 75),
        ('Quiz Ace', average if len(answered) >= 5 else 0, 80, 100),
        ('Subject Master', courses, 1, 150),
    ]
    xp = 20 * completed + sum(min(45, 5 + 2 * quiz['correct_answers']) for quiz in answered) + 20 * perfect
    xp += sum(reward for _, value, target, reward in badges if value >= target)
    level = 1
    while xp >= 50 * level * (level + 1):
        level += 1
    badges.append(('Level 5 Reached', level, 5, 100))
    if level >= 5:
        xp += 100
        while xp >= 50 * level * (level + 1):
            level += 1
    return xp, level, 50 * level * (level + 1) - xp, badges
