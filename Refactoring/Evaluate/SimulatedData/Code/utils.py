import pandas as pd
from typing import Optional, Tuple, Union
from pathlib import Path

def get_overlap_length(seg_start: int, seg_end: int, region_start: int, region_end: int) -> int:
    """Tính độ dài overlap giữa segment và region."""
    overlap_start = max(seg_start, region_start)
    overlap_end = min(seg_end, region_end)
    return max(0, overlap_end - overlap_start)

def get_region_copy_number(segments_df: pd.DataFrame, region_chrom: str, 
                           region_start: int, region_end: int) -> Optional[float]:
    """Xác định CN đại diện cho vùng theo CN của phân đoạn overlap với vùng nhiều nhất."""
    if segments_df.empty:
        return None
    
    # Lọc các segments trên cùng NST
    sub = segments_df[segments_df['chrom'] == region_chrom].copy()
    if sub.empty:
        return None
    
    # Tính overlap với từng segment
    sub['overlap'] = sub.apply(
        lambda row: get_overlap_length(
            row['chromStart'], row['chromEnd'], 
            region_start, region_end
        ),
        axis=1
    )
    
    # Lấy segment có overlap lớn nhất
    max_overlap_seg = sub.loc[sub['overlap'].idxmax()]
    if max_overlap_seg['overlap'] == 0:
        return None
    
    return float(max_overlap_seg['copyNumber'])