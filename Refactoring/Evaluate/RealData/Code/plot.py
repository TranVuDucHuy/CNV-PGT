import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

def _plot_half_violin(ax, data: list, position: float, y_limits: tuple = None) -> None:
    """Vẽ nửa violin ở bên trái."""
    if len(data) == 0:
        return
    width = 0.8
    violin_plot = ax.violinplot([data], positions=[position], widths=width, showextrema=False)
    half_width = width / 2
    for body in violin_plot['bodies']:
        body.set_facecolor('lightblue')
        body.set_edgecolor('lightblue')
        body.set_alpha(0.6)
        body.set_zorder(1)
        if y_limits:
            y_min, y_max = y_limits
            x0 = position - half_width
            clip_rect = Rectangle((x0, y_min), half_width, y_max - y_min, transform=ax.transData)
            body.set_clip_path(clip_rect)

def _plot_box(ax, data: list, position: float) -> None:
    """Vẽ biểu đồ hộp."""
    if len(data) == 0:
        return
    box_plot = ax.boxplot([data], positions=[position], widths=0.4, vert=True,
                    patch_artist=True, showfliers=True, zorder=3)
    for patch in box_plot['boxes']:
        patch.set_facecolor('none')
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)
    for key in ('whiskers', 'caps', 'medians'):
        for line in box_plot[key]:
            line.set_color('black')
            line.set_linewidth(1.5)
    for flier in box_plot['fliers']:
        flier.set_markerfacecolor('none')
        flier.set_markeredgecolor('black')
        flier.set_alpha(0.7)

def run_plot(experiment_id: str, summary_file: str, output_dir: str):
    """Vẽ biểu đồ phân phối độ lệch tương đối."""
    summary_file = Path(summary_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not summary_file.exists():
        return
        
    df = pd.read_csv(summary_file, sep='\t')
    if df.empty:
        return

    algorithms = sorted(df['algorithm'].unique())
    
    # Vẽ biểu đồ độ lệch tương đối
    fig, ax = plt.subplots(figsize=(12, 6))
    data_to_plot = []
    labels = []
    
    for algorithm in algorithms:
        sub = df[df['algorithm'] == algorithm]
        rels = sub['algorithmRelative'].dropna()
        rels = rels.str.rstrip('%').astype(float)
        if not rels.empty:
            data_to_plot.append(rels.values)
            labels.append(algorithm.capitalize())
            
    if data_to_plot:
        positions = np.arange(1, len(data_to_plot) + 1)
        y_limits = (min([min(d) for d in data_to_plot]) - 0.01, 
                   max([max(d) for d in data_to_plot]) + 0.01)
        
        for pos, data in zip(positions, data_to_plot):
            _plot_half_violin(ax, data, pos, y_limits=y_limits)
            _plot_box(ax, data, pos)
        
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
        ax.set_title(f'{experiment_id} - Relative Distribution', fontsize=14)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:.0f}%'))
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        out_png = output_dir / f"{experiment_id}_relative.png"
        plt.savefig(out_png, dpi=300, bbox_inches='tight')
        plt.close()
