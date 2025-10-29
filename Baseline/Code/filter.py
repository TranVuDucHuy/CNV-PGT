import gzip
import numpy as np
from pathlib import Path

def initial_safe_bool_array(x, fill=True):
    """
    Create a boolean array with the same length as the input and a uniform initial value

    Args:
        x (array-like): Reference array whose length determines the output length
        fill (bool): Initial boolean value to fill the array with

    Returns:
        np.ndarray: Boolean array of shape (len(x),) filled with `fill`
    """
    return np.full(len(x), bool(fill), dtype=bool)

def normalize_chromosome_name(chromosome_name: str) -> str:
    """
    Normalize a chromosome name by removing a leading 'chr' prefix if present

    Args:
        chromosome_name (str): Chromosome name (e.g., 'chr1', '1', 'chrX')

    Returns:
        str: Normalized chromosome name without the 'chr' prefix (e.g., '1', 'X')
    """
    chromosome_name = str(chromosome_name).strip()
    if chromosome_name.lower().startswith("chr"):
        chromosome_name = chromosome_name[3:]
    return chromosome_name

def read_bed_intervals(bed_file):
    """
    Read a BED (or BED.GZ) file and collect genomic intervals by chromosome

    Args:
        bed_file (str): Path to a BED or BED.GZ file. Only the first three columns are used

    Returns:
        dict[str, np.ndarray]: Mapping {chromosome -> array of shape (M, 2) with [start, end]}
    """
    open_function = gzip.open if bed_file.endswith(".gz") else open
    chromosome_to_intervals = {}

    with open_function(bed_file, "rt") as file:
        for line in file:
            if not line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue

            chromosome_name, start_str, end_str = parts[0], parts[1], parts[2]
            chromosome_name = normalize_chromosome_name(chromosome_name)

            start_position = int(start_str)
            end_position = int(end_str)
            if end_position <= start_position:
                continue

            chromosome_to_intervals.setdefault(chromosome_name, []).append((start_position, end_position))

    for chromosome, interval_list in chromosome_to_intervals.items():
        chromosome_to_intervals[chromosome] = np.asarray(interval_list, dtype=np.int64)

    return chromosome_to_intervals

def generate_bed_mask(bed_file, bin_coordinate_file):
    """
    Build a boolean keep-mask per chromosome by excluding bins overlapping BED intervals

    Args:
        bed_file (str): Path to BED/BED.GZ file containing regions to exclude
        bin_coordinate_file (str): Path to NPZ with per-chromosome bin coordinates (N x 2: [start, end])

    Returns:
        dict[str, np.ndarray]: Mapping {chromosome -> boolean keep mask of length N} (True = keep)
    """
    bed_data = read_bed_intervals(bed_file)
    coord_data = np.load(bin_coordinate_file, allow_pickle=True)

    mask_dict = {}
    total_bins = total_removed = 0

    for chromosome in coord_data.files:
        bins = np.asarray(coord_data[chromosome])
        starts, ends = bins[:, 0], bins[:, 1]
        keep = initial_safe_bool_array(starts, fill=True)

        if chromosome in bed_data:
            intervals = np.asarray(bed_data[chromosome], dtype=np.int64)
            for bed_start, bed_end in intervals:
                overlap = (starts < bed_end) & (ends > bed_start)
                if np.any(overlap):
                    keep[overlap] = False

        mask_dict[chromosome] = keep
        total_bins += len(keep)
        total_removed += np.count_nonzero(~keep)

    print(f"[BED MASK] Removed {total_removed}/{total_bins} bins "
          f"({100 * total_removed / max(1, total_bins):.2f}%)")

    return mask_dict

def zscore(x):
    """
    Compute absolute z-scores for an array, using NaN-safe mean and std

    Args:
        x (array-like): Input numeric array

    Returns:
        np.ndarray: Absolute z-scores with the same shape as `x`
    """
    x = np.asarray(x, dtype=float)
    mu = np.nanmean(x)
    sigma = np.nanstd(x)
    if sigma == 0:
        sigma = 1e-12
    z = (x - mu) / sigma
    return np.abs(z)

def expand_false(mask, k = 1):
    """
    Expand False (dropped) positions in a boolean mask to k neighbors on both sides

    Args:
        mask (np.ndarray): Boolean array where True=keep and False=drop
        k (int): Number of neighboring indices to expand on each side

    Returns:
        np.ndarray: Boolean mask after expansion (more positions may be False)
    """
    if k <= 0 or mask.size == 0:
        return mask

    bad = ~mask
    n = bad.size

    sum = np.zeros(n + 1, dtype=int)
    bad_bin_index_list = np.flatnonzero(bad)
    for bin_index in bad_bin_index_list:
        low = max(0, bin_index - k)
        high = min(n, bin_index + k + 1)
        sum[low] += 1
        sum[high] -= 1
    expanded_mask = np.cumsum(sum[:-1]) > 0
    return ~(expanded_mask)

def filter_bins(cv_file, bed_file, bin_coordinate_file, filter_ratio, output_dir):
    """
    Create a blacklist mask of bins by combining BED exclusion and CV-based outlier filtering.

    Args:
        cv_file (str): Path to NPZ containing per-chromosome CV (coefficient of variation) arrays.
        bed_file (str): Path to BED/BED.GZ file with regions to exclude.
        bin_coordinate_file (str): Path to NPZ with bin coordinates (N x 2) per chromosome.
        filter_ratio (float): Fraction of bins to keep per chromosome (0 < ratio ≤ 1).
        output_dir (Path): Directory to write the output blacklist NPZ.

    Returns:
        str: File path to the saved `blacklist.npz` containing boolean keep masks per chromosome.
    """
    cv_data = np.load(cv_file, allow_pickle=True)
    bed_mask_data = generate_bed_mask(bed_file, bin_coordinate_file)

    keep_dict = {}
    total_bins = 0
    total_removed = 0

    for chromosome in cv_data.files:
        cv_array = cv_data[chromosome]
        num_bins = len(cv_array)

        if num_bins == 0:
            keep_dict[chromosome] = np.array([], dtype=bool)
            continue

        keep = initial_safe_bool_array(cv_array, fill=True)

        # 1) BED mask (True=keep, False=exclude)
        if chromosome in bed_mask_data:
            bed_mask = bed_mask_data[chromosome]
            if bed_mask.size == num_bins:
                keep &= bed_mask
            else:
                print(f"[WARN] BedMask size mismatch on chr{chromosome}: "
                      f"mask={bed_mask.size}, bins={num_bins}")

        # 2) Outlier filter
        base_value = np.asarray(cv_array, dtype=float)
        abs_z = zscore(base_value)
        num_drop = int(np.ceil(num_bins * (1 - filter_ratio)))
        worst_index = np.argpartition(- abs_z, num_drop - 1)[:num_drop]
        keep[worst_index] = False

        # 3) Original filter
        eligible_index = np.flatnonzero(keep)
        if eligible_index.size > 0:
            num_keep = int(np.ceil(num_bins * filter_ratio))
            num_keep = max(1, min(num_keep, eligible_index.size))
            sort_local = np.argsort(cv_array[eligible_index], kind="mergesort")
            keep_local = eligible_index[sort_local[:num_keep]]
            keep_new = initial_safe_bool_array(cv_array, fill=False)
            keep_new[keep_local] = True
            keep &= keep_new
        else:
            num_keep = max(1, int(np.ceil(num_bins * filter_ratio)))
            cv_order = np.argsort(cv_array, kind="mergesort")
            keep = initial_safe_bool_array(cv_array, fill=True)
            keep[cv_order[:num_keep]] = True

        # 4) Expand dropped bins to ±k neighbors
        keep = expand_false(keep, 1)

        keep_dict[chromosome] = keep.astype(bool)
        total_bins += num_bins
        total_removed += np.count_nonzero(~keep)

    blacklist_file = output_dir / "blacklist_1.npz"
    np.savez_compressed(blacklist_file, **keep_dict)

    removed_percent = 100.0 * total_removed / max(1, total_bins)
    print(f"[FILTER] Saved filtered bins to: {blacklist_file}")
    print(f"[FILTER] Removed {total_removed}/{total_bins} bins ({removed_percent:.2f}%)")

    # Optional: print per-chromosome summary
    print("\n[SUMMARY] Removed bin ratio per chromosome:")
    for chromosome in cv_data.files:
        kept = keep_dict[chromosome]
        if kept.size == 0:
            continue
        removed = np.count_nonzero(~kept)
        removed_ratio = 100.0 * removed / kept.size
        print(f"  chr{chromosome:>2}: {removed:>6}/{kept.size:<6} ({removed_ratio:5.2f}%)")

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
    blacklist_file = Path(train_dir).parent / "Blacklist.npz"
    if blacklist_file.exists():
        print(f"Blacklist file already exists: {blacklist_file}")
        return str(blacklist_file)

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
    np.savez_compressed(blacklist_file, **final_mask)
    return str(blacklist_file)