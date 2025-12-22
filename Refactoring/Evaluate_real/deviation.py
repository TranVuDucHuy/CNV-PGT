import os
import argparse
from typing import Optional
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

AUTOSOMES = [str(i) for i in range(1, 23)]  # 1..22


def load_integrated_file(file_path: str) -> pd.DataFrame:
    """Load integrated TSV file."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path, sep='\t')
    return df


def calculate_deviation_1(algo_cn: Optional[float], bf_cn: Optional[float]) -> Optional[float]:
    """
    Calculate deviation-1 metric.
    """
    if pd.isna(algo_cn) or pd.isna(bf_cn):
        return None
    
    if bf_cn > 2:
        return algo_cn - bf_cn
    elif bf_cn < 2:
        return bf_cn - algo_cn
    else:  # bf_cn == 2
        return None


def calculate_deviation_2(algo_cn: Optional[float], bf_cn: Optional[float]) -> Optional[float]:
    """
    Calculate deviation-2 metric.
    - If bf_cn > 2 or bf_cn < 2: result = None
    - If bf_cn = 2: result = algo_cn - 2
    """
    if pd.isna(algo_cn) or pd.isna(bf_cn):
        return None
    
    if bf_cn == 2:
        return algo_cn - 2
    else:
        return None


def calculate_relative_1(algo_cn: Optional[float], bf_cn: Optional[float]) -> Optional[float]:
    """
    Calculate relative-1 metric.
    - If bf_cn > 2: result = (algo_cn - bf_cn) / bf_cn
    - If bf_cn < 2: result = (bf_cn - algo_cn) / bf_cn
    - If bf_cn = 2: result = None
    """
    if pd.isna(algo_cn) or pd.isna(bf_cn):
        return None
    
    if bf_cn > 2:
        return (algo_cn - bf_cn) / bf_cn
    elif bf_cn < 2:
        return (bf_cn - algo_cn) / bf_cn
    else:  # bf_cn == 2
        return None


def calculate_relative_2(algo_cn: Optional[float], bf_cn: Optional[float]) -> Optional[float]:
    """
    Calculate relative-2 metric.
    - If bf_cn > 2 or bf_cn < 2: result = None
    - If bf_cn = 2: result = (algo_cn - 2) / 2
    """
    if pd.isna(algo_cn) or pd.isna(bf_cn):
        return None
    
    if bf_cn == 2:
        return (algo_cn - 2) / 2
    else:
        return None


def compute_deviation_metrics(algo_df: pd.DataFrame, bf_df: pd.DataFrame, 
                             metric_type: str) -> pd.DataFrame:
    """
    Compute deviation metrics between algorithm and BlueFuse data.
    """
    # Merge on sample_id
    merged = algo_df.merge(bf_df, on='sample_id', suffixes=('_algo', '_bf'))
    
    result_data = []
    
    for idx, row in merged.iterrows():
        sample_id = row['sample_id']
        result_row = {'sample_id': sample_id}
        
        for chr_ in AUTOSOMES:
            algo_col = f"{chr_}_algo"
            bf_col = f"{chr_}_bf"
            
            algo_cn = row[algo_col]
            bf_cn = row[bf_col]
            
            if metric_type == 'deviation-1':
                value = calculate_deviation_1(algo_cn, bf_cn)
            elif metric_type == 'deviation-2':
                value = calculate_deviation_2(algo_cn, bf_cn)
            elif metric_type == 'relative-1':
                value = calculate_relative_1(algo_cn, bf_cn)
            elif metric_type == 'relative-2':
                value = calculate_relative_2(algo_cn, bf_cn)
            else:
                raise ValueError(f"Unknown metric type: {metric_type}")
            
            result_row[chr_] = value
        
        result_data.append(result_row)
    
    result_df = pd.DataFrame(result_data)
    return result_df


def process_deviation_metrics(input_dir: str, output_dir: str) -> None:
    """
    Process all deviation metrics.
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load integrated files
    logger.info("Loading integrated files...")
    baseline_df = load_integrated_file(os.path.join(input_dir, 'baseline_integrated.tsv'))
    wisecondorx_df = load_integrated_file(os.path.join(input_dir, 'wisecondorx_integrated.tsv'))
    bluefuse_df = load_integrated_file(os.path.join(input_dir, 'bluefuse_integrated.tsv'))
    
    if baseline_df is None or wisecondorx_df is None or bluefuse_df is None:
        logger.error("Failed to load one or more integrated files")
        return
    
    logger.info(f"Loaded baseline: {len(baseline_df)} samples")
    logger.info(f"Loaded wisecondorx: {len(wisecondorx_df)} samples")
    logger.info(f"Loaded bluefuse: {len(bluefuse_df)} samples")
    
    # Compute metrics for baseline vs bluefuse
    logger.info("Computing deviation metrics for baseline vs bluefuse...")
    
    dev1_baseline = compute_deviation_metrics(baseline_df, bluefuse_df, 'deviation-1')
    dev2_baseline = compute_deviation_metrics(baseline_df, bluefuse_df, 'deviation-2')
    rel1_baseline = compute_deviation_metrics(baseline_df, bluefuse_df, 'relative-1')
    rel2_baseline = compute_deviation_metrics(baseline_df, bluefuse_df, 'relative-2')
    
    # Compute metrics for wisecondorx vs bluefuse
    logger.info("Computing deviation metrics for wisecondorx vs bluefuse...")
    
    dev1_wisecondorx = compute_deviation_metrics(wisecondorx_df, bluefuse_df, 'deviation-1')
    dev2_wisecondorx = compute_deviation_metrics(wisecondorx_df, bluefuse_df, 'deviation-2')
    rel1_wisecondorx = compute_deviation_metrics(wisecondorx_df, bluefuse_df, 'relative-1')
    rel2_wisecondorx = compute_deviation_metrics(wisecondorx_df, bluefuse_df, 'relative-2')
    
    # Save to TSV files
    output_files = {
        'deviation-1-baseline-bluefuse.tsv': dev1_baseline,
        'deviation-2-baseline-bluefuse.tsv': dev2_baseline,
        'relative-1-baseline-bluefuse.tsv': rel1_baseline,
        'relative-2-baseline-bluefuse.tsv': rel2_baseline,
        'deviation-1-wisecondorx-bluefuse.tsv': dev1_wisecondorx,
        'deviation-2-wisecondorx-bluefuse.tsv': dev2_wisecondorx,
        'relative-1-wisecondorx-bluefuse.tsv': rel1_wisecondorx,
        'relative-2-wisecondorx-bluefuse.tsv': rel2_wisecondorx,
    }
    
    for filename, df in output_files.items():
        output_path = os.path.join(output_dir, filename)
        # Save with NaN values as empty (null)
        df.to_csv(output_path, sep='\t', index=False, na_rep='')
        logger.info(f"Saved: {output_path}")
    
    logger.info("Deviation analysis complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Calculate deviation metrics between algorithms and BlueFuse'
    )
    parser.add_argument(
        'input_dir',
        help='Input directory containing integrated TSV files (baseline_integrated.tsv, wisecondorx_integrated.tsv, bluefuse_integrated.tsv)'
    )
    parser.add_argument(
        'output_dir',
        help='Output directory for deviation metric files'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_dir):
        logger.error(f"Input directory does not exist: {args.input_dir}")
        return
    
    process_deviation_metrics(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
