import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import logging
import numpy as np
from matplotlib.patches import Rectangle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

AUTOSOMES = [str(i) for i in range(1, 23)]  # 1..22
Y_LIMITS = (-0.4, 0.4)
EXCLUDED_SAMPLES = [
    'HLT37BGXN-P2302029-BVPD-23048725-H4',
    'H73LLAFX7-P2219663-NAMHOC-123001-AG1'
]


def load_deviation_file(file_path: str) -> pd.DataFrame:
    """Load deviation/relative TSV file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path, sep='\t')
    return df


def extract_data_values(df: pd.DataFrame, exclude_samples: list = None) -> list:
    """
    Extract all non-null values from all chromosome columns in a DataFrame.
    
    Args:
        df: DataFrame with structure (sample_id, 1, 2, ..., 22)
        exclude_samples: Optional list of sample_ids to exclude from extraction
    
    Returns:
        List of all non-null numeric values
    """
    # Filter out excluded samples if specified
    if exclude_samples:
        df = df[~df['sample_id'].isin(exclude_samples)].copy()
    
    values = []
    
    for chr_ in AUTOSOMES:
        if chr_ in df.columns:
            col_data = df[chr_].dropna()
            values.extend(col_data.tolist())
    
    return values


def collect_metric_values(file_paths: list, exclude_samples: list = None) -> list:
    """Aggregate values from multiple TSV files."""
    values = []
    for path in file_paths:
        df = load_deviation_file(path)
        if df is None:
            continue
        values.extend(extract_data_values(df, exclude_samples=exclude_samples))
    return values


def _create_half_clip(ax, position: float, half_width: float, side: str) -> Rectangle:
    """Return a rectangular clip path covering either left or right half."""
    if half_width <= 0:
        half_width = 0.001
    y_min, y_max = Y_LIMITS
    if side == 'left':
        x0 = position - half_width
    else:
        x0 = position
    return Rectangle((x0, y_min), half_width, y_max - y_min, transform=ax.transData)


def _plot_half_violin(ax, data: list, position: float, color: str,
                      width: float = 0.8, side: str = 'left') -> None:
    vp = ax.violinplot([data], positions=[position], widths=width,
                       showmeans=False, showmedians=False, showextrema=False)
    half_width = width / 2
    for body in vp['bodies']:
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.6)
        body.set_zorder(1)
        clip_rect = _create_half_clip(ax, position, half_width, side)
        body.set_clip_path(clip_rect)


def _plot_half_box(ax, data: list, position: float, color: str,
                   width: float = 0.35, side: str = 'right') -> None:
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


def create_half_violin_boxplot(input_dir: str, suffixes: list, output_path: str) -> None:
    """Create combined plot with half violins (left) and half boxplots (right) per suffix."""
    dataset_specs = [
        (
            'Baseline', 'Deviation',
            [
                os.path.join(input_dir, f'deviation-{suffix}-baseline-bluefuse.tsv')
                for suffix in suffixes
            ]
        ),
        (
            'WisecondorX', 'Deviation',
            [
                os.path.join(input_dir, f'deviation-{suffix}-wisecondorx-bluefuse.tsv')
                for suffix in suffixes
            ]
        ),
        (
            'Baseline', 'Relative deviation',
            [
                os.path.join(input_dir, f'relative-{suffix}-baseline-bluefuse.tsv')
                for suffix in suffixes
            ]
        ),
        (
            'WisecondorX', 'Relative deviation',
            [
                os.path.join(input_dir, f'relative-{suffix}-wisecondorx-bluefuse.tsv')
                for suffix in suffixes
            ]
        )
    ]

    labels, values, methods = [], [], []
    for method, metric_type, files in dataset_specs:
        vals = collect_metric_values(files, exclude_samples=EXCLUDED_SAMPLES)
        if not vals:
            logger.warning(f"No values collected for {method} {metric_type} with suffixes {suffixes}; skipping")
            continue
        labels.append(f'{method}\n{metric_type}')
        values.append(vals)
        methods.append(method)

    if not values:
        logger.error('No data available for the combined half violin-box plot')
        return

    positions = np.arange(1, len(values) + 1)
    color_map = {'Baseline': 'lightblue', 'WisecondorX': 'lightgreen'}
    colors = [color_map[method] for method in methods]

    suffix_text = ', '.join(f"-{suffix}" for suffix in suffixes)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_ylim(*Y_LIMITS)
    for pos, label, data, method in zip(positions, labels, values, methods):
        color = color_map[method]
        _plot_half_violin(ax, data, pos, color, side='left')
        _plot_half_box(ax, data, pos, color, side='right')

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=0, ha='center', style='normal', fontsize=10)
    ax.set_ylabel('Value')
    ax.set_ylim(*Y_LIMITS)
    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.grid(axis='y', linestyle='--', alpha=0.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Saved combined half violin-box plot for suffixes {suffixes}: {output_path}")
    plt.close()




def generate_plots(input_dir: str, output_dir: str) -> None:
    """
    Generate combined half violin-box plots for all suffixes.
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    combined_plot_file = os.path.join(output_dir, 'combined-half-plot.png')
    create_half_violin_boxplot(input_dir, ['1'], combined_plot_file)
    
    logger.info("Plot generation complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Generate box plots for deviation and relative metrics'
    )
    parser.add_argument(
        'input_dir',
        help='Input directory containing deviation/relative TSV files'
    )
    parser.add_argument(
        'output_dir',
        help='Output directory for PNG files'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return
    
    generate_plots(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
