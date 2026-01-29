import pandas as pd
import numpy as np
from pathlib import Path

def run_mean_statistic(deviation_files: list, relative_files: list, output_dir: Path, experiment_id: str):
    """Tạo bảng thống kê mean."""
    mean_rows = []
    
    for dev_file in deviation_files:
        algorithm_id = dev_file.name.replace("_deviation.tsv", "")
        dev_df = pd.read_csv(dev_file, sep='\t')
        rel_file = None
        for rel_file_path in relative_files:
            if rel_file_path.name.replace("_relative.tsv", "") == algorithm_id:
                rel_file = rel_file_path
                break
        rel_df = pd.read_csv(rel_file, sep='\t') if rel_file and rel_file.exists() else pd.DataFrame()
        
        # Lấy danh sách các cột region (bỏ qua cột 'sample')
        region_cols = [col for col in dev_df.columns if col != 'sample']
        for region_id in region_cols:
            dev_values = pd.to_numeric(dev_df[region_id], errors='coerce').dropna()
            if dev_values.empty:
                continue
            
            mean_abs_dev = dev_values.abs().mean()
            mean_squared_dev = (dev_values ** 2).mean()
            
            mean_abs_rel = None
            if not rel_df.empty and region_id in rel_df.columns:
                rel_values = pd.to_numeric(rel_df[region_id].astype(str).str.rstrip('%'), errors='coerce').dropna()
                if not rel_values.empty:
                    mean_abs_rel = rel_values.abs().mean()
            
            mean_rows.append({
                'region': region_id,
                'algorithm': algorithm_id,
                'meanAbsoluteDeviation': f"{mean_abs_dev:.4f}",
                'meanAbsoluteRelative': f"{mean_abs_rel:.2f}%" if mean_abs_rel is not None else None,
                'meanSquaredDeviation': f"{mean_squared_dev:.4f}"
            })
    
    mean_df = pd.DataFrame(mean_rows)
    mean_file = output_dir / f"{experiment_id}_mean.tsv"
    mean_df.to_csv(mean_file, sep='\t', index=False)

def run_deviation_statistic(deviation_files: list, output_dir: Path, experiment_id: str):
    """Tạo bảng thống kê deviation (ngưỡng lệch)."""
    deviation_stat_rows = []
    
    for dev_file in deviation_files:
        algorithm_id = dev_file.name.replace("_deviation.tsv", "")
        dev_df = pd.read_csv(dev_file, sep='\t')
        
        region_cols = [col for col in dev_df.columns if col != 'sample']
        for region_id in region_cols:
            dev_values = pd.to_numeric(dev_df[region_id], errors='coerce').dropna()
            if dev_values.empty:
                continue
            
            mean_val = dev_values.mean()
            percentiles = [10, 20, 30, 40, 60, 70, 80, 90]
            p = {pct: np.percentile(dev_values, pct) for pct in percentiles}
            
            deviation_stat_rows.append({
                'region': region_id,
                'algorithm': algorithm_id,
                'mean': f"{mean_val:.4f}",
                '20%': f"[{p[40]:.4f}, {p[60]:.4f}]",
                '40%': f"[{p[30]:.4f}, {p[70]:.4f}]",
                '60%': f"[{p[20]:.4f}, {p[80]:.4f}]",
                '80%': f"[{p[10]:.4f}, {p[90]:.4f}]"
            })
    
    dev_stat_df = pd.DataFrame(deviation_stat_rows)
    dev_stat_file = output_dir / f"{experiment_id}_deviation.tsv"
    dev_stat_df.to_csv(dev_stat_file, sep='\t', index=False)

def run_relative_statistic(relative_files: list, output_dir: Path, experiment_id: str):
    """Tạo bảng thống kê relative (phân bố trong các khoảng)."""
    relative_stat_rows = []
    
    for rel_file in relative_files:
        algorithm_id = rel_file.name.replace("_relative.tsv", "")
        rel_df = pd.read_csv(rel_file, sep='\t')
        
        region_cols = [col for col in rel_df.columns if col != 'sample']
        for region_id in region_cols:
            rel_values = pd.to_numeric(rel_df[region_id].astype(str).str.rstrip('%'), errors='coerce').dropna()
            if rel_values.empty:
                continue
            
            total = len(rel_values)
            
            # Đếm số lượng trong từng khoảng (giống RealData, dùng %)
            c1 = ((rel_values >= -10) & (rel_values < -5)).sum()
            c2 = ((rel_values >= -5) & (rel_values < 0)).sum()
            c3 = ((rel_values >= 0) & (rel_values < 5)).sum()
            c4 = ((rel_values >= 5) & (rel_values <= 10)).sum()
            
            relative_stat_rows.append({
                'region': region_id,
                'algorithm': algorithm_id,
                '[-10%, -5%)': f"{(c1 / total) * 100:.2f}%",
                '[-5%, 0%)': f"{(c2 / total) * 100:.2f}%",
                '[0%, 5%)': f"{(c3 / total) * 100:.2f}%",
                '[5%, 10%]': f"{(c4 / total) * 100:.2f}%"
            })
    
    rel_stat_df = pd.DataFrame(relative_stat_rows)
    rel_stat_file = output_dir / f"{experiment_id}_relative.tsv"
    rel_stat_df.to_csv(rel_stat_file, sep='\t', index=False)

def run_statistic(experiment_id: str, deviation_dir: Path, output_dir: Path, gt_type: str):
    """Tạo các bảng thống kê cho deviation và relative."""
    deviation_dir = deviation_dir / gt_type
    output_dir.mkdir(parents=True, exist_ok=True)
    if not deviation_dir.exists():
        return
    
    deviation_files = list(deviation_dir.glob("*_deviation.tsv"))
    relative_files = list(deviation_dir.glob("*_relative.tsv"))
    if not deviation_files:
        return
    
    run_mean_statistic(deviation_files, relative_files, output_dir, experiment_id)
    run_deviation_statistic(deviation_files, output_dir, experiment_id)
    run_relative_statistic(relative_files, output_dir, experiment_id)
    
