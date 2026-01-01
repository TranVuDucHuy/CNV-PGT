import os
import argparse
from typing import Dict, List, Tuple
import pandas as pd
import logging

AUTOSOMES = [str(i) for i in range(1, 23)]  # 1..22

def compute_metrics(tp: int, fp: int, tn: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    return {
        "Precision": precision,
        "Recall": recall,
        "Specificity": specificity,
        "Accuracy": accuracy
    }

def load_segments(path: str) -> pd.DataFrame:
    """Đọc TSV đã chuẩn hoá cột và chỉ giữ autosome 1..22."""
    try:
        df = pd.read_csv(path, sep='\t')
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=['Chromosome', 'Start', 'End', 'Copy Number'])

    df['Chromosome'] = df['Chromosome'].astype(str)
    df['Start'] = pd.to_numeric(df['Start'], errors='coerce')
    df['End'] = pd.to_numeric(df['End'], errors='coerce')
    df['Copy Number'] = pd.to_numeric(df['Copy Number'], errors='coerce')
    df = df.dropna(subset=['Chromosome', 'Start', 'End', 'Copy Number'])
    df = df[df['End'] > df['Start']].copy()

    df = df[df['Chromosome'].isin(AUTOSOMES)].copy()
    return df

def percent_types_by_chr(df: pd.DataFrame, gain_thr: float, loss_thr: float
                        ) -> Dict[str, Dict[str, float]]:
    """
    Trả về map: chr -> {'Gain': %, 'Loss': %, 'No Change': %}
    """
    out: Dict[str, Dict[str, float]] = {}
    for chr_ in AUTOSOMES:
        sub = df[df['Chromosome'] == chr_]

        lengths = (sub['End'] - sub['Start']).clip(lower=0)
        total = lengths.sum()

        gain_len = sub.loc[sub['Copy Number'] >= gain_thr, ['Start', 'End']].eval('End - Start').clip(lower=0).sum()
        loss_len = sub.loc[sub['Copy Number'] <= loss_thr, ['Start', 'End']].eval('End - Start').clip(lower=0).sum()
        no_len = max(0.0, total - gain_len - loss_len)

        out[chr_] = {
            'Gain': 100.0 * gain_len / total if total else 0.0,
            'Loss': 100.0 * loss_len / total if total else 0.0,
            'No Change': 100.0 * no_len / total if total else 0.0
        }
    return out

def type_from_percents(pcts: Dict[str, float]) -> str:
    """Chọn nhãn có % lớn nhất. Nếu hòa, ưu tiên Gain > Loss > No Change."""
    order = ['Gain', 'Loss', 'No Change']
    best = max(order, key=lambda k: (pcts.get(k, 0.0), -order.index(k)))
    return best

def tally_confusion(basetype: str, bftype: str) -> Tuple[int, int, int, int]:
    """(TP, FP, FN, TN)"""
    if basetype == bftype:
        if basetype == 'No Change':
            return 0, 0, 0, 1   # TN
        else:
            return 1, 0, 0, 0   # TP
    else:
        if bftype == 'No Change' and basetype != 'No Change':
            return 0, 1, 0, 0   # FP
        # if basetype != 'No Change' and bftype in ('Gain', 'Loss'):
        return 0, 0, 1, 0   # FN

def fmt_pcts(p):
    # p là dict {'Gain':%, 'Loss':%, 'No Change':%}
    return f"G={p['Gain']:.2f}% | L={p['Loss']:.2f}% | N={p['No Change']:.2f}%"

def evaluate_sample(sample_id: str, sample_dir: str, gain_thr: float, loss_thr: float,
                   method: str = 'baseline') -> Dict[str, int]:
    """Tính TP/FP/FN/TN tổng cho sample + bảng debug loại chr.
    method: 'baseline' hoặc 'wisecondorx'
    """
    if method == 'baseline':
        test_path = os.path.join(sample_dir, f"{sample_id}_baseline_segments.tsv")
        method_label = 'baseline'
    elif method == 'wisecondorx':
        test_path = os.path.join(sample_dir, f"{sample_id}_wisecondorx_segments.tsv")
        method_label = 'wisecondorx'
    else:
        raise ValueError(f"method không hợp lệ: {method}")
    
    bluefuse_path = os.path.join(sample_dir, f"{sample_id}_bluefuse_segments.tsv")

    if not os.path.isfile(test_path):
        raise FileNotFoundError(f"Thiếu file: {test_path}")
    if not os.path.isfile(bluefuse_path):
        raise FileNotFoundError(f"Thiếu file: {bluefuse_path}")

    test_df = load_segments(test_path)
    bf_df = load_segments(bluefuse_path)

    test_pcts = percent_types_by_chr(test_df, gain_thr, loss_thr)
    bf_pcts = percent_types_by_chr(bf_df, gain_thr, loss_thr)

    tp=fp=fn=tn=0
    for chr_ in AUTOSOMES:
        t_type = type_from_percents(test_pcts[chr_])
        f_type = type_from_percents(bf_pcts[chr_])
        d_tp, d_fp, d_fn, d_tn = tally_confusion(t_type, f_type)
        tp += d_tp; fp += d_fp; fn += d_fn; tn += d_tn
        if d_fp == 1:
            logging.info(
                "[FP] sample=%s chr=%s | %s=%s (%s) | bluefuse=%s (%s)",
                sample_id, chr_, method_label,
                t_type, fmt_pcts(test_pcts[chr_]),
                f_type, fmt_pcts(bf_pcts[chr_])
            )
        if d_fn == 1:
            logging.info(
                "[FN] sample=%s chr=%s | %s=%s (%s) | bluefuse=%s (%s)",
                sample_id, chr_, method_label,
                t_type, fmt_pcts(test_pcts[chr_]),
                f_type, fmt_pcts(bf_pcts[chr_])
            )
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn}

def evaluate_method(input_dir: str, sample_ids: List[str], method: str, 
                   gain_thr: float, loss_thr: float, output_file: str):
    """Đánh giá một phương pháp (baseline hoặc wisecondorx) so với bluefuse."""
    rows = []
    tp_all=fp_all=fn_all=tn_all = 0

    print(f"\n{'='*60}")
    print(f"Đánh giá {method.upper()} vs BLUEFUSE")
    print(f"{'='*60}")
    
    for sid in sample_ids:
        print(f"\n--- Mẫu: {sid} ---")
        sdir = os.path.join(input_dir, sid)
        try:
            counts = evaluate_sample(sid, sdir, gain_thr, loss_thr, method=method)
        except Exception as e:
            print(f"  [BỎ QUA] {sid}: {e}")
            continue

        tp, fp, fn, tn = counts['TP'], counts['FP'], counts['FN'], counts['TN']
        m = compute_metrics(tp, fp, tn, fn)
        print(f"  KQ: TP={tp} FP={fp} FN={fn} TN={tn} | "
              f"Prec={m['Precision']:.2f} Rec={m['Recall']:.2f} "
              f"Spec={m['Specificity']:.2f} Acc={m['Accuracy']:.2f}")

        if m['Accuracy'] < 1:
            logging.info(f"{method}: {sid}")

        rows.append({
            'sample_id': sid,
            'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'Precision': round(m['Precision'], 6),
            'Recall': round(m['Recall'], 6),
            'Specificity': round(m['Specificity'], 6),
            'Accuracy': round(m['Accuracy'], 6),
        })

        tp_all += tp; fp_all += fp; fn_all += fn; tn_all += tn

    m_all = compute_metrics(tp_all, fp_all, tn_all, fn_all)
    rows.append({
        'sample_id': 'ALL',
        'TP': tp_all, 'FP': fp_all, 'FN': fn_all, 'TN': tn_all,
        'Precision': round(m_all['Precision'], 6),
        'Recall': round(m_all['Recall'], 6),
        'Specificity': round(m_all['Specificity'], 6),
        'Accuracy': round(m_all['Accuracy'], 6),
    })

    df_out = pd.DataFrame(rows)
    df_out.to_csv(output_file, sep='\t', index=False)
    print(f"\n[OK] Đã ghi kết quả {method}: {output_file}")


# ==== CLI ====
def main():
    parser = argparse.ArgumentParser(description="Đánh giá TP/FP/FN/TN theo chromosome giữa baseline/wisecondorx và bluefuse.")
    parser.add_argument('-i', '--input_dir', required=True, help="Thư mục chứa các thư mục sample.")
    parser.add_argument('--gain-thr', type=float, default=2.45, help="Ngưỡng CN cho Gain (>=). Mặc định 2.45")
    parser.add_argument('--loss-thr', type=float, default=1.55, help="Ngưỡng CN cho Loss (<=). Mặc định 1.55")
    args = parser.parse_args()

    if not logging.getLogger().handlers:
        logging.basicConfig(
            filename='chrEval.log',
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"[LỖI] Thư mục đầu vào không tồn tại: {input_dir}")
        return

    sample_ids = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    sample_ids.sort()

    print(f"Bắt đầu chr-eval trên {len(sample_ids)} mẫu | gain_thr={args.gain_thr} loss_thr={args.loss_thr}")
    
    # Đánh giá baseline vs bluefuse
    evaluate_method(input_dir, sample_ids, 'baseline', args.gain_thr, args.loss_thr, 
                   'chr_eval_baseline.tsv')
    
    # Đánh giá wisecondorx vs bluefuse
    evaluate_method(input_dir, sample_ids, 'wisecondorx', args.gain_thr, args.loss_thr, 
                   'chr_eval_wisecondorx.tsv')
    
    print(f"\n{'='*60}")
    print("HOÀN TẤT ĐÁNH GIÁ!")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
