#!/usr/bin/env python3

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys
from typing import Dict, List

import pandas as pd

# ===================== Cấu hình =====================
SUFFIX = "_BlueFuse_segments.tsv"  # hậu tố file cần tìm

# Các chromosome hợp lệ: 1..24
CHR_RANGE = list(range(1, 25))

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tạo bảng tóm tắt copy number trung bình theo chromosome (trọng số độ dài segment).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-i", "--input", dest="input", type=str, default=".",
        help=f"Thư mục chứa các file *{SUFFIX}",
    )
    parser.add_argument("-o", "--output", dest="output", type=str, default=None,
        help="Đường dẫn file TSV kết quả (stdout nếu bỏ trống)",
    )
    return parser.parse_args(argv)

def process_file(path: Path) -> Dict[str, object]:
    name = path.name
    sample = name[:-len(SUFFIX)] if name.endswith(SUFFIX) else name.rsplit(".", 1)[0]

    try:
        df = pd.read_csv(path, sep="\t", dtype=str, engine="python")
    except Exception:
        return {"Sample": sample}

    # Chromosome đã chuẩn hoá dạng số 1..24; chuyển trực tiếp sang numeric
    df["Chromosome_norm"] = pd.to_numeric(df["Chromosome"], errors="coerce")
    df = df[df["Chromosome_norm"].isin(CHR_RANGE)]

    # Numeric start/end + length
    df["Start"] = pd.to_numeric(df["Start"], errors="coerce")
    df["End"] = pd.to_numeric(df["End"], errors="coerce")
    df["Copy Number"] = pd.to_numeric(df["Copy Number"], errors="coerce")
    df = df.dropna(subset=["Start", "End", "Copy Number"])

    df["length"] = df["End"] - df["Start"]
    df = df[df["length"] > 0]
    if df.empty:
        return {"Sample": sample, "segment_number": 0}

    segment_number = len(df)

    # Tạo cột weighted_cn = copy_number * length và gom nhóm lấy tổng
    weighted = (
        df.assign(weighted_cn=df["Copy Number"] * df["length"])  # copy number đã numeric
          .groupby("Chromosome_norm")
          .agg(total_weighted=("weighted_cn", "sum"), total_len=("length", "sum"))
    )
    weighted["mean_cn"] = weighted["total_weighted"] / weighted["total_len"]
    grouped = weighted["mean_cn"]  # Series index = Chromosome_norm

    row: Dict[str, object] = {"Sample": sample, "segment_number": segment_number}
    for chr_id in CHR_RANGE:
        val = grouped.get(chr_id, float("nan"))
        if pd.notna(val):
            # Làm tròn half-up đến 1 chữ số sau dấu phẩy (inline thay cho round_half_up_1)
            try:
                _d = Decimal(str(val)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                row[str(chr_id)] = float(_d)
            except Exception:
                row[str(chr_id)] = float("nan")
        else:
            row[str(chr_id)] = ""  # để trống nếu không có dữ liệu

    # Xác định giới tính
    chrX = row.get("23")
    chrY = row.get("24")
    gender = "Nan"
    try:
        x_val = float(chrX)
        y_val = float(chrY)
        if 1.8 <= x_val <= 2.2 and y_val < 0.2:
            gender = "female"
        elif 0.8 <= x_val <= 1.2 and 0.8 <= y_val <= 1.2:
            gender = "male"
    except Exception:
        pass
    row["gender"] = gender

    return row


def build_header() -> List[str]:
    return ["Sample"] + [str(c) for c in CHR_RANGE] + ["gender", "segment_number"]


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    input_dir = Path(args.input).resolve()
    if not input_dir.exists():
        print(f"[ERROR] Thư mục input không tồn tại: {input_dir}", file=sys.stderr)
        return 1

    files = sorted(input_dir.rglob(f"*{SUFFIX}"))
    rows: List[Dict[str, object]] = [process_file(p) for p in files]

    header = build_header()
    if rows:
        df_out = pd.DataFrame(rows)
    else:
        df_out = pd.DataFrame(columns=header)

    # Sắp xếp cột theo header chuẩn & fill
    df_out = df_out.reindex(columns=header, fill_value="")

    output_path = Path(args.output).resolve() if args.output else None
    out_fh = sys.stdout if output_path is None else output_path.open("w", encoding="utf-8", newline="")
    close_after = output_path is not None
    try:
        df_out.to_csv(out_fh, sep="\t", index=False)
    finally:
        if close_after:
            out_fh.close()

    print(f"[INFO] Đã xử lý {len(files)} file(s).", file=sys.stderr)
    if output_path:
        print(f"[INFO] Kết quả được ghi vào: {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
