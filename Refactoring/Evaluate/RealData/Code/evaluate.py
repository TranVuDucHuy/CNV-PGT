import pandas as pd
from pathlib import Path
from Code import utils

def get_chromosome_type(df: pd.DataFrame, chromosome: str, gender: str) -> tuple[str, float]:
    """Xác định trạng thái Gain/Loss/Normal của một NST và phần trăm của loại đó."""
    df = df.copy()
    df['chrom'] = df['chrom'].astype(str)
    
    sub = df[df['chrom'] == chromosome]
    if sub.empty:
        return 'No Change', 0.0
        
    lengths = (sub['chromEnd'] - sub['chromStart']).clip(lower=0)
    total_length = lengths.sum()
    if total_length == 0:
        return 'No Change', 0.0

    # Xác định ngưỡng dựa trên giá trị CN bình thường dự kiến
    expected_copy_number = utils.get_expected_copy_number(chromosome, gender)
    gain_threshold = expected_copy_number + utils.MOSAIC_THRESHOLD
    loss_threshold = expected_copy_number - utils.MOSAIC_THRESHOLD
    
    # Tính độ dài các phân đoạn Gain/Loss
    gain_length = sub.loc[sub['copyNumber'] >= gain_threshold, ['chromStart', 'chromEnd']].eval('chromEnd - chromStart').sum()
    loss_length = sub.loc[sub['copyNumber'] <= loss_threshold, ['chromStart', 'chromEnd']].eval('chromEnd - chromStart').sum()
    no_change_length = total_length - gain_length - loss_length
    
    # Tính phần trăm và chọn loại có % lớn nhất
    pcts = {
        'Gain': gain_length / total_length,
        'Loss': loss_length / total_length,
        'No Change': no_change_length / total_length
    }
    
    order = ['Gain', 'Loss', 'No Change']
    chromosome_type = max(order, key=lambda k: (pcts.get(k, 0.0), -order.index(k)))
    
    return chromosome_type, pcts[chromosome_type]

def calculate_confusion(bluefuse_type: str, algorithm_type: str) -> str:
    """Xác định loại kết quả so sánh: TP, FP, FN, hoặc TN."""
    if bluefuse_type == algorithm_type:
        return 'TN' if bluefuse_type == 'No Change' else 'TP'
    else:
        return 'FP' if bluefuse_type == 'No Change' else 'FN'

def summarize_results(result_df: pd.DataFrame, experiment_id: str, output_dir: Path):
    """Tổng hợp và xuất kết quả đánh giá."""
    # Summary gộp theo algorithm
    summary_total = result_df.groupby(['algorithm', 'type']).size().unstack(fill_value=0).reset_index()
    for column in ['TP', 'FP', 'FN', 'TN']:
        if column not in summary_total.columns:
            summary_total[column] = 0
    summary_total = summary_total[['algorithm', 'TP', 'FP', 'FN', 'TN']]
    
    summary_dst = output_dir / f"{experiment_id}_chrEval_summary.tsv"
    summary_total.to_csv(summary_dst, sep='\t', index=False)
    
    # FP, FN chi tiết
    fp_df = result_df[result_df['type'] == 'FP'][['algorithm', 'sample', 'chromosome', 'algorithmType', 'algorithmTypePercent', 'bluefuseType', 'bluefuseTypePercent']]
    fp_dst = output_dir / f"{experiment_id}_chrEval_FP.tsv"
    fp_df.to_csv(fp_dst, sep='\t', index=False)

    fn_df = result_df[result_df['type'] == 'FN'][['algorithm', 'sample', 'chromosome', 'algorithmType', 'algorithmTypePercent', 'bluefuseType', 'bluefuseTypePercent']]
    fn_dst = output_dir / f"{experiment_id}_chrEval_FN.tsv"
    fn_df.to_csv(fn_dst, sep='\t', index=False)

def run_evaluate(experiment_id: str, merge_dir: str, output_dir: str, chromosome_type: str = 'Autosome'):
    """Đánh giá hiệu suất các thuật toán so với BlueFuse."""
    merge_dir = Path(merge_dir)
    output_dir = Path(output_dir)
    
    chromosomes_list = utils.AUTOSOMES if chromosome_type == 'Autosome' else utils.GONOSOMES
    
    results = []    
    samples = [d for d in merge_dir.iterdir() if d.is_dir()]
    for sample_dir in samples:
        sample_id = sample_dir.name
        
        # Ground Truth
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
        
        # Xác định trạng thái của BlueFuse cho từng NST
        bluefuse_type_map = {}
        for chromosome in chromosomes_list:
            bluefuse_type_map[chromosome] = get_chromosome_type(bluefuse_df, chromosome, gender)
            
        # Đánh giá các thuật toán khác
        algorithm_files = list(sample_dir.glob("*_segments.bed"))
        for algorithm_file in algorithm_files:
            algorithm_id = algorithm_file.name.replace(f"{sample_id}_", "").replace("_segments.bed", "")
            if algorithm_id == 'bluefuse':
                continue
            algorithm_df = pd.read_csv(algorithm_file, sep='\t') if algorithm_file.exists() else pd.DataFrame()
            
            # Tính metrics cho từng NST
            for chromosome in chromosomes_list:
                algorithm_type, algorithm_percent = get_chromosome_type(algorithm_df, chromosome, gender)
                bluefuse_type, bluefuse_percent = bluefuse_type_map[chromosome]
                confusion_type = calculate_confusion(bluefuse_type, algorithm_type)
                results.append({
                    'sample': sample_id,
                    'algorithm': algorithm_id,
                    'chromosome': chromosome,
                    'algorithmType': algorithm_type,
                    'algorithmTypePercent': algorithm_percent,
                    'bluefuseType': bluefuse_type,
                    'bluefuseTypePercent': bluefuse_percent,
                    'type': confusion_type,
                    'gender': gender
                })
                
    # Tổng hợp kết quả
    if results:
        result_df = pd.DataFrame(results)
        summarize_results(result_df, experiment_id, output_dir)
