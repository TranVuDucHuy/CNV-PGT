#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pysam
import re

# Độ dài chromosome cho GRCh37
CHROMOSOME_LENGTHS_GRCh37 = {
    "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276,
    "5": 180915260, "6": 171115067, "7": 159138663, "8": 146364022,
    "9": 141213431, "10": 135534747, "11": 135006516, "12": 133851895,
    "13": 115169878, "14": 107349540, "15": 102531392, "16": 90354753,
    "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
    "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566,
}

def standardize_chromosomes(chrom):
    """Chuẩn hóa chromosome: X -> 23, Y -> 24, và đảm bảo là int."""
    chrom = str(chrom).replace('chr', '')
    replacements = {'X': '23', 'Y': '24'}
    chrom = replacements.get(chrom, chrom)
    return int(chrom)

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

def collect_bins(log2ratio_npz: Path, bin_size: int):
    """Thu thập bins từ NPZ, trả về danh sách dict cho BED."""
    bins = []
    ratio = np.load(log2ratio_npz)
    for chrom in ratio.files:
        chrom_std = standardize_chromosomes(chrom)
        if not (1 <= chrom_std <= 24):
            continue
        arr = ratio[chrom]
        n = len(arr)
        for i in range(n):
            r = float(arr[i])
            if r <= -10:  # bin bị che
                continue
            start = i * bin_size
            end = min((i + 1) * bin_size, CHROMOSOME_LENGTHS_GRCh37.get(str(chrom), 0))
            cn = float(2.0 ** (r + 1.0))
            bins.append({
                'chrom': chrom_std,
                'chromStart': int(start),
                'chromEnd': int(end),
                'copyNumber': cn
            })
    return bins

def collect_segments(segments_csv: Path):
    """Thu thập segments từ CSV, trả về danh sách dict cho BED."""
    segments = []
    df = pd.read_csv(segments_csv)
    for _, row in df.iterrows():
        chrom_std = standardize_chromosomes(row.get("chrom"))
        if not (1 <= chrom_std <= 24):
            continue
        start = int(row.get("loc.start", 0))
        end = int(row.get("loc.end", start))
        seg_mean = float(row.get("seg.mean", 0.0))
        cn = float(2.0 ** (seg_mean + 1.0))
        segments.append({
            'chrom': chrom_std,
            'chromStart': start,
            'chromEnd': end,
            'copyNumber': cn
        })
    return segments

def write_bed(file_path: Path, data: list, columns: list):
    """Ghi dữ liệu vào file BED."""
    with open(file_path, 'w') as f:
        f.write('\t'.join(columns) + '\n')
        for row in data:
            f.write('\t'.join(str(row[col]) for col in columns) + '\n')

def process_sample_outputs(run_output_dir, exp_output_dir):
    """Xử lý output cho từng sample"""
    log2_files = sorted(run_output_dir.glob("*_log2Ratio.npz"))
    for log2_npz in log2_files:
        sample_name_raw = log2_npz.stem.replace("_log2Ratio", "")
        sample_name = re.sub(r'_S\d+$', '', sample_name_raw)
        sample_output_dir = exp_output_dir / sample_name
        sample_output_dir.mkdir(parents=True, exist_ok=True)

        # Chuyển đổi bins sang BED
        bins_raw = collect_bins(log2_npz, bin_size=400000)  # Default bin_size
        bins_bed = sample_output_dir / f"{sample_name}_baseline_bins.bed"
        write_bed(bins_bed, bins_raw, ['chrom', 'chromStart', 'chromEnd', 'copyNumber'])
        print(f"    - Ghi {bins_bed}")

        # Chuyển đổi segments sang BED
        segments_csv = run_output_dir / f"{sample_name_raw}_segments.csv"
        segments_raw = collect_segments(segments_csv)
        segments_bed = sample_output_dir / f"{sample_name}_baseline_segments.bed"
        write_bed(segments_bed, segments_raw, ['chrom', 'chromStart', 'chromEnd', 'copyNumber'])
        print(f"    - Ghi {segments_bed}")

        # Đổi tên và di chuyển scatterChart
        scatter_src = run_output_dir / f"{sample_name_raw}_scatterChart.png"
        scatter_dst = sample_output_dir / f"{sample_name}_baseline_scatterChart.png"
        shutil.move(str(scatter_src), str(scatter_dst))
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

    experiments = [d for d in sorted(input_dir.iterdir()) if d.is_dir()]
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

        # 3. Chạy Baseline
        cmd = [sys.executable, str(code_dir / "baseline.py"), "-o", str(run_dir)]
        print(f"  - Chạy: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=str(code_dir))

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