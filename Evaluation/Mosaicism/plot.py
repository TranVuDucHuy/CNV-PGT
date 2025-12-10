#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RESULT_BASE = "result"
OUT_BASE = "result"

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

def load_results_for_groundtruth(exp_name, gt_type):
    """Load evaluation results for a single experiment and groundtruth type.
    Returns dict: {algo: list of values}"""
    data = {algo: [] for algo in ALGOS}
    
    for algo in ALGOS:
        result_file = os.path.join(RESULT_BASE, f"{exp_name}-{algo}-{gt_type}.tsv")
        if not os.path.isfile(result_file):
            continue
        df = pd.read_csv(result_file, sep="\t")
        # Skip the last row (mean row)
        df_samples = df[:-1]

        for col in df_samples.columns[1:]:
            try:
                for val_str in df_samples[col]:
                    if val_str and str(val_str).strip():  # Skip empty values
                        val = float(val_str)
                        data[algo].append(val)
            except (ValueError, TypeError):
                pass
    
    return data

def plot_boxplot_for_groundtruth(exp_name, gt_type, output_file):
    data = load_results_for_groundtruth(exp_name, gt_type)
    
    box_data = [data[algo] for algo in ALGOS]
    fig, ax = plt.subplots(figsize=(10, 6))
    bp = ax.boxplot(box_data, patch_artist=True)
    ax.set_xticks(list(range(1, len(ALGOS) + 1)))
    ax.set_xticklabels(ALGOS)
    
    parts = exp_name.split('-')
    mid = parts[1].upper() if len(parts) > 1 else ''
    if mid.startswith('G'):
        color = 'lightyellow'   # light yellow for gain
        y_max = 0.1
    else:
        color = 'lightblue'   # light blue for loss (default)
        y_max = 0.01

    for patch in bp['boxes']:
        patch.set_facecolor(color)
    # Set y-axis limits (start at 0)
    ax.set_ylim(bottom=0, top=y_max)
    
    # Labels and title
    ax.set_ylabel('Squared Deviation', fontsize=12)
    ax.set_xlabel('Algorithm', fontsize=12)
    ax.set_title(f'[{exp_name}] - {gt_type}', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

if __name__ == "__main__":
    os.makedirs(OUT_BASE, exist_ok=True)

    for exp in NEW_EXPERIMENTS:
        for gt_type in GROUNDTRUTHS:
            output_file = os.path.join(OUT_BASE, f"{exp}_{gt_type}.png")
            plot_boxplot_for_groundtruth(exp, gt_type, output_file)
    
    print("Done.")
