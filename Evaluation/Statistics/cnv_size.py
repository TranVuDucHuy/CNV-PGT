#!/usr/bin/env python3

from __future__ import annotations

import argparse
import pandas as pd  # sử dụng pandas theo yêu cầu dữ liệu nhỏ (~200 dòng)
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Tuple


# ===================== Cấu hình các bins và copy number levels =====================
SIZE_BINS: List[Tuple[str, int, int]] = [
    ("<20Mbp", 0, 20_000_000),        # [0, 20M)
    ("20-40Mbp", 20_000_000, 40_000_000),  # [20M, 40M)
    ("40-80Mbp", 40_000_000, 80_000_000),  # [40M, 80M)
    (">80Mbp", 80_000_000, -1),       # [80M, +inf)
]

COPY_NUMBER_LEVELS: List[float] = [round(1.0 + i * 0.1, 1) for i in range(0, 21)]  # 1.0 .. 3.0

# Hậu tố file cần loại khỏi tên sample
SUFFIX = "_BlueFuse_segments.tsv"


def round_copy_number(value: str) -> float:
    """Làm tròn half-up đến 1 chữ số sau dấu phẩy, clamp vào [1.0, 3.0]."""
    try:
        d = Decimal(value)
    except Exception:
        return 0.0  # giá trị lỗi -> sẽ bị bỏ qua vì không match list
    d = d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    f = float(d)
    if f < 1.0:
        f = 1.0
    elif f > 3.0:
        f = 3.0
    return round(f, 1)


def length_to_bin(length_bp: int) -> str | None:
    for name, start, end in SIZE_BINS:
        if end == -1:  # open ended
            if length_bp >= start:
                return name
        else:
            if start <= length_bp < end:
                return name
    return None


def build_header() -> List[str]:
    header: List[str] = ["Sample"]
    for size_name, _, _ in SIZE_BINS:
        for cn in COPY_NUMBER_LEVELS:
            header.append(f"{size_name}_CN{cn:.1f}")
    return header

def count_segments(file_path: Path) -> pd.DataFrame:
    name = file_path.name
    # Loại bỏ đuôi _BlueFuse_segments.tsv để lấy sample name chuẩn
    sample_name = name[:-len(SUFFIX)] if name.endswith(SUFFIX) else name.rsplit('.', 1)[0]

    try:
        df = pd.read_csv(file_path, sep='\t', dtype=str, engine='python')
    except Exception:
        return pd.DataFrame([{"Sample": sample_name}])
    if df.empty or not {'Start', 'End', 'Copy Number'}.issubset(df.columns):
        return pd.DataFrame([{"Sample": sample_name}])

    df['Start'] = pd.to_numeric(df['Start'], errors='coerce')
    df['End'] = pd.to_numeric(df['End'], errors='coerce')

    df['length'] = df['End'] - df['Start']
    df['size_bin'] = df['length'].apply(lambda length: length_to_bin(int(length)))
    df = df[df['size_bin'].notna()]
    if df.empty:
        return pd.DataFrame([{"Sample": sample_name}])

    df['CN_Rounded'] = df['Copy Number'].astype(str).apply(round_copy_number)
    df = df[df['CN_Rounded'].isin(COPY_NUMBER_LEVELS)]
    if df.empty:
        return pd.DataFrame([{"Sample": sample_name}])

    grouped = (df.groupby(['size_bin', 'CN_Rounded'])
                 .size()
                 .reset_index(name='count'))
    row: Dict[str, int | str] = {"Sample": sample_name}
    for _, r in grouped.iterrows():
        key = f"{r['size_bin']}_CN{r['CN_Rounded']:.1f}"
        row[key] = int(r['count'])
    return pd.DataFrame([row])

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tạo bảng đếm số lượng segment theo bins chiều dài và copy number.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', dest='input', type=str, default='.',
                        help=f'Thư mục chứa các file *{SUFFIX}')
    parser.add_argument('-o', '--output', dest='output', type=str, default=None,
                        help='Đường dẫn file TSV kết quả (stdout nếu bỏ trống)')
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    input_dir = Path(args.input).resolve()
    if not input_dir.exists():
        print(f"[ERROR] Thư mục input không tồn tại: {input_dir}", file=sys.stderr)
        return 1
    # Tìm các file theo mẫu cố định với hậu tố _BlueFuse_segments.tsv
    files = sorted(input_dir.rglob(f"*{SUFFIX}"))
    # Tạo DataFrame tổng hợp từ từng file
    df_list: List[pd.DataFrame] = [count_segments(p) for p in files]
    if df_list:
        df = pd.concat(df_list, ignore_index=True)
    else:
        df = pd.DataFrame(columns=["Sample"])  # không có file nào -> chỉ có header Sample (sau sẽ expand header chuẩn)

    # Chuẩn bị ghi
    header = build_header()
    if df.empty:
        df_out = pd.DataFrame(columns=header)
    else:
        df_out = df.reindex(columns=header, fill_value=0)

    output_path = Path(args.output).resolve() if args.output else None
    out_fh = sys.stdout if output_path is None else output_path.open('w', encoding='utf-8', newline='')
    close_after = output_path is not None
    try:
        df_out.to_csv(out_fh, sep='\t', index=False)
    finally:
        if close_after:
            out_fh.close()
    # Thông tin tóm tắt
    print(f"[INFO] Đã xử lý {len(files)} file(s).", file=sys.stderr)
    if output_path:
        print(f"[INFO] Kết quả được ghi vào: {output_path}", file=sys.stderr)
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
