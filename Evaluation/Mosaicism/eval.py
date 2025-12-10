#!/usr/bin/env python3
import os, sys
import pandas as pd

NEW_EXPERIMENTS = [
    "1-G-30", "1-L-30",
    "2-G-30", "2-L-30",
    "3-G-30", "3-L-30",
    "4-G-30", "4-L-30",
    "5-G-30", "5-L-30",
    "6-G-30", "6-L-30",
    "7-G-30", "7-L-30",
    "8-G-30", "8-L-30",
    "9-G-30", "9-L-30",
    "10-G-30", "10-L-30",
    "11-G-30", "11-L-30",
    "12-G-30", "12-L-30",
    "13-G-30", "13-L-30",
    "14-G-30", "14-L-30",
    "15-G-30", "15-L-30",
    "16-G-30", "16-L-30",
    "17-G-30", "17-L-30",
    "18-G-30", "18-L-30",
    "19-G-30", "19-L-30",
    "20-G-30", "20-L-30",
    "21-G-30", "21-L-30",
    "22-G-30", "22-L-30"
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


def evaluate_experiment(exp_name):
    # Parse experiment name to get target chromosome(s)
    parts = exp_name.split("-")
    chrom_part = parts[0]
    target_chroms = [3, 4] if chrom_part == "34" else [int(chrom_part)]
    
    exp_dir = os.path.join(NORM_BASE, exp_name)
    if not os.path.isdir(exp_dir):
        return []

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
            if bf_file and os.path.isfile(bf_file):
                algo_map = load_rep_segments(bf_file)
                row = [sd] + [((algo_map.get(c, float('nan')) - gt_map.get(c, float('nan'))) ** 2) for c in target_chroms]
                results["bluefuse"][gt_type].append(row)
            if bl_file and os.path.isfile(bl_file):
                algo_map = load_rep_segments(bl_file)
                row = [sd] + [((algo_map.get(c, float('nan')) - gt_map.get(c, float('nan'))) ** 2) for c in target_chroms]
                results["baseline"][gt_type].append(row)
            if wise_file and os.path.isfile(wise_file):
                algo_map = load_rep_segments(wise_file)
                row = [sd] + [((algo_map.get(c, float('nan')) - gt_map.get(c, float('nan'))) ** 2) for c in target_chroms]
                results["wisecondorx"][gt_type].append(row)

    # write outputs
    os.makedirs(OUT_BASE, exist_ok=True)
    
    # Collect mean values for summary
    mean_summary = []
    
    for algo in ALGOS:
        for gt_type in GROUNDTRUTHS:
            rows = results[algo][gt_type]
            if not rows:
                continue
            cols = ["Sample"] + [str(c) for c in target_chroms]
            df = pd.DataFrame(rows, columns=cols)
            mean_vals = ["mean"] + [df[str(c)].astype(float).mean(skipna=True) for c in target_chroms]
            df = pd.concat([df, pd.DataFrame([mean_vals], columns=cols)], ignore_index=True)
            
            for c in target_chroms:
                col = str(c)
                df[col] = df[col].apply(lambda x: ("" if pd.isna(x) else f"{float(x):.6f}"))
            out_path = os.path.join(OUT_BASE, f"{exp_name}-{algo}-{gt_type}.tsv")
            df.to_csv(out_path, sep="\t", index=False)
            
            # Add to mean summary
            mean_summary.append({
                "Experiment": exp_name,
                "Algorithm": algo,
                "GroundTruth": gt_type,
                **{"MeanSquaredDeviation": f"{float(mean_vals[i+1]):.6f}" for i, c in enumerate(target_chroms)}
            })

    return mean_summary


if __name__ == "__main__":
    exps = sys.argv[1:] if len(sys.argv) > 1 else NEW_EXPERIMENTS
    all_means = []
    for exp in exps:
        mean_summary = evaluate_experiment(exp)
        all_means.extend(mean_summary)
    
    # Write consolidated summary
    if all_means:
        os.makedirs(OUT_BASE, exist_ok=True)
        mean_df = pd.DataFrame(all_means)
        mean_out_path = os.path.join(OUT_BASE, "all_means.tsv")
        mean_df.to_csv(mean_out_path, sep="\t", index=False)
    
    print("Done.")
