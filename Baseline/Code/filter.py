import gzip
import numpy as np

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

    blacklist_file = output_dir / "blacklist.npz"
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

def create_filter_files(mean_file, blacklist_file, output_dir):
    """
    Apply the boolean `blacklist` mask to the per-bin mean signals and write a filtered mean file.

    Args:
        mean_file (str): Path to `Mean.npz` (or any NPZ with per-chromosome mean arrays).
        blacklist_file (str): Path to `blacklist.npz` containing boolean keep masks per chromosome.
        output_dir (pathlib.Path): Directory to write `Mean_filtered.npz`.

    Returns:
        str: File path to the saved `Mean_filtered.npz` with filtered mean arrays per chromosome.
    """
    mean_data = np.load(mean_file)
    blacklist_data = np.load(blacklist_file)

    filtered_data = {}

    for chromosome in mean_data.files:
        mean_array = mean_data[chromosome]

        if chromosome in blacklist_data.files:
            mask = blacklist_data[chromosome].astype(bool)
            filtered_array = mean_array[mask]
        else:
            filtered_array = mean_array

        filtered_data[chromosome] = filtered_array

    mean_filtered_file = output_dir / "Mean_filtered.npz"
    np.savez_compressed(mean_filtered_file, **filtered_data)
    return str(mean_filtered_file)