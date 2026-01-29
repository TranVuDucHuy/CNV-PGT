import argparse
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(command):
    command_str = [str(c) for c in command]             
    try:
        result = subprocess.run(command_str, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

def convert_bam_to_npz(bam_dir, output_dir):
    bam_files = list(bam_dir.glob("*.bam"))                 
    if not bam_files:
        print(f"Lỗi: Không tìm thấy tệp .bam nào trong {bam_dir} để chuyển đổi.", file=sys.stderr)
        sys.exit(1)
    for bam_file in bam_files:
        sample_id = bam_file.stem
        output_npz = output_dir / f"{sample_id}.npz"    
        if output_npz.exists():
            print(f"   - Tệp {output_npz.name} đã tồn tại, bỏ qua bước convert.")           
            continue
        command = ["WisecondorX", "convert", bam_file, output_npz, "--binsize", "400000"]
        print(f"   - Chuyển đổi {bam_file.name} sang {output_npz.name}")
        run_command(command)

def main():
    parser = argparse.ArgumentParser(description="Pipeline của WisecondorX.")
    parser.add_argument("-o", "--work_dir", required=True, help="Root working directory")
    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    test_bam_dir = work_dir / "Input" / "Test"
    train_bam_dir = work_dir / "Input" / "Train"
    reference_dir = work_dir / "Temporary"
    output_dir = work_dir / "Output"
    test_npz_dir = work_dir / "Temporary" / "Test"
    train_npz_dir = work_dir / "Temporary" / "Train"
    train_npz_dir.mkdir(exist_ok=True)

    # 1. Chuyển BAM sang NPZ
    print("\n>>> Bước 1: Chuyển đổi tệp BAM test sang định dạng .npz")
    convert_bam_to_npz(test_bam_dir, test_npz_dir)

    # 2. Tạo tệp Reference
    print("\n>>> Bước 2: Kiểm tra và tạo tệp Reference")
    reference_file = reference_dir / "Reference.npz"

    if reference_file.exists():
        print(f"   - Tệp reference đã tồn tại tại: {reference_file}. Bỏ qua bước tạo mới.")
    else:
        convert_bam_to_npz(train_bam_dir, train_npz_dir)
        npz_ref_files = list(train_npz_dir.glob("*.npz"))
        if not npz_ref_files:
            print(f"Lỗi: Không tìm thấy tệp .npz nào trong {train_npz_dir} để tạo reference", file=sys.stderr)
            sys.exit(1)

        command = ["WisecondorX", "newref"] + npz_ref_files + [reference_file] + ["--binsize", "400000"]
        run_command(command)

    # 3. Chạy predict
    print("\n>>> Bước 3: Chạy WisecondorX predict cho từng mẫu test")
    npz_files_test = list(test_npz_dir.glob("*.npz"))
    for idx, npz_file in enumerate(npz_files_test):
        print(f"\n   - Xử lý mẫu {idx + 1}/{len(npz_files_test)}: {npz_file.name}")

        sample_name = npz_file.stem
        sample_dir = output_dir / sample_name
        sample_dir.mkdir(exist_ok=True)
        output_prefix = sample_dir / sample_name

        command = ["WisecondorX", "predict", npz_file, reference_file, output_prefix, "--bed", "--plot", "--seed", "42"]
        run_command(command)

if __name__ == "__main__":
    main()