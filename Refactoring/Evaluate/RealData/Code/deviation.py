import pandas as pd
from pathlib import Path
from typing import Optional
from collections import defaultdict
from Code import utils

def get_chromosome_copy_number(df: pd.DataFrame, chrom: str) -> Optional[float]:
    """Xác định CN đại diện cho NST theo CN của phân đoạn dài nhất."""
    df = df.copy()
    df['chrom'] = df['chrom'].astype(str)
    
    sub = df[df['chrom'] == chrom]
    if sub.empty:
        return None
    
    sub = sub.copy()
    sub['length'] = sub['chromEnd'] - sub['chromStart']
    longest = sub.loc[sub['length'].idxmax()]
    return longest['copyNumber']

def run_deviation(experiment_id: str, merge_dir: str, integrate_dir: str, output_dir: str, chromosome_type: str = 'Autosome'):
    """Tính toán độ lệch giữa các thuật toán và BlueFuse."""
    merge_dir = Path(merge_dir)
    integrate_dir = Path(integrate_dir)
    output_dir = Path(output_dir)
    
    chromosomes_list = utils.AUTOSOMES if chromosome_type == 'Autosome' else utils.GONOSOMES
    integrate_rows_per_algorithm = defaultdict(list)
    summary_rows = []
    
    samples = [d for d in merge_dir.iterdir() if d.is_dir()]
    for sample_dir in samples:
        sample_id = sample_dir.name
        
        # Tải BlueFuse trước để xác định giới tính và CN tham chiếu
        bluefuse_file = sample_dir / f"{sample_id}_bluefuse_segments.bed"
        if not bluefuse_file.exists():
            continue
        bluefuse_df = pd.read_csv(bluefuse_file, sep='\t') if bluefuse_file.exists() else pd.DataFrame()
        if bluefuse_df.empty: 
            continue
        gender = utils.determine_gender(bluefuse_df)
        
        # Bỏ qua mẫu nữ nếu đang xử lý Gonosome
        if chromosome_type == 'Gonosome' and gender != 'Male':
            continue
        
        # Lấy CN đại diện của BlueFuse
        bluefuse_copy_numbers = {}
        for chromosome in chromosomes_list:
            bluefuse_copy_numbers[chromosome] = get_chromosome_copy_number(bluefuse_df, chromosome)
            
        # Xử lý tất cả thuật toán (bao gồm cả BlueFuse để tạo bảng tích hợp)
        algorithm_files = list(sample_dir.glob("*_segments.bed"))
        for algorithm_file in algorithm_files:
            algorithm_id = algorithm_file.name.replace(f"{sample_id}_", "").replace("_segments.bed", "")
            algorithm_df = pd.read_csv(algorithm_file, sep='\t') if algorithm_file.exists() else pd.DataFrame()
            
            # 1. Tích hợp dữ liệu
            row_integrate = {'sample': sample_id}
            algorithm_copy_numbers = {}
            for chromosome in chromosomes_list:
                copy_number = get_chromosome_copy_number(algorithm_df, chromosome)
                algorithm_copy_numbers[chromosome] = copy_number
                row_integrate[chromosome] = copy_number
            integrate_rows_per_algorithm[algorithm_id].append(row_integrate)
            
            # 2. Tính độ lệch (Cho các thuật toán khác so với BlueFuse)
            if algorithm_id == 'bluefuse':
                continue
                
            for chromosome in chromosomes_list:
                bluefuse_value = bluefuse_copy_numbers.get(chromosome)
                algorithm_value = algorithm_copy_numbers.get(chromosome)
                
                if bluefuse_value is None or algorithm_value is None:
                    continue
                
                if chromosome_type == 'Gonosome' and gender != 'Male':
                    continue
                
                expected = utils.get_expected_copy_number(chromosome, gender)
                if bluefuse_value == expected:
                    continue
                
                raw = algorithm_value - bluefuse_value
                if bluefuse_value > expected:
                    deviation = raw
                else:
                    deviation = -raw
                    
                # Relative
                if bluefuse_value != 0:
                    relative = round((deviation / bluefuse_value) * 100, 2)
                else:
                    relative = None
                    
                summary_rows.append({
                    'sample': sample_id,
                    'chrom': chromosome,
                    'BlueFuseCopyNumber': bluefuse_value,
                    'algorithm': algorithm_id,
                    'algorithmCopyNumber': algorithm_value,
                    'algorithmDeviation': deviation,
                    'algorithmRelative': f"{relative}%" if relative is not None else None
                })

    # Lưu bảng tích hợp
    for algorithm, rows in integrate_rows_per_algorithm.items():
        if rows:
            integrate_df = pd.DataFrame(rows)
            cols = ['sample'] + chromosomes_list
            for c in cols:
                if c not in integrate_df.columns:
                    integrate_df[c] = None
            integrate_df = integrate_df[cols]
            
            integrate_file = integrate_dir / f"{algorithm}_{chromosome_type.lower()}_integrate.tsv"
            integrate_df.to_csv(integrate_file, sep='\t', index=False)

    # Lưu bảng tổng hợp
    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        summary_file = output_dir / f"{experiment_id}_summary.tsv"
        summary_df.to_csv(summary_file, sep='\t', index=False)
