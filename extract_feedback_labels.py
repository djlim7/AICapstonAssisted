"""
Re-run LCF sentence classification on stored feedback texts and save
raw per-proposal binary labels to results/feedback_labels.csv and
results/feedback_labels.json.

Usage:
    python extract_feedback_labels.py --results results/run_20260531_011922.json --workers 8
"""

import argparse
import csv
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from evaluation.feedback import classify_feedback
import config

COMPONENTS = list(config.LEARNER_CENTERED_COMPONENTS.keys())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, help="Path to saved results JSON")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out_dir", default="results")
    args = parser.parse_args()

    with open(args.results) as f:
        d = json.load(f)

    raw_results = d["raw_results"]
    proposals   = d["proposals"]
    configs     = list(raw_results.keys())
    pid_to_meta = {p["id"]: p for p in proposals}

    # Build flat list of (pid, cfg, feedback_text) to classify
    tasks = [
        (pid, cfg, raw_results[cfg][pid]["feedback"])
        for cfg in configs
        for pid in raw_results[cfg]
    ]
    print(f"Classifying {len(tasks)} feedback texts "
          f"({len(configs)} configs × {len(tasks)//len(configs)} proposals) "
          f"with {args.workers} workers...")

    rows: list[dict] = [None] * len(tasks)
    lock = threading.Lock()

    def _classify(idx_task):
        idx, (pid, cfg, text) = idx_task
        labels = classify_feedback(text)
        meta   = pid_to_meta.get(pid, {})
        row = {
            "proposal_id":       pid,
            "config":            cfg,
            "performance_group": meta.get("performance_group", ""),
            "human_score":       meta.get("human_score", ""),
        }
        row.update(labels)
        return idx, row

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_classify, (i, t)): i for i, t in enumerate(tasks)}
        for future in tqdm(as_completed(futures), total=len(tasks), desc="Feedback"):
            idx, row = future.result()
            rows[idx] = row

    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    # CSV
    csv_path = out_dir / "feedback_labels.csv"
    fieldnames = ["proposal_id", "config", "performance_group", "human_score"] + COMPONENTS
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # JSON
    json_path = out_dir / "feedback_labels.json"
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    # Quick sanity: recompute proportions and print
    from collections import defaultdict
    counts = defaultdict(lambda: defaultdict(int))
    totals = defaultdict(int)
    for row in rows:
        cfg = row["config"]
        totals[cfg] += 1
        for comp in COMPONENTS:
            if row[comp]:
                counts[cfg][comp] += 1

    print()
    print(f"{'Component':<30}" + "".join(f"{c:>8}" for c in configs))
    print("-" * (30 + 8 * len(configs)))
    for comp in COMPONENTS:
        row_str = f"{comp:<30}"
        for cfg in configs:
            pct = counts[cfg][comp] / totals[cfg] * 100 if totals[cfg] else 0
            row_str += f"{pct:8.1f}"
        print(row_str)

    print(f"\nSaved raw labels to:\n  {csv_path}\n  {json_path}")
    print(f"Shape: {len(rows)} rows × {len(fieldnames)} columns")


if __name__ == "__main__":
    main()
