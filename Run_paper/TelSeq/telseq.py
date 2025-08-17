#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

def run_command(command, stdout_file=None):
    """
    Chạy một lệnh hệ thống và xử lý kết quả.

    Args:
        command (list): Danh sách các thành phần của lệnh.
        stdout_file (file object, optional): Đối tượng tệp để ghi stdout.
    """
    print(f"INFO: Đang chạy lệnh: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            check=True,       # Báo lỗi nếu lệnh trả về mã khác 0
            capture_output=True, # Bắt stdout và stderr
            text=True,        # Giải mã stdout/stderr dưới dạng văn bản
            encoding='utf-8'
        )
        # In các thông báo trạng thái từ telseq (stderr) ra console
        if process.stderr:
            print("INFO: Telseq log:\n---")
            print(process.stderr.strip())
            print("---\n")
        
        # Ghi kết quả chính (stdout) vào tệp nếu được cung cấp
        if stdout_file:
            stdout_file.write(process.stdout)

    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy lệnh '{command[0]}'. Hãy đảm bảo nó đã được cài đặt và nằm trong PATH của hệ thống, hoặc cung cấp đường dẫn đúng qua --telseq-path.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"LỖI: Lệnh '{' '.join(command)}' thất bại với mã lỗi {e.returncode}", file=sys.stderr)
        print(f"Stderr:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

def main():
    """Hàm chính để chạy pipeline."""
    parser = argparse.ArgumentParser(
        description="Chạy TelSeq trên tất cả các tệp BAM trong một thư mục và gộp kết quả.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Đường dẫn đến thư mục chứa các tệp BAM."
    )
    parser.add_argument(
        "--output-file",
        required=True,
        type=Path,
        help="Đường dẫn đến tệp kết quả đầu ra (sẽ được tạo hoặc ghi đè)."
    )
    parser.add_argument(
        "--telseq-path",
        default="telseq",
        help="Đường dẫn đến tệp thực thi telseq nếu nó không nằm trong PATH.\n"
             "Ví dụ: /mnt/d/documents/lab/tool/telseq/telseq/src/Telseq/telseq"
    )
    args = parser.parse_args()

    # --- Bước 1: Tìm tất cả các tệp .bam trong thư mục đầu vào ---
    print(f"INFO: Đang tìm kiếm các tệp .bam trong: {args.input_dir}")
    bam_files = sorted(list(args.input_dir.glob("*.bam")))

    if not bam_files:
        print(f"CẢNH BÁO: Không tìm thấy tệp .bam nào trong {args.input_dir}. Thoát.", file=sys.stderr)
        sys.exit(0)

    print(f"INFO: Tìm thấy {len(bam_files)} tệp BAM.")
    
    # Tạo thư mục chứa tệp output nếu chưa tồn tại
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    # --- Bước 2: Mở tệp output và ghi header ---
    print(f"INFO: Đang ghi header vào tệp kết quả: {args.output_file}")
    with open(args.output_file, "w", encoding='utf-8') as f_out:
        # Chạy `telseq -h` để lấy header duy nhất
        # Chúng ta chỉ cần chạy với một tệp BAM bất kỳ để tạo header
        header_command = [args.telseq_path, "-h"]
        run_command(header_command, stdout_file=f_out)

        # --- Bước 3: Chạy telseq cho từng tệp và nối kết quả ---
        for i, bam_file in enumerate(bam_files, 1):
            print(f"--- Đang xử lý tệp {i}/{len(bam_files)}: {bam_file.name} ---")
            
            # Sử dụng -H để bỏ qua header cho các tệp sau
            telseq_command = [args.telseq_path, "-H", "-k 1", str(bam_file)]
            run_command(telseq_command, stdout_file=f_out)

    print("\n----------------------------------------------------")
    print(f"INFO: Hoàn tất! Kết quả đã được lưu tại: {args.output_file}")
    print("----------------------------------------------------")

if __name__ == "__main__":
    main()