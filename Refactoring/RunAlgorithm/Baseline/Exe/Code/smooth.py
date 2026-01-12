from pathlib import Path
from typing import Optional
import numpy as np


def median_smooth(log2_ratio_file: str, output_dir: str, smooth: int = 1) -> str:
    """
    Median smooth per-chromosome log2 ratios with masked-bin awareness.
    """
    # name = Path(log2_ratio_file).stem
    # out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_median_log2Ratio')}.npz"
    # half_window = max(0, int(smooth) // 2)

    # log2_ratio_data = np.load(log2_ratio_file)
    # out_dict = {}
    # for chromosome in log2_ratio_data.files:
    #     arr = log2_ratio_data[chromosome]
    #     n = len(arr)
    #     out = arr.copy()

    #     for i in range(n):
    #         low = max(0, i - half_window)
    #         high = min(n - 1, i + half_window)
    #         window = arr[low : high + 1]
    #         valid_vals = window[window > -10]
    #         if valid_vals.size > 0:
    #             out[i] = float(np.median(valid_vals))
    #     out_dict[chromosome] = out

    # np.savez_compressed(out_file, **out_dict)
    # return str(out_file)

    name = Path(log2_ratio_file).stem
    out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_mean_log2Ratio')}.npz"
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
            while len(chosen) < int(smooth) and (left >= 0 or right < valid_idx.size):
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
                out[i] = float(np.median(vals))

        out_dict[chromosome] = out

    np.savez_compressed(out_file, **out_dict)
    return str(out_file)

def mean_smooth(log2_ratio_file: str, output_dir: str, smooth: int = 1) -> str:
    """
    Mean smooth per-chromosome log2 ratios using nearest valid bins.
    """
    name = Path(log2_ratio_file).stem
    out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_mean_log2Ratio')}.npz"
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
            while len(chosen) < int(smooth) and (left >= 0 or right < valid_idx.size):
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


def bilateral_smooth(
    log2_ratio_file: str,
    output_dir: str,
    smooth: int = 5,
    sigma: Optional[float] = None,
    sigma_intensity: Optional[float] = None,
) -> str:
    """
    Bilateral filtering (spatial + intensity) for per-chromosome log2 ratios with masked-bin awareness.

    Thay vì chỉ Gaussian theo khoảng cách, bộ lọc song phương (bilateral) kết hợp:
    - Trọng số không gian (spatial): gần nhau theo chỉ số bin được ưu tiên (Gaussian theo khoảng cách).
    - Trọng số cường độ (range/intensity): giá trị log2 tương tự nhau được ưu tiên (Gaussian theo |x_j - x_ref|).

    Quy ước mask: chỉ dùng các bin hợp lệ (giá trị > -10) để tính trọng số và trung bình.
    Nếu vị trí trung tâm i bị mask (<= -10), GIỮ NGUYÊN giá trị tại i và bỏ qua lọc tại vị trí đó.

    Tham số
    --------
    log2_ratio_file : str
        Đường dẫn tới file .npz đầu vào (mỗi key là 1 NST, value là mảng log2 ratio).
    output_dir : str
        Thư mục ghi kết quả .npz.
    smooth : int, mặc định 5
        Kích thước cửa sổ (số bin). half-window = floor(smooth/2).
    sigma : Optional[float], mặc định None
        Sigma không gian (spatial) theo đơn vị bin. Nếu None, dùng max(1e-6, half_window/2)
        để ~±2σ ≈ half_window (≈95% khối lượng trong cửa sổ).
    sigma_intensity : Optional[float], mặc định None
        Sigma cường độ (range) theo đơn vị log2. Nếu None, ước lượng robust theo MAD trên
        các bin hợp lệ của nhiễm sắc thể: sigma_r = max(1e-6, 1.4826·MAD). Nếu MAD=0, fallback 0.2.
    """
    name = Path(log2_ratio_file).stem
    out_file = Path(output_dir) / f"{name.replace('_log2Ratio', '_bilateral_log2Ratio')}.npz"

    # Define window and kernel width
    half_window = int(smooth) // 2
    if sigma is None:
        # Sigma không gian: ~95% (±2σ) trong cửa sổ
        sigma = max(1e-6, float(half_window) / 2.0)
    log2_ratio_data = np.load(log2_ratio_file)
    out_dict = {}

    for chromosome in log2_ratio_data.files:
        arr = log2_ratio_data[chromosome]
        n = len(arr)
        out = arr.copy()

        # Identify valid (unmasked) bins once
        valid_mask = arr > -10
        valid_idx = np.flatnonzero(valid_mask)
        if valid_idx.size == 0:
            out_dict[chromosome] = out
            continue

        # Range sigma: estimate robustly if not provided
        if sigma_intensity is None:
            valid_vals = arr[valid_mask]
            med = np.median(valid_vals)
            mad = np.median(np.abs(valid_vals - med))
            sigma_r = 1.5 * mad
            if sigma_r <= 0:
                sigma_r = 0.2
        else:
            sigma_r = max(1e-6, float(sigma_intensity))

        for i in range(n):
            # If center bin is masked, skip filtering and keep original value
            if not valid_mask[i]:
                continue

            # Window bounds
            low = max(0, i - half_window)
            high = min(n - 1, i + half_window)

            # Restrict to valid indices within the window
            # Using searchsorted on valid_idx for efficiency
            start = np.searchsorted(valid_idx, low, side="left")
            end = np.searchsorted(valid_idx, high, side="right")
            win_idx = valid_idx[start:end]

            if win_idx.size == 0:
                # No valid neighbor in the window; keep original
                continue

            # Spatial weights (Gaussian by distance)
            d = win_idx.astype(float) - float(i)
            w_s = np.exp(-0.5 * (d / sigma) ** 2)

            # Range weights (Gaussian by intensity difference)
            vals = arr[win_idx]
            x_ref = float(arr[i])
            w_r = np.exp(-0.5 * ((vals - x_ref) / sigma_r) ** 2)

            w = w_s * w_r
            denom = w.sum()
            if denom > 0:
                out[i] = float(np.dot(w, vals) / denom)

        out_dict[chromosome] = out

    np.savez_compressed(out_file, **out_dict)
    return str(out_file)
