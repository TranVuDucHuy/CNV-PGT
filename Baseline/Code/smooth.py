from pathlib import Path
import numpy as np


def median_smooth(log2_ratio_file: str, output_dir: str, smooth: int = 1) -> str:
    """
    Median smooth per-chromosome log2 ratios with masked-bin awareness.
    """
    name = Path(log2_ratio_file).stem
    out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_median_log2Ratio')}.npz"
    half_window = max(0, int(smooth) // 2)

    log2_ratio_data = np.load(log2_ratio_file)
    out_dict = {}
    for chromosome in log2_ratio_data.files:
        arr = log2_ratio_data[chromosome]
        n = len(arr)
        out = arr.copy()

        for i in range(n):
            low = max(0, i - half_window)
            high = min(n - 1, i + half_window)
            window = arr[low : high + 1]
            valid_vals = window[window > -10]
            if valid_vals.size > 0:
                out[i] = float(np.median(valid_vals))
        out_dict[chromosome] = out

    np.savez_compressed(out_file, **out_dict)
    return str(out_file)


def mean_smooth(log2_ratio_file: str, output_dir: str, smooth: int = 1) -> str:
    """
    Mean smooth per-chromosome log2 ratios using nearest valid bins.
    """
    name = Path(log2_ratio_file).stem
    out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_mean_log2Ratio')}.npz"
    k = max(1, int(smooth))

    log2_ratio_data = np.load(log2_ratio_file)
    out_dict = {}
    for chromosome in log2_ratio_data.files:
        arr = log2_ratio_data[chromosome]
        n = len(arr)
        out = arr.copy()

        # indices of valid (unmasked) bins
        valid_idx = np.flatnonzero(arr > -10)
        if valid_idx.size == 0:
            out_dict[chromosome] = out
            continue

        # For each position, pick k nearest valid indices by distance
        for i in range(n):
            pos = np.searchsorted(valid_idx, i)
            left = pos - 1
            right = pos
            chosen = []
            while len(chosen) < k and (left >= 0 or right < valid_idx.size):
                if left < 0:
                    chosen.append(valid_idx[right])
                    right += 1
                elif right >= valid_idx.size:
                    chosen.append(valid_idx[left])
                    left -= 1
                else:
                    if abs(valid_idx[left] - i) <= abs(valid_idx[right] - i):
                        chosen.append(valid_idx[left])
                        left -= 1
                    else:
                        chosen.append(valid_idx[right])
                        right += 1

            vals = arr[np.array(chosen, dtype=int)]
            if vals.size > 0:
                out[i] = float(np.mean(vals))

        out_dict[chromosome] = out

    np.savez_compressed(out_file, **out_dict)
    return str(out_file)
