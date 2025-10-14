import numpy as np
from pathlib import Path

def filter_bins(cv_file, filter_ratio, output_dir):
    """
    Create a boolean mask ("blacklist") of stable bins based on Coefficient of Variation (CV).

    Args:
        cv_file (str): Path to an NPZ file that contains per-bin CV arrays for each chromosome.
        filter_ratio (float): Fraction of bins to retain (0 < filter_ratio <= 1). Higher means keep more bins.
        output_dir (pathlib.Path): Directory to write the resulting `blacklist.npz` file.

    Returns:
        str: File path to the saved `blacklist.npz` containing boolean masks per chromosome.
    """
    cv_data = np.load(cv_file, allow_pickle=True)
    keep_dict = {}

    for chromosome in cv_data.files:
        cv_array = cv_data[chromosome]
        num_bins = len(cv_array)

        if num_bins == 0:
            keep_dict[chromosome] = np.array([], dtype=bool)
            continue

        num_keep = int(np.ceil(num_bins * filter_ratio))

        threshold = np.sort(cv_array)[num_keep - 1]
        keep_mask = cv_array <= threshold

        keep_dict[chromosome] = keep_mask

    blacklist_file = output_dir / "blacklist_1.npz"
    np.savez_compressed(blacklist_file, **keep_dict)
    return str(blacklist_file)


def filter_base(gc_file, n_file, max_N=0.1, min_GC=0.0):
    """
    Create a per-chromosome boolean mask that marks bins NOT eligible for normalization
    based on base composition thresholds.
    """
    gc_data = np.load(gc_file)
    n_data = np.load(n_file)

    base_filter = {}
    for chrom in gc_data.files:
        gc_arr = gc_data[chrom]
        n_arr = n_data[chrom]
        base_filter[chrom] = (n_arr >= max_N) | (gc_arr <= min_GC)

    # Save alongside gc_file (expected to be in Prepare directory)
    from pathlib import Path
    base_file = Path(gc_file).parent / "Base_filter.npz"
    np.savez_compressed(base_file, **base_filter)
    return str(base_file)


def filter_import(bed_file, pipeline_obj):
    """
    Đọc các vùng blacklist từ tệp BED và tạo mặt nạ (boolean) theo bin cho từng nhiễm sắc thể.
    """
    bin_size = pipeline_obj.bin_size

    mask_dict = {}
    for chrom in pipeline_obj.chromosome_list:
        num_bins = pipeline_obj.chromosome_lengths[chrom] // bin_size
        mask_dict[chrom] = np.zeros(num_bins, dtype=bool)

    # Đọc BED, cắt tiền tố 'chr' và ánh xạ vùng sang các bin
    bed_path = str(bed_file)
    try:
        with open(bed_path, 'r') as f:
            for line in f:
                parts = line.strip().split()

                chrom = parts[0][3:]
                if chrom not in mask_dict:
                    continue
                start = int(parts[1])
                end = int(parts[2])

                num_bins = mask_dict[chrom].shape[0]
                bin_start = start // bin_size
                bin_end = (end - 1) // bin_size

                if bin_start >= num_bins or bin_end < 0:
                    continue

                # Clip vào khoảng hợp lệ
                mask_dict[chrom][bin_start:bin_end + 1] = True
    except FileNotFoundError:
        raise FileNotFoundError(f"Không tìm thấy tệp BED: {bed_path}")

    import_filter_path = pipeline_obj.work_directory / "Prepare" / "Import_filter.npz"
    np.savez_compressed(import_filter_path, **mask_dict)
    return str(import_filter_path)


def combine_filters(work_dir):
    """
    Kết hợp Base_filter.npz và Import_filter.npz thành một tệp duy nhất Combined_filter.npz.
    """
    base_path = work_dir / "Base_filter.npz"
    import_path = work_dir / "Import_filter.npz"

    base_data = np.load(base_path)
    import_data = np.load(import_path)

    # Theo giả định: cùng tập key và cùng chiều dài cho từng key
    combined = {}
    for chrom in base_data.files:
        base_filter = base_data[chrom].astype(bool, copy=False)
        import_filter = import_data[chrom].astype(bool, copy=False)
        combined[chrom] = np.logical_or(base_filter, import_filter)

    out_path = work_dir / "Combined_filter.npz"
    np.savez_compressed(out_path, **combined)
    return str(out_path)


def create_blacklist(train_dir, combined_filter_file, z_score=3.0, cv_threshold=0.2):
    """
    Tạo Blacklist.npz dựa trên:
    - combined_filter: mặt nạ loại bỏ sẵn
    - outlier theo z-score trên mean frequency của từng chromosome
    - các bin có CV cao nhất (trong phần còn lại)
    """

    frequency_list = list(Path(train_dir).glob("*_frequency.npz"))

    # 2) Tải dữ liệu tần suất (frequency) của từng mẫu -> gom theo chromosome
    all_data = {}
    for frequency_file in frequency_list:
        data = np.load(frequency_file)
        for chromosome in data.files:
            all_data.setdefault(chromosome, []).append(data[chromosome])

    # 3) Tính mean/std/cv như statistics
    mean_dict, std_dict, cv_dict = {}, {}, {}
    for chromosome, arr_list in all_data.items():
        stack = np.array(arr_list)  # (n_samples, n_bins)
        mean_dict[chromosome] = stack.mean(axis=0)
        std_dict[chromosome] = stack.std(axis=0)
        cv_dict[chromosome] = np.divide(std_dict[chromosome], mean_dict[chromosome], out=np.zeros_like(std_dict[chromosome]), where=mean_dict[chromosome] != 0)

    # 4) Tính mean_x, std_x theo chromosome (chỉ trên bin KHÔNG bị combined_filter), rồi đánh dấu outlier
    combined = np.load(combined_filter_file)
    outlier_dict = {}
    for chromosome, mean_arr in mean_dict.items():
        keep = ~combined[chromosome].astype(bool, copy=False)
        vals = mean_arr[keep]
        mean_x, std_x = (0.0, 0.0) if vals.size == 0 else (vals.mean(), vals.std())
        outlier_dict[chromosome] = np.zeros_like(mean_arr, dtype=bool) if std_x <= 0 else (mean_arr - mean_x) > (z_score * std_x)

    # 6) Lọc theo CV trong phần còn lại (không thuộc combined_filter hoặc outlier)
    # Gom các cv của bin được giữ lại để xếp hạng
    keep_values_list, idx_map = [], []
    for chromosome, cv_arr in cv_dict.items():
        keep_mask = (~combined[chromosome].astype(bool, copy=False)) & (~outlier_dict[chromosome])
        idxs = np.flatnonzero(keep_mask)
        if idxs.size:
            keep_values_list.append(cv_arr[idxs])
            idx_map.append((chromosome, idxs))

    cv_selected = {chrom: np.zeros_like(cv_arr, dtype=bool) for chrom, cv_arr in cv_dict.items()}
    if keep_values_list:
        all_cv = np.concatenate(keep_values_list)
        k = int(np.ceil(cv_threshold * all_cv.size))
        if k:
            top_idx = np.argpartition(-all_cv, kth=k-1)[:k]
            offsets = np.cumsum([0] + [len(v) for v in keep_values_list])
            for pos in top_idx:
                grp = np.searchsorted(offsets, pos, side='right') - 1
                chromosome, idxs = idx_map[int(grp)]
                cv_selected[chromosome][int(idxs[int(pos - offsets[int(grp)])])] = True

    # 7) Gộp mask và nới rộng 1 bin kề mỗi bin bị đánh dấu
    final_mask = {}
    for chromosome in mean_dict.keys():
        base_mask = combined[chromosome].astype(bool, copy=False) | outlier_dict[chromosome] | cv_selected[chromosome]
        if base_mask.size:
            expanded = base_mask.copy()
            expanded[:-1] |= base_mask[1:]
            expanded[1:] |= base_mask[:-1]
            final_mask[chromosome] = expanded
        else:
            final_mask[chromosome] = base_mask

    # 8) Lưu Blacklist.npz cùng chỗ với combined_filter
    out_path = Path(train_dir).parent / "Blacklist.npz"
    np.savez_compressed(out_path, **final_mask)
    return str(out_path)