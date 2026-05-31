"""
Scoring evaluation metrics from the paper (Section 3.5.1):

- MAE  : Mean Absolute Error
- RMSE : Root Mean Squared Error
- RMC  : Relative Merit Consensus (rank-order consistency, Chang & Ginter 2024)

Statistical tests:
- Shapiro-Wilk normality test on error distributions (§3.5.1 / Appendix B)
- Two-sided paired permutation test (10 000 resamples) on absolute / squared errors
- BCa bootstrap confidence intervals around mean differences (Bestgen 2022)

Additional analyses (§5.1):
- Spearman correlation between text length and scores (human and GPT)
- Length-controlled MAE: same-score pairs split by word count
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, shapiro, spearmanr, ttest_rel
from itertools import combinations


# ---------------------------------------------------------------------------
# Point-estimate metrics
# ---------------------------------------------------------------------------

def compute_mae(predictions: list[float], targets: list[float]) -> float:
    p, t = np.array(predictions), np.array(targets)
    return float(np.mean(np.abs(p - t)))


def compute_rmse(predictions: list[float], targets: list[float]) -> float:
    p, t = np.array(predictions), np.array(targets)
    return float(np.sqrt(np.mean((p - t) ** 2)))


def compute_rmc(predictions: list[float], targets: list[float]) -> float:
    """
    Relative Merit Consensus: for every ordered pair (i, j) where human_score[i] >
    human_score[j], count it as concordant when model_score[i] >= model_score[j].
    RMC = concordant / total_ordered_pairs.
    """
    p, t = np.array(predictions), np.array(targets)
    n = len(p)
    concordant = total = 0
    for i in range(n):
        for j in range(n):
            if t[i] > t[j]:
                total += 1
                if p[i] >= p[j]:
                    concordant += 1
    return concordant / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

def permutation_test(
    errors_a: np.ndarray,
    errors_b: np.ndarray,
    n_resamples: int = 10_000,
    seed: int | None = 42,
) -> float:
    """
    Two-sided paired permutation test on the mean difference of per-sample errors.

    H0: no difference in mean error between prompt A and prompt B.
    Returns the two-sided p-value.
    """
    rng = np.random.default_rng(seed)
    observed = np.mean(errors_a) - np.mean(errors_b)
    diffs = errors_a - errors_b
    count = 0
    for _ in range(n_resamples):
        signs = rng.choice([-1.0, 1.0], size=len(diffs))
        if abs(np.mean(signs * diffs)) >= abs(observed):
            count += 1
    return count / n_resamples


def bca_bootstrap_ci(
    errors_a: np.ndarray,
    errors_b: np.ndarray,
    n_bootstrap: int = 10_000,
    ci: float = 0.95,
    seed: int | None = 42,
) -> tuple[float, float]:
    """
    BCa (bias-corrected and accelerated) bootstrap CI for
    mean(errors_a) - mean(errors_b).

    Returns (lower, upper) bounds of the CI.
    """
    rng = np.random.default_rng(seed)
    diffs = errors_a - errors_b
    n = len(diffs)
    observed_mean = float(np.mean(diffs))

    # Bootstrap distribution
    boot_means = np.array([
        np.mean(rng.choice(diffs, size=n, replace=True))
        for _ in range(n_bootstrap)
    ])

    # Bias-correction factor z0
    prop_below = np.mean(boot_means < observed_mean)
    prop_below = np.clip(prop_below, 1e-6, 1 - 1e-6)
    z0 = float(norm.ppf(prop_below))

    # Acceleration factor via jackknife
    jack_means = np.array([np.mean(np.delete(diffs, i)) for i in range(n)])
    jack_mean = np.mean(jack_means)
    deviations = jack_mean - jack_means
    num = float(np.sum(deviations ** 3))
    den = 6.0 * float(np.sum(deviations ** 2) ** 1.5)
    a = num / den if den != 0 else 0.0

    alpha = 1.0 - ci

    def _adjusted_pct(z_crit: float) -> float:
        inner = z0 + z_crit
        p = float(norm.cdf(z0 + inner / (1.0 - a * inner)))
        p = np.clip(p, 0.0, 1.0)
        return float(np.percentile(boot_means, 100.0 * p))

    lower = _adjusted_pct(float(norm.ppf(alpha / 2)))
    upper = _adjusted_pct(float(norm.ppf(1 - alpha / 2)))
    return lower, upper


# ---------------------------------------------------------------------------
# Full evaluation table
# ---------------------------------------------------------------------------

def evaluate_all_configs(
    results_by_config: dict[str, list[float]],  # config_name -> list of mean scores
    human_scores: list[float],
    performance_groups: list[str],              # "High" or "Low" per proposal
) -> dict:
    """
    Compute MAE, RMSE, RMC per config, split by performance group and overall.

    Args:
        results_by_config: {config: [score_for_proposal_0, score_for_proposal_1, ...]}
        human_scores: ground-truth scores aligned with the score lists above
        performance_groups: "High" or "Low" per proposal

    Returns:
        Nested dict: {config: {group: {metric: value}}}
    """
    hs = np.array(human_scores)
    groups = np.array(performance_groups)
    masks = {
        "All":  np.ones(len(hs), dtype=bool),
        "High": groups == "High",
        "Low":  groups == "Low",
    }

    out: dict = {}
    for cfg, preds in results_by_config.items():
        ps = np.array(preds)
        out[cfg] = {}
        for group_name, mask in masks.items():
            p_sub = ps[mask].tolist()
            h_sub = hs[mask].tolist()
            out[cfg][group_name] = {
                "MAE":  compute_mae(p_sub, h_sub),
                "RMSE": compute_rmse(p_sub, h_sub),
                "RMC":  compute_rmc(p_sub, h_sub),
                "n":    int(mask.sum()),
            }
    return out


def evaluate_all_configs_with_sd(
    all_scores_by_config: dict[str, list[list[float]]],
    human_scores: list[float],
    performance_groups: list[str],
) -> dict:
    """
    Replicate Table 1 of the paper: compute MAE, RMSE, and RMC separately for
    each of the N individual runs, then report mean ± SD of those run-level values.

    Args:
        all_scores_by_config: {config: [[run0..runN-1 scores for proposal 0],
                                        [run0..runN-1 scores for proposal 1], ...]}
        human_scores: ground-truth scores, one per proposal.
        performance_groups: "High" or "Low" per proposal.

    Returns:
        Nested dict: {config: {group: {metric: (mean, sd), "n": int}}}
        where mean and sd are computed across the N run-level metric values.
    """
    hs = np.array(human_scores)
    groups = np.array(performance_groups)
    masks = {
        "All":  np.ones(len(hs), dtype=bool),
        "High": groups == "High",
        "Low":  groups == "Low",
    }

    out: dict = {}
    for cfg, per_proposal in all_scores_by_config.items():
        n_proposals = len(per_proposal)
        n_runs = len(per_proposal[0])

        out[cfg] = {}
        for group_name, mask in masks.items():
            h_sub = hs[mask].tolist()
            run_maes, run_rmses, run_rmcs = [], [], []

            for k in range(n_runs):
                run_k = np.array([per_proposal[i][k] for i in range(n_proposals)])[mask].tolist()
                run_maes.append(compute_mae(run_k, h_sub))
                run_rmses.append(compute_rmse(run_k, h_sub))
                run_rmcs.append(compute_rmc(run_k, h_sub))

            out[cfg][group_name] = {
                "MAE":  (float(np.mean(run_maes)),  float(np.std(run_maes))),
                "RMSE": (float(np.mean(run_rmses)), float(np.std(run_rmses))),
                "RMC":  (float(np.mean(run_rmcs)),  float(np.std(run_rmcs))),
                "n":    int(mask.sum()),
            }
    return out


def pairwise_significance_table(
    results_by_config: dict[str, list[float]],
    human_scores: list[float],
    performance_groups: list[str],
    metric: str = "RMSE",
    n_resamples: int = 10_000,
) -> dict:
    """
    Run pairwise permutation tests and BCa CIs for all config pairs.

    Returns:
        {group: {(cfg_row, cfg_col): {"diff": float, "ci": (lo, hi), "p": float}}}
    """
    hs = np.array(human_scores)
    groups = np.array(performance_groups)
    masks = {"All": np.ones(len(hs), dtype=bool), "High": groups == "High", "Low": groups == "Low"}

    cfg_names = list(results_by_config.keys())
    out: dict = {}

    for group_name, mask in masks.items():
        h_sub = hs[mask]
        out[group_name] = {}
        for cfg_a, cfg_b in combinations(cfg_names, 2):
            pa = np.array(results_by_config[cfg_a])[mask]
            pb = np.array(results_by_config[cfg_b])[mask]

            if metric == "RMSE":
                ea = (pa - h_sub) ** 2
                eb = (pb - h_sub) ** 2
            else:  # MAE
                ea = np.abs(pa - h_sub)
                eb = np.abs(pb - h_sub)

            diff = float(np.mean(ea) - np.mean(eb))
            p = permutation_test(ea, eb, n_resamples=n_resamples)
            ci = bca_bootstrap_ci(ea, eb, n_bootstrap=n_resamples)
            out[group_name][(cfg_a, cfg_b)] = {"diff": diff, "ci": ci, "p": p}

    return out


# ---------------------------------------------------------------------------
# §3.5.1 / Appendix B  –  Shapiro–Wilk normality test
# ---------------------------------------------------------------------------

def shapiro_wilk_test(
    results_by_config: dict[str, list[float]],
    human_scores: list[float],
) -> dict[str, dict[str, dict]]:
    """
    Run Shapiro–Wilk normality tests on per-proposal absolute errors (MAE)
    and squared errors (RMSE) for every prompt configuration.

    The paper (§3.5.1) uses this to justify the choice of permutation tests
    over parametric t-tests ("a distributional property confirmed in our data
    by Shapiro–Wilk tests and Q–Q plot results, Appendix B").

    Returns:
        {config: {"absolute_errors": {"W": float, "p": float, "normal": bool},
                  "squared_errors":  {"W": float, "p": float, "normal": bool}}}
    """
    hs = np.array(human_scores)
    out: dict = {}
    for cfg, preds in results_by_config.items():
        ps = np.array(preds)
        abs_err = np.abs(ps - hs)
        sq_err  = (ps - hs) ** 2
        out[cfg] = {}
        for label, errors in [("absolute_errors", abs_err), ("squared_errors", sq_err)]:
            w, p = shapiro(errors)
            out[cfg][label] = {
                "W":      float(w),
                "p":      float(p),
                "normal": bool(p >= 0.05),   # fail to reject H0 of normality
            }
    return out


# ---------------------------------------------------------------------------
# §5.1  –  Spearman correlation: text length vs. scores
# ---------------------------------------------------------------------------

def spearman_length_correlation(
    texts: list[str],
    human_scores: list[float],
    pred_scores_by_config: dict[str, list[float]],
) -> dict[str, dict[str, float]]:
    """
    Compute Spearman rank correlation between proposal word count and scores
    for human ratings and for each prompt configuration's GPT-assigned scores.

    Paper §5.1: "for human scores, the Spearman correlation with essay length
    was approximately 0.25 (p < .001), while it ranged from 0.20 to 0.28
    (p < .01) for GPT-assigned scores."

    Returns:
        {source: {"rho": float, "p": float}}
        where source is "human" or a config name (e.g. "C-SF").
    """
    lengths = np.array([len(t.split()) for t in texts])
    out: dict = {}

    rho, p = spearmanr(lengths, human_scores)
    out["human"] = {"rho": float(rho), "p": float(p)}

    for cfg, preds in pred_scores_by_config.items():
        rho, p = spearmanr(lengths, preds)
        out[cfg] = {"rho": float(rho), "p": float(p)}

    return out


# ---------------------------------------------------------------------------
# §5.1  –  Length-controlled MAE sanity check
# ---------------------------------------------------------------------------

def length_controlled_mae(
    texts: list[str],
    human_scores: list[float],
    pred_scores_by_config: dict[str, list[float]],
    score_bin_width: float = 1.0,
) -> dict[str, dict[str, float]]:
    """
    Sanity check from paper §5.1: group proposals by rounded human score
    (controlling for quality), split each group at the median word count
    into "longer" and "shorter" halves, then compare MAE.

    Paper §5.1: "GPT scores for longer submissions had a higher MAE (1.92)
    than shorter submissions (1.71), although a paired t-test confirmed that
    this difference was not statistically significant."

    Args:
        texts:               proposal text strings (for word-count derivation).
        human_scores:        ground-truth scores per proposal.
        pred_scores_by_config: {config: [mean_score per proposal]}.
        score_bin_width:     rounding unit for grouping scores (default 1.0).

    Returns:
        {config: {"mae_longer":  float,
                  "mae_shorter": float,
                  "n_longer":    int,
                  "n_shorter":   int,
                  "t_stat":      float,
                  "p_value":     float}}
    """
    lengths = np.array([len(t.split()) for t in texts])
    hs      = np.array(human_scores)
    binned  = np.round(hs / score_bin_width) * score_bin_width

    out: dict = {}
    for cfg, preds in pred_scores_by_config.items():
        ps     = np.array(preds)
        errors = np.abs(ps - hs)

        longer_errors:  list[float] = []
        shorter_errors: list[float] = []

        for score_val in np.unique(binned):
            mask = binned == score_val
            if mask.sum() < 2:
                continue
            grp_lengths = lengths[mask]
            grp_errors  = errors[mask]
            median_len  = float(np.median(grp_lengths))

            long_mask  = grp_lengths >= median_len
            short_mask = grp_lengths <  median_len
            longer_errors.extend(grp_errors[long_mask].tolist())
            shorter_errors.extend(grp_errors[short_mask].tolist())

        la = np.array(longer_errors)
        sa = np.array(shorter_errors)

        mae_l = float(np.mean(la)) if len(la) > 0 else float("nan")
        mae_s = float(np.mean(sa)) if len(sa) > 0 else float("nan")

        # Paired t-test on the minimum-overlap length
        min_n = min(len(la), len(sa))
        if min_n >= 2:
            t_stat, p_val = ttest_rel(la[:min_n], sa[:min_n])
        else:
            t_stat, p_val = float("nan"), float("nan")

        out[cfg] = {
            "mae_longer":  mae_l,
            "mae_shorter": mae_s,
            "n_longer":    len(la),
            "n_shorter":   len(sa),
            "t_stat":      float(t_stat),
            "p_value":     float(p_val),
        }
    return out
