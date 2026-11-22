# Taleem Dost AI — Phase 7 (Smart AI Learning & Exam Intelligence)

Phase 7 combines the previous roadmap items 7, 8 and 9 into one upgrade. It builds on Phase 6 and retains the existing login, learning library, content studio, practice engine, study planner, notes, bookmarks and progress.

## New features
1. **Photo question solver:** upload PNG/JPG/JPEG/WEBP (up to 12 MB) and receive a step-by-step explanation. Images are read from disk and sent to the configured AI provider; this app does not save the image to its local database.
2. **Navigation:** the main menu is in the left sidebar. The AI Tutor tab has been removed; Smart Learning tools remain available.
3. **AI quiz generator:** create original topic-based MCQs. Questions are saved as `AI-generated practice`, not past-paper questions, and appear in Exam Preparation.
4. **Weak-topic insights:** analyze saved answers to topic-linked questions and rank topics by accuracy. It requires practice history and topic-linked questions.
5. **Flashcards and spaced repetition:** generate cards from saved lesson content, then review them with Again / Hard / Good / Easy scheduling.
6. **Board-paper intelligence:** summarize only entries explicitly marked verified past-paper questions with board, year and source reference. The report is descriptive, not predictive.

## Install / run on Windows
1. Extract Phase 7 into a **new folder**. Keep Phase 6 as a backup.
2. Back up Phase 6's `data/taleem_dost.db`, then copy it into Phase 7's `data` folder.
3. Open the Phase 7 folder in PyCharm.
4. Install packages:
   `python -m pip install -r requirements.txt`
5. Copy `.env.example` to `.env`, add your own API key, and save.
6. Run:
   `python main.py`

Example `.env`:
```env
OPENAI_API_KEY=your_secret_key
OPENAI_MODEL=gpt-5.5
```
The selected API model must be available to your API account and support image input for Photo Solver. API charges are separate from a ChatGPT subscription.

## KPK study library

The bundled Grade XI supplementary pack contains 65 lessons, 195 original practice
questions, and 20 formula entries across 10 subjects. It installs automatically
without overwriting existing lessons or duplicating content. See
[data/CURRICULUM_COVERAGE.md](data/CURRICULUM_COVERAGE.md) for coverage, official
reference links and edition limits. This is foundational study support, not a
complete verified syllabus or an official past-paper archive.

## Important accuracy rules
- AI-generated questions are labelled as practice. They are not historical BISE Peshawar questions.
- Board trend summaries include only database entries marked verified and carrying board/year/source reference. They do not independently verify those claims or represent a complete archive.
- Trend counts are not guaranteed exam predictions. Do not use them as a substitute for the current official syllabus and textbook.
- Weak-topic insights need topic-linked question attempts. Written answers in the existing quiz engine are still exact-text matched, not intelligently graded.
- Flashcards are generated only from saved lesson text supplied to the AI. Review scheduling is a lightweight aid, not a guarantee of retention.

## Privacy and safety
- Photo questions and lesson text used for AI generation are sent to the configured AI provider. Do not upload images containing private information.
- API requests may incur charges. Never share your `.env` file or API key.
- This remains a local desktop prototype using SQLite, not a production public multi-user platform.

## Troubleshooting
- If AI features say the model is unavailable, set `OPENAI_MODEL` to a model available to your API account that supports the needed input types.
- If photo solving fails, check internet access, API key, API billing, model image support and image file size.
- If the board report is empty, add properly sourced verified past-paper entries through Content Studio.


## If the app still says "AI is not configured"
This build explicitly loads `.env` from the same project folder as `main.py`, even if PyCharm's working directory is different.

1. Make sure `.env` is in the project root, beside `main.py` (not inside `app` or `app/services`).
2. Make sure the filename is exactly `.env`, not `.env.txt`. In File Explorer enable **View → Show → File name extensions** to check.
3. The file must contain one line like `OPENAI_API_KEY=sk-your-real-key` (do not add spaces around the `=`; quotes are not needed).
4. Save the file and fully close/restart the app.
5. To check whether Python can read it, open PowerShell in this project folder and run:
   `python check_api_setup.py`
   This script reports only whether a key was detected; it never prints the key.

If the script detects the key but an AI request fails, the issue is no longer `.env` detection. Check the exact API error for an invalid/revoked key, project permissions, API billing/credits, rate limits, or an unavailable model. The ChatGPT subscription does not pay for API usage.
