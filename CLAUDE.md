# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python implementation of the paper:
> AlGhamdi et al. (2026). "Leveraging prompt-based LLMs for automated scoring and feedback generation in higher education." *Computers & Education* 243, 105511.

The system compares four GPT-4o prompting configurations for automated essay scoring (AES) and learner-centered feedback generation on postgraduate data-science proposals.

## Setup

```bash
pip install -r requirements.txt
# Place your OpenAI key in key.txt (preferred), or set OPENAI_API_KEY env var as fallback.
echo "sk-..." > key.txt
```

## Running experiments

```bash
# Quick smoke-test on built-in synthetic data (1 API call per proposal per config):
python run_experiment.py --n_runs 1 --skip_feedback

# Full paper replication (5 runs, all 4 configs, with feedback evaluation):
python run_experiment.py --data path/to/data.json --n_runs 5

# Specific configs only:
python run_experiment.py --configs C-SF C-FF --n_runs 1

# Reload saved results and recompute metrics without API calls:
python run_experiment.py --results results/run_<timestamp>.json --metrics_only
```

Results JSON is written to `results/run_<timestamp>.json` automatically.

## Architecture

### Four prompt configurations (paper §3.4)

| Code | Name | Structure |
|------|------|-----------|
| `C-SF` | Composition-Scoring-First | Single prompt: score → feedback |
| `C-FF` | Composition-Feedback-First | Single prompt: feedback → score |
| `D-SF` | Decomposition-Scoring-First | Two prompts: turn 1 = score, turn 2 = feedback |
| `D-FF` | Decomposition-Feedback-First | Two prompts: turn 1 = feedback, turn 2 = score |

### Key files

- **[config.py](config.py)** — model, temperature, rubric, task description, LCF component names.
- **[prompts/base.py](prompts/base.py)** — role string, learner-centered feedback definition, exemplar formatter, context block builder.
- **[prompts/composition.py](prompts/composition.py)** — `build_scoring_first` / `build_feedback_first` for single-prompt configs.
- **[prompts/decomposition.py](prompts/decomposition.py)** — same, returns `(prompt1, prompt2)` for two-turn configs.
- **[pipeline.py](pipeline.py)** — calls GPT-4o with OpenAI Structured Outputs (Pydantic schemas), runs N_RUNS times per proposal, averages scores.
- **[evaluation/scoring.py](evaluation/scoring.py)** — MAE, RMSE, RMC (rank-order consensus), paired permutation tests, BCa bootstrap CIs.
- **[evaluation/feedback.py](evaluation/feedback.py)** — sentence-level GPT-4o classifier for the 7 Learner-Centered Feedback components; computes proportion of proposals containing each component.
- **[data/proposals_214.json](data/proposals_214.json)** — 214 synthetic proposals (107 High / 107 Low) + 4 exemplars; the default dataset used when `--data` is not specified.
- **[data/generate_dataset.py](data/generate_dataset.py)** — script that generated `proposals_214.json`; re-run to regenerate with a different random seed.
- **[run_experiment.py](run_experiment.py)** — CLI entrypoint; orchestrates pipeline → metrics → significance tests → feedback evaluation → console output.

### Data format

Custom datasets are loaded from a JSON file with two keys:
```json
{
  "proposals": [
    {"id": "p001", "text": "...", "human_score": 12.5, "performance_group": "High"}
  ],
  "exemplars": [
    {"id": "e001", "text": "...", "score": 13, "performance_group": "High"}
  ]
}
```
`performance_group` is `"High"` (HD or D) or `"Low"` (C, P, or N), following the paper's binary grouping. The paper uses 4 exemplars (2 High + 2 Low) selected from outside the 214-proposal evaluation set.

### Prompt engineering choices (paper §3.3)

- **Role**: "an experienced teacher in a master's-level data science course"
- **CoT**: "Let's think step by step"
- **Few-shot**: 4 exemplars shuffled each run to reduce ordering bias
- **Delimiters**: triple-quotes `"""` around each long text block
- **Structured outputs**: OpenAI `beta.chat.completions.parse()` with Pydantic schemas
- **Temperature = 0, top_p = 0.01** to minimize randomness

### Evaluation (paper §3.5)

**Scoring**: MAE, RMSE, RMC computed overall and split by performance group. Pairwise significance via two-sided paired permutation test (10 000 resamples); effect size via BCa bootstrap 95% CI.

**Feedback**: The paper uses the Aldino et al. (2024) BERT classifier (not public). This implementation approximates it with GPT-4o sentence-level classification against the same 7 LCF components. Metric: proportion of feedback instances containing at least one sentence per component.

## API cost considerations

Each `--n_runs 5` call on 214 proposals × 4 configs ≈ 5 680 API calls (decomposition configs need 2 calls per run). Use `--n_runs 1` and `--skip_feedback` for cheap development runs.
