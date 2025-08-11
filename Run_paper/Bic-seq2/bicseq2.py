import os
import argparse
import subprocess
import glob
from pathlib import Path
import time


# --- CẤU HÌNH CỐ ĐỊNH ---
CHROMOSOMES_TO_TRY = [f'chr{i}' for i in range(1, 23)] + ['chrX', 'chrY', 'chrM']
BICSEQ_NORM_SCRIPT = '/mnt/d/documents/lab/tool/gpt/Bicseq2/Code/NBICseq-norm_v0.2.4/NBICseq-norm.pl'
BICSEQ_SEG_SCRIPT = '/mnt/d/documents/lab/tool/gpt/Bicseq2/Code/NBICseq-seg_v0.7.2/NBICseq-seg.pl'

# --- THAM SỐ ĐÃ NHÚNG CỨNG CHO DỮ LIỆU CỦA BẠN ---
# Dựa trên phân tích file FASTQ (single-end, 36bp)
READ_LENGTH = 36
FRAGMENT_SIZE = 36

def run_command(command, log_prefix=""):
    """Hàm helper để chạy lệnh shell và hiển thị output theo thời gian thực."""
    print(f"[{log_prefix}] Executing: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, text=True, errors='ignore')
        print(f"[{log_prefix}] Command successful.")
    except subprocess.CalledProcessError as e:
        print(f"\n[{log_prefix}] ERROR: Command failed with exit code {e.returncode}")
        print(f"[{log_prefix}] Please check the log messages above for details.")
        raise

def generate_seq_files(bam_path, seq_output_dir):
    """Bước 2: Tạo các tệp .seq."""
    sample_name = bam_path.name.replace('.sorted.bam', '')
    print(f"\n--- Step 2: Generating .seq files for {sample_name} ---")
    seq_output_dir.mkdir(parents=True, exist_ok=True)
    if list(seq_output_dir.glob('*.seq')):
        print(f"Found existing .seq files in {seq_output_dir}. Skipping generation.")
        return
    print(f"Creating .seq files in: {seq_output_dir}")
    for chrom in CHROMOSOMES_TO_TRY:
        output_seq_file = seq_output_dir / f"{chrom}.seq"
        command = ['samtools', 'view', '-F', '4', str(bam_path), chrom]
        try:
            samtools_process = subprocess.Popen(command, stdout=subprocess.PIPE)
            cut_process = subprocess.Popen(['cut', '-f', '4'], stdin=samtools_process.stdout, stdout=subprocess.PIPE)
            samtools_process.stdout.close()
            output_bytes = cut_process.communicate()[0]
            with open(output_seq_file, 'w') as f_out:
                f_out.write(output_bytes.decode('utf-8', errors='ignore'))
            print(f"  - Created {output_seq_file.name}")
        except Exception as e:
            print(f"  - Failed to create {output_seq_file.name} for {chrom}. Error: {e}")
            output_seq_file.touch()

def run_normalization(sample_name, seq_dir, fa_dir, map_dir, norm_output_dir):
    """Bước 3: Tạo config và chạy NBICseq-norm.pl."""
    print(f"\n--- Step 3: Running BIC-seq2 Normalization for {sample_name} ---")
    norm_output_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = norm_output_dir / f"{sample_name}.norm.config"
    gam_output_path = norm_output_dir / f"{sample_name}.gam.txt"

    print(f"Creating normalization config file: {config_file_path}")
    with open(config_file_path, 'w') as f:
        f.write("chromName\tfaFile\tMapFile\treadPosFile\tbinFileNorm\n")
        for chrom in CHROMOSOMES_TO_TRY:
            fa_file, map_file, seq_file = fa_dir/f"{chrom}.fa", map_dir/f"hg19.50mer.CRC.{chrom}.txt", seq_dir/f"{chrom}.seq"
            if not all([fa_file.exists(), map_file.exists(), seq_file.exists() and seq_file.stat().st_size > 0]):
                continue
            row = [chrom, str(fa_file), str(map_file), str(seq_file), str(norm_output_dir / f"{chrom}.norm.bin")]
            f.write('\t'.join(row) + '\n')

    # Tự động sử dụng các tham số đã được nhúng cứng
    command = [
        'perl', BICSEQ_NORM_SCRIPT,
        f'-l={READ_LENGTH}',
        f'-s={FRAGMENT_SIZE}',
        str(config_file_path),
        str(gam_output_path)
    ]
    run_command(command, log_prefix=sample_name)

def run_segmentation(sample_name, norm_dir, seg_output_dir):
    """Bước 4: Tạo config và chạy NBICseq-seg.pl."""
    print(f"\n--- Step 4: Running BIC-seq2 Segmentation for {sample_name} ---")
    seg_output_dir.mkdir(parents=True, exist_ok=True)
    config_file_path = norm_dir / f"{sample_name}.seg.config"
    final_output_path = seg_output_dir / f"{sample_name}.bicseq2.seg"

    print(f"Creating segmentation config file: {config_file_path}")
    with open(config_file_path, 'w') as f:
        f.write("chromName\tbinFileNorm\n")
        for chrom in CHROMOSOMES_TO_TRY:
            bin_file = norm_dir / f"{chrom}.norm.bin"
            if bin_file.exists():
                f.write(f"{chrom}\t{str(bin_file)}\n")

    command = ['perl', BICSEQ_SEG_SCRIPT, '--lambda=2', '--bootstrap', str(config_file_path), str(final_output_path)]
    run_command(command, log_prefix=sample_name)
    print(f"Segmentation result saved to: {final_output_path}")

def main():

    start_time = time.time()  # Thời điểm bắt đầu

    parser = argparse.ArgumentParser(description="Sequential Python pipeline for BIC-seq2 with live logging.")
    parser.add_argument('bam_dir', type=str, help="A: Path to the directory containing BAM files.")
    parser.add_argument('fa_dir', type=str, help="B: Path to the directory containing reference FASTA files.")
    parser.add_argument('map_dir', type=str, help="C: Path to the directory containing mappability files.")
    parser.add_argument('output_dir', type=str, help="D: Path to the final output directory for .seg files.")
    parser.add_argument('intermediate_dir', type=str, help="E: Path for all intermediate files.")
    args = parser.parse_args()

    bam_dir, fa_dir, map_dir, output_dir, intermediate_dir = (Path(p) for p in [
        args.bam_dir, args.fa_dir, args.map_dir, args.output_dir, args.intermediate_dir
    ])
    bam_files = list(bam_dir.glob('*.sorted.bam'))
    if not bam_files:
        print(f"Error: No '*.sorted.bam' files found in {bam_dir}")
        return

    print(f"Found {len(bam_files)} BAM files to process sequentially.")
    successful_runs = 0

    for bam_file_path in bam_files:
        sample_name = bam_file_path.name.replace('.sorted.bam', '')
        print(f"\n================ PROCESSING SAMPLE: {sample_name} ================")
        try:
            seq_output_dir = intermediate_dir / sample_name / 'seq_files'
            norm_output_dir = intermediate_dir / sample_name / 'norm_files'
            
            generate_seq_files(bam_file_path, seq_output_dir)
            run_normalization(sample_name, seq_output_dir, fa_dir, map_dir, norm_output_dir)

            mid_time = time.time()  # Thời điểm giữa
            elapsed_norm = mid_time - start_time

            run_segmentation(sample_name, norm_output_dir, output_dir)
            
            print(f"\n================ SUCCESSFULLY FINISHED SAMPLE: {sample_name} ================")
            successful_runs += 1
        except Exception as e:
            print(f"\n!!!!!!!!!!!!!!!! An error occurred while processing {sample_name}. Moving to the next sample. !!!!!!!!!!!!!!!!")
            continue

    print("\n================ PIPELINE FINISHED ================")
    print(f"Successfully processed {successful_runs} out of {len(bam_files)} samples.")
    if successful_runs < len(bam_files):
        print("Some samples failed. Please check the logs above for errors.")
    
    end_time = time.time()  # Thời điểm kết thúc
    elapsed = end_time - start_time
    print(f"\n>>> Thời gian thực thi pipeline: {elapsed:.2f} giây = ({elapsed/60:.2f} phút)")
    print(f"\n>>> Thời gian chuẩn hóa: {elapsed_norm:.2f} giây = ({elapsed_norm/60:.2f} phút)")


if __name__ == '__main__':
    main()