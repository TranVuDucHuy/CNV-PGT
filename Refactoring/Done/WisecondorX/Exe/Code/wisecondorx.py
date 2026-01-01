import argparse
import subprocess
import sys
import shutil
from pathlib import Path
import time

def run_command(command):
    command_str = [str(c) for c in command]             # Chuyển đổi các phần tử của lệnh thành chuỗi
    try:
        result = subprocess.run(                        # Chạy lệnh trong shell
            command_str,
            check=True,                                 # Ném ngoại lệ nếu lệnh trả về mã lỗi khác 0
            text=True,                                  # Để nhận kết quả dưới dạng chuỗi
            capture_output=True                         # Để thu thập stdout và stderr (print ở dưới)
        )
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy lệnh '{' '.join(command_str)}': {e}", file=sys.stderr)
        if e.stderr:
            print(f"STDERR:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

def convert_bam_to_npz(bam_dir, output_dir):
    bam_files = list(bam_dir.glob("*.bam"))                 # Tìm tất cả file .bam trong thư mục sử dụng wildcard
    if not bam_files:
        print(f"Lỗi: Không tìm thấy tệp .bam nào trong {bam_dir} để chuyển đổi.", file=sys.stderr)
        sys.exit(1)
    for bam_file in bam_files:
        sample_id = bam_file.stem
        output_npz = output_dir / f"{sample_id}.npz"    # Tạo tên tệp NPZ từ tên tệp BAM (name = stem + suffix)
        if output_npz.exists():
            print(f"   - Tệp {output_npz.name} đã tồn tại, bỏ qua bước convert.")           
            continue
        command = ["WisecondorX", "convert", bam_file, output_npz, "--binsize", "400000"]
        print(f"   - Chuyển đổi {bam_file.name} sang {output_npz.name}")
        run_command(command)

def main():
    # --- 1. THAM SỐ ĐẦU VÀO ---
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

    reference_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    test_npz_dir.mkdir(exist_ok=True)

    # --- 2. CHUYỂN BAM SANG NPZ ---
    print("\n>>> Bước 1: Chuyển đổi tệp BAM test sang định dạng .npz")
    convert_bam_to_npz(test_bam_dir, test_npz_dir)

    # --- 3. TẠO TỆP REFERENCE ---
    print("\n>>> Bước 2: Kiểm tra và tạo tệp Reference")
    reference_file = reference_dir / "Reference.npz"

    if reference_file.exists():
        print(f"   - Tệp reference đã tồn tại tại: {reference_file}. Bỏ qua bước tạo mới.")
    else:
        start_ns = time.time_ns()
        convert_bam_to_npz(train_bam_dir, train_npz_dir)
        npz_ref_files = list(train_npz_dir.glob("*.npz"))
        if not npz_ref_files:
            print(f"Lỗi: Không tìm thấy tệp .npz nào trong {train_npz_dir} để tạo reference", file=sys.stderr)
            sys.exit(1)

        command = ["WisecondorX", "newref"] + npz_ref_files + [reference_file] + ["--binsize", "400000"]
        run_command(command)
        end_ns = time.time_ns()
        duration_s = (end_ns - start_ns) / 1e9
        
        # Write timing to reference_run_time.txt
        timing_file = work_dir / "reference_run_time.txt"
        with open(timing_file, "w") as fh:
            fh.write(f"start_ns\t{start_ns}\n")
            fh.write(f"end_ns\t{end_ns}\n")
            fh.write(f"duration_s\t{duration_s:.6f}\n")
        print(f"   - Thời gian tạo reference được lưu vào: {timing_file}")

    # --- 4. CHẠY PREDICT ---
    print("\n>>> Bước 3: Chạy WisecondorX predict cho từng mẫu test")
    npz_files_test = list(test_npz_dir.glob("*.npz"))
    total_samples = len(npz_files_test)
    processed_samples = 0

    for npz_file in npz_files_test:
        print(f"\n   - Xử lý mẫu {processed_samples + 1}/{total_samples}: {npz_file.name}")

        sample_name = npz_file.stem
        sample_dir = output_dir / sample_name
        sample_dir.mkdir(exist_ok=True)

        output_prefix = sample_dir / sample_name

        command = ["WisecondorX", "predict", npz_file, reference_file, output_prefix, "--bed", "--plot"]
        run_command(command)
        processed_samples += 1

if __name__ == "__main__":
    if shutil.which("WisecondorX") is None:
        print("Lỗi: Không tìm thấy lệnh 'WisecondorX'.", file=sys.stderr)
        print("Đảm bảo đã cài đặt WisecondorX và kích hoạt môi trường conda chứa nó.", file=sys.stderr)
        sys.exit(1)
    main()