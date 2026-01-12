import pandas as pd
import numpy as np
from pathlib import Path

def run_deviation_statistic(df: pd.DataFrame, experiment_id: str, output_dir: Path):
    """Tính toán thống kê cho deviation distribution."""
    dev_dist_rows = []
    algorithms = df['algorithm'].unique()
    
    for algorithm in algorithms:
        sub = df[df['algorithm'] == algorithm]
        devs = sub['algorithmDeviation'].dropna()
        if devs.empty:
            continue
            
        mean_val = devs.mean()
        percentiles = [10, 20, 30, 40, 60, 70, 80, 90]
        p = {pct: np.percentile(devs, pct) for pct in percentiles}
        
        dev_dist_rows.append({
            'algorithm': algorithm,
            'mean': round(mean_val, 4),
            '20%': f"[{p[40]:.4f}, {p[60]:.4f}]",
            '40%': f"[{p[30]:.4f}, {p[70]:.4f}]",  
            '60%': f"[{p[20]:.4f}, {p[80]:.4f}]",  
            '80%': f"[{p[10]:.4f}, {p[90]:.4f}]"   
        })
        
    if dev_dist_rows:
        df_dev_dist = pd.DataFrame(dev_dist_rows)
        out_dev = output_dir / f"{experiment_id}_deviation.tsv"
        df_dev_dist.to_csv(out_dev, sep='\t', index=False)

def run_relative_statistic(df: pd.DataFrame, experiment_id: str, output_dir: Path):
    """Tính toán thống kê cho relative distribution."""
    rel_dist_rows = []
    algorithms = df['algorithm'].unique()
    
    for algorithm in algorithms:
        sub = df[df['algorithm'] == algorithm]
        rels = sub['algorithmRelative'].dropna()
        rels = rels.str.rstrip('%').astype(float)
        if rels.empty:
            continue
            
        total = len(rels)        
        c1 = ((rels >= -10) & (rels < -5)).sum()
        c2 = ((rels >= -5) & (rels < 0)).sum()
        c3 = ((rels >= 0) & (rels < 5)).sum()
        c4 = ((rels >= 5) & (rels <= 10)).sum()
        
        rel_dist_rows.append({
            'algorithm': algorithm,
            '[-10%, -5%)': f"{(c1 / total) * 100:.2f}%",
            '[-5%, 0%)': f"{(c2 / total) * 100:.2f}%",
            '[0%, 5%)': f"{(c3 / total) * 100:.2f}%",
            '[5%, 10%]': f"{(c4 / total) * 100:.2f}%"
        })
        
    if rel_dist_rows:
        df_rel_dist = pd.DataFrame(rel_dist_rows)
        out_rel = output_dir / f"{experiment_id}_relative.tsv"
        df_rel_dist.to_csv(out_rel, sep='\t', index=False)

def run_statistic(experiment_id: str, summary_file: str, output_dir: str):
    """Chạy thống kê cho deviation và relative distributions."""
    summary_file = Path(summary_file)
    output_dir = Path(output_dir)
    
    if not summary_file.exists():
        return
        
    df = pd.read_csv(summary_file, sep='\t')
    if df.empty:
        return
        
    run_deviation_statistic(df, experiment_id, output_dir)
    run_relative_statistic(df, experiment_id, output_dir)
