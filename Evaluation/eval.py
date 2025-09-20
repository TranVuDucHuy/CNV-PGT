import os
import pandas as pd
import argparse
from typing import Tuple

def classify_segment(row: pd.Series, mosaicism: float, min_length: int) -> Tuple[bool, str]:
    length = row['End'] - row['Start']
    if length < min_length:
        return False, ""
    cn = row['Copy Number']
    if cn < 2 - mosaicism:
        return True, "DEL"
    if cn > 2 + mosaicism:
        return True, "DUP"
    return False, ""

def fraction_same_type(segment: pd.Series, gt_segments: pd.DataFrame, mosaicism: float, min_length: int) -> float:
    """Tính tỷ lệ độ dài của segment (thuật toán) được ground truth báo cáo cùng loại CNV hoặc cùng trạng thái non-CNV.
    """
    chrom = str(segment['Chromosome'])
    length = segment['End'] - segment['Start']

    is_cnv_algo, algo_type = classify_segment(segment, mosaicism, min_length)

    matched = 0
    overlaps = gt_segments[gt_segments['Chromosome'].astype(str) == chrom]
    for _, gt_row in overlaps.iterrows():
        overlap_length = max(0, min(segment['End'], gt_row['End']) - max(segment['Start'], gt_row['Start']))
        if overlap_length == 0:
            continue
        gt_is_cnv, gt_type = classify_segment(gt_row, mosaicism, min_length)
        if is_cnv_algo:
            if gt_is_cnv and gt_type == algo_type:
                matched += overlap_length
        else:
            if not gt_is_cnv:
                matched += overlap_length
    return matched / length if length > 0 else 0.0

def main():
    parser = argparse.ArgumentParser(description="Đánh giá hiệu suất phát hiện CNV so với ground truth dựa trên tệp segment.")
    parser.add_argument('-i', '--input_dir', required=True, help="Đường dẫn đến thư mục chứa các tệp segment của thuật toán (thư mục Segment hoặc tương tự).")
    parser.add_argument('--mosaicism', type=float, default=0.5, help="Ngưỡng mosaicism (mặc định 0.5). CNV nếu CN < 2 - mosaicism hoặc CN > 2 + mosaicism.")
    parser.add_argument('--overlap', type=float, default=0.5, help="Ngưỡng phần trăm overlap để đánh giá (mặc định 0.5).")
    parser.add_argument('--min_length', type=int, default=5000000, help="Độ dài tối thiểu của segment để xét là CNV (mặc định 5 Mbp).")
    args = parser.parse_args()

    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"[LỖI] Thư mục đầu vào không tồn tại: {input_dir}")
        return

    # Danh sách thuật toán cần đánh giá: giả sử tên thư mục file có pattern <sample>_<algo>_segments.tsv
    algorithms_to_test = ['WisecondorX', 'Bicseq2', 'Baseline']
    total_scores = {algo: {'TP': 0, 'FP': 0, 'FN': 0, 'TN': 0} for algo in algorithms_to_test}

    sample_ids = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    
    print(f"Bắt đầu đánh giá trên {len(sample_ids)} mẫu với ngưỡng mosaicism={args.mosaicism}, overlap={args.overlap}, min_length={args.min_length}.")

    excluded_chroms = ['23','24']

    for sample_id in sample_ids:
        print(f"\n--- Mẫu: {sample_id} ---")
        sample_path = os.path.join(input_dir, sample_id)
        if not os.path.isdir(sample_path):
            print(f"  [BỎ QUA] Không tìm thấy thư mục sample: {sample_path}")
            continue

        # Ground truth giả định là file BlueFuse: <sample>_BlueFuse_segments.tsv hoặc tương tự
        gt_file = os.path.join(sample_path, f"{sample_id}_Bicseq2_segments.tsv")
        if gt_file is None:
            print("  [CẢNH BÁO] Không tìm thấy tệp ground truth (BlueFuse/Bicseq2). Bỏ qua mẫu này.")
            continue
        try:
            ground_truth_df = pd.read_csv(gt_file, sep='\t')
        except pd.errors.EmptyDataError:
            ground_truth_df = pd.DataFrame()

        ground_truth_df['Chromosome'] = ground_truth_df['Chromosome'].astype(str)
        ground_truth_df = ground_truth_df[~ground_truth_df['Chromosome'].isin(excluded_chroms)].copy()

        for algo in algorithms_to_test:
            algo_file = os.path.join(sample_path, f"{sample_id}_{algo}_segments.tsv")

            try:
                algo_df = pd.read_csv(algo_file, sep='\t')
            except pd.errors.EmptyDataError:
                algo_df = pd.DataFrame()

            algo_df['Chromosome'] = algo_df['Chromosome'].astype(str)
            algo_df = algo_df[~algo_df['Chromosome'].isin(excluded_chroms)].copy()

            tp=fp=tn=fn=0
            for _, segment in algo_df.iterrows():
                is_cnv, seg_type = classify_segment(segment, args.mosaicism, args.min_length)
                frac = fraction_same_type(segment, ground_truth_df, args.mosaicism, args.min_length)
                if is_cnv:
                    if frac >= args.overlap:
                        tp += 1
                    else:
                        fp += 1
                else:
                    if frac >= args.overlap:
                        tn += 1
                    else:
                        fn += 1
            print(f"  - {algo}: TP={tp} FP={fp} TN={tn} FN={fn}")
            total_scores[algo]['TP'] += tp
            total_scores[algo]['FP'] += fp
            total_scores[algo]['TN'] += tn
            total_scores[algo]['FN'] += fn

    # 3. Tính toán và in kết quả cuối cùng
    print("\n\n--- TỔNG KẾT HIỆU SUẤT TRÊN CÁC NHIỄM SẮC THỂ THƯỜNG ---")
    for algo, scores in total_scores.items():
        tp = scores['TP']
        fp = scores['FP']
        fn = scores['FN']
        tn = scores.get('TN', 0)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print(f"\n# Thuật toán: {algo}")
        print(f"  - TP: {tp}  FP: {fp}  TN: {tn}  FN: {fn}")
        print(f"  - Precision:  {precision:.2f}")
        print(f"  - Recall:     {recall:.2f}")
        print(f"  - Specificity:{specificity:.2f}")
        print(f"  - Accuracy:   {accuracy:.2f}")
        print(f"  - F1-Score:   {f1_score:.2f}")

if __name__ == '__main__':
    main()