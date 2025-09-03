import numpy as np
from pathlib import Path

try:
    from scipy.interpolate import interp1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from statsmodels.nonparametric.smoothers_lowess import lowess
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

def gccount(pipeline_obj, fasta_file):
    """Return two separate dicts (gc_dict, n_dict) with counts per full bin (floor logic).
    Two NPZ cache files are written: *_gc.npz and *_n.npz.
    Trailing partial bins are ignored to stay consistent with readcount binning (floor).
    """
    gc_file = pipeline_obj.work_directory / "Temporary" / f"gc_content_binsize_{pipeline_obj.bin_size}_gc.npz"
    n_file = pipeline_obj.work_directory / "Temporary" / f"gc_content_binsize_{pipeline_obj.bin_size}_n.npz"

    if gc_file.exists() and n_file.exists():
        gc_loaded = np.load(gc_file)
        n_loaded = np.load(n_file)
        return ({k: gc_loaded[k] for k in gc_loaded.files}, {k: n_loaded[k] for k in n_loaded.files})

    gc_counts = {chrom: [] for chrom in pipeline_obj.chromosome_list}
    n_counts = {chrom: [] for chrom in pipeline_obj.chromosome_list}

    current_chromosome = None
    current_pos = 0
    gc_count = 0
    n_count = 0
    bin_filled = 0

    def finish_bin(bin_index):
        nonlocal gc_count, n_count
        if current_chromosome and current_chromosome in gc_counts:
            while len(gc_counts[current_chromosome]) <= bin_index:
                gc_counts[current_chromosome].append(0)
                n_counts[current_chromosome].append(0)
            gc_counts[current_chromosome][bin_index] = gc_count
            n_counts[current_chromosome][bin_index] = n_count
        gc_count = 0
        n_count = 0

    try:
        with open(fasta_file, 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    # Ignore trailing partial bin (not saved) when switching chromosomes
                    current_pos = 0
                    header = line[1:].split()[0]
                    if header.startswith('chr'):
                        header = header[3:]
                    current_chromosome = header if header in gc_counts else None
                    continue
                if current_chromosome is None:
                    continue
                for base in line.upper():
                    bin_index = current_pos // pipeline_obj.bin_size
                    # Only count bases for full bins; once bin fills, finalize
                    if base in ('G', 'C'):
                        gc_count += 1
                    if base == 'N':
                        n_count += 1
                    current_pos += 1
                    bin_filled += 1
                    if bin_filled == pipeline_obj.bin_size:
                        finish_bin(bin_index)
                        bin_filled = 0
        # Do NOT save last partial bin (ignored) -> ensures floor logic
    except Exception as e:
        print(f"Lỗi khi đọc file FASTA: {e}")
        return None, None

    gc_dict = {chrom: np.array(gc_counts[chrom], dtype=np.int32) for chrom in pipeline_obj.chromosome_list}
    n_dict = {chrom: np.array(n_counts[chrom], dtype=np.int32) for chrom in pipeline_obj.chromosome_list}
    np.savez_compressed(gc_file, **gc_dict)
    np.savez_compressed(n_file, **n_dict)
    return gc_dict, n_dict

def lowess_normalize(pipeline_obj, sample_data, gc_data, n_data, max_n=0.1, min_rd=0.0001, frac=0.1):

    all_gc = []
    all_reads = []

    for chromosome in sample_data.keys():
        if chromosome in gc_data and chromosome in n_data:
            sample_counts = sample_data[chromosome]
            gc_counts = gc_data[chromosome]
            n_content = n_data[chromosome]

            min_len = min(len(sample_counts), len(gc_counts), len(n_content))

            for bin_index in range(min_len):
                # Tính tỷ lệ bases N trong bin (N ratio)
                n_ratio = n_content[bin_index] / pipeline_obj.bin_size if pipeline_obj.bin_size > 0 else 0
                read_count = sample_counts[bin_index]

                # Tính GC content từ GC count
                total_bases = pipeline_obj.bin_size - n_content[bin_index]  # Tổng số bases hợp lệ (loại trừ N)
                gc_content = gc_counts[
                                 bin_index] / total_bases if total_bases > 0 else 0  # GC content = GC count / total valid bases

                # Áp dụng các tiêu chí lọc để chọn bin hợp lệ
                if (n_ratio < max_n and  # Tỷ lệ N < ngưỡng tối đa
                        read_count > min_rd and  # Read count > ngưỡng tối thiểu
                        gc_content > 0 and  # GC content > 0
                        total_bases > pipeline_obj.bin_size * 0.5):  # Ít nhất 50% bases hợp lệ trong bin
                    # Thêm điểm dữ liệu hợp lệ vào danh sách để fit LOWESS
                    all_gc.append(gc_content)  # Thêm GC content
                    all_reads.append(sample_counts[bin_index])  # Thêm read count tương ứng

    if len(all_gc) < 10:
        print("Cảnh báo: Không đủ điểm dữ liệu để thực hiện LOWESS normalization")
        return sample_data.copy()  # Trả về dữ liệu gốc nếu không đủ điểm

    # Chuyển đổi list thành numpy arrays để xử lý
    all_gc = np.array(all_gc)  # Array chứa GC content
    all_reads = np.array(all_reads)  # Array chứa read count

    # Sử dụng statsmodels LOWESS nếu có, nếu không sẽ fallback về phương pháp đơn giản
    if HAS_STATSMODELS:
        try:
            # statsmodels lowess với return_sorted=False để giữ nguyên thứ tự
            # Trả về mảng smoothed values có cùng thứ tự với input
            smoothed_reads = lowess(all_reads, all_gc, frac=frac, return_sorted=False)
            print("Sử dụng statsmodels LOWESS với return_sorted=False")
        except Exception as e:
            print(f"Lỗi khi sử dụng statsmodels LOWESS: {e}")
            print("Không thể thực hiện LOWESS normalization")
            return sample_data.copy()  # Trả về dữ liệu gốc nếu lỗi
    else:
        print("Cảnh báo: statsmodels không có sẵn, không thể thực hiện LOWESS normalization")
        return sample_data.copy()  # Trả về dữ liệu gốc nếu không có statsmodels

    # Áp dụng correction cho sample data sử dụng smoothed values
    corrected_sample = {}

    # Index để theo dõi vị trí trong mảng all_gc và smoothed_reads
    global_index = 0

    # Duyệt qua tất cả chromosome để áp dụng normalization
    for chromosome in sample_data.keys():
        if chromosome in gc_data and chromosome in n_data:
            sample_counts = sample_data[chromosome]
            gc_counts = gc_data[chromosome]
            n_content = n_data[chromosome]

            # Tìm độ dài tối thiểu để đảm bảo index không vượt quá
            min_len = min(len(sample_counts), len(gc_counts), len(n_content))
            # Khởi tạo array để lưu kết quả đã correction
            corrected_counts = np.zeros(len(sample_counts))

            # Duyệt qua từng bin để áp dụng correction
            for bin_index in range(min_len):
                # Tính tỷ lệ N trong bin
                n_ratio = n_content[bin_index] / pipeline_obj.bin_size if pipeline_obj.bin_size > 0 else 0
                # Lấy read count trong bin này
                read_count = sample_counts[bin_index]

                # Tính GC content từ GC count
                total_bases = pipeline_obj.bin_size - n_content[bin_index]
                gc_content = gc_counts[bin_index] / total_bases if total_bases > 0 else 0  # GC content

                # Kiểm tra bin có hợp lệ để áp dụng correction không
                if (n_ratio < max_n and  # Tỷ lệ N < ngưỡng tối đa
                        read_count > min_rd and  # Read count > ngưỡng tối thiểu
                        gc_content > 0 and  # GC content > 0
                        total_bases > pipeline_obj.bin_size * 0.5):  # Ít nhất 50% bases hợp lệ

                    # Lấy giá trị expected từ smoothed values tại vị trí global_index
                    try:
                        # Kiểm tra xem global_index có hợp lệ không
                        if global_index < len(smoothed_reads):
                            expected_value = float(smoothed_reads[global_index])

                            if expected_value > 0:
                                # Chuẩn hóa: observed / expected (loại bỏ bias do GC)
                                corrected_value = sample_counts[bin_index] / expected_value
                            else:
                                corrected_value = sample_counts[bin_index]

                            corrected_counts[bin_index] = corrected_value
                            # Tăng global_index để chuyển sang điểm dữ liệu tiếp theo
                            global_index += 1
                        else:
                            # Nếu vượt quá số lượng smoothed values, giữ nguyên giá trị gốc
                            corrected_counts[bin_index] = sample_counts[bin_index]
                    except Exception as e:
                        # Nếu có lỗi, giữ nguyên giá trị gốc
                        corrected_counts[bin_index] = sample_counts[bin_index]
                else:
                    # Bin không hợp lệ thì giữ nguyên giá trị gốc
                    corrected_counts[bin_index] = sample_counts[bin_index]

            # Điền các vị trí còn lại với giá trị gốc (nếu có)
            for bin_index in range(min_len, len(sample_counts)):
                corrected_counts[bin_index] = sample_counts[bin_index]

            # Lưu kết quả đã correction cho chromosome này
            corrected_sample[chromosome] = corrected_counts
        else:
            # Chromosome không có dữ liệu GC thì copy nguyên dữ liệu gốc
            corrected_sample[chromosome] = sample_data[chromosome].copy()

    return corrected_sample

def normalize_readcount(pipeline_obj, raw_readcount_file, output_dir):

    raw_name = Path(raw_readcount_file).stem
    normalized_file = output_dir / f"{raw_name.replace('_raw', '_normalized')}.npz"

    if normalized_file.exists():
        return str(normalized_file)

    raw_data = np.load(raw_readcount_file)
    chromosome_data = {}

    for chromosome in pipeline_obj.chromosome_list:
        if chromosome in raw_data.files:
            chromosome_data[chromosome] = raw_data[chromosome].copy()
        else:
            chromosome_data[chromosome] = np.array([])

    gc_data, n_data = gccount(pipeline_obj, pipeline_obj.work_directory / "Input" / "hg19.fa")
    if gc_data is None or n_data is None:
        np.savez_compressed(normalized_file, **chromosome_data)
        return str(normalized_file)
    chromosome_data = lowess_normalize(pipeline_obj, chromosome_data, gc_data, n_data)

    np.savez_compressed(normalized_file, **chromosome_data)

    return str(normalized_file)