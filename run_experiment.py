"""
Main experiment runner.

Usage examples
--------------
# Run all 4 configs on the built-in synthetic data (default, 1 run to save API cost):
    python run_experiment.py --n_runs 1

# Run on a custom JSON dataset, all configs, 5 runs per proposal:
    python run_experiment.py --data path/to/data.json --n_runs 5

# Run only two specific configs:
    python run_experiment.py --configs C-SF C-FF --n_runs 1

# Skip feedback evaluation (saves many API calls):
    python run_experiment.py --skip_feedback --n_runs 1

# Resume from an existing results file (re-uses cached scores, re-evaluates metrics):
    python run_experiment.py --results results/run_20240101_120000.json --metrics_only

Data JSON format
----------------
{
  "proposals": [
    {"id": "p001", "text": "...", "human_score": 12.5, "performance_group": "High"},
    ...
  ],
  "exemplars": [
    {"id": "e001", "text": "...", "score": 13, "performance_group": "High"},
    ...
  ]
}
"""

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

import config
from pipeline import run_proposal, CONFIG_NAMES
from evaluation.scoring import (evaluate_all_configs_with_sd,
                                pairwise_significance_table,
                                shapiro_wilk_test,
                                spearman_length_correlation,
                                length_controlled_mae)
from evaluation.feedback import compare_configs_feedback

_DEFAULT_DATA = config.ROOT_DIR / "data" / "proposals_214.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_data(path: str | None) -> tuple[list[dict], list[dict]]:
    target = Path(path) if path else _DEFAULT_DATA
    with open(target) as f:
        d = json.load(f)
    return d["proposals"], d["exemplars"]


def _save_results(results: dict, out_dir: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"run_{ts}.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_file}")
    return out_file


def _print_scoring_table(metrics: dict) -> None:
    """Print Table 1 from the paper: mean ± SD across N runs per metric."""
    configs = list(metrics.keys())
    groups = ["High", "Low", "All"]
    col_w = 16  # width for each "mean ± sd" cell
    hdr_w = col_w * 3

    print("\n" + "=" * (8 + hdr_w * 3))
    print("SCORING PERFORMANCE  (mean ± SD across runs, matching paper Table 1)")
    print("=" * (8 + hdr_w * 3))
    print(f"{'':8}" + "".join(f"{'─── ' + g + ' ───':^{hdr_w}}" for g in groups))
    print(f"{'Config':<8}" + "".join(
        f"{'MAE':>{col_w}}{'RMSE':>{col_w}}{'RMC':>{col_w}}" for _ in groups
    ))
    print("-" * (8 + hdr_w * 3))

    for cfg in configs:
        row = f"{cfg:<8}"
        for g in groups:
            m = metrics[cfg][g]
            for metric in ("MAE", "RMSE", "RMC"):
                mean, sd = m[metric]
                cell = f"{mean:.2f}±{sd:.2f}"
                row += f"{cell:>{col_w}}"
        print(row)
    print("=" * (8 + hdr_w * 3))


def _print_shapiro_wilk(sw: dict) -> None:
    """§3.5.1 / Appendix B — normality of error distributions."""
    print("\n" + "=" * 72)
    print("SHAPIRO-WILK NORMALITY TEST  (justifies permutation over t-test)")
    print("=" * 72)
    print(f"{'Config':<8}  {'Error type':<18}  {'W':>8}  {'p':>10}  Normal?")
    print("-" * 72)
    for cfg, parts in sw.items():
        for etype, vals in parts.items():
            label = "absolute (MAE)" if "absolute" in etype else "squared (RMSE)"
            normal = "yes (p≥.05)" if vals["normal"] else "NO  (p<.05)"
            print(f"{cfg:<8}  {label:<18}  {vals['W']:8.4f}  {vals['p']:10.4f}  {normal}")
    print("=" * 72)


def _print_spearman(corr: dict) -> None:
    """§5.1 — text length vs. score correlation."""
    print("\n" + "=" * 60)
    print("SPEARMAN CORRELATION — text length vs. score  (§5.1)")
    print("=" * 60)
    print(f"{'Source':<10}  {'rho':>8}  {'p':>10}  Sig?")
    print("-" * 60)
    for source, vals in corr.items():
        sig = ("***" if vals["p"] < 0.001 else
               "**"  if vals["p"] < 0.01  else
               "*"   if vals["p"] < 0.05  else "")
        print(f"{source:<10}  {vals['rho']:8.4f}  {vals['p']:10.4f}  {sig}")
    print("=" * 60)


def _print_length_mae(lm: dict) -> None:
    """§5.1 — length-controlled MAE sanity check."""
    print("\n" + "=" * 76)
    print("LENGTH-CONTROLLED MAE  (same-score pairs, longer vs shorter)  (§5.1)")
    print("=" * 76)
    print(f"{'Config':<8}  {'MAE longer':>12}  {'MAE shorter':>12}  "
          f"{'n_long':>7}  {'n_short':>8}  {'p':>10}  Sig?")
    print("-" * 76)
    for cfg, vals in lm.items():
        sig = ("***" if vals["p_value"] < 0.001 else
               "**"  if vals["p_value"] < 0.01  else
               "*"   if vals["p_value"] < 0.05  else "ns")
        print(f"{cfg:<8}  {vals['mae_longer']:12.4f}  {vals['mae_shorter']:12.4f}  "
              f"{vals['n_longer']:7d}  {vals['n_shorter']:8d}  "
              f"{vals['p_value']:10.4f}  {sig}")
    print("=" * 76)


def _print_feedback_table(feedback_metrics: dict) -> None:
    """Figure 3 comparison — LCF component proportions per config."""
    if not feedback_metrics:
        return

    # Paper Figure 3 values (%)
    paper_fig3 = {
        'C-SF': {'learning_outcomes':0.0,'future_improvement':100.0,'performance_summary':37.9,
                 'strengths_weaknesses':100.0,'active_role':9.3,'affirm_encourage':0.5,'strengthen_relationship':66.4},
        'C-FF': {'learning_outcomes':0.0,'future_improvement':100.0,'performance_summary':36.9,
                 'strengths_weaknesses':100.0,'active_role':24.8,'affirm_encourage':0.0,'strengthen_relationship':56.1},
        'D-SF': {'learning_outcomes':0.0,'future_improvement':100.0,'performance_summary':37.9,
                 'strengths_weaknesses':100.0,'active_role':11.2,'affirm_encourage':0.0,'strengthen_relationship':66.8},
        'D-FF': {'learning_outcomes':0.0,'future_improvement':100.0,'performance_summary':39.3,
                 'strengths_weaknesses':100.0,'active_role':32.7,'affirm_encourage':0.0,'strengthen_relationship':51.4},
    }
    component_labels = {
        'learning_outcomes':       'Learning Outcomes (FI)',
        'future_improvement':      'Future Improvement (FI)',
        'performance_summary':     'Performance Summary (SM)',
        'strengths_weaknesses':    'Strengths & Weaknesses (SM)',
        'active_role':             'Active Role (AG)',
        'affirm_encourage':        'Affirm & Encourage (AG)',
        'strengthen_relationship': 'Strengthen Relationship (AG)',
    }
    configs = list(feedback_metrics.keys())
    components = list(component_labels.keys())

    w = 9
    header_cfg = "".join(f"{c:>{w}}" for c in configs)
    header_pap = "".join(f"{'paper':>{w}}" for _ in configs)

    print("\n" + "=" * (35 + w * len(configs) * 2 + 4))
    print("FIGURE 3 — LCF COMPONENT PROPORTIONS  (% of proposals, ours vs. paper)")
    print("=" * (35 + w * len(configs) * 2 + 4))
    print(f"{'Component':<35}" + header_cfg + "  |" + header_pap)
    print(f"{'':35}" + "".join(f"{'ours':>{w}}" for _ in configs)
          + "  |" + "".join(f"{'paper':>{w}}" for _ in configs))
    print("-" * (35 + w * len(configs) * 2 + 4))
    for comp in components:
        label = component_labels[comp]
        row_ours  = "".join(f"{feedback_metrics[c].get(comp,0)*100:{w}.1f}" for c in configs)
        row_paper = "".join(
            f"{paper_fig3[c].get(comp,float('nan')):{w}.1f}"
            if c in paper_fig3 else f"{'N/A':>{w}}"
            for c in configs
        )
        print(f"{label:<35}{row_ours}  |{row_paper}")
    print("=" * (35 + w * len(configs) * 2 + 4))


def _print_significance_table(sig: dict, metric: str, configs: list[str]) -> None:
    """Format Tables 2 / 3 as the paper's row × column matrix."""

    # Paper Table 2 (RMSE) and Table 3 (MAE) values
    paper_tables = {
        "RMSE": {
            "High": {
                ("C-SF","C-FF"): (0.11,[0.06,0.17],"***"),
                ("C-SF","D-SF"): (0.23,[0.14,0.33],"***"),
                ("C-SF","D-FF"): (0.04,[-0.07,0.16],""),
                ("C-FF","D-SF"): (0.12,[0.05,0.20],"**"),
                ("C-FF","D-FF"): (-0.07,[-0.19,0.04],""),
                ("D-SF","D-FF"): (-0.19,[-0.31,-0.10],"***"),
            },
            "Low": {
                ("C-SF","C-FF"): (-0.04,[-0.11,0.04],""),
                ("C-SF","D-SF"): (-0.13,[-0.23,-0.07],"***"),
                ("C-SF","D-FF"): (-0.10,[-0.21,-0.03],"*"),
                ("C-FF","D-SF"): (-0.10,[-0.19,-0.02],"*"),
                ("C-FF","D-FF"): (-0.06,[-0.15,0.00],""),
                ("D-SF","D-FF"): (0.03,[-0.03,0.12],""),
            },
            "All": {
                ("C-SF","C-FF"): (0.03,[-0.02,0.08],""),
                ("C-SF","D-SF"): (0.03,[-0.04,0.09],""),
                ("C-SF","D-FF"): (-0.04,[-0.11,0.03],""),
                ("C-FF","D-SF"): (-0.002,[-0.07,0.06],""),
                ("C-FF","D-FF"): (-0.07,[-0.14,-0.01],"*"),
                ("D-SF","D-FF"): (-0.07,[-0.13,0.00],""),
            },
        },
        "MAE": {
            "High": {
                ("C-SF","C-FF"): (0.09,[0.05,0.15],"***"),
                ("C-SF","D-SF"): (0.18,[0.11,0.28],"***"),
                ("C-SF","D-FF"): (0.01,[-0.08,0.10],""),
                ("C-FF","D-SF"): (0.09,[0.03,0.17],"*"),
                ("C-FF","D-FF"): (-0.08,[-0.18,0.01],""),
                ("D-SF","D-FF"): (-0.17,[-0.27,-0.09],"***"),
            },
            "Low": {
                ("C-SF","C-FF"): (-0.07,[-0.14,0.02],""),
                ("C-SF","D-SF"): (-0.17,[-0.26,-0.08],"***"),
                ("C-SF","D-FF"): (-0.10,[-0.20,-0.03],"*"),
                ("C-FF","D-SF"): (-0.10,[-0.19,-0.01],"*"),
                ("C-FF","D-FF"): (-0.03,[-0.13,0.05],""),
                ("D-SF","D-FF"): (0.07,[-0.01,0.15],""),
            },
            "All": {
                ("C-SF","C-FF"): (0.01,[-0.04,0.06],""),
                ("C-SF","D-SF"): (0.01,[-0.06,0.08],""),
                ("C-SF","D-FF"): (-0.05,[-0.11,0.02],""),
                ("C-FF","D-SF"): (-0.002,[-0.06,0.06],""),
                ("C-FF","D-FF"): (-0.06,[-0.12,0.01],""),
                ("D-SF","D-FF"): (-0.05,[-0.12,0.00],""),
            },
        },
    }

    col_cfgs = [c for c in configs if c != configs[0]]  # all except first row config
    groups = ["High", "Low", "All"]

    print(f"\n{'='*90}")
    print(f"TABLE {'2' if metric=='RMSE' else '3'} — Pairwise {metric} permutation tests  "
          f"(row − col, 95% BCa CI)  [paper values in brackets]")
    print(f"{'='*90}")

    for grp in groups:
        print(f"\n  Group: {grp}")
        print(f"  {'Row':>5}  {'Col':>5}  {'Our diff':>10}  {'Our CI':>22}  {'Our p':>8}"
              f"  |  {'Paper diff':>11}  {'Paper CI':>20}  {'Sig':>5}")
        print(f"  {'-'*5}  {'-'*5}  {'-'*10}  {'-'*22}  {'-'*8}"
              f"  |  {'-'*11}  {'-'*20}  {'-'*5}")

        grp_data = sig.get(grp, {})
        for (a, b), stats in grp_data.items():
            diff = stats["diff"]
            lo, hi = stats["ci"]
            p = stats["p"]
            stars = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else ""
            our_str = f"{diff:+.3f}  [{lo:+.3f},{hi:+.3f}]  {p:.3f}{stars}"

            # lookup paper value
            pap = paper_tables.get(metric,{}).get(grp,{}).get((a,b))
            if pap:
                pd, pci, psig = pap
                pap_str = f"{pd:+.3f}  [{pci[0]:+.3f},{pci[1]:+.3f}]  {psig}"
            else:
                pap_str = "N/A"

            print(f"  {a:>5}  {b:>5}  {diff:+10.3f}  [{lo:+.3f},{hi:+.3f}]  {p:8.3f}{stars}"
                  f"  |  {pap_str}")
    print(f"{'='*90}")


def _print_significance(sig: dict, metric: str) -> None:
    print(f"\n--- Pairwise permutation test on {metric} differences ---")
    for group, pairs in sig.items():
        print(f"\n  Group: {group}")
        for (a, b), stats in pairs.items():
            p = stats["p"]
            lo, hi = stats["ci"]
            stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            print(
                f"    {a} vs {b}: diff={stats['diff']:+.3f}  "
                f"95%CI=[{lo:.3f}, {hi:.3f}]  p={p:.3f}{stars}"
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="AES + feedback experiment runner")
    parser.add_argument("--data",          type=str,  default=None,
                        help="Path to dataset JSON file (default: data/proposals_214.json)")
    parser.add_argument("--configs",       nargs="+", default=CONFIG_NAMES,
                        choices=CONFIG_NAMES, help="Prompt configurations to run")
    parser.add_argument("--n_runs",        type=int,  default=config.N_RUNS,
                        help="Number of API calls per proposal per config (paper uses 5)")
    parser.add_argument("--skip_feedback", action="store_true",
                        help="Skip feedback classification (saves many API calls)")
    parser.add_argument("--results",          type=str,  default=None,
                        help="Path to existing results JSON to load instead of running pipeline")
    parser.add_argument("--metrics_only",     action="store_true",
                        help="Only compute metrics from --results file, skip API calls")
    parser.add_argument("--out_dir",          type=str,  default=str(config.RESULTS_DIR))
    parser.add_argument("--workers",          type=int,  default=5,
                        help="Parallel workers for proposal processing (default 5)")
    parser.add_argument("--checkpoint_every", type=int,  default=20,
                        help="Save a checkpoint every N proposals (default 20)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # Load or run pipeline
    # -----------------------------------------------------------------------
    if args.results and args.metrics_only:
        print(f"Loading existing results from {args.results}")
        with open(args.results) as f:
            saved = json.load(f)
        proposals = saved["proposals"]
        raw_results = saved["raw_results"]
    else:
        proposals, exemplars = _load_data(args.data)

        api_calls = len(proposals) * args.n_runs * (
            sum(2 if c in ("D-SF", "D-FF") else 1 for c in args.configs)
        )
        print(
            f"\nRunning experiment: {len(proposals)} proposals × "
            f"{len(args.configs)} configs × {args.n_runs} runs"
            f"  ≈ {api_calls} API calls  (workers={args.workers})\n"
        )

        raw_results: dict = {cfg: {} for cfg in args.configs}
        lock = threading.Lock()
        completed = 0

        def _process(proposal: dict) -> tuple[str, dict | None, str | None]:
            pid = proposal["id"]
            try:
                result = run_proposal(
                    proposal, exemplars,
                    configs=args.configs, n_runs=args.n_runs,
                )
                row = {
                    cfg: {
                        "mean_score": agg.mean_score,
                        "std_score":  agg.std_score,
                        "all_scores": agg.all_scores,
                        "feedback":   agg.feedback,
                    }
                    for cfg, agg in result.items()
                }
                return pid, row, None
            except Exception as e:
                return pid, None, str(e)

        ckpt_path = out_dir / "checkpoint.json"

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(_process, p): p for p in proposals}
            pbar = tqdm(as_completed(futures), total=len(proposals), desc="Proposals")
            for future in pbar:
                pid, row, err = future.result()
                if err:
                    print(f"\n  ERROR on {pid}: {err}", file=sys.stderr)
                    continue
                with lock:
                    for cfg, data in row.items():
                        raw_results[cfg][pid] = data
                    completed += 1
                    if completed % args.checkpoint_every == 0:
                        ckpt = {
                            "timestamp":   datetime.now().isoformat(),
                            "configs":     args.configs,
                            "n_runs":      args.n_runs,
                            "proposals":   proposals,
                            "exemplars":   exemplars,
                            "raw_results": raw_results,
                        }
                        with open(ckpt_path, "w") as f:
                            json.dump(ckpt, f)
                        pbar.set_postfix({"saved": completed})

        # Final save
        save_payload = {
            "timestamp":   datetime.now().isoformat(),
            "configs":     args.configs,
            "n_runs":      args.n_runs,
            "proposals":   proposals,
            "exemplars":   exemplars,
            "raw_results": raw_results,
        }
        _save_results(save_payload, out_dir)
        if ckpt_path.exists():
            ckpt_path.unlink()  # remove checkpoint once final file is written

    # -----------------------------------------------------------------------
    # Scoring metrics
    # -----------------------------------------------------------------------
    valid_proposals = [
        p for p in proposals
        if all(p["id"] in raw_results.get(cfg, {}) for cfg in args.configs)
    ]
    if not valid_proposals:
        print("No complete results found. Exiting.")
        return

    human_scores   = [p["human_score"]      for p in valid_proposals]
    perf_groups    = [p["performance_group"] for p in valid_proposals]

    # all_scores_by_config[cfg][proposal_index] = [run0_score, run1_score, ...]
    all_scores_by_config: dict[str, list[list[float]]] = {
        cfg: [raw_results[cfg][p["id"]]["all_scores"] for p in valid_proposals]
        for cfg in args.configs
    }

    # Per-run mean scores used for the significance tests (averaged across runs)
    pred_by_config: dict[str, list[float]] = {
        cfg: [raw_results[cfg][p["id"]]["mean_score"] for p in valid_proposals]
        for cfg in args.configs
    }

    metrics = evaluate_all_configs_with_sd(all_scores_by_config, human_scores, perf_groups)
    _print_scoring_table(metrics)

    # Statistical tests (Tables 2 and 3)
    if len(args.configs) > 1 and len(valid_proposals) >= 10:
        for metric in ["RMSE", "MAE"]:
            sig = pairwise_significance_table(
                pred_by_config, human_scores, perf_groups, metric=metric
            )
            _print_significance_table(sig, metric, args.configs)

    # -----------------------------------------------------------------------
    # §3.5.1 / Appendix B — Shapiro–Wilk normality test
    # -----------------------------------------------------------------------
    sw = shapiro_wilk_test(pred_by_config, human_scores)
    _print_shapiro_wilk(sw)

    # -----------------------------------------------------------------------
    # §5.1 — Spearman correlation: text length vs. scores
    # -----------------------------------------------------------------------
    proposal_texts = [p["text"] for p in valid_proposals]
    corr = spearman_length_correlation(proposal_texts, human_scores, pred_by_config)
    _print_spearman(corr)

    # -----------------------------------------------------------------------
    # §5.1 — Length-controlled MAE sanity check
    # -----------------------------------------------------------------------
    lm = length_controlled_mae(proposal_texts, human_scores, pred_by_config)
    _print_length_mae(lm)

    # -----------------------------------------------------------------------
    # Feedback evaluation
    # -----------------------------------------------------------------------
    if not args.skip_feedback:
        feedback_by_config: dict[str, list[str]] = {
            cfg: [raw_results[cfg][p["id"]]["feedback"] for p in valid_proposals]
            for cfg in args.configs
        }
        print(f"\nEvaluating feedback quality "
              f"({len(next(iter(feedback_by_config.values())))} instances × "
              f"{len(feedback_by_config)} configs, workers={args.workers})...")
        feedback_metrics = compare_configs_feedback(
            feedback_by_config, verbose=True, workers=args.workers
        )
        _print_feedback_table(feedback_metrics)
    else:
        print("\n(Feedback evaluation skipped via --skip_feedback)")


if __name__ == "__main__":
    main()
