#!/usr/bin/env python3
import os
import argparse
import shutil
import pandas as pd


def standardize_chromosomes(df, chromosome_col):
    """
    Chuẩn hóa cột nhiễm sắc thể trong một DataFrame.
    - Chuyển đổi X -> 23, Y -> 24
    - Lọc bỏ các nhiễm sắc thể 'M', 'MT', '25'
    """
    # Đảm bảo cột là kiểu string để xử lý
    df_copy = df.copy()  # Tạo một bản sao tường minh để tránh cảnh báo
    df_copy[chromosome_col] = df_copy[chromosome_col].astype(str)

    # Loại bỏ tiền tố 'chr' (nếu có)
    df_copy[chromosome_col] = df_copy[chromosome_col].str.replace('chr', '', regex=False)

    # Lọc bỏ các hàng không mong muốn
    unwanted_chroms = ['M', 'MT', '25']
    df_filtered = df_copy[~df_copy[chromosome_col].isin(unwanted_chroms)]

    # Thay thế X và Y. Dùng .loc để đảm bảo gán giá trị an toàn.
    replacements = {'X': '23', 'Y': '24'}
    df_final = df_filtered.copy()  # Tạo bản sao mới để thực hiện replace
    df_final.loc[:, chromosome_col] = df_final[chromosome_col].replace(replacements)

    return df_final


def process_baseline_segment(baseline_dir, out_dir, sample_id):
    """Đọc {sample_id}_S93_segments.csv từ baseline và ghi {sample_id}_baseline_segments.tsv vào output"""
    input_file = os.path.join(baseline_dir, f"{sample_id}_S93_segments.csv")
    output_file = os.path.join(out_dir, f"{sample_id}_baseline_segments.tsv")

    # print(f"  -> Đang xử lý Baseline cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep=',')

        # Chuẩn hóa và tính Copy Number
        df = standardize_chromosomes(df, 'chrom')
        df['seg.mean'] = pd.to_numeric(df['seg.mean'], errors='coerce')
        df['Copy Number'] = 2 ** (df['seg.mean'] + 1)

        df_out = df[['chrom', 'loc.start', 'loc.end', 'Copy Number']].copy()
        df_out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

        df_out.to_csv(output_file, sep='\t', index=False)
        # print(f"    [OK] Ghi tệp: {output_file}")
    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")


def copy_baseline_plot(baseline_dir, out_dir, sample_id):
    """Sao chép và đổi tên {sample_id}_S93_scatterChart.png -> {sample_id}.png vào output"""
    src = os.path.join(baseline_dir, f"{sample_id}_S93_scatterChart.png")
    dst = os.path.join(out_dir, f"{sample_id}.png")
    if not os.path.exists(src):
        print(f"  [CẢNH BÁO] Không tìm thấy plot baseline: {src}")
        return
    try:
        shutil.copy2(src, dst)
        # print(f"  [OK] Sao chép plot -> {dst}")
    except Exception as e:
        print(f"  [LỖI] Không thể sao chép plot từ {src} sang {dst}: {e}")


def process_wisecondorx_segment(wisecondorx_dir, out_sample_dir, sample_id):
    """Đọc {sample_id}_segments.bed từ wisecondorx/{sample_id} và ghi {sample_id}_wisecondorx_segments.tsv vào output"""
    input_file = os.path.join(wisecondorx_dir, sample_id, f"{sample_id}_segments.bed")
    output_file = os.path.join(out_sample_dir, f"{sample_id}_wisecondorx_segments.tsv")

    # print(f"  -> Đang xử lý WisecondorX cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep='\t')

        # Chuẩn hóa và tính Copy Number
        df = standardize_chromosomes(df, 'chr')
        df['ratio'] = pd.to_numeric(df['ratio'], errors='coerce')
        df['Copy Number'] = 2 ** (df['ratio'] + 1)

        df_out = df[['chr', 'start', 'end', 'Copy Number']].copy()
        df_out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

        df_out.to_csv(output_file, sep='\t', index=False)
        # print(f"    [OK] Ghi tệp: {output_file}")
    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")


def copy_wisecondorx_plot(wisecondorx_dir, out_sample_dir, sample_id):
    """Sao chép genome_wide.png -> {sample_id}_wisecondorx_scatterChart.png vào output"""
    src = os.path.join(wisecondorx_dir, sample_id, f"{sample_id}.plots", "genome_wide.png")
    dst = os.path.join(out_sample_dir, f"{sample_id}_wisecondorx_scatterChart.png")
    if not os.path.exists(src):
        print(f"  [CẢNH BÁO] Không tìm thấy plot wisecondorx: {src}")
        return
    try:
        shutil.copy2(src, dst)
        # print(f"  [OK] Sao chép plot wisecondorx -> {dst}")
    except Exception as e:
        print(f"  [LỖI] Không thể sao chép plot từ {src} sang {dst}: {e}")


def copy_from_bluefuse(bluefuse_dir, out_dir, sample_id):
    """Sao chép {sample_id}_bluefuse_segments.tsv và {sample_id}.jpg từ bluefuse/{sample_id} vào output"""
    bluefuse_sample_dir = os.path.join(bluefuse_dir, sample_id)
    if not os.path.isdir(bluefuse_sample_dir):
        print(f"  [CẢNH BÁO] Không có thư mục trong bluefuse cho mẫu {sample_id}: {bluefuse_sample_dir}")
        return

    items = [
        (os.path.join(bluefuse_sample_dir, f"{sample_id}_bluefuse_segments.tsv"), os.path.join(out_dir, f"{sample_id}_bluefuse_segments.tsv")),
        (os.path.join(bluefuse_sample_dir, f"{sample_id}.jpg"), os.path.join(out_dir, f"{sample_id}.jpg")),
    ]
    for src, dst in items:
        if not os.path.exists(src):
            print(f"  [CẢNH BÁO] Thiếu tệp trong bluefuse: {src}")
            continue
        try:
            shutil.copy2(src, dst)
            # print(f"  [OK] Sao chép {os.path.basename(src)} -> {dst}")
        except Exception as e:
            print(f"  [LỖI] Không thể sao chép {src} sang {dst}: {e}")


def collect_sample_ids_from_baseline(baseline_dir):
    if not os.path.isdir(baseline_dir):
        print(f"[LỖI] Không tìm thấy thư mục baseline: {baseline_dir}")
        return []
    sample_ids = []
    suffix = '_S93_segments.csv'
    try:
        for name in os.listdir(baseline_dir): 
            if not os.path.isfile(os.path.join(baseline_dir, name)):
                continue
            if name.endswith(suffix):
                sample_ids.append(name[: -len(suffix)])
    except OSError as e:
        print(f"[LỖI] Không thể đọc thư mục baseline: {e}")
        return []
    return sorted(sample_ids)


def main():
    parser = argparse.ArgumentParser(description='Chuẩn bị dữ liệu đánh giá từ baseline, bluefuse, wisecondorx sang output')
    parser.add_argument('baseline', help='Thư mục baseline')
    parser.add_argument('wisecondorx', help='Thư mục wisecondorx')
    parser.add_argument('bluefuse', help='Thư mục bluefuse')
    parser.add_argument('output', help='Thư mục output (đầu ra)')
    args = parser.parse_args()

    baseline_dir = args.baseline
    wisecondorx_dir = args.wisecondorx
    bluefuse_dir = args.bluefuse
    output_dir = args.output

    if not os.path.isdir(baseline_dir):
        print(f"[LỖI] Thư mục baseline không tồn tại: {baseline_dir}")
        return
    if not os.path.isdir(wisecondorx_dir):
        print(f"[CẢNH BÁO] Thư mục wisecondorx không tồn tại: {wisecondorx_dir}")
    if not os.path.isdir(bluefuse_dir):
        print(f"[CẢNH BÁO] Thư mục bluefuse không tồn tại: {bluefuse_dir}")
        
    os.makedirs(output_dir, exist_ok=True)

    sample_ids = collect_sample_ids_from_baseline(baseline_dir)
    print(f"Tìm thấy {len(sample_ids)} mẫu từ baseline")
    if not sample_ids:
        return

    for sample_id in sample_ids:
        # print(f"\nBắt đầu xử lý mẫu: {sample_id}")
        out_sample_dir = os.path.join(output_dir, sample_id)
        os.makedirs(out_sample_dir, exist_ok=True)

        # 2) Baseline từ baseline -> output/{sample_id}/{sample_id}_baseline_segments.tsv
        process_baseline_segment(baseline_dir, out_sample_dir, sample_id)

        # 3) Plot từ baseline -> output/{sample_id}/{sample_id}.png
        copy_baseline_plot(baseline_dir, out_sample_dir, sample_id)

        # 4) Bổ sung tệp từ bluefuse/{sample_id} -> output/{sample_id}
        copy_from_bluefuse(bluefuse_dir, out_sample_dir, sample_id)

        # 5) WisecondorX từ wisecondorx/{sample_id} -> output/{sample_id}/{sample_id}_wisecondorx_segments.tsv
        process_wisecondorx_segment(wisecondorx_dir, out_sample_dir, sample_id)

        # 6) Plot từ wisecondorx/{sample_id} -> output/{sample_id}/{sample_id}_wisecondorx_scatterChart.png
        copy_wisecondorx_plot(wisecondorx_dir, out_sample_dir, sample_id)

    print("\nHoàn tất chuẩn bị dữ liệu đánh giá!")


if __name__ == '__main__':
    main()
