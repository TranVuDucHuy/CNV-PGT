import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    """Vẽ biểu đồ hộp ở bên phải."""
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

def run_plot(experiment_id: str, deviation_dir: Path, output_dir: Path, gt_type: str):
    """Vẽ biểu đồ half violin boxplot cho relative của từng region."""
    deviation_dir = deviation_dir / gt_type    
    if not deviation_dir.exists():
        return
    
    relative_files = list(deviation_dir.glob("*_relative.tsv"))
    if not relative_files:
        return
    
    # Đọc tất cả dữ liệu
    all_data = {}
    all_regions = set()
    
    for rel_file in relative_files:
        algorithm_id = rel_file.name.replace("_relative.tsv", "")
        rel_df = pd.read_csv(rel_file, sep='\t')
        
        region_cols = [col for col in rel_df.columns if col != 'sample']
        all_regions.update(region_cols)
        
        all_data[algorithm_id] = rel_df
    
    # Vẽ biểu đồ cho từng region
    algorithms = sorted(all_data.keys())
    
    for region_id in sorted(all_regions, key=lambda x: int(x) if x.isdigit() else x):
        fig, ax = plt.subplots(figsize=(12, 6))
        
        data_to_plot = []
        labels = []
        
        for algorithm_id in algorithms:
            if algorithm_id not in all_data:
                continue
            
            df = all_data[algorithm_id]
            if region_id not in df.columns:
                continue
            
            rel_values = pd.to_numeric(df[region_id].astype(str).str.rstrip('%'), errors='coerce').dropna()
            if rel_values.empty:
                continue
            
            data_to_plot.append(rel_values.values)
            labels.append(algorithm_id.capitalize())
        
        if not data_to_plot:
            plt.close()
            continue
        
        positions = np.arange(1, len(data_to_plot) + 1)
        
        # Xác định y_limits
        all_values = np.concatenate(data_to_plot)
        y_min = np.min(all_values) - 0.01
        y_max = np.max(all_values) + 0.01
        y_limits = (y_min, y_max)
        
        # Vẽ half violin và box cho từng thuật toán
        for pos, data in zip(positions, data_to_plot):
            _plot_half_violin(ax, data, pos, y_limits=y_limits)
            _plot_box(ax, data, pos)
        
        # Tùy chỉnh biểu đồ
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=10)
        ax.set_title(f'{experiment_id} - Region {region_id} - Relative', fontsize=14)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:.0f}%'))
        ax.axhline(0, color='gray', linestyle='--', linewidth=1)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        out_png = output_dir / f"{experiment_id}_{region_id}_relative.png"
        plt.savefig(out_png, dpi=300, bbox_inches='tight')
        plt.close()    