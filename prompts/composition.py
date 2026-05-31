"""
Prompt composition configurations (single prompt, both tasks).

C-SF: Composition-Scoring-First  — score requested before feedback
C-FF: Composition-Feedback-First — feedback requested before score
"""

from .base import SCORE_TASK, FEEDBACK_TASK, build_context_block


def build_scoring_first(task: str, rubric: str, exemplars: list[dict], proposal: str) -> str:
    """C-SF: single prompt, step 2 = score, step 3 = feedback."""
    context = build_context_block(task, rubric, exemplars)
    return (
        f"{context}\n\n"
        "Instructions: Let's think step by step:\n\n"
        "1. Analyze the proposal using the provided scoring rubrics and examples.\n\n"
        f"2. Based on the provided rubric, {SCORE_TASK}\n\n"
        f"3. Based on the provided rubric and the predicted assessment score above, {FEEDBACK_TASK}\n\n"
        f"Based on the context and instructions above, evaluate the following proposal: "
        f"\"\"\"{proposal.strip()}\"\"\""
    )


def build_feedback_first(task: str, rubric: str, exemplars: list[dict], proposal: str) -> str:
    """C-FF: single prompt, step 2 = feedback, step 3 = score."""
    context = build_context_block(task, rubric, exemplars)
    return (
        f"{context}\n\n"
        "Instructions: Let's think step by step:\n\n"
        "1. Analyze the proposal using the provided scoring rubrics and examples.\n\n"
        f"2. Based on the provided rubric, {FEEDBACK_TASK}\n\n"
        f"3. Based on the provided rubric and the feedback you generated above, {SCORE_TASK}\n\n"
        f"Based on the context and instructions above, evaluate the following proposal: "
        f"\"\"\"{proposal.strip()}\"\"\""
    )
