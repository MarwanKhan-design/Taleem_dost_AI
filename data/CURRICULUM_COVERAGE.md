# KPK Grade XI supplementary library

The app currently targets Grade XI. The bundled pack adds 65 original lessons and
195 original practice questions across Physics, Mathematics, Computer Science,
Chemistry, Biology, English, Urdu, Pakistan Studies, Islamiat and
Mutala-e-Quran Hakeem. Each lesson includes an explanation, example, misconception,
revision material, learning objectives and source/scope notes. Quantitative topics
also have formula entries with symbols and units.

Practice includes 65 MCQs, 65 short questions and 65 extended-response questions.
Written answers are model responses for comparison: the existing quiz engine
uses exact text matching, so its score is not a reliable grade for equivalent
free-text answers. Worked numerical examples are included in the lessons.

## Source and edition limits

Official discovery references, consulted 13 November 2026:

- BISE Peshawar curriculum index: https://bisep.gov.pk/page-10030.html
- DCTE KP curriculum authority: https://dcte.kp.gov.pk/
- KP Textbook Board: https://tbb.kp.gov.pk/

These links establish the official places to obtain curriculum documents. They
do not authenticate every statement or certify this pack's coverage. The notes
are original foundational study support, not copied textbook pages. The learning
units are thematic and have no claimed official chapter numbers. Exact textbook
editions, pages, prescribed literary selections, prescribed Quran translations,
full SLO mappings, practical syllabuses and exam schemes remain unverified.
Foundational topics may also serve as revision from earlier grades. Listing a
subject does not mean it is compulsory for every Grade XI group or cohort.

This is **not a complete KPK syllabus for every grade, group or edition**. Current
and forthcoming curricula must be checked for the student's academic year.
No historical past papers, predictions, fabricated board provenance or official
translation claims are included. Teachers can expand and correct the library in
Content Studio using the student's assigned books.

## Installation and preservation

`app/database/curriculum.py` installs the versioned JSON pack during normal app
startup. Installation is additive and transactional. Reopening the app does not
duplicate content. Existing lessons, accounts, notes, progress and attempts are
preserved. Existing starter outlines are retained because students may have
bookmarks or progress linked to them. Each entry is labelled as original practice
and remains excluded from verified past-paper trend counts.

To edit the bundled material, update `build_curriculum_pack.py` and rebuild with
`python data/build_curriculum_pack.py`. A new pack version is required for a new
installation; existing teacher-written lessons are never overwritten by the
installer.
