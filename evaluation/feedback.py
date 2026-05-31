"""
Feedback evaluation using the Learner-Centered Feedback framework (Ryan et al., 2023).

The paper uses the BERT-based multi-label classifier from Aldino et al. (2024), which
is not publicly available. This module approximates it with GPT-4o sentence-level
classification, following the same evaluation logic:

1. Split feedback into sentences (NLTK).
2. Classify each sentence against the 7 learner-centered components.
3. A feedback instance "has" component X if at least one sentence is labelled X.
4. Report the proportion of instances (across N proposals) that include each component.
"""

from __future__ import annotations

import json

import nltk
from openai import OpenAI
from pydantic import BaseModel, Field

import config

# Download punkt if not already present
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

client = OpenAI(api_key=config.OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Component descriptions fed to the classifier prompt
# ---------------------------------------------------------------------------

_COMPONENT_DESCRIPTIONS: dict[str, str] = {
    "future_improvement": (
        "Offers guidance for improving future work or future tasks."
    ),
    "learning_outcomes": (
        "Aligns the feedback with broader academic or professional skills "
        "and learning outcomes."
    ),
    "strengths_weaknesses": (
        "Identifies specific strengths or areas for improvement in the current work."
    ),
    "performance_summary": (
        "Provides an overall assessment of performance relative to the assessment criteria."
    ),
    "active_role": (
        "Encourages the student to take an active role in their own learning, "
        "such as seeking resources, revisiting material, or engaging with the feedback."
    ),
    "affirm_encourage": (
        "Explicitly affirms or encourages the student in an emotional or motivational sense "
        "(e.g., 'Well done', 'Great effort', 'Your work is appreciated')."
    ),
    "strengthen_relationship": (
        "Fosters a supportive connection between the student and teacher, "
        "such as inviting the student to reach out or expressing care for their progress."
    ),
}


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class _SentenceLabels(BaseModel):
    future_improvement:      bool = Field(description="Future Impact — Future Improvement")
    learning_outcomes:       bool = Field(description="Future Impact — Learning Outcomes")
    strengths_weaknesses:    bool = Field(description="Sensemaking — Strengths and Weaknesses")
    performance_summary:     bool = Field(description="Sensemaking — Performance Summary")
    active_role:             bool = Field(description="Agency — Active Role")
    affirm_encourage:        bool = Field(description="Agency — Affirm and Encourage")
    strengthen_relationship: bool = Field(description="Agency — Strengthen Relationship")


# ---------------------------------------------------------------------------
# Core classification functions
# ---------------------------------------------------------------------------

def classify_sentence(sentence: str) -> dict[str, bool]:
    """Return binary label for each component for a single sentence."""
    desc_lines = "\n".join(
        f"  - {key}: {desc}"
        for key, desc in _COMPONENT_DESCRIPTIONS.items()
    )
    prompt = (
        "You are a feedback researcher. For each learner-centered feedback component "
        "below, decide whether the following sentence expresses that component "
        "(true) or not (false).\n\n"
        f"Components:\n{desc_lines}\n\n"
        f'Sentence: "{sentence.strip()}"'
    )
    response = client.beta.chat.completions.parse(
        model=config.MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        top_p=0.01,
        response_format=_SentenceLabels,
    )
    return response.choices[0].message.parsed.model_dump()


def classify_feedback(feedback_text: str) -> dict[str, bool]:
    """
    Classify an entire feedback string at the document level.
    A component is present if at least one sentence contains it.
    """
    try:
        sentences = nltk.sent_tokenize(feedback_text)
    except Exception:
        sentences = [s.strip() for s in feedback_text.split(".") if s.strip()]

    doc_labels: dict[str, bool] = {k: False for k in _COMPONENT_DESCRIPTIONS}
    for sentence in sentences:
        if not sentence.strip():
            continue
        sent_labels = classify_sentence(sentence)
        for k, v in sent_labels.items():
            if v:
                doc_labels[k] = True

    return doc_labels


# ---------------------------------------------------------------------------
# Aggregate over a list of feedback strings
# ---------------------------------------------------------------------------

def evaluate_feedback_list(
    feedback_list: list[str],
    verbose: bool = False,
    workers: int = 1,
) -> dict[str, float]:
    """
    For each component, compute the proportion of feedback instances (across the list)
    that include at least one sentence with that component.

    This mirrors the paper's Figure 3 metric.

    Args:
        workers: number of parallel threads for document classification (default 1).
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    n = len(feedback_list)
    component_counts: dict[str, int] = {k: 0 for k in _COMPONENT_DESCRIPTIONS}
    lock = threading.Lock()
    done = 0

    def _classify_one(idx_text):
        idx, text = idx_text
        return idx, classify_feedback(text)

    if workers <= 1:
        for i, feedback in enumerate(feedback_list):
            if verbose:
                print(f"  Classifying feedback {i + 1}/{n}...", flush=True)
            doc_labels = classify_feedback(feedback)
            for k, present in doc_labels.items():
                if present:
                    component_counts[k] += 1
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_classify_one, (i, fb)): i
                       for i, fb in enumerate(feedback_list)}
            for future in as_completed(futures):
                _, doc_labels = future.result()
                with lock:
                    nonlocal_done = done + 1
                    for k, present in doc_labels.items():
                        if present:
                            component_counts[k] += 1
                    if verbose:
                        print(f"  done {nonlocal_done}/{n}", flush=True)

    return {k: count / n for k, count in component_counts.items()}


def compare_configs_feedback(
    feedback_by_config: dict[str, list[str]],
    verbose: bool = False,
    workers: int = 1,
) -> dict[str, dict[str, float]]:
    """
    Run evaluate_feedback_list for each config and return proportions.

    Returns:
        {config_name: {component: proportion}}
    """
    out: dict[str, dict[str, float]] = {}
    for cfg, feedback_list in feedback_by_config.items():
        if verbose:
            print(f"\nEvaluating feedback for config {cfg} ({len(feedback_list)} instances)...")
        out[cfg] = evaluate_feedback_list(feedback_list, verbose=verbose, workers=workers)
    return out
