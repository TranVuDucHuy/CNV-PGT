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