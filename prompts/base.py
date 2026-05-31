"""
Shared text blocks and formatting utilities used across all four prompt configurations.

Prompt engineering practices from Chen et al. (2025) and Ziems et al. (2024):
- Role prompting
- Zero-Shot Chain-of-Thought ("Let's think step by step")
- Few-shot prompting with balanced exemplars
- Structured formatting with triple-quote delimiters
- Context before instruction
- Explicit constraints on output range
"""

ROLE = (
    "You are an experienced teacher in a master's-level data science course. "
    "Your task is to evaluate students' assignments on developing a data science "
    "project proposal. Your evaluation must include an overall score and constructive "
    "feedback to support students to learn better. You will be provided with the "
    "assignment specification, scoring rubric, exemplar responses and their "
    "corresponding scores, as detailed below:"
)

# Learner-Centered Feedback framework definition (Ryan et al., 2023)
# Embedded verbatim in prompts requesting feedback.
LCF_DEFINITION = (
    "Learner-centred feedback is structured around three key dimensions: "
    "(i) Future Impact refers to feedback that guides refining key aspects of future "
    "similar tasks, supports students in achieving subject-specific learning outcomes, "
    "and delivers practical guidance to help them develop academic and professional skills. "
    "(ii) Sensemaking refers to feedback that offers an overall assessment of the "
    "student's performance, aligns with the marking rubric, and identifies both strengths "
    "and areas for improvement within specific aspects of the student's work. "
    "(iii) Agency refers to feedback that encourages students to contact teachers or "
    "explore additional learning resources, recognizes their successful efforts, and "
    "strengthens the teacher-student bond through nurturing and supportive interactions."
)

FEEDBACK_TASK = (
    "generate learner-centred feedback for students to improve their work, which "
    "focuses on delivering personalized guidance to help students improve their "
    f"understanding, skills, and engagement. {LCF_DEFINITION}"
)

SCORE_TASK = (
    "assign a holistic numerical assessment score between 0 and 15 for the project "
    "proposal, allowing decimals. Even if uncertain, you must still select a score "
    "within this range."
)


def format_exemplars(exemplars: list[dict]) -> str:
    """
    Format few-shot exemplars as a single string.

    Each exemplar dict must have 'text' (str) and 'score' (float|int).
    The paper presents exemplars in random order; caller is responsible for shuffling.
    """
    parts: list[str] = []
    for i, ex in enumerate(exemplars, 1):
        parts.append(
            f"Example {i}:\n"
            f"Proposal: \"\"\"{ex['text'].strip()}\"\"\"\n"
            f"Score: {ex['score']}"
        )
    return "\n\n".join(parts)


def build_context_block(task: str, rubric: str, exemplars: list[dict]) -> str:
    """Shared header block: role + task spec + rubric + few-shot examples."""
    examples_str = format_exemplars(exemplars)
    return (
        f"{ROLE}\n\n"
        f"Assignment specification: \"\"\"{task}\"\"\"\n\n"
        f"Scoring Rubric: \"\"\"{rubric}\"\"\"\n\n"
        f"Examples: \"\"\"{examples_str}\"\"\""
    )
