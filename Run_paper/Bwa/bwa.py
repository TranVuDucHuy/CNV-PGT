import os
import subprocess
import sys
import multiprocessing
import glob
import datetime
import time

# --- PHẦN CẤU HÌNH ---
# Vui lòng kiểm tra và chỉnh sửa các đường dẫn dưới đây cho phù hợp với môi trường của bạn.

# 1. Đường dẫn tuyệt đối đến thư mục chứa các tệp FASTQ đầu vào.
INPUT_FASTQ_DIR = "/mnt/d/lab/experiment/Fastq/BinhThuong"

# 2. Đường dẫn tuyệt đối đến thư mục đầu ra cho các tệp BAM.
OUTPUT_BAM_DIR = "/mnt/d/lab/experiment/CreateBam/New_control/BAM"

# 3. Đường dẫn tuyệt đối đến tệp gen tham chiếu (reference genome) FASTA.
REFERENCE_FASTA = "/mnt/d/lab/experiment/CreateBam/Reference/hg19.p13.plusMT.no_alt_analysis_set.fa"

# 3. Số luồng (threads) để sử dụng.
#    Tự động lấy số luồng CPU tối đa. Bạn có thể thay đổi thành một số cụ thể, ví dụ: THREADS = 8.
THREADS = multiprocessing.cpu_count()

# 4. Tùy chọn dọn dẹp.
CLEANUP_INTERMEDIATE_FILES = True

# --- KẾT THÚC PHẦN CẤU HÌNH ---


def run_command(command):
    """Thực thi một lệnh shell, in lệnh và kiểm tra lỗi."""
    print(f"Lệnh đang chạy: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, stderr=subprocess.STDOUT, stdout=sys.stdout)
        print(f"--- HOÀN TẤT ---\n")
    except FileNotFoundError:
        print(f"\n[LỖI] Lệnh '{command[0]}' không tìm thấy.")
        print("Hãy chắc chắn rằng BWA và Samtools đã được cài đặt và có trong biến môi trường PATH của hệ thống.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n[LỖI] Lệnh không thực thi thành công. Mã lỗi: {e.returncode}")
        sys.exit(1)

def run_bwa_mem(command, output_sam_file):
    """Thực thi BWA-MEM và chuyển hướng output vào tệp SAM."""
    command_str_display = ' '.join(command) + f" > {output_sam_file}"
    print(f"Lệnh đang chạy: {command_str_display}")
    try:
        with open(output_sam_file, 'w') as f_out:
            process = subprocess.run(command, check=True, stdout=f_out, stderr=subprocess.PIPE, text=True)
            if process.stderr:
                print("Thông tin tiến trình từ BWA-MEM:")
                print(process.stderr, file=sys.stderr)
        print(f"--- HOÀN TẤT ---\n")
    except FileNotFoundError:
        print(f"\n[LỖI] Lệnh '{command[0]}' không tìm thấy. BWA chưa được cài đặt hoặc không có trong PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n[LỖI] BWA-MEM không thực thi thành công. Mã lỗi: {e.returncode}")
        if e.stderr:
            print("Thông báo lỗi từ stderr:")
            print(e.stderr, file=sys.stderr)
        sys.exit(1)

def find_fastq_files(input_dir):
    """Tìm tất cả các tệp FASTQ trong thư mục đầu vào."""
    fastq_pattern = "*.fastq"
    pattern_path = os.path.join(input_dir, fastq_pattern)
    fastq_files = glob.glob(pattern_path)
    fastq_files.sort()
    return fastq_files

def process_single_fastq(input_fastq, output_dir, reference_fasta, threads, cleanup):
    """Xử lý một tệp FASTQ đơn lẻ."""
    print(f"\n{'='*80}")
    print(f"BẮT ĐẦU XỬ LÝ: {os.path.basename(input_fastq)}")
    print(f"{'='*80}")
    
    # Tạo thư mục đầu ra nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    
    # Xác định tên tệp đầu ra chỉ cho .fastq
    base_name = os.path.splitext(os.path.basename(input_fastq))[0]
    
    sam_file = os.path.join(output_dir, f"{base_name}.sam")
    fixmate_bam_file = os.path.join(output_dir, f"{base_name}.fixmate.bam")
    final_bam_file = os.path.join(output_dir, f"{base_name}.bam")
    temp_sort_prefix = os.path.join(output_dir, f"{base_name}_temp_sort")
    sorted_bam_file = os.path.join(output_dir, f"{base_name}.sorted.bam")
    
    print(f"  - Tệp FASTQ đầu vào : {input_fastq}")
    print(f"  - Tệp BAM cuối cùng : {final_bam_file}")
    print(f"  - Số luồng          : {threads}")
    
    try:
        # Pipeline Step 1: Tạo Index cho gen tham chiếu (chỉ cần làm một lần)
        index_file_check = f"{reference_fasta}.bwt"
        if not os.path.exists(index_file_check):
            cmd = ["bwa", "index", "-p", reference_fasta, reference_fasta]
            run_command(cmd)
        
        # Pipeline Step 2: Căn chỉnh (Alignment) với BWA-MEM
        rg_header = f'@RG\\tID:{base_name}\\tPL:ILLUMINA\\tSM:{base_name}'
        cmd = ["bwa", "mem", "-M", "-t", str(threads), "-R", rg_header, reference_fasta, input_fastq]
        run_bwa_mem(cmd, sam_file)
        
        # Pipeline Step 3: Chuyển đổi SAM sang BAM và Fixmate
        cmd = ["samtools", "fixmate", "-O", "bam", sam_file, fixmate_bam_file]
        run_command(cmd)
        
        # Pipeline Step 4: Sắp xếp tệp BAM theo tọa độ
        cmd = ["samtools", "sort",
               "-T", temp_sort_prefix,
               "-O", "bam", 
               "-@", str(threads),
               "-o", sorted_bam_file,
               fixmate_bam_file]
        run_command(cmd)
        
        # Pipeline Step 5: Lọc bỏ multiply-aligned reads, chỉ giữ uniquely aligned reads
        # -F 256: loại bỏ secondary alignments
        # -F 2048: loại bỏ supplementary alignments  
        # -q 1: chỉ giữ reads có mapping quality >= 1
        cmd = ["samtools", "view",
               "-F", "256",  # Loại bỏ secondary alignments
            #    "-F", "2048", # Loại bỏ supplementary alignments
            #    "-q", "1",    # Chỉ giữ reads có MAPQ >= 1
               "-O", "bam",
               "-o", final_bam_file,
               sorted_bam_file]
        run_command(cmd)
        
        # Pipeline Step 6: Index tệp BAM đã lọc
        cmd = ["samtools", "index", final_bam_file]
        run_command(cmd)
        
        # Pipeline Step 7: Dọn dẹp các tệp trung gian
        if cleanup:
            try:
                if os.path.exists(sam_file):
                    os.remove(sam_file)
                    print(f"Đã xóa: {sam_file}")
                if os.path.exists(fixmate_bam_file):
                    os.remove(fixmate_bam_file)
                    print(f"Đã xóa: {fixmate_bam_file}")
                if os.path.exists(sorted_bam_file):
                    os.remove(sorted_bam_file)
                    print(f"Đã xóa: {sorted_bam_file}")
            except OSError as e:
                print(f"Lỗi khi xóa tệp trung gian: {e}")
        
        print(f"HOÀN TẤT XỬ LÝ: {base_name}")
        return True
        
    except Exception as e:
        print(f"LỖI KHI XỬ LÝ {base_name}: {e}")
        return False

def main_pipeline():
    """Hàm chính điều phối toàn bộ pipeline xử lý hàng loạt."""
    start_time = time.time()
    print(">>> BẮT ĐẦU PIPELINE ALIGNMENT BWA-MEM <<<")
    
    # 1. Kiểm tra các thư mục và tệp tham chiếu
    if not os.path.exists(INPUT_FASTQ_DIR):
        print(f"[LỖI] Thư mục FASTQ đầu vào không tồn tại: {INPUT_FASTQ_DIR}")
        sys.exit(1)
    
    if not os.path.exists(REFERENCE_FASTA):
        print(f"[LỖI] Tệp tham chiếu FASTA không tồn tại: {REFERENCE_FASTA}")
        sys.exit(1)
    
    # 2. Tìm tất cả các tệp FASTQ
    fastq_files = find_fastq_files(INPUT_FASTQ_DIR)
    
    if not fastq_files:
        print(f"[LỖI] Không tìm thấy tệp FASTQ nào trong thư mục: {INPUT_FASTQ_DIR}")
        print("Định dạng được hỗ trợ: .fastq")
        sys.exit(1)
    
    print(f"\n--- Tổng quan cấu hình ---")
    print(f"  - Thư mục FASTQ đầu vào: {INPUT_FASTQ_DIR}")
    print(f"  - Thư mục BAM đầu ra   : {OUTPUT_BAM_DIR}")
    print(f"  - Tệp tham chiếu       : {REFERENCE_FASTA}")
    print(f"  - Số luồng            : {THREADS}")
    print(f"  - Tổng số tệp FASTQ    : {len(fastq_files)}")
    print(f"  - Dọn dẹp tệp trung gian: {CLEANUP_INTERMEDIATE_FILES}")
    
    
    # 3. Xử lý từng tệp FASTQ
    successful_count = 0
    failed_files = []
    
    for i, fastq_file in enumerate(fastq_files, 1):
        print(f"\nTiến trình: {i}/{len(fastq_files)}")
        
        success = process_single_fastq(
            input_fastq=fastq_file,
            output_dir=OUTPUT_BAM_DIR,
            reference_fasta=REFERENCE_FASTA,
            threads=THREADS,
            cleanup=CLEANUP_INTERMEDIATE_FILES
        )
        
        if success:
            successful_count += 1
        else:
            failed_files.append(os.path.basename(fastq_file))
    
    # Tính thời gian chạy
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*80}")
    print(">>> KẾT QUÁ PIPELINE <<<")
    print(f"{'='*80}")
    print(f"Tổng số tệp xử lý    : {len(fastq_files)}")
    print(f"Xử lý thành công     : {successful_count}")
    print(f"Xử lý thất bại       : {len(failed_files)}")
    print(f"Thời gian chạy       : {total_time:.2f} giây ({total_time/60:.2f} phút)")
    
    if failed_files:
        print(f"\nCác tệp xử lý thất bại:")
        for failed_file in failed_files:
            print(f"  - {failed_file}")
    
    print(f"\nTất cả tệp BAM đã được lưu trong: {OUTPUT_BAM_DIR}")
    
    if successful_count == len(fastq_files):
        print("PIPELINE ĐÃ HOÀN TẤT THÀNH CÔNG CHO TẤT CẢ CÁC TỆP!")
    else:
        print(f"PIPELINE HOÀN TẤT VỚI {len(failed_files)} LỖI")
        sys.exit(1)

# Chạy hàm chính của pipeline
if __name__ == "__main__":
    main_pipeline()