import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configuration for y-axis limits (you can adjust these values)
Y_LIMITS = {
    ('G', 'Mean Absolute Deviation'): 0.30,
    ('G', 'Mean Squared Deviation'): 0.06,
    ('G', 'Mean Absolute Relative Deviation'): 0.08,
    ('L', 'Mean Absolute Deviation'): 0.15,
    ('L', 'Mean Squared Deviation'): 0.01,
    ('L', 'Mean Absolute Relative Deviation'): 0.08,
}

# Color mapping according to the provided images
COLORS = {
    (100, 'baseline'): 'red',
    (100, 'wisecondorx'): 'cyan',
    (50, 'baseline'): 'orange',
    (50, 'wisecondorx'): 'blue',
    (30, 'baseline'): 'yellow',
    (30, 'wisecondorx'): 'purple',
}

# Labels for legend
LABELS = {
    (100, 'baseline'): '100% - Baseline',
    (100, 'wisecondorx'): '100% - WisecondorX',
    (50, 'baseline'): '50% - Baseline',
    (50, 'wisecondorx'): '50% - WisecondorX',
    (30, 'baseline'): '30% - Baseline',
    (30, 'wisecondorx'): '30% - WisecondorX',
}

# Groundtruth name mapping
GT_NAMES = {
    'groundtruth_bf': 'GT_BF',
    'groundtruth_2': 'GT_2',
}

# Type name mapping
TYPE_NAMES = {
    'G': 'Gain',
    'L': 'Loss',
}

def load_data():
    """Load mean.tsv files from different mosaic levels"""
    data_frames = []
    
    for mosaic in [30, 50, 100]:
        file_path = f'experiment_data/{mosaic}/summary/mean.tsv'
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, sep='\t')
            df['Mosaic'] = mosaic
            data_frames.append(df)
        else:
            print(f"Warning: {file_path} not found")
    
    if not data_frames:
        raise FileNotFoundError("No mean.tsv files found")
    
    return pd.concat(data_frames, ignore_index=True)

def extract_info(experiment):
    """Extract chromosome number and type from experiment name"""
    # Format: "1-G-100" -> chromosome=1, type=G
    parts = experiment.split('-')
    chromosome = int(parts[0])
    exp_type = parts[1]
    return chromosome, exp_type

def plot_line_chart(data, exp_type, metric, groundtruth, output_dir):
    """Create a line chart for specific combination"""
    
    # Filter data
    filtered = data[
        (data['GroundTruth'] == groundtruth)
    ].copy()
    
    # Extract chromosome and type info
    filtered[['Chromosome', 'Type']] = filtered['Experiment'].apply(
        lambda x: pd.Series(extract_info(x))
    )
    
    # Filter by type
    filtered = filtered[filtered['Type'] == exp_type]
    
    if filtered.empty:
        print(f"No data for {exp_type}, {metric}, {groundtruth}")
        return
    
    # Create figure - wider to accommodate legend at top
    plt.figure(figsize=(13, 5))
    
    # Plot lines for each mosaic and algorithm combination
    for mosaic in [100, 50, 30]:
        for algorithm in ['baseline', 'wisecondorx']:
            subset = filtered[
                (filtered['Mosaic'] == mosaic) &
                (filtered['Algorithm'] == algorithm)
            ].sort_values('Chromosome')
            
            if not subset.empty:
                plt.plot(
                    subset['Chromosome'],
                    subset[metric],
                    color=COLORS[(mosaic, algorithm)],
                    label=LABELS[(mosaic, algorithm)],
                    linewidth=2
                )
    
    # Customize plot
    gt_name = GT_NAMES.get(groundtruth, groundtruth)
    type_name = TYPE_NAMES.get(exp_type, exp_type)
    plt.title(f'{gt_name} - {type_name} - {metric}', pad=10)
    plt.xlabel('')
    plt.ylabel('')
    
    # Set x-axis to show chromosomes 1-22
    plt.xlim(1, 22)
    plt.xticks(range(1, 23), fontsize=10)
    plt.yticks(fontsize=10)
    
    # Set y-axis limits
    y_max = Y_LIMITS.get((exp_type, metric), 0.05)
    plt.ylim(0, y_max)
    
    # Place legend below the x-axis (bottom center) with 6 columns
    plt.legend(loc='lower center', fontsize=10, ncol=6, frameon=False,
               bbox_to_anchor=(0.5, -0.18), handlelength=2)

    # Add grid
    plt.grid(True, alpha=0.3)

    # Reserve space at the bottom for the legend and tighten layout
    plt.subplots_adjust(bottom=0.22, top=0.92)
    plt.tight_layout()
    
    # Save figure
    metric_short = metric.replace(' ', '_').replace('Mean_', '').replace('_Deviation', '')
    filename = f'{gt_name}_{exp_type}_{metric_short}.png'
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {filename}")

def main():
    """Main function to generate all line charts"""
    
    # Create output directory
    output_dir = 'line_chart'
    Path(output_dir).mkdir(exist_ok=True)
    
    # Load data
    print("Loading data...")
    data = load_data()
    
    # Metrics to plot
    metrics = [
        # 'Mean Absolute Deviation',
        # 'Mean Squared Deviation',
        'Mean Absolute Relative Deviation'
    ]
    
    # Types
    types = ['G', 'L']
    
    # Groundtruths
    groundtruths = ['groundtruth_bf', 'groundtruth_2']
    
    # Generate all combinations (12 charts)
    print("Generating line charts...")
    for exp_type in types:
        for metric in metrics:
            for groundtruth in groundtruths:
                plot_line_chart(data, exp_type, metric, groundtruth, output_dir)
    
    print(f"\nAll charts saved to {output_dir}/")

if __name__ == '__main__':
    main()
