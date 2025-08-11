import numpy as np

def filter_bins(mean_npz, std_npz, chromosomes=None, temp_dir=None, threshold=5, pipeline_obj=None):
    """
    Lọc các bin không ổn định dựa trên độ lệch chuẩn

    Args:
        mean_npz (str): Đường dẫn file NPZ chứa mean
        std_npz (str): Đường dẫn file NPZ chứa standard deviation
        chromosomes (list, optional): Danh sách chromosome (nếu None sẽ lấy từ pipeline_obj)
        temp_dir (Path, optional): Thư mục tạm để lưu file kết quả (nếu None sẽ lấy từ pipeline_obj)
        threshold (float, optional): Ngưỡng độ lệch chuẩn (nếu None sẽ lấy từ pipeline_obj)
        pipeline_obj (optional): Object CNVPipeline để truy cập các thuộc tính

    Returns:
        str: Đường dẫn file NPZ đã lọc
    """
    # Nếu có pipeline_obj, sử dụng các thuộc tính từ đó
    if pipeline_obj is not None:
        if chromosomes is None:
            chromosomes = pipeline_obj.chromosomes
        if temp_dir is None:
            temp_dir = pipeline_obj.temp_dir
        if threshold is None or threshold == 5:  # Sử dụng threshold từ pipeline nếu là giá trị mặc định
            threshold = pipeline_obj.threshold
    
    # Kiểm tra các tham số bắt buộc
    if chromosomes is None:
        raise ValueError("chromosomes parameter is required when pipeline_obj is not provided")
    if temp_dir is None:
        raise ValueError("temp_dir parameter is required when pipeline_obj is not provided")
    
    print(f"Đang lọc bin với ngưỡng độ lệch chuẩn: {threshold}")

    mean_data = np.load(mean_npz)
    std_data = np.load(std_npz)
    filtered_mean = {}

    for chrom in chromosomes:
        if chrom in mean_data.files and chrom in std_data.files:
            mean_values = mean_data[chrom].copy()
            std_values = std_data[chrom]
            unstable_bins = std_values > threshold
            mean_values[unstable_bins] = -1
            filtered_mean[chrom] = mean_values
            num_unstable = np.sum(unstable_bins)
            total_bins = len(mean_values)
            print(f"  Chromosome {chrom}: {num_unstable}/{total_bins} bin không ổn định")
        else:
            print(f"Cảnh báo: Không có dữ liệu cho chromosome {chrom}")
            filtered_mean[chrom] = np.array([])

    filtered_file = temp_dir / "mean_filtered.npz"
    np.savez_compressed(filtered_file, **filtered_mean)
    print(f"Đã lưu mean đã lọc vào: {filtered_file}")
    return str(filtered_file)

# Alias để tương thích với code cũ
filter = filter_bins
