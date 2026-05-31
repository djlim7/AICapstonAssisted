"""
Prompt decomposition configurations (two consecutive prompts within the same session).

D-SF: Decomposition-Scoring-First  — turn 1 = score, turn 2 = feedback
D-FF: Decomposition-Feedback-First — turn 1 = feedback, turn 2 = score based on feedback

Each function returns (prompt1, prompt2). The caller builds the multi-turn conversation
by appending the assistant response from turn 1 before sending prompt 2.
"""

from .base import SCORE_TASK, FEEDBACK_TASK, build_context_block


def build_scoring_first(
    task: str, rubric: str, exemplars: list[dict], proposal: str
) -> tuple[str, str]:
    """D-SF: turn 1 requests only the score; turn 2 requests feedback."""
    context = build_context_block(task, rubric, exemplars)

    prompt1 = (
        f"{context}\n\n"
        "Instructions: Let's think step by step:\n\n"
        "1. Analyze the proposal using the provided scoring rubrics and examples.\n\n"
        f"2. Based on the provided rubric, {SCORE_TASK}\n\n"
        f"Based on the context and instructions above, evaluate the following proposal: "
        f"\"\"\"{proposal.strip()}\"\"\""
    )

    prompt2 = (
        f"Based on the provided rubric and the predicted assessment score above, {FEEDBACK_TASK}"
    )

    return prompt1, prompt2


def build_feedback_first(
    task: str, rubric: str, exemplars: list[dict], proposal: str
) -> tuple[str, str]:
    """D-FF: turn 1 requests only feedback; turn 2 requests the score based on that feedback."""
    context = build_context_block(task, rubric, exemplars)

    prompt1 = (
        f"{context}\n\n"
        "Instructions: Let's think step by step:\n\n"
        "1. Analyze the proposal using the provided scoring rubrics and examples.\n\n"
        f"2. Based on the provided rubric, {FEEDBACK_TASK}\n\n"
        f"Based on the context and instructions above, evaluate the following proposal: "
        f"\"\"\"{proposal.strip()}\"\"\""
    )

    prompt2 = (
        f"Based on the feedback you generated above and the provided scoring rubric, {SCORE_TASK}"
    )

    return prompt1, prompt2
