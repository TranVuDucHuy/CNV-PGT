import argparse
import shutil
import subprocess
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def prepare_cbs_input(df: pd.DataFrame, sample_id: str) -> pd.DataFrame:
    # Ép kiểu & loại bỏ hàng không hợp lệ
    work = df.copy()
    work['BIN COPY #'] = pd.to_numeric(work['BIN COPY #'], errors='coerce')
    work['CHROMOSOME'] = pd.to_numeric(work['CHROMOSOME'], errors='coerce', downcast='integer')
    work['POSITION'] = pd.to_numeric(work['POSITION'], errors='coerce')
    # Thay vì loại bỏ copy <= 0, gán pseudo-count 0.01 để vẫn giữ bin
    invalid_mask = (~np.isfinite(work['BIN COPY #'])) | (work['BIN COPY #'] <= 0)
    if invalid_mask.any():
        n_invalid = invalid_mask.sum()
        print(f"  [CẢNH BÁO] {n_invalid} bins có copy<=0 hoặc NA được gán giá trị 0.01 (sample {sample_id}). Ví dụ:")
        print(work.loc[invalid_mask, ['CHROMOSOME','POSITION','BIN COPY #']].head(1).to_string(index=False))
        work.loc[invalid_mask, 'BIN COPY #'] = 0.01
    # Tính log2 ratio (log2(CN) - 1)
    work['log2_ratio'] = np.log2(work['BIN COPY #']) - 1

    # DataFrame chuẩn cho CBS.R
    out_df = pd.DataFrame({
        'sample.name': sample_id,
        'chrom_numeric': work['CHROMOSOME'].astype(int),  # CBS.R yêu cầu chrom_numeric
        'maploc': work['POSITION'].astype(int),
        'log2_ratio': work['log2_ratio']
    })

    # Sắp xếp để đảm bảo thứ tự
    out_df = out_df.sort_values(['chrom_numeric', 'maploc']).reset_index(drop=True)
    return out_df


def run_cbs(cbs_r_path: Path, rscript_exec: str, input_csv: Path, output_csv: Path, sample_id: str):
    """Thực thi script CBS.R bằng Rscript."""
    cmd = [
        rscript_exec,
        str(cbs_r_path),
        '--input', str(input_csv),
        '--output', str(output_csv),
        '--sample', sample_id,
        '--alpha', '0.0001',
        '--nperm', '10000',
        '--min.width', '2',
        '--undo.splits', 'sdundo',
        '--undo.SD', '20.0'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            # DNAcopy đôi khi in cảnh báo vào stderr - chỉ log
            print(result.stderr.strip())
    except subprocess.CalledProcessError as e:
        print(f"    [LỖI] CBS thất bại cho sample {sample_id}: {e}")
        raise


def build_segments_tsv(seg_csv: Path, segments_tsv: Path):
    """Đọc file .csv do CBS.R tạo và sinh file .tsv với các cột yêu cầu + Type & Mosaic Percentage.

    Quy ước:
      - Type: No Change nếu 1.7 <= Copy Number <= 2.3; Loss nếu <1.7; Gain nếu >2.3
      - Mosaic Percentage: 'nan' nếu Type = No Change, ngược lại = round(|CN-2|*10)*10 kèm '%'
        (VD: CN=1.639891085 => |1.639891085-2|=0.360108915 *10=3.60108915 ~ 4 -> 4*10 = 40%)
    """
    if not seg_csv.exists():
        raise FileNotFoundError(f"Không tìm thấy file kết quả CBS: {seg_csv}")

    df = pd.read_csv(seg_csv)
    # Tính Copy Number từ seg.mean (seg.mean = log2(CN) - 1)
    df['Copy Number'] = np.power(2, df['seg.mean'] + 1)

    out = df[['chrom', 'loc.start', 'loc.end', 'Copy Number']].copy()
    out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

    # Phân loại Type
    cn = out['Copy Number']
    conditions = [cn < 1.7, (cn >= 1.7) & (cn <= 2.3), cn > 2.3]
    choices = ['Loss', 'No Change', 'Gain']
    out['Type'] = np.select(conditions, choices, default='No Change')

    # Tính Mosaic Percentage
    def mosaic_percent(row_cn, row_type):
        if row_type == 'No Change' or pd.isna(row_cn):
            return 'nan'
        val = int(round(abs(row_cn - 2) * 10)) * 10
        return f"{val}%"

    out['Mosaic Percentage'] = [mosaic_percent(cn_val, t) for cn_val, t in zip(out['Copy Number'], out['Type'])]

    out.to_csv(segments_tsv, sep='\t', index=False)


def process_bluefuse_sample(bins_file: Path, output_root: Path, cbs_r_path: Path, rscript_exec: str):
    sample_id = bins_file.name.replace('_bluefuse_bins.tsv', '')

    # Tạo thư mục sample trong output
    sample_out_dir = output_root / sample_id
    sample_out_dir.mkdir(parents=True, exist_ok=True)

    # Đọc dữ liệu bins gốc
    try:
        df_bins = pd.read_csv(bins_file, sep='\t')
    except Exception as e:
        print(f"  [BỎ QUA] Không đọc được {bins_file}: {e}")
        return

    # Sinh file [Sample]_bluefuse_bins.tsv mới (không chỉ copy) với 4 trường yêu cầu
    try:
        bins_out = df_bins.copy()
        # Ép kiểu cần thiết
        bins_out['CHROMOSOME'] = pd.to_numeric(bins_out['CHROMOSOME'], errors='coerce', downcast='integer')
        bins_out['POSITION'] = pd.to_numeric(bins_out['POSITION'], errors='coerce')
        bins_out['BIN COPY #'] = pd.to_numeric(bins_out['BIN COPY #'], errors='coerce')
        bins_out = bins_out.dropna(subset=['CHROMOSOME', 'POSITION', 'BIN COPY #'])
        # Tính End = POSITION kế tiếp - 1, riêng bin cuối = 59400000
        positions = bins_out['POSITION'].astype(int).values
        if len(positions) > 1:
            end_vals = np.concatenate([positions[1:] - 1, [59400000]])
        else:
            end_vals = np.array([59400000])
        bins_formatted = pd.DataFrame({
            'Chromosome': bins_out['CHROMOSOME'].astype(int).values,
            'Start': positions,
            'End': end_vals,
            'Copy Number': bins_out['BIN COPY #'].values
        })
        target_bins = sample_out_dir / bins_file.name
        bins_formatted.to_csv(target_bins, sep='\t', index=False)
    except Exception as e:
        print(f"  [BỎ QUA] Lỗi tạo file bins output cho {sample_id}: {e}")
        return

    # Chuẩn bị input cho CBS từ dữ liệu gốc (chưa rút gọn cột)
    try:
        cbs_df = prepare_cbs_input(df_bins, sample_id)
    except Exception as e:
        print(f"  [BỎ QUA] Lỗi chuẩn bị dữ liệu CBS cho {sample_id}: {e}")
        return

    cbs_input_csv = sample_out_dir / f"{sample_id}_cbs_input.csv"
    cbs_df.to_csv(cbs_input_csv, index=False)
    seg_output_csv = sample_out_dir / f"{sample_id}_bluefuse_segments_raw.csv"

    # Chạy CBS
    try:
        run_cbs(cbs_r_path, rscript_exec, cbs_input_csv, seg_output_csv, sample_id)
    except Exception:
        print(f"  [BỎ QUA] CBS thất bại cho sample {sample_id}")
        return

    # Sinh tệp segments TSV cuối cùng (có Type & Mosaic Percentage)
    final_segments_tsv = sample_out_dir / f"{sample_id}_bluefuse_segments.tsv"
    try:
        build_segments_tsv(seg_output_csv, final_segments_tsv)
        print(f"  -> Đã tạo {final_segments_tsv}")
    except Exception as e:
        print(f"  [LỖI] Không tạo được segments TSV: {e}")

    # Dọn dẹp (tuỳ chọn)
    cbs_input_csv.unlink(missing_ok=True)
    seg_output_csv.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Chạy CBS cho dữ liệu BlueFuse bins.")
    parser.add_argument('-i', '--input_dir', required=True, help='Thư mục A: chứa các thư mục con/mẫu với *_bluefuse_bins.tsv')
    parser.add_argument('-o', '--output_dir', required=True, help='Thư mục B đầu ra')
    parser.add_argument('--rscript', default='Rscript', help='Tên hoặc đường dẫn thực thi Rscript (mặc định: Rscript trong PATH)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    rscript_exec = args.rscript

    if not input_dir.is_dir():
        print(f"[LỖI] Thư mục đầu vào không tồn tại: {input_dir}")
        sys.exit(1)

    cbs_r_path = Path(__file__).resolve().parent.parent / 'Baseline' / 'Code' / 'CBS.R'
    if not cbs_r_path.is_file():
        print(f"[LỖI] Không tìm thấy CBS.R tại {cbs_r_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== BẮT ĐẦU PHÂN ĐOẠN BLUEFUSE ===")
    print(f"CBS.R: {cbs_r_path}")

    bins_files = sorted(input_dir.rglob("*_bluefuse_bins.tsv"))
    print(f"Tìm thấy {len(bins_files)} tệp bins.")

    for bf in bins_files:
        process_bluefuse_sample(bf, output_dir, cbs_r_path, rscript_exec)

    print("\n=== HOÀN TẤT ===")

if __name__ == '__main__':
    main()
