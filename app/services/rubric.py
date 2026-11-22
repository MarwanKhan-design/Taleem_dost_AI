"""Local marking rules for written practice questions."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MarkingPoint:
    description: str
    accepted: tuple[str, ...]
    contradictions: tuple[str, ...] = ()


VECTOR_EXAMPLE = "Illustrate vector components with an example and explain one common mistake."
IMAGERY_EXAMPLE = "Illustrate imagery and metaphor with an example and explain one common mistake."
RUBRIC_PROMPTS = {
    "Explain imagery and metaphor in your own words.": (
        "Explain imagery and metaphor in your own words. How does a simile differ from a metaphor?"
    ),
    "Illustrate main idea and inference with an example and explain one common mistake.": (
        "A school planted trees. Shaded classrooms became cooler and electricity use fell. "
        "Identify one detail, explain what it suggests about planting trees, and describe one mistake to avoid."
    ),
    "Illustrate subject–verb agreement with an example and explain one common mistake.": (
        "Complete “The box of pencils ___ on the desk” with is or are. Write the full sentence, "
        "identify the main subject noun, and explain why the nearer plural noun can mislead you."
    ),
    "Illustrate tense and aspect with an example and explain one common mistake.": (
        "Say you visited Peshawar yesterday and that you have finished your homework. Use the "
        "simple past for the visit and the present perfect for the homework. Explain one common mistake."
    ),
    "Illustrate active and passive voice with an example and explain one common mistake.": (
        "Write “The students solved the problem” in both active and passive voice. "
        "Explain one mistake to avoid when forming the passive."
    ),
    "Illustrate paragraph structure with an example and explain one common mistake.": (
        "Write a topic sentence about how daily reading improves vocabulary. "
        "Support it with a detail about context, then explain one mistake that weakens paragraph unity."
    ),
    VECTOR_EXAMPLE: (
        "A 10 N force acts at 30° above the positive x-axis. Give its x and y components "
        "and explain why simply adding magnitudes can give the wrong resultant."
    ),
    IMAGERY_EXAMPLE: (
        'In “The air smelled of wet soil. The classroom was a beehive,” identify the sensory '
        "detail, explain the metaphor, and explain why it should not be read literally."
    ),
}

RUBRIC_SAMPLES = {
    VECTOR_EXAMPLE: (
        "The x-component is 8.66 N and the y-component is 5 N. "
        "You cannot just add magnitudes because the forces can point in different directions."
    ),
    IMAGERY_EXAMPLE: (
        "The smell of wet soil is imagery. The beehive suggests that the classroom was busy. "
        "The classroom was not literally a beehive."
    ),
}

RUBRICS = {
    "Explain main idea and inference in your own words.": (
        MarkingPoint("The main idea is the central message.", ("central message", "main point", "central point")),
        MarkingPoint("Details support or explain the main idea.",
                     ("supporting details explain", "details support", "details explain", "details back up")),
        MarkingPoint("An inference is a conclusion based on clues or evidence.",
                     ("combines textual evidence", "conclusion based on clues", "conclusion based on evidence",
                      "inference uses evidence", "inference uses clues"),
                     ("guess without evidence",)),
    ),
    "Illustrate main idea and inference with an example and explain one common mistake.": (
        MarkingPoint("Identify a concrete detail about the trees or the shaded classrooms.",
                     ("school planted trees", "trees shaded", "shaded classrooms")),
        MarkingPoint("Identify a reasonable main idea or inference supported by those details.",
                     ("reduce cooling needs", "reduce electricity use", "trees help cool", "trees cool classrooms",
                      "shade reduces electricity use")),
        MarkingPoint("Avoid unsupported inferences or confusing a minor detail with the main idea.",
                     ("minor detail as the central idea", "minor detail for the main idea",
                      "claim contradicted by the passage", "inference without evidence", "ignore the evidence")),
    ),
    "Explain subject–verb agreement in your own words.": (
        MarkingPoint("The verb agrees with the subject in number and person.",
                     ("person and number", "number and person", "matches the subject in number",
                      "singular subject takes a singular verb")),
        MarkingPoint("Words between the subject and the verb do not change agreement.",
                     ("intervening phrases do not change", "ignore words between",
                      "ignore the phrase between", "words in between do not change")),
        MarkingPoint("Identify the main noun of the subject before choosing the verb.",
                     ("identify the head noun", "find the head noun", "find the main noun",
                      "use the head noun", "use the main noun")),
    ),
    "Illustrate subject–verb agreement with an example and explain one common mistake.": (
        MarkingPoint("Use the singular verb in the example.", ("box of pencils is", "box is singular so use is"),
                     ("box of pencils are",)),
        MarkingPoint("Identify box as the subject's main noun.",
                     ("subject head is box", "head noun is box", "box is the subject", "subject is box")),
        MarkingPoint("Do not choose the verb based on the nearer plural noun.",
                     ("do not make the verb agree with the nearest noun", "ignore the nearest noun",
                      "do not use the closest noun", "pencils does not control the verb")),
    ),
    "Explain tense and aspect in your own words.": (
        MarkingPoint("Tense tells when the action or situation happens.",
                     ("locates a situation in time", "tells when", "shows when", "time of the action")),
        MarkingPoint("Aspect shows whether an action is ongoing, completed, or habitual.",
                     ("ongoing completed or habitual", "ongoing or completed", "in progress or complete",
                      "how the action unfolds")),
        MarkingPoint("Explain how context or a time expression guides the choice.",
                     ("using context and time expressions", "depends on the context", "yesterday signals",
                      "finished past time", "connects a past event to the present")),
    ),
    "Illustrate tense and aspect with an example and explain one common mistake.": (
        MarkingPoint("Give a past-tense example with a finished time.",
                     ("visited peshawar yesterday", "went to school yesterday", "visited yesterday")),
        MarkingPoint("Give a present-perfect example with present relevance.",
                     ("have finished my homework", "have completed my homework", "has finished her homework")),
        MarkingPoint("Explain the mistake of combining the present perfect with a finished time.",
                     ("avoid combining present perfect with a specific finished time",
                      "do not use present perfect with yesterday", "present perfect does not go with yesterday")),
    ),
    "Explain active and passive voice in your own words.": (
        MarkingPoint("In active voice the subject performs the action.",
                     ("subject performs the action", "subject does the action", "subject carries out the action")),
        MarkingPoint("In passive voice the subject receives the action.",
                     ("subject receives the action", "subject receives it", "subject is acted on")),
        MarkingPoint("Form the passive with be and a past participle.",
                     ("form of be and the past participle", "be and a past participle", "be plus a past participle",
                      "be followed by the past participle")),
    ),
    "Illustrate active and passive voice with an example and explain one common mistake.": (
        MarkingPoint("Give the active sentence with the students as the subject.",
                     ("students solved the problem", "students solved a problem")),
        MarkingPoint("Give the passive sentence in the same tense.",
                     ("problem was solved by the students", "problem was solved by students")),
        MarkingPoint("Use a past participle after be, avoiding the base form.",
                     ("does not use the base verb after be", "use the past participle", "not was solve",
                      "use solved instead of solve")),
    ),
    "Explain paragraph structure in your own words.": (
        MarkingPoint("A topic sentence states the paragraph's main idea.",
                     ("topic sentence", "opening sentence states the main idea")),
        MarkingPoint("The body develops that idea with relevant supporting details.",
                     ("supporting details", "body gives examples", "body supports the main idea")),
        MarkingPoint("A closing sentence ties the paragraph together.",
                     ("closing sentence", "concluding sentence", "conclusion sums up")),
    ),
    "Illustrate paragraph structure with an example and explain one common mistake.": (
        MarkingPoint("Start with a topic sentence about reading and vocabulary.",
                     ("reading improves vocabulary", "reading builds vocabulary", "reading helps you learn new words")),
        MarkingPoint("Support the idea with an explanation about learning words in context.",
                     ("words in context", "infer meanings", "learn meanings from context")),
        MarkingPoint("Avoid mixing unrelated ideas in one paragraph.",
                     ("unrelated ideas in one paragraph", "unrelated details", "stay on topic",
                      "avoid adding unrelated ideas")),
    ),
    "Explain imagery and metaphor in your own words.": (
        MarkingPoint(
            "Imagery uses sensory details to help the reader imagine an experience.",
            (
                "sensory language", "sensory details", "sensory descriptions",
                "appeals to the senses", "appeals to our senses", "describes what we can see hear",
                "describes what you can see hear", "helps readers see hear",
                "uses the five senses", "uses the senses",
            ),
            ("does not appeal to the senses", "does not use sensory details",
             "only describes what we see"),
        ),
        MarkingPoint(
            "A metaphor describes one thing as another to suggest a shared quality.",
            (
                "describes one thing as another", "says one thing is another",
                "says something is something else", "calls one thing another",
                "compares two things without using like or as", "compares things without like or as",
                "a direct comparison without like or as",
            ),
            ("compares using like or as", "uses like or as to compare",
             "literally the same thing", "literally become the same"),
        ),
        MarkingPoint("A simile explicitly compares things, often using like or as.",
                     ("simile makes an explicit comparison", "simile uses like or as",
                      "simile compares using like or as", "simile uses words like like or as")),
    ),
    IMAGERY_EXAMPLE: (
        MarkingPoint("The smell of wet soil is an example of imagery.",
                     ("smell of wet soil", "air smelled of wet soil", "wet soil appeals to smell")),
        MarkingPoint("The beehive metaphor suggests the classroom was busy.",
                     ("beehive suggests busy", "beehive suggests that the classroom was busy",
                      "classroom was busy", "classroom was buzzing with activity")),
        MarkingPoint("The classroom was not literally a beehive.",
                     ("not literally a beehive", "not a real beehive", "not an actual hive",
                      "not physically a beehive")),
    ),
    "Explain vector components in your own words.": (
        MarkingPoint(
            "A vector has both magnitude and direction.",
            ("magnitude and direction", "direction and magnitude", "size and direction", "direction and size"),
            ("no direction", "without direction", "vector has only magnitude", "vector has magnitude only",
             "does not have magnitude and direction", "does not have size and direction"),
        ),
        MarkingPoint(
            "A vector can be split into perpendicular components.",
            ("perpendicular components", "components at right angles", "horizontal and vertical components"),
            ("cannot be split", "can't be split", "cannot be resolved", "are not perpendicular"),
        ),
        MarkingPoint(
            "From the positive x-axis, use cosine for x and sine for y.",
            ("cosine for x and sine for y", "cos for x and sin for y", "x uses cosine and y uses sine"),
            ("sine for x and cosine for y", "sin for x and cos for y"),
        ),
    ),
    VECTOR_EXAMPLE: (
        MarkingPoint(
            "For the 10 N example, the x-component is approximately 8.66 N.",
            ("fx 8.66", "x 8.66", "x is 8.66", "x component is 8.66", "horizontal component is 8.66"),
        ),
        MarkingPoint(
            "For the 10 N example, the y-component is 5 N.",
            ("y component is 5", "fy 5", "vertical component is 5", "y is 5"),
        ),
        MarkingPoint(
            "Adding magnitudes alone gives the wrong resultant for different directions.",
            ("adding magnitudes alone gives the wrong resultant", "cannot just add magnitudes",
             "adding the magnitudes ignores direction", "you cannot add their sizes"),
        ),
    ),
}


def tokenize(text):
    return re.findall(r"\d+(?:\.\d+)?|[^\W\d_]+", text.casefold())


def normalize(text):
    words = tokenize(text)
    return f" {' '.join(words)} "


WRITTEN_TYPES = ("Short question", "Long question")
COMMON_WORDS = frozenset(
    "a an and are as at be been by can for from has have in is it of on or that the their this to was were which with "
    "اور ایک اس ان یہ وہ ہیں ہے میں سے کے کی کو پر کا کہ".split()
)
NEGATIONS = frozenset("no not never cannot without نہیں نہ بغیر".split())


def split_ideas(text):
    # Split prose boundaries while preserving decimal numbers and formula punctuation.
    return [
        idea.strip()
        for idea in re.split(r"(?<=[.!?۔؟;؛])\s+|\n+", text.strip())
        if tokenize(idea)
    ]


def reference_points(question):
    sample = question["answer"] or ""
    if question["question_type"] == "Long question":
        application, _, correction = sample.partition("\n")
        examples = split_ideas(application)
        # Leave a separate mark for the misconception when the sample supplies one.
        limit = 2 if correction.strip() else 3
        points = examples[:limit - 1] + [" ".join(examples[limit - 1:])]
        if correction.strip():
            points.append(correction.strip())
    else:
        ideas = split_ideas(sample)
        points = ideas[:2] + [" ".join(ideas[2:])]
    return [point for point in points if tokenize(point)]


def matches_reference(reference, answer_ideas):
    expected = set(tokenize(reference))
    numbers = {word for word in expected if word[0].isdecimal()}
    terms = expected - COMMON_WORDS - NEGATIONS
    terms = terms or expected
    # Require at least 80% of distinct terms, all numbers, and compatible negation.
    return any(
        numbers <= actual
        and bool(expected & NEGATIONS) == bool(actual & NEGATIONS)
        and 5 * len(terms & actual) >= 4 * len(terms)
        for actual in answer_ideas
    )


def written_mark_count(question):
    rubric = RUBRICS.get(question["question"])
    return len(rubric) if rubric else len(reference_points(question))


def grade_answer(question, response):
    question_type = question["question_type"]
    if question_type in WRITTEN_TYPES:
        rubric = RUBRICS.get(question["question"])
        if rubric:
            answer = normalize(response)
            points = [
                (point.description,
                 any(normalize(phrase) in answer for phrase in point.accepted)
                 and not any(normalize(phrase) in answer for phrase in point.contradictions))
                for point in rubric
            ]
        else:
            ideas = split_ideas(response)
            references = reference_points(question)
            answer_ideas = [set(tokenize(idea)) for idea in ideas]
            # Some reference points group adjacent sentences into one marking point.
            max_span = max((len(split_ideas(point)) for point in references), default=1)
            answer_ideas.extend(
                set(tokenize(" ".join(ideas[start:start + length])))
                for length in range(2, min(len(ideas), max_span) + 1)
                for start in range(len(ideas) - length + 1)
            )
            points = [
                (point, matches_reference(point, answer_ideas))
                for point in references
            ]
        return {"earned": sum(earned for _, earned in points), "possible": len(points), "points": points}
    matched = bool(response.strip()) and response.strip().casefold() == question["answer"].strip().casefold()
    return {"earned": int(matched), "possible": 1, "points": []}
