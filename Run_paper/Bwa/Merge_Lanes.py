import os
import argparse
import shutil
import time  # <--- 1. Thêm thư viện time
from collections import defaultdict

def merge_fastq_lanes(input_dir, output_dir):
    """
    Ghép các tệp FASTQ từ 4 lane thành một tệp duy nhất và đo thời gian thực thi.

    Args:
        input_dir (str): Đường dẫn đến thư mục A chứa các file fastq nguồn.
        output_dir (str): Đường dẫn đến thư mục B để lưu các file đã ghép.
    """
    # <--- 2. Bắt đầu đếm thời gian
    start_time = time.time()

    # 1. Kiểm tra và chuẩn bị thư mục
    if not os.path.isdir(input_dir):
        print(f"Lỗi: Thư mục đầu vào '{input_dir}' không tồn tại.")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Các tệp đã ghép sẽ được lưu vào: '{output_dir}'")

    # 2. Nhóm các tệp theo Sample ID
    sample_groups = defaultdict(list)
    
    print("\nĐang quét và nhóm các tệp FASTQ...")
    for filename in os.listdir(input_dir):
        if filename.endswith('.fastq'):
            if '_L00' in filename:
                prefix = filename.split('_L00')[0]
                sample_groups[prefix].append(filename)

    if not sample_groups:
        print("Không tìm thấy tệp FASTQ nào có định dạng lane (_L00*) trong thư mục đầu vào.")
        return

    # 3. Xử lý từng nhóm
    merged_file_count = 0
    deleted_incomplete_count = 0
    output_file_count = 0

    print(f"\nBắt đầu xử lý {len(sample_groups)} nhóm mẫu...")
    for prefix, file_list in sample_groups.items():
        if len(file_list) == 4:
            output_base_name = prefix.rsplit('_', 1)[0]
            output_filename = f"{output_base_name}.fastq"
            output_filepath = os.path.join(output_dir, output_filename)
            file_list.sort()
            
            try:
                with open(output_filepath, 'wb') as outfile:
                    for source_filename in file_list:
                        source_filepath = os.path.join(input_dir, source_filename)
                        with open(source_filepath, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                output_file_count += 1
                
                for source_filename in file_list:
                    os.remove(os.path.join(input_dir, source_filename))
                merged_file_count += 4

            except Exception as e:
                print(f"   Lỗi khi xử lý nhóm '{prefix}': {e}")

        else:
            print(f"-> Nhóm '{prefix}' không đủ 4 lane (tìm thấy {len(file_list)} tệp). Tiến hành xóa...")
            try:
                for source_filename in file_list:
                    os.remove(os.path.join(input_dir, source_filename))
                deleted_incomplete_count += len(file_list)
            except Exception as e:
                print(f"   Lỗi khi xóa các tệp của nhóm '{prefix}': {e}")
    
    # <--- 3. Dừng đếm thời gian và tính toán
    end_time = time.time()
    elapsed_time = end_time - start_time
    # Chuyển đổi sang định dạng phút và giây để dễ đọc
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60

    # 4. In báo cáo tổng kết (đã bao gồm thời gian)
    print("\n--- BÁO CÁO TỔNG KẾT ---")
    # <--- 4. Hiển thị thời gian chạy
    print(f"Tổng thời gian xử lý: {minutes} phút {seconds:.2f} giây.")
    print(f"Có {merged_file_count} tệp FASTQ đã được ghép từ thư mục A, tạo ra {output_file_count} tệp FASTQ ở thư mục B.")
    print(f"Có {deleted_incomplete_count} tệp FASTQ ở thư mục A đã bị xóa do không đủ 4 lane.")
    print("-------------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ghép các tệp FASTQ từ nhiều lane thành một. Các nhóm không đủ 4 lane sẽ bị xóa.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_dir",
        help="Đường dẫn đến thư mục A chứa các file .fastq nguồn."
    )
    parser.add_argument(
        "output_dir",
        help="Đường dẫn đến thư mục B để lưu các file .fastq đã được ghép."
    )

    args = parser.parse_args()
    merge_fastq_lanes(args.input_dir, args.output_dir)