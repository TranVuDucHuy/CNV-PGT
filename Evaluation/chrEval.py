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

def evaluate_sample(sample_id: str, sample_dir: str, gain_thr: float, loss_thr: float
                   ) -> Dict[str, int]:
    """Tính TP/FP/FN/TN tổng cho sample + bảng debug loại chr."""
    baseline_path = os.path.join(sample_dir, f"{sample_id}_baseline_segments.tsv")
    bluefuse_path = os.path.join(sample_dir, f"{sample_id}_bluefuse_segments.tsv")

    if not os.path.isfile(baseline_path):
        raise FileNotFoundError(f"Thiếu file: {baseline_path}")
    if not os.path.isfile(bluefuse_path):
        raise FileNotFoundError(f"Thiếu file: {bluefuse_path}")

    base_df = load_segments(baseline_path)
    bf_df = load_segments(bluefuse_path)
    # base_df = pd.read_csv(baseline_path, sep='\t')
    # bf_df = pd.read_csv(bluefuse_path, sep='\t')

    base_pcts = percent_types_by_chr(base_df, gain_thr, loss_thr)
    bf_pcts = percent_types_by_chr(bf_df, gain_thr, loss_thr)

    tp=fp=fn=tn=0
    for chr_ in AUTOSOMES:
        b_type = type_from_percents(base_pcts[chr_])
        f_type = type_from_percents(bf_pcts[chr_])
        d_tp, d_fp, d_fn, d_tn = tally_confusion(b_type, f_type)
        tp += d_tp; fp += d_fp; fn += d_fn; tn += d_tn
        if d_fp == 1:
            logging.info(
                "[FP] sample=%s chr=%s | baseline=%s (%s) | bluefuse=%s (%s)",
                sample_id, chr_,
                b_type, fmt_pcts(base_pcts[chr_]),
                f_type, fmt_pcts(bf_pcts[chr_])
            )
        if d_fn == 1:
            logging.info(
                "[FN] sample=%s chr=%s | baseline=%s (%s) | bluefuse=%s (%s)",
                sample_id, chr_,
                b_type, fmt_pcts(base_pcts[chr_]),
                f_type, fmt_pcts(bf_pcts[chr_])
            )
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn}

# ==== CLI ====
def main():
    parser = argparse.ArgumentParser(description="Đánh giá TP/FP/FN/TN theo chromosome giữa baseline và bluefuse.")
    parser.add_argument('-i', '--input_dir', required=True, help="Thư mục chứa các thư mục sample (A).")
    parser.add_argument('--gain-thr', type=float, default=2.45, help="Ngưỡng CN cho Gain (>=). Mặc định 2.5")
    parser.add_argument('--loss-thr', type=float, default=1.55, help="Ngưỡng CN cho Loss (<=). Mặc định 1.5")
    parser.add_argument('--output', type=str, default='chr_eval.tsv', help="Bảng kết quả (tsv/csv). Mặc định chr_eval.tsv")
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

    rows = []
    tp_all=fp_all=fn_all=tn_all = 0

    print(f"Bắt đầu chr-eval trên {len(sample_ids)} mẫu | gain_thr={args.gain_thr} loss_thr={args.loss_thr}")
    for sid in sample_ids:
        print(f"\n--- Mẫu: {sid} ---")
        sdir = os.path.join(input_dir, sid)
        try:
            counts = evaluate_sample(sid, sdir, args.gain_thr, args.loss_thr)
        except Exception as e:
            print(f"  [BỎ QUA] {sid}: {e}")
            continue

        tp, fp, fn, tn = counts['TP'], counts['FP'], counts['FN'], counts['TN']
        m = compute_metrics(tp, fp, tn, fn)
        print(f"  KQ: TP={tp} FP={fp} FN={fn} TN={tn} | "
              f"Prec={m['Precision']:.2f} Rec={m['Recall']:.2f} "
              f"Spec={m['Specificity']:.2f} Acc={m['Accuracy']:.2f}")

        if m['Accuracy'] < 1:
            logging.info(f"{sid}")

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
    out_path = args.output
    _, ext = os.path.splitext(out_path.lower())
    if ext == '.csv':
        df_out.to_csv(out_path, index=False)
    else:
        if ext != '.tsv':
            print(f"[CẢNH BÁO] Đuôi '{ext}' không quen, mặc định ghi TSV.")
        df_out.to_csv(out_path, sep='\t', index=False)
    print(f"\n[OK] Đã ghi kết quả: {out_path}")

if __name__ == '__main__':
    main()
