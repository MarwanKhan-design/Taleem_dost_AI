# Taleem Dost AI

Taleem Dost AI is a Windows desktop study app for the KPK under-17 AI tournament. It includes a Grade XI study library, exam practice, a study planner, and reports based on locally saved data.

Tournament Phase 2 development happens on `main`. To open the original prototype in a separate folder, run `git worktree add --detach ../Taleem_Dost_AI_Phase1 phase-1`.

## Run on Windows

1. Open the project folder in PowerShell or PyCharm.
2. Install the dependencies with `python -m pip install -r requirements.txt`.
3. Start the app with `python main.py`.
4. Create an administrator account if prompted, then sign in.

The app stores accounts and study records in `data/taleem_dost.db`. Back up that file before moving the app to a new folder if you want to carry over existing records.

## Tournament demo

1. Open **Learn** and show a lesson from the bundled KPK Grade XI curriculum.
2. Complete a practice session in **Revision & Practice** and review the result.
3. Open **Study Insights** to see how saved answers to topic-linked questions contribute to the weak-topic report.

## Curriculum and reports

The bundled supplementary pack contains 65 lessons, 195 original practice questions, and 20 formula entries across 10 subjects. It installs automatically and preserves existing lessons. See [curriculum coverage](data/CURRICULUM_COVERAGE.md) for sources and edition limits.

- **My Weak Topics** ranks topics by accuracy on recorded answers.
- **Flashcards** schedules reviews for cards already saved in the local account.
- **Board Trends** counts entries marked as verified past-paper questions with a board, year, and source reference. Its coverage depends on the records entered by the content team.

The current reports use saved records and descriptive counts. Linear regression and decision trees are planned for Phase 2.

## Tests

Run `python -m unittest discover -s tests` to check curriculum installation.
