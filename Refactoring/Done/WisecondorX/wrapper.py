#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pandas as pd
import pysam

def standardize_chromosomes(df, chromosome_col):
    """
    Chuẩn hóa cột NST trong một DataFrame.
    """
    df_copy = df.copy()
    df_copy[chromosome_col] = df_copy[chromosome_col].astype(str)
    df_copy[chromosome_col] = df_copy[chromosome_col].str.replace('chr', '', regex=False)
    replacements = {'X': '23', 'Y': '24'}
    df_copy.loc[:, chromosome_col] = df_copy[chromosome_col].replace(replacements)
    df_copy[chromosome_col] = pd.to_numeric(df_copy[chromosome_col], errors='coerce')
    df_filtered = df_copy[(df_copy[chromosome_col] >= 1) & (df_copy[chromosome_col] <= 24)]
    return df_filtered

def move_bam_files(src_dir, dst_dir):
    """Di chuyển BAM và BAI từ src_dir sang dst_dir, tạo BAI nếu thiếu"""
    for bam_file in src_dir.glob("*.bam"):
        bam_dest = dst_dir / bam_file.name
        shutil.move(bam_file, bam_dest)
        bai_file = bam_file.with_suffix('.bam.bai')
        bai_dest = bam_dest.with_suffix('.bam.bai')
        if bai_file.exists():
            shutil.move(bai_file, bai_dest)
        else:
            print(f"  - Tạo BAI cho {bam_file.name}")
            pysam.index(str(bam_dest))

def process_bed_file(bed_file, output_file):
    """Xử lý file BED (bins hoặc segments) và ghi ra định dạng chuẩn."""
    df = pd.read_csv(bed_file, sep='\t')
    df = standardize_chromosomes(df, 'chr')
    df['copyNumber'] = 2 ** (df['ratio'] + 1)
    df = df.dropna(subset=['copyNumber'])  # Lọc bỏ hàng có copyNumber NaN
    df_out = df[['chr', 'start', 'end', 'copyNumber']].copy()
    df_out.columns = ['chrom', 'chromStart', 'chromEnd', 'copyNumber']
    df_out.to_csv(output_file, sep='\t', index=False)
    print(f"    - Ghi {output_file}")

def process_sample_outputs(run_output_dir, output_experiment_dir):
    """Xử lý output cho từng sample"""
    for sample_dir in run_output_dir.iterdir():
        sample_id = sample_dir.name
        sample_output_dir = output_experiment_dir / sample_id
        sample_output_dir.mkdir(parents=True, exist_ok=True)

        # Xử lý bins.bed
        bins_raw = sample_dir / f"{sample_id}_bins.bed"
        bins_bed = sample_output_dir / f"{sample_id}_wisecondorx_bins.bed"
        process_bed_file(bins_raw, bins_bed)

        # Xử lý segments.bed
        segments_raw = sample_dir / f"{sample_id}_segments.bed"
        segments_bed = sample_output_dir / f"{sample_id}_wisecondorx_segments.bed"
        process_bed_file(segments_raw, segments_bed)

        # Sao chép ảnh
        plots_dir = sample_dir / f"{sample_id}.plots"
        scatter_src = plots_dir / "genome_wide.png"
        scatter_dst = sample_output_dir / f"{sample_id}_wisecondorx_scatterChart.png"
        shutil.copy2(scatter_src, scatter_dst)
        print(f"    - Sao chép {scatter_dst}")

def main():
    root_dir = Path(__file__).resolve().parent
    input_dir = root_dir / "Input"
    exe_dir = root_dir / "Exe"
    output_dir = root_dir / "Output"
    run_dir = exe_dir / "Run"
    code_dir = exe_dir / "Code"
    test_dir = run_dir / "Input" / "Test"
    temp_test_dir = run_dir / "Temporary" / "Test"
    run_output_dir = run_dir / "Output"

    if not input_dir.exists():
        print("Không tìm thấy thư mục Input")
        return

    experiments = [d for d in input_dir.iterdir() if d.is_dir()]
    if not experiments:
        print("Không có experiment nào trong Input")
        return

    for i, experiment_dir in enumerate(experiments, 1):
        experiment_name = experiment_dir.name
        print(f"\033[1m\n=== XỬ LÝ THÍ NGHIỆM [{i}/{len(experiments)}]: {experiment_name} ===\033[0m")

        # 1. Dọn dẹp thư mục tạm thời và đầu ra
        print("  - Dọn dẹp thư mục run")
        if temp_test_dir.exists():
            shutil.rmtree(temp_test_dir)
            temp_test_dir.mkdir(parents=True)
        if run_output_dir.exists():
            shutil.rmtree(run_output_dir)
            run_output_dir.mkdir(parents=True)

        # 2. Di chuyển file BAM vào test_dir và xử lý .bai
        print("  - Chuyển BAM vào Test")
        move_bam_files(experiment_dir, test_dir)

        # 3. Chạy WisecondorX
        cmd = [sys.executable, str(code_dir / "wisecondorx.py"), "-o", str(run_dir)]
        print(f"  - Chạy: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # 4. Tạo thư mục đầu ra cho thí nghiệm
        experiment_output_directory = output_dir / experiment_name
        experiment_output_directory.mkdir(parents=True, exist_ok=True)

        # 5. Xử lý đầu ra cho mỗi mẫu
        if run_output_dir.exists():
            process_sample_outputs(run_output_dir, experiment_output_directory)

        # 6. Khôi phục BAM
        print("  - Khôi phục BAM về Input")
        move_bam_files(test_dir, experiment_dir)

    print("\nHoàn tất!")

if __name__ == "__main__":
    main()