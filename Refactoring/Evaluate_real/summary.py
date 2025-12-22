import os
import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

AUTOSOMES = [str(i) for i in range(1, 23)]
EXCLUDED_SAMPLES = [
    # 'HLT37BGXN-P2302029-BVPD-23048725-H4',
    # 'H73LLAFX7-P2219663-NAMHOC-123001-AG1'
]


def load_deviation_file(file_path: str) -> pd.DataFrame:
    """Load deviation/relative TSV file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    df = pd.read_csv(file_path, sep='\t')
    return df


def create_summary_table(input_dir: str, output_dir: str, integrated_dir: str) -> pd.DataFrame:
    """Merge 4 input files into a summary table with integrated predictions."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Load files
    baseline_dev = load_deviation_file(os.path.join(input_dir, 'deviation-1-baseline-bluefuse.tsv'))
    wisecondorx_dev = load_deviation_file(os.path.join(input_dir, 'deviation-1-wisecondorx-bluefuse.tsv'))
    baseline_rel = load_deviation_file(os.path.join(input_dir, 'relative-1-baseline-bluefuse.tsv'))
    wisecondorx_rel = load_deviation_file(os.path.join(input_dir, 'relative-1-wisecondorx-bluefuse.tsv'))
    
    if any(df is None for df in [baseline_dev, wisecondorx_dev, baseline_rel, wisecondorx_rel]):
        logger.error("Failed to load all input files")
        return None
    
    # Load integrated prediction files
    baseline_pred = load_deviation_file(os.path.join(integrated_dir, 'baseline_integrated.tsv'))
    bluefuse_pred = load_deviation_file(os.path.join(integrated_dir, 'bluefuse_integrated.tsv'))
    wisecondorx_pred = load_deviation_file(os.path.join(integrated_dir, 'wisecondorx_integrated.tsv'))
    
    # Build summary by iterating through all non-null values
    rows = []
    
    for chr_ in AUTOSOMES:
        if chr_ not in baseline_dev.columns:
            continue
        
        # Get all sample_ids from baseline_dev (using it as reference)
        for idx, sample_id in enumerate(baseline_dev['sample_id']):
            if sample_id in EXCLUDED_SAMPLES:
                continue
            
            # Check if there's any non-null value in baseline_dev for this sample-chromosome
            dev_val = baseline_dev.iloc[idx][chr_]
            if pd.isna(dev_val):
                continue
            
            # Get corresponding values from all 4 tables
            baseline_dev_val = baseline_dev.iloc[idx][chr_]
            wisecondorx_dev_val = wisecondorx_dev.iloc[idx][chr_]
            baseline_rel_val = baseline_rel.iloc[idx][chr_]
            wisecondorx_rel_val = wisecondorx_rel.iloc[idx][chr_]
            
            # Get integrated predictions
            bluefuse_pred_val = bluefuse_pred.iloc[idx][chr_]
            baseline_pred_val = baseline_pred.iloc[idx][chr_]
            wisecondorx_pred_val = wisecondorx_pred.iloc[idx][chr_]
            
            row = {
                'Sample': sample_id,
                'Chromosome': chr_,
                'BlueFuse CN': bluefuse_pred_val,
                'Baseline CN': baseline_pred_val,
                'WisecondorX CN': wisecondorx_pred_val,
                'Baseline Deviation': baseline_dev_val,
                'WisecondorX Deviation': wisecondorx_dev_val,
                'Baseline Relative Deviation': baseline_rel_val,
                'WisecondorX Relative Deviation': wisecondorx_rel_val
            }
            
            rows.append(row)
    
    summary_df = pd.DataFrame(rows)
    output_path = os.path.join(output_dir, 'summary.tsv')
    summary_df.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Saved summary table: {output_path} ({len(summary_df)} rows)")
    
    return summary_df


def analyze_deviation(summary_df: pd.DataFrame, output_dir: str) -> None:
    """Analyze deviation thresholds for 20%, 40%, 60%, 80% percentiles."""
    os.makedirs(output_dir, exist_ok=True)
    
    baseline_abs = np.abs(summary_df['Baseline Deviation'].dropna())
    wisecondorx_abs = np.abs(summary_df['WisecondorX Deviation'].dropna())
    
    percentiles = [20, 40, 60, 80]
    results = []
    
    for percentile in percentiles:
        baseline_threshold = np.percentile(baseline_abs, percentile)
        wisecondorx_threshold = np.percentile(wisecondorx_abs, percentile)
        
        results.append({
            'Percentile': f"{percentile}%",
            'Baseline Deviation Threshold': f"{baseline_threshold:.4f}",
            'WisecondorX Deviation Threshold': f"{wisecondorx_threshold:.4f}"
        })
    
    results_df = pd.DataFrame(results)
    output_path = os.path.join(output_dir, 'deviation_thresholds.tsv')
    results_df.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Saved deviation thresholds: {output_path}")


def analyze_relative_deviation(summary_df: pd.DataFrame, output_dir: str) -> None:
    """Analyze relative deviation distribution in bins."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Define bins: (-0.12, -0.09], (-0.09, -0.06], ..., (0.06, 0.09], (0.09, 0.12)
    bins = [-0.12, -0.09, -0.06, -0.03, 0, 0.03, 0.06, 0.09, 0.12]
    labels = [
        '(-0.12, -0.09]',
        '(-0.09, -0.06]',
        '(-0.06, -0.03]',
        '(-0.03, 0]',
        '(0, 0.03]',
        '(0.03, 0.06]',
        '(0.06, 0.09]',
        '(0.09, 0.12)'
    ]
    
    baseline_rel = summary_df['Baseline Relative Deviation'].dropna()
    wisecondorx_rel = summary_df['WisecondorX Relative Deviation'].dropna()
    
    baseline_counts = pd.cut(baseline_rel, bins=bins, labels=labels, right=True).value_counts().sort_index()
    wisecondorx_counts = pd.cut(wisecondorx_rel, bins=bins, labels=labels, right=True).value_counts().sort_index()
    
    baseline_total = baseline_counts.sum()
    wisecondorx_total = wisecondorx_counts.sum()
    
    # Ensure all bins are present (fill with 0 if not)
    results = []
    for label in labels:
        baseline_count = baseline_counts.get(label, 0)
        wisecondorx_count = wisecondorx_counts.get(label, 0)
        baseline_pct = (baseline_count / baseline_total * 100) if baseline_total > 0 else 0
        wisecondorx_pct = (wisecondorx_count / wisecondorx_total * 100) if wisecondorx_total > 0 else 0
        
        results.append({
            'Bin': label,
            'Baseline Count': baseline_count,
            'Baseline %': f"{baseline_pct:.2f}%",
            'WisecondorX Count': wisecondorx_count,
            'WisecondorX %': f"{wisecondorx_pct:.2f}%"
        })
    
    results_df = pd.DataFrame(results)
    output_path = os.path.join(output_dir, 'relative_deviation_distribution.tsv')
    results_df.to_csv(output_path, sep='\t', index=False)
    logger.info(f"Saved relative deviation distribution: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate summary statistics from deviation files')
    parser.add_argument('input_dir', help='Input directory containing deviation/relative TSV files')
    parser.add_argument('output_dir', help='Output directory for summary files')
    parser.add_argument('integrated_dir', help='Directory containing integrated prediction files')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return
    
    # Step 1: Create summary table
    summary_df = create_summary_table(args.input_dir, args.output_dir, args.integrated_dir)
    
    if summary_df is None or len(summary_df) == 0:
        logger.error("Summary table is empty")
        return
    
    # Step 2: Analyze deviation
    analyze_deviation(summary_df, args.output_dir)
    
    # Step 3: Analyze relative deviation
    analyze_relative_deviation(summary_df, args.output_dir)
    
    logger.info("Summary analysis complete!")


if __name__ == '__main__':
    main()
