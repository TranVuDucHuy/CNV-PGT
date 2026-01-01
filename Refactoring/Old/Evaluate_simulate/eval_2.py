#!/usr/bin/env python3
import os, sys
import pandas as pd

NEW_EXPERIMENTS = [
    "1-G-100", "1-L-100",
    "2-G-100", "2-L-100",
    "3-G-100", "3-L-100",
    "4-G-100", "4-L-100",
    "5-G-100", "5-L-100",
    "6-G-100", "6-L-100",
    "7-G-100", "7-L-100",
    "8-G-100", "8-L-100",
    "9-G-100", "9-L-100",
    "10-G-100", "10-L-100",
    "11-G-100", "11-L-100",
    "12-G-100", "12-L-100",
    "13-G-100", "13-L-100",
    "14-G-100", "14-L-100",
    "15-G-100", "15-L-100",
    "16-G-100", "16-L-100",
    "17-G-100", "17-L-100",
    "18-G-100", "18-L-100",
    "19-G-100", "19-L-100",
    "20-G-100", "20-L-100",
    "21-G-100", "21-L-100",
    "22-G-100", "22-L-100"
]

ALGOS = [
    "bluefuse", 
    "baseline", 
    "wisecondorx"
]

GROUNDTRUTHS = [
    "groundtruth_bf", 
    "groundtruth_2"
]

NORM_BASE = "norm"
OUT_BASE = "result"

def load_rep_segments(path):
    # Read tsv with columns: Chromosome, Start, End, Copy Number
    df = pd.read_csv(path, sep="\t", dtype=str)
    df = df[["Chromosome", "Start", "End", "Copy Number"]].copy()
    df["Chromosome"] = pd.to_numeric(df["Chromosome"], errors="coerce")
    df["Start"] = pd.to_numeric(df["Start"], errors="coerce")
    df["End"] = pd.to_numeric(df["End"], errors="coerce")
    df["Copy Number"] = pd.to_numeric(df["Copy Number"], errors="coerce")
    df = df.dropna(subset=["Chromosome", "Start", "End", "Copy Number"])  # minimal cleanup
    df["length"] = df["End"] - df["Start"]

    # pick longest segment per chromosome
    rep = df.sort_values(["Chromosome", "length"], ascending=[True, False]).drop_duplicates("Chromosome")
    return {int(row.Chromosome): float(row["Copy Number"]) for _, row in rep.iterrows()}


def compute_deviation_metrics(algo_file, gt_val, exp_type, c, sd):
    """Compute deviation metrics for a single algorithm result"""
    if not algo_file or not os.path.isfile(algo_file):
        return None
    
    algo_map = load_rep_segments(algo_file)
    algo_val = algo_map.get(c, float('nan'))
    # Deviation calculation: positive for Gain, negative for Loss
    deviation = algo_val - gt_val if exp_type == "G" else -algo_val + gt_val
    squared_dev = deviation ** 2
    rel_dev = deviation / gt_val if (not pd.isna(gt_val) and gt_val != 0) else float('nan')
    
    return {
        "Sample": sd,
        "Deviation": deviation,
        "Squared Deviation": squared_dev,
        "Relative Deviation": rel_dev
    }


def evaluate_experiment(exp_name):
    # Parse experiment name to get target chromosome(s) and type (G or L)
    parts = exp_name.split("-")
    chrom_part = parts[0]
    exp_type = parts[1]  # "G" for Gain or "L" for Loss
    target_chroms = [3, 4] if chrom_part == "34" else [int(chrom_part)]
    
    exp_dir = os.path.join(NORM_BASE, exp_name)
    if not os.path.isdir(exp_dir):
        return

    subdirs = [d for d in os.listdir(exp_dir) if os.path.isdir(os.path.join(exp_dir, d))]
    subdirs.sort()
    results = {algo: {gt: [] for gt in GROUNDTRUTHS} for algo in ALGOS}

    for sd in subdirs:
        sample_dir = os.path.join(exp_dir, sd)
        gt_bf_file = None
        gt_2_file = None
        bf_file = None
        bl_file = None
        wise_file = None
        for f in os.listdir(sample_dir):
            if f.endswith("_groundtruth_bf_segments.tsv"): gt_bf_file = os.path.join(sample_dir, f)
            elif f.endswith("_groundtruth_2_segments.tsv"): gt_2_file = os.path.join(sample_dir, f)
            elif f.endswith("_bluefuse_segments.tsv"): bf_file = os.path.join(sample_dir, f)
            elif f.endswith("_baseline_segments.tsv"): bl_file = os.path.join(sample_dir, f)
            elif f.endswith("_wisecondorx_segments.tsv"): wise_file = os.path.join(sample_dir, f)

        # process each groundtruth 
        for gt_type, gt_file in [("groundtruth_bf", gt_bf_file), ("groundtruth_2", gt_2_file)]:
            if not gt_file or not os.path.isfile(gt_file):
                continue
            gt_map = load_rep_segments(gt_file)

            # per algorithm compare to this groundtruth (only for target chromosomes)
            for c in target_chroms:
                gt_val = gt_map.get(c, float('nan'))
                
                metrics = compute_deviation_metrics(bf_file, gt_val, exp_type, c, sd)
                if metrics:
                    results["bluefuse"][gt_type].append(metrics)
                
                metrics = compute_deviation_metrics(bl_file, gt_val, exp_type, c, sd)
                if metrics:
                    results["baseline"][gt_type].append(metrics)
                
                metrics = compute_deviation_metrics(wise_file, gt_val, exp_type, c, sd)
                if metrics:
                    results["wisecondorx"][gt_type].append(metrics)

    # write outputs
    os.makedirs(OUT_BASE, exist_ok=True)
    
    for algo in ALGOS:
        for gt_type in GROUNDTRUTHS:
            rows = results[algo][gt_type]
            if not rows:
                continue
            df = pd.DataFrame(rows)
            
            # Format numeric columns to 6 decimal places
            for col in ["Deviation", "Squared Deviation", "Relative Deviation"]:
                df[col] = df[col].apply(lambda x: ("" if pd.isna(x) else f"{float(x):.6f}"))
            
            out_path = os.path.join(OUT_BASE, f"{exp_name}-{algo}-{gt_type}.tsv")
            df.to_csv(out_path, sep="\t", index=False)


if __name__ == "__main__":
    exps = sys.argv[1:] if len(sys.argv) > 1 else NEW_EXPERIMENTS
    for exp in exps:
        evaluate_experiment(exp)
    
    print("Done.")
