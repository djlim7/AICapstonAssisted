"""
Pipeline for calling GPT-4o with the four prompt configurations.

Key design choices from the paper:
- temperature=0, top_p=0.01 to minimize randomness
- N_RUNS=5 runs per proposal; scores are averaged, one feedback sample is kept
- Each proposal is processed in a fresh API context to prevent context leakage
- OpenAI Structured Outputs enforce JSON schema compliance
- Few-shot exemplars are shuffled before each run to reduce ordering bias
"""

import json
import random
from dataclasses import dataclass, field

from openai import OpenAI
from pydantic import BaseModel, Field

import config
from prompts import composition as comp
from prompts import decomposition as decomp

client = OpenAI(api_key=config.OPENAI_API_KEY)

CONFIG_NAMES = ["C-SF", "C-FF", "D-SF", "D-FF"]


# ---------------------------------------------------------------------------
# Output schemas for OpenAI Structured Outputs
# ---------------------------------------------------------------------------

class _ScoreOnly(BaseModel):
    score: float = Field(description="Holistic score between 0 and 15, decimals allowed.")


class _FeedbackOnly(BaseModel):
    feedback: str = Field(description="Learner-centred feedback text.")


class _ScoreThenFeedback(BaseModel):
    score: float = Field(description="Holistic score between 0 and 15, decimals allowed.")
    feedback: str = Field(description="Learner-centred feedback text.")


class _FeedbackThenScore(BaseModel):
    feedback: str = Field(description="Learner-centred feedback text.")
    score: float = Field(description="Holistic score between 0 and 15, decimals allowed.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse(messages: list[dict], response_format) -> object:
    response = client.beta.chat.completions.parse(
        model=config.MODEL,
        messages=messages,
        temperature=config.TEMPERATURE,
        top_p=config.TOP_P,
        response_format=response_format,
    )
    return response.choices[0].message.parsed


def _clamp(score: float) -> float:
    return max(config.SCORE_MIN, min(config.SCORE_MAX, score))


# ---------------------------------------------------------------------------
# Per-run result
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    score: float
    feedback: str


# ---------------------------------------------------------------------------
# Single-run implementations for each configuration
# ---------------------------------------------------------------------------

def _run_csf_once(proposal: str, exemplars: list[dict]) -> RunResult:
    prompt = comp.build_scoring_first(
        config.TASK_DESCRIPTION, config.RUBRIC, exemplars, proposal
    )
    parsed: _ScoreThenFeedback = _parse(
        [{"role": "user", "content": prompt}], _ScoreThenFeedback
    )
    return RunResult(score=_clamp(parsed.score), feedback=parsed.feedback)


def _run_cff_once(proposal: str, exemplars: list[dict]) -> RunResult:
    prompt = comp.build_feedback_first(
        config.TASK_DESCRIPTION, config.RUBRIC, exemplars, proposal
    )
    parsed: _FeedbackThenScore = _parse(
        [{"role": "user", "content": prompt}], _FeedbackThenScore
    )
    return RunResult(score=_clamp(parsed.score), feedback=parsed.feedback)


def _run_dsf_once(proposal: str, exemplars: list[dict]) -> RunResult:
    p1, p2 = decomp.build_scoring_first(
        config.TASK_DESCRIPTION, config.RUBRIC, exemplars, proposal
    )
    messages: list[dict] = [{"role": "user", "content": p1}]
    score_parsed: _ScoreOnly = _parse(messages, _ScoreOnly)
    score = _clamp(score_parsed.score)

    messages.append({"role": "assistant", "content": json.dumps({"score": score})})
    messages.append({"role": "user", "content": p2})
    feedback_parsed: _FeedbackOnly = _parse(messages, _FeedbackOnly)

    return RunResult(score=score, feedback=feedback_parsed.feedback)


def _run_dff_once(proposal: str, exemplars: list[dict]) -> RunResult:
    p1, p2 = decomp.build_feedback_first(
        config.TASK_DESCRIPTION, config.RUBRIC, exemplars, proposal
    )
    messages: list[dict] = [{"role": "user", "content": p1}]
    feedback_parsed: _FeedbackOnly = _parse(messages, _FeedbackOnly)

    messages.append(
        {"role": "assistant", "content": json.dumps({"feedback": feedback_parsed.feedback})}
    )
    messages.append({"role": "user", "content": p2})
    score_parsed: _ScoreOnly = _parse(messages, _ScoreOnly)

    return RunResult(score=_clamp(score_parsed.score), feedback=feedback_parsed.feedback)


_RUNNERS = {
    "C-SF": _run_csf_once,
    "C-FF": _run_cff_once,
    "D-SF": _run_dsf_once,
    "D-FF": _run_dff_once,
}


# ---------------------------------------------------------------------------
# Multi-run aggregation
# ---------------------------------------------------------------------------

@dataclass
class AggregatedResult:
    """Average score across N_RUNS; feedback from the first run."""
    config_name: str
    proposal_id: str
    mean_score: float
    std_score: float
    feedback: str
    all_scores: list[float] = field(default_factory=list)


def run_proposal(
    proposal: dict,
    exemplars: list[dict],
    configs: list[str] | None = None,
    n_runs: int = config.N_RUNS,
) -> dict[str, AggregatedResult]:
    """
    Run all (or specified) configurations for a single proposal.

    Args:
        proposal: dict with 'id' and 'text' keys.
        exemplars: list of few-shot exemplar dicts ('text', 'score').
        configs: subset of CONFIG_NAMES to run; None = all four.
        n_runs: number of times to repeat each config (paper uses 5).

    Returns:
        dict mapping config name -> AggregatedResult
    """
    if configs is None:
        configs = CONFIG_NAMES

    results: dict[str, AggregatedResult] = {}

    for cfg in configs:
        runner = _RUNNERS[cfg]
        scores: list[float] = []
        first_feedback = ""

        for run_idx in range(n_runs):
            # Shuffle exemplars each run to minimize ordering bias (paper §3.3)
            shuffled = exemplars.copy()
            random.shuffle(shuffled)
            run_result = runner(proposal["text"], shuffled)
            scores.append(run_result.score)
            if run_idx == 0:
                first_feedback = run_result.feedback

        import numpy as np
        results[cfg] = AggregatedResult(
            config_name=cfg,
            proposal_id=proposal["id"],
            mean_score=float(np.mean(scores)),
            std_score=float(np.std(scores)),
            feedback=first_feedback,
            all_scores=scores,
        )

    return results
