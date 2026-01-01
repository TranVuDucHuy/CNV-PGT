#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

RESULT_BASE = "result"
OUT_BASE = "plot"

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

FIELDS = [
    # "Deviation", 
    # "Squared Deviation", 
    "Relative Deviation"
]

ALGO_GT_PAIRS = [
    ("baseline", "groundtruth_2"),
    ("wisecondorx", "groundtruth_2"),
    ("baseline", "groundtruth_bf"),
    ("wisecondorx", "groundtruth_bf")
]

# Pretty labels for algorithms (capitalize / preserve camelcase where needed)
ALGO_LABELS = {
    'baseline': 'Baseline',
    'wisecondorx': 'WisecondorX'
}
def load_field_data(exp_name, algo, gt_type, field):
    """Load data for a specific field from a result file"""
    result_file = os.path.join(RESULT_BASE, f"{exp_name}-{algo}-{gt_type}.tsv")
    if not os.path.isfile(result_file):
        return []
    
    df = pd.read_csv(result_file, sep="\t")
    # Skip the last row (mean row)
    df_samples = df[:-1]
    
    if field not in df_samples.columns:
        return []
    
    values = []
    for val_str in df_samples[field]:
        try:
            if val_str and str(val_str).strip():
                val = float(val_str)
                values.append(val)
        except (ValueError, TypeError):
            pass
    
    return values

def _create_half_clip(ax, position: float, half_width: float, side: str, y_limits: tuple) -> Rectangle:
    """Return a rectangular clip path covering either left or right half."""
    if half_width <= 0:
        half_width = 0.001
    y_min, y_max = y_limits
    if side == 'left':
        x0 = position - half_width
    else:
        x0 = position
    return Rectangle((x0, y_min), half_width, y_max - y_min, transform=ax.transData)


def _plot_half_violin(ax, data: list, position: float, color: str,
                      width: float = 0.8, side: str = 'left', y_limits: tuple = None) -> None:
    """Plot half violin on specified side."""
    if not data:
        return
    vp = ax.violinplot([data], positions=[position], widths=width,
                       showmeans=False, showmedians=False, showextrema=False)
    half_width = width / 2
    for body in vp['bodies']:
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.6)
        body.set_zorder(1)
        if y_limits:
            clip_rect = _create_half_clip(ax, position, half_width, side, y_limits)
            body.set_clip_path(clip_rect)


def _plot_half_box(ax, data: list, position: float, color: str,
                   width: float = 0.35, side: str = 'right') -> None:
    """Plot half boxplot on specified side."""
    if not data:
        return
    bp = ax.boxplot([data], positions=[position], widths=width, vert=True,
                    patch_artist=True, showfliers=True, zorder=3)
    for patch in bp['boxes']:
        patch.set_facecolor('none')
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)
    for key in ('whiskers', 'caps', 'medians'):
        for line in bp[key]:
            line.set_color('black')
            line.set_linewidth(1.5)
    for flier in bp['fliers']:
        flier.set_markerfacecolor('none')
        flier.set_markeredgecolor('black')
        flier.set_alpha(0.7)


def plot_field_comparison(exp_name, field, output_file):
    """Create half violin-box plot comparing 4 algo-gt combinations for a field"""
    box_data = []
    labels = []
    gt_label_map = {"groundtruth_2": "GT_2", "groundtruth_bf": "GT_BF"}
    
    for algo, gt_type in ALGO_GT_PAIRS:
        data = load_field_data(exp_name, algo, gt_type, field)
        box_data.append(data)
        gt_label = gt_label_map.get(gt_type, gt_type)
        algo_label = ALGO_LABELS.get(algo, algo.capitalize())
        labels.append(f"{algo_label}\n{gt_label}")
    
    # Set y-axis limits based on field
    if field == "Deviation":
        y_limits = (-0.3, 0.2)
    elif field == "Relative Deviation":
        y_limits = (-0.15, 0.1)
    else:
        y_limits = None
    
    # Determine colors per algorithm (baseline -> lightblue, wisecondorx -> lightgreen)
    algo_list = [algo for algo, _ in ALGO_GT_PAIRS]

    fig, ax = plt.subplots(figsize=(12, 6))

    positions = np.arange(1, len(box_data) + 1)

    # Plot half violin (left) and half box (right) for each position,
    # choosing color based on the algorithm for that position
    for pos, data, algo in zip(positions, box_data, algo_list):
        color = 'lightblue' if algo == 'baseline' else 'lightgreen'
        _plot_half_violin(ax, data, pos, color, side='left', y_limits=y_limits)
        _plot_half_box(ax, data, pos, color, side='right')
    
    # Configure axes
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
    ax.set_title(f'{exp_name} - {field}', fontsize=14)
    
    if y_limits:
        ax.set_ylim(*y_limits)
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

if __name__ == "__main__":
    os.makedirs(OUT_BASE, exist_ok=True)
    
    for exp in NEW_EXPERIMENTS:
        for field in FIELDS:
            output_file = os.path.join(OUT_BASE, f"{exp}-{field}.png")
            plot_field_comparison(exp, field, output_file)
    
    print("Done.")
