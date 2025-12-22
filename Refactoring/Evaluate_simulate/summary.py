#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

RESULT_BASE = "result"
OUT_BASE = "summary"

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

ALGOS = ["bluefuse", "baseline", "wisecondorx"]
GROUNDTRUTHS = ["groundtruth_bf", "groundtruth_2"]


def load_data(exp_name, algo, gt_type):
    """Load deviation data from result file"""
    result_file = os.path.join(RESULT_BASE, f"{exp_name}-{algo}-{gt_type}.tsv")
    if not os.path.isfile(result_file):
        return None
    
    df = pd.read_csv(result_file, sep="\t")
    # Skip the last row (mean row if exists)
    df_samples = df[:-1] if len(df) > 0 else df
    
    # Convert columns to numeric
    deviation = pd.to_numeric(df_samples["Deviation"], errors="coerce").dropna()
    squared_dev = pd.to_numeric(df_samples["Squared Deviation"], errors="coerce").dropna()
    relative_dev = pd.to_numeric(df_samples["Relative Deviation"], errors="coerce").dropna()
    
    return {
        "deviation": deviation.values,
        "squared_dev": squared_dev.values,
        "relative_dev": relative_dev.values
    }


def compute_mean_summary():
    """Compute mean values for all experiments"""
    mean_data = []
    
    for exp in NEW_EXPERIMENTS:
        for algo in ALGOS:
            for gt_type in GROUNDTRUTHS:
                data = load_data(exp, algo, gt_type)
                if data is None or len(data["deviation"]) == 0:
                    continue
                
                mean_abs_dev = np.mean(np.abs(data["deviation"]))
                mean_sq_dev = np.mean(data["squared_dev"])
                mean_abs_rel_dev = np.mean(np.abs(data["relative_dev"]))
                
                mean_data.append({
                    "Experiment": exp,
                    "Algorithm": algo,
                    "GroundTruth": gt_type,
                    "Mean Absolute Deviation": f"{mean_abs_dev:.6f}",
                    "Mean Squared Deviation": f"{mean_sq_dev:.6f}",
                    "Mean Absolute Relative Deviation": f"{mean_abs_rel_dev:.6f}"
                })
    
    return pd.DataFrame(mean_data)


def compute_absolute_quantiles():
    """Compute quantiles of Absolute Deviation"""
    abs_data = []
    quantiles = [0.2, 0.4, 0.6, 0.8]
    
    for exp in NEW_EXPERIMENTS:
        for algo in ALGOS:
            for gt_type in GROUNDTRUTHS:
                data = load_data(exp, algo, gt_type)
                if data is None or len(data["deviation"]) == 0:
                    continue
                
                abs_deviation = np.abs(data["deviation"])
                q_values = np.quantile(abs_deviation, quantiles)
                
                row = {
                    "Experiment": exp,
                    "Algorithm": algo,
                    "GroundTruth": gt_type
                }
                for q, val in zip(quantiles, q_values):
                    row[f"Q{int(q*30)}"] = f"{val:.6f}"
                
                abs_data.append(row)
    
    return pd.DataFrame(abs_data)


def compute_relative_distribution():
    """Count samples in relative deviation ranges"""
    rel_data = []
    bins = [(-0.1, -0.05), (-0.05, 0), (0, 0.05), (0.05, 0.1)]
    bin_labels = ["[-0.1, -0.05)", "[-0.05, 0)", "[0, 0.05)", "[0.05, 0.1]"]
    
    for exp in NEW_EXPERIMENTS:
        for algo in ALGOS:
            for gt_type in GROUNDTRUTHS:
                data = load_data(exp, algo, gt_type)
                if data is None or len(data["relative_dev"]) == 0:
                    continue
                
                rel_dev = data["relative_dev"]
                row = {
                    "Experiment": exp,
                    "Algorithm": algo,
                    "GroundTruth": gt_type
                }
                
                # Count samples in each bin
                for (low, high), label in zip(bins, bin_labels):
                    if label == "[0.05, 0.1]":
                        # Last bin is inclusive on both ends
                        count = np.sum((rel_dev >= low) & (rel_dev <= high))
                    else:
                        count = np.sum((rel_dev >= low) & (rel_dev < high))
                    row[label] = int(count)
                
                rel_data.append(row)
    
    return pd.DataFrame(rel_data)


if __name__ == "__main__":
    os.makedirs(OUT_BASE, exist_ok=True)
    
    # Compute and save mean summary
    mean_df = compute_mean_summary()
    mean_df.to_csv(os.path.join(OUT_BASE, "mean.tsv"), sep="\t", index=False)
    print("Saved: mean.tsv")
    
    # Compute and save absolute deviation quantiles
    abs_df = compute_absolute_quantiles()
    abs_df.to_csv(os.path.join(OUT_BASE, "absolute.tsv"), sep="\t", index=False)
    print("Saved: absolute.tsv")
    
    # Compute and save relative deviation distribution
    rel_df = compute_relative_distribution()
    rel_df.to_csv(os.path.join(OUT_BASE, "relative.tsv"), sep="\t", index=False)
    print("Saved: relative.tsv")
    
    print("Done.")
