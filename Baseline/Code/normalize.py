import numpy as np
from pathlib import Path

try:
    from statsmodels.nonparametric.smoothers_lowess import lowess
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

from estimate import CHROMOSOME_LENGTHS_GRCh37
def nucleotide_content(pipeline_obj, fasta_file):
    """Return two separate dicts (gc_dict, n_dict) with counts per full bin (floor logic).
    Two NPZ cache files are written: *_gc.npz and *_n.npz.
    Trailing partial bins are ignored to stay consistent with readcount binning (floor).
    """
    gc_file = pipeline_obj.work_directory / "Temporary" / "GC-content.npz"
    n_file = pipeline_obj.work_directory / "Temporary" / "N-content.npz"

    if gc_file.exists() and n_file.exists():
        gc_loaded = np.load(gc_file)
        n_loaded = np.load(n_file)
        return ({k: gc_loaded[k] for k in gc_loaded.files}, {k: n_loaded[k] for k in n_loaded.files})

    # Pre-allocate arrays per chromosome like readcount: num_bins = chrom_length // bin_size
    gc_counts = {}
    n_counts = {}
    for chromosome in pipeline_obj.chromosome_list:
        chrom_len = CHROMOSOME_LENGTHS_GRCh37[str(chromosome)]
        num_bins = chrom_len // pipeline_obj.bin_size
        gc_counts[chromosome] = np.zeros(num_bins, dtype=np.int32)
        n_counts[chromosome] = np.zeros(num_bins, dtype=np.int32)

    current_chromosome = None
    current_pos = 0
    gc_count = 0
    n_count = 0
    bin_filled = 0

    def finish_bin(bin_index):
        nonlocal gc_count, n_count
        # Only write counts if within allocated bins
        if current_chromosome is not None:
            arr = gc_counts[current_chromosome]
            if 0 <= bin_index < arr.shape[0]:
                gc_counts[current_chromosome][bin_index] = gc_count
                n_counts[current_chromosome][bin_index] = n_count
            else:
                # bin_index out of range: skip or log
                pass
        # reset counters
        gc_count = 0
        n_count = 0

    try:
        with open(fasta_file, 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    # Bắt đầu chromosome mới: bỏ tiền tố 'chr', chỉ xử lý nếu nằm trong danh sách interest
                    current_pos = 0
                    header_raw = line[1:].split()[0]
                    header = header_raw[3:]  # cắt bỏ 'chr'
                    if header in pipeline_obj.chromosome_list:
                        current_chromosome = header
                    else:
                        current_chromosome = None
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
    except Exception as e:
        print(f"Lỗi khi đọc file FASTA: {e}")
        return None, None

    # Save raw counts for potential debugging
    np.savez_compressed(gc_file, **gc_counts)
    np.savez_compressed(n_file, **n_counts)
    # Compute GC content and N ratio per bin for LOWESS
    gc_content = {}
    n_content = {}
    for chromosome in pipeline_obj.chromosome_list:
        counts_gc = gc_counts[chromosome]
        counts_n = n_counts[chromosome]
        # N ratio = n_count / bin_size
        n_content[chromosome] = counts_n.astype(float) / pipeline_obj.bin_size
        # DEBUG: print computed N ratio
        print(f"[DEBUG N_CONTENT:{chromosome}] len={len(n_content[chromosome])}, sample[:5]={n_content[chromosome][:5]}")
        # GC fraction = gc_count / (bin_size - n_count)
        total_bases = pipeline_obj.bin_size - counts_n
        gc_content[chromosome] = np.where(total_bases > 0,
                                  counts_gc.astype(float) / total_bases,
                                  0.0)
        # DEBUG: print computed GC fraction
        print(f"[DEBUG GC_CONTENT:{chromosome}] len={len(gc_content[chromosome])}, sample[:5]={gc_content[chromosome][:5]}")
    return gc_content, n_content

def lowess_normalize(raw_data, gc_data, n_data, max_n=0.1, min_rd=0.0001, frac=0.1):

    all_gc = []
    all_reads = []
    for chrom in raw_data:
        read_count = raw_data[chrom]
        gc_content = gc_data[chrom]
        n_content_list = n_data[chrom]
        # mask các bin hợp lệ: N ratio thấp, read > min_rd, GC fraction > 0
        mask = (n_content_list < max_n) & (read_count > min_rd) & (gc_content > 0)
        if mask.any():
            all_gc.extend(gc_content[mask].tolist())
            all_reads.extend(read_count[mask].tolist())

    all_gc = np.array(all_gc)
    all_reads = np.array(all_reads)

    if HAS_STATSMODELS:
        try:
            # Trả về mảng smoothed values có cùng thứ tự với input
            smoothed_reads = lowess(all_reads, all_gc, frac=frac, return_sorted=False)
        except Exception as e:
            print(f"Lỗi khi sử dụng statsmodels LOWESS: {e}")
            return raw_data.copy()
    else:
        print("Cảnh báo: statsmodels không có sẵn, không thể thực hiện LOWESS normalization")
        return raw_data.copy()

    # Áp dụng correction cho sample data sử dụng smoothed values
    corrected_data = {}

    # Index để theo dõi vị trí trong mảng all_gc và smoothed_reads
    global_index = 0

    # Duyệt qua tất cả chromosome để áp dụng normalization
    for chromosome in raw_data.keys():
        # Keys in raw_data, gc_data and n_data are guaranteed aligned
        read_count_list = raw_data[chromosome]
        gc_content_list = gc_data[chromosome]
        n_content_list = n_data[chromosome]

        length = len(read_count_list)
        corrected_counts = np.zeros(length, dtype=read_count_list.dtype)

        for bin_index in range(length):
            read_count = read_count_list[bin_index]
            gc_content = gc_content_list[bin_index]
            n_content = n_content_list[bin_index]

            # Kiểm tra bin có hợp lệ để áp dụng correction không
            if (n_content < max_n and read_count > min_rd and gc_content > 0):
                # Lấy giá trị expected từ smoothed values tại vị trí global_index
                try:
                    # Kiểm tra xem global_index có hợp lệ không
                    if global_index < len(smoothed_reads):
                        expected_value = float(smoothed_reads[global_index])

                        if expected_value > 0:
                            corrected_value = read_count_list[bin_index] / expected_value
                        else:
                            corrected_value = read_count_list[bin_index]

                        corrected_counts[bin_index] = corrected_value
                        global_index += 1
                    else:
                        # Nếu vượt quá số lượng smoothed values, giữ nguyên giá trị gốc
                        corrected_counts[bin_index] = read_count_list[bin_index]
                except Exception as e:
                    # Nếu có lỗi, giữ nguyên giá trị gốc
                    corrected_counts[bin_index] = read_count_list[bin_index]
            else:
                # Bin không hợp lệ thì giữ nguyên giá trị gốc
                corrected_counts[bin_index] = read_count_list[bin_index]

        # Lưu kết quả đã correction cho chromosome này
        corrected_data[chromosome] = corrected_counts

    return corrected_data

def normalize_readcount(pipeline_obj, raw_readcount_file, output_dir):

    raw_name = Path(raw_readcount_file).stem
    normalized_file = output_dir / f"{raw_name.replace('_raw', '_normalized')}.npz"

    if normalized_file.exists():
        return str(normalized_file)

    raw_data = np.load(raw_readcount_file)
    gc_data, n_data = nucleotide_content(pipeline_obj, pipeline_obj.work_directory / "Input" / "hg19.fa")
    chromosome_data = lowess_normalize(raw_data, gc_data, n_data)

    np.savez_compressed(normalized_file, **chromosome_data)

    return str(normalized_file)