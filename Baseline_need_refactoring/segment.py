import subprocess
import pandas as pd
import numpy as np
from pathlib import Path

def cbs(ratio_npz, temp_dir=None, binsize=None, chromosomes=None, pipeline_obj=None):
    """
    Thực hiện CBS (Circular Binary Segmentation) để phân đoạn dữ liệu log2 ratio
    
    Args:
        ratio_npz (str): Đường dẫn file NPZ chứa log2 ratio
        temp_dir (Path, optional): Thư mục tạm (nếu None sẽ lấy từ pipeline_obj)
        binsize (int, optional): Kích thước bin (nếu None sẽ lấy từ pipeline_obj)
        chromosomes (list, optional): Danh sách chromosome (nếu None sẽ lấy từ pipeline_obj)
        pipeline_obj (optional): Object CNVPipeline để truy cập các thuộc tính
        
    Returns:
        str: Đường dẫn file CSV chứa kết quả segmentation
    """
    # Nếu có pipeline_obj, sử dụng các thuộc tính từ đó
    if pipeline_obj is not None:
        if temp_dir is None:
            temp_dir = pipeline_obj.temp_dir
        if binsize is None:
            binsize = pipeline_obj.binsize
        if chromosomes is None:
            chromosomes = pipeline_obj.chromosomes
    
    # Kiểm tra các tham số bắt buộc
    if temp_dir is None:
        raise ValueError("temp_dir parameter is required when pipeline_obj is not provided")
    if binsize is None:
        raise ValueError("binsize parameter is required when pipeline_obj is not provided")
    if chromosomes is None:
        raise ValueError("chromosomes parameter is required when pipeline_obj is not provided")
    
    print(f"Đang thực hiện CBS segmentation cho: {ratio_npz}")
    ratio_name = Path(ratio_npz).stem.replace('_ratio', '')
    segments_file = Path(temp_dir) / 'ratio_npz' / f"{ratio_name}_segments.csv"
    print("Đang chuẩn bị dữ liệu cho CBS...")
    temp_csv = prepare_cbs_data(ratio_npz, ratio_name, temp_dir, binsize, chromosomes)
    if not temp_csv:
        print("Lỗi: Không thể chuẩn bị dữ liệu cho CBS")
        return None
    cbs_script = Path(__file__).parent / "CBS.R"
    if not cbs_script.exists():
        raise FileNotFoundError(f"Không tìm thấy script CBS.R tại: {cbs_script}")
    try:
        command = [
            "Rscript", str(cbs_script),
            "--input", temp_csv,
            "--output", str(segments_file),
            "--sample", ratio_name,
            "--alpha", "0.001",
            "--nperm", "10000"
        ]
        print(f"Chạy lệnh: {' '.join(command)}")
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True
        )
        print("CBS segmentation hoàn thành:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors từ R:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy CBS: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy Rscript. Đảm bảo R đã được cài đặt và có trong PATH.")
        return None
    finally:
        if temp_csv and Path(temp_csv).exists():
            Path(temp_csv).unlink()
            print(f"Đã xóa file tạm thời: {temp_csv}")
    if segments_file.exists():
        print(f"Đã lưu segments vào: {segments_file}")
        return str(segments_file)
    else:
        print("Lỗi: File segments không được tạo")
        return None

def prepare_cbs_data(ratio_npz, sample_name, temp_dir, binsize, chromosomes):
    """
    Chuẩn bị dữ liệu từ NPZ thành CSV cho CBS
    Args:
        ratio_npz (str): Đường dẫn file NPZ chứa log2 ratio
        sample_name (str): Tên mẫu
        temp_dir (Path): Thư mục tạm
        binsize (int): Kích thước bin
        chromosomes (list): Danh sách chromosome
    Returns:
        str: Đường dẫn file CSV tạm thời hoặc None nếu lỗi
    """
    try:
        data = np.load(ratio_npz)
        all_data = []
        for chrom in chromosomes:
            if chrom in data.files:
                ratios = data[chrom]
                num_bins = len(ratios)
                bin_positions = [i * binsize + binsize // 2 for i in range(num_bins)]
                for i, ratio in enumerate(ratios):
                    if ratio != -2:
                        all_data.append({
                            "sample.name": sample_name,
                            "chrom": chrom,
                            "maploc": bin_positions[i],
                            "log2_ratio": ratio
                        })
        if not all_data:
            print("Không có dữ liệu hợp lệ để tạo file CSV")
            return None
        df = pd.DataFrame(all_data)
        df['chrom_numeric'] = df['chrom'].apply(lambda x: 23 if x == 'X' else (24 if x == 'Y' else int(x)))
        df = df.sort_values(['chrom_numeric', 'maploc']).reset_index(drop=True)
        temp_csv = Path(temp_dir) / f"{sample_name}_cbs_input.csv"
        df.to_csv(temp_csv, index=False)
        print(f"Đã chuẩn bị {len(df)} điểm dữ liệu cho CBS")
        print(f"File CSV tạm thời: {temp_csv}")
        return str(temp_csv)
    except Exception as e:
        print(f"Lỗi khi chuẩn bị dữ liệu CBS: {e}")
        return None
