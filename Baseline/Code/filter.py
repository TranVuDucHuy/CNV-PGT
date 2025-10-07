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