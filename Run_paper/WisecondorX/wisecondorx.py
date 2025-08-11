import argparse
import subprocess
import sys
import shutil
from pathlib import Path
import time


# --- HÀM ĐỂ CHẠY LỆNH VỚI ĐỐI SỐ (chú ý lược bỏ stepname)---
def run_command(command, step_name):
    command_str = [str(c) for c in command]             # Chuyển đổi các phần tử của lệnh thành chuỗi
    print(f"--- BẮT ĐẦU: {step_name} ---")              # f giúp chèn giá trị của biến vào chuỗi
    print(f"Lệnh: {' '.join(command_str)}")
    try:
        result = subprocess.run(                        # Chạy lệnh trong shell
            command_str,               
            check=True,                                 # Ném ngoại lệ nếu lệnh trả về mã lỗi khác 0
            text=True,                                  # Để nhận kết quả dưới dạng chuỗi
            capture_output=True                         # Để thu thập stdout và stderr (print ở dưới) 
        )
        print(f"STDOUT:\n{result.stdout}")
        print(f"--- HOÀN TẤT: {step_name} ---")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi ở bước '{step_name}': {e}", file=sys.stderr)
        sys.exit(1)

def convert_bam_to_npz(bam_dir, output_dir):
    bam_files = list(bam_dir.glob("*.bam"))                 # Tìm tất cả file .bam trong thư mục sử dụng wildcard
    if not bam_files:
        print(f"Lỗi: Không tìm thấy tệp .bam nào trong {bam_dir} để chuyển đổi.", file=sys.stderr)
        sys.exit(1)
    for bam_file in bam_files:
        output_npz = output_dir / f"{bam_file.stem}.npz"    # Tạo tên tệp NPZ từ tên tệp BAM (name = stem + suffix)
        if output_npz.exists():
            print(f"   - Tệp {output_npz.name} đã tồn tại, bỏ qua bước convert.")
            continue
        command = ["WisecondorX", "convert", bam_file, output_npz]
        run_command(command, f"Chuyển đổi {bam_file.name}")

def main():

    start_time = time.time()  # Thời điểm bắt đầu

    # --- 1. THAM SỐ ĐẦU VÀO ---
    parser = argparse.ArgumentParser(description="Pipeline của WisecondorX.")
    # Thêm các tham số bắt buộc (required=True)
    parser.add_argument("--test_bams", required=True, help="Đường dẫn đến thư mục A chứa tệp BAM/BAI để test.")
    parser.add_argument("--ref_bams", required=True, help="Đường dẫn đến thư mục B chứa tệp BAM/BAI để tạo reference.")
    parser.add_argument("--ref_dir", required=True, help="Đường dẫn đến thư mục C chứa tệp reference cuối cùng.")
    parser.add_argument("--output_dir", required=True, help="Đường dẫn đến thư mục D chứa kết quả đầu ra.")
    
    args = parser.parse_args()

    test_bam_path = Path(args.test_bams)
    ref_bam_path = Path(args.ref_bams)
    reference_path = Path(args.ref_dir)
    output_path = Path(args.output_dir)
    test_npz_path = output_path / "intermediate_npz"

    # Tạo thư mục đầu ra nếu chưa tồn tại
    reference_path.mkdir(exist_ok=True)
    output_path.mkdir(exist_ok=True)
    test_npz_path.mkdir(exist_ok=True)

    # --- 2. CHUYỂN BAM SANG NPZ ---
    print("\n>>> Bước 2: Chuyển đổi tệp BAM test sang định dạng .npz")
    convert_bam_to_npz(test_bam_path, test_npz_path)

    # --- 3. TẠO TỆP REFERENCE ---
    print("\n>>> Bước 3: Kiểm tra và tạo tệp reference")
    final_ref_file = reference_path / "reference.npz"

    if final_ref_file.exists():
        print(f"Tệp reference đã tồn tại tại: {final_ref_file}. Bỏ qua bước tạo mới.")
    else:
        print("Tạo tệp reference do chưa tồn tại.")
        temp_ref_npz_path = reference_path / "temp_ref_npz"
        temp_ref_npz_path.mkdir(exist_ok=True)

        convert_bam_to_npz(ref_bam_path, temp_ref_npz_path)
        
        npz_ref_files = list(temp_ref_npz_path.glob("*.npz"))
        if not npz_ref_files:
            print(f"Lỗi: Không tìm thấy tệp .npz nào trong {temp_ref_npz_path} để tạo reference", file=sys.stderr)
            sys.exit(1)

        command = ["WisecondorX", "newref", "--nipt"] + npz_ref_files + [final_ref_file]

        run_command(command, "Tạo tệp reference với --nipt .npz")

        print(f"Dọn dẹp thư mục tạm: {temp_ref_npz_path}")
        shutil.rmtree(temp_ref_npz_path)                    # Xóa thư mục tạm sau khi tạo reference
        print("Tạo reference hoàn tất.")

# --- 4. CHẠY PREDICT ---
    print("\n>>> Bước 4: Chạy WisecondorX predict cho từng mẫu test")
    npz_files_test = list(test_npz_path.glob("*.npz"))

    for npz_file in npz_files_test:
        sample_name = npz_file.stem
        # Tạo thư mục con cho mẫu
        sample_dir = output_path / sample_name
        sample_dir.mkdir(exist_ok=True)

        # Tạo tiền tố đầu ra (output_id) nằm BÊN TRONG thư mục con
        output_prefix = sample_dir / sample_name

        # Xây dựng lệnh với `output_id` chính xác
        command = [
            "WisecondorX", "predict",
            npz_file,
            final_ref_file,
            output_prefix,
            "--bed",
            "--plot"
        ]
            
        run_command(command, f"Chạy predict cho mẫu {sample_name}")

    print("\n Pipeline đã hoàn thành!")
    end_time = time.time()  # Thời điểm kết thúc
    elapsed = end_time - start_time
    print(f"\n>>> Thời gian thực thi pipeline: {elapsed:.2f} giây = ({elapsed/60:.2f} phút)")


if __name__ == "__main__":
    if shutil.which("WisecondorX") is None:
        print("Lỗi: Không tìm thấy lệnh 'WisecondorX'.", file=sys.stderr)
        print("Đảm bảo đã cài đặt WisecondorX và kích hoạt môi trường conda chứa nó.", file=sys.stderr)
        sys.exit(1)
    main()