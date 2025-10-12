import numpy as np

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

    blacklist_file = output_dir / "blacklist.npz"
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