import os
import argparse
from typing import Dict, List, Optional
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

AUTOSOMES = [str(i) for i in range(1, 23)]  # 1..22


def load_segments(path: str) -> pd.DataFrame:
    """Load a segments TSV file and normalize columns."""
    try:
        df = pd.read_csv(path, sep='\t')
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=['Chromosome', 'Start', 'End', 'Copy Number'])
    
    # Normalize column names and data types
    df['Chromosome'] = df['Chromosome'].astype(str)
    df['Start'] = pd.to_numeric(df['Start'], errors='coerce')
    df['End'] = pd.to_numeric(df['End'], errors='coerce')
    df['Copy Number'] = pd.to_numeric(df['Copy Number'], errors='coerce')
    df = df.dropna(subset=['Chromosome', 'Start', 'End', 'Copy Number'])
    df = df[df['Chromosome'].isin(AUTOSOMES)].copy()
    
    return df


def get_longest_segment_cn(df: pd.DataFrame, chromosome: str) -> Optional[float]:
    """
    Get the Copy Number of the longest segment for a given chromosome.
    """
    chr_segments = df[df['Chromosome'] == chromosome]
    
    if chr_segments.empty:
        return None
    
    chr_segments = chr_segments.copy()
    chr_segments['Length'] = chr_segments['End'] - chr_segments['Start']
    longest = chr_segments.loc[chr_segments['Length'].idxmax()]
    
    return longest['Copy Number']


def process_sample(sample_dir: str, sample_id: str, tool_name: str) -> Dict[str, Optional[float]]:
    """
    Process a single sample for a specific tool (baseline, wisecondorx, or bluefuse).
    """
    segments_file = os.path.join(sample_dir, f"{sample_id}_{tool_name}_segments.tsv")
    
    if not os.path.exists(segments_file):
        logger.warning(f"File not found: {segments_file}")
        return {chr_: None for chr_ in AUTOSOMES}
    
    df = load_segments(segments_file)
    
    result = {}
    for chromosome in AUTOSOMES:
        cn = get_longest_segment_cn(df, chromosome)
        result[chromosome] = cn
    
    return result


def integrate_results(input_dir: str, output_dir: str) -> None:
    """
    Integrate results from baseline, wisecondorx, and bluefuse tools.
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    sample_dirs = []
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path):
            sample_dirs.append((item, item_path))
    
    if not sample_dirs:
        logger.warning(f"No sample directories found in {input_dir}")
        return
    
    sample_dirs.sort()
    logger.info(f"Found {len(sample_dirs)} sample directories")
    
    # Process each tool
    tools = ['baseline', 'wisecondorx', 'bluefuse']
    
    for tool_name in tools:
        logger.info(f"Processing {tool_name}...")
        
        # Collect results for all samples
        results = []
        
        for sample_id, sample_dir in sample_dirs:
            chr_cn_map = process_sample(sample_dir, sample_id, tool_name)
            
            # Build row data
            row_data = {'sample_id': sample_id}
            for chr_ in AUTOSOMES:
                row_data[chr_] = chr_cn_map[chr_]
            
            results.append(row_data)
        
        # Create DataFrame
        df_result = pd.DataFrame(results)
        
        # Reorder columns: sample_id first, then chromosomes 1-22
        columns = ['sample_id'] + AUTOSOMES
        df_result = df_result[columns]
        
        # Save to TSV
        output_file = os.path.join(output_dir, f"{tool_name}_integrated.tsv")
        df_result.to_csv(output_file, sep='\t', index=False)
        logger.info(f"Saved: {output_file}")
    
    logger.info("Integration complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Integrate chromosome copy number results from multiple tools'
    )
    parser.add_argument(
        'input_dir',
        help='Input directory containing sample subdirectories'
    )
    parser.add_argument(
        'output_dir',
        help='Output directory for integrated results'
    )
    
    args = parser.parse_args()
    
    integrate_results(args.input_dir, args.output_dir)


if __name__ == '__main__':
    main()
