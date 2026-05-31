import os
from pathlib import Path

def _load_api_key() -> str:
    key_file = Path(__file__).parent / "key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    return os.environ.get("OPENAI_API_KEY", "")

OPENAI_API_KEY: str = _load_api_key()
MODEL: str = "gpt-4o"
TEMPERATURE: float = 0.0
TOP_P: float = 0.01
N_RUNS: int = 5  # times each prompt is run per proposal; results are averaged

SCORE_MIN: int = 0
SCORE_MAX: int = 15

ROOT_DIR = Path(__file__).parent
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

TASK_DESCRIPTION = (
    "Students are required to submit a proposal for a data science project of their choice, "
    "comprising two sections: (1) the Project Description, which outlines project goals and "
    "relevant data professionals' roles, and (2) the Business Model, which describes the "
    "target beneficiaries, value proposition, and anticipated challenges."
)

RUBRIC = (
    "1. Clarity of goals: Proposal clearly states what the project aims to achieve and why.\n"
    "2. Relevance to data science: Project is grounded in data science concepts and methods.\n"
    "3. Articulation of business value: Business model and real-world impact are well-described.\n"
    "4. Creativity: Project shows originality and innovation.\n"
    "5. Overall clarity: Proposal is well-organized, coherent, and free of ambiguity."
)

# Learner-Centered Feedback framework (Ryan et al., 2023)
LEARNER_CENTERED_COMPONENTS: dict[str, str] = {
    "future_improvement":      "Future Impact — Future Improvement",
    "learning_outcomes":       "Future Impact — Learning Outcomes and Skill Development",
    "strengths_weaknesses":    "Sensemaking — Strengths and Weaknesses",
    "performance_summary":     "Sensemaking — Performance Summary",
    "active_role":             "Agency — Active Role",
    "affirm_encourage":        "Agency — Affirm and Encourage",
    "strengthen_relationship": "Agency — Strengthen Relationship",
}

GRADE_BANDS: dict[str, tuple[int, int]] = {
    "HD": (80, 100),
    "D":  (70, 79),
    "C":  (60, 69),
    "P":  (50, 59),
    "N":  (0,  49),
}
