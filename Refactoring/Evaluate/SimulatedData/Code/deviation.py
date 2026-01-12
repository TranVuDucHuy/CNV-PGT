import pandas as pd
from pathlib import Path
from collections import defaultdict
from Code import utils

def create_gt2(metadata_df: pd.DataFrame, samples: list) -> pd.DataFrame:
    """Tạo ground truth GT2 (baseline = 2 cho mọi NST)."""
    integrate_rows = []
    region_cols = [col for col in metadata_df.columns if col != 'sample']
    
    for sample_id in samples:
        sample_meta = metadata_df[metadata_df['sample'] == sample_id]
        if sample_meta.empty:
            continue
        
        row = {'sample': sample_id}
        for region_col in region_cols:
            scale_ratio = float(sample_meta.iloc[0][region_col])
            expected_cn = scale_ratio * 2.0
            row[region_col] = expected_cn
        
        integrate_rows.append(row)
    
    return pd.DataFrame(integrate_rows)

def create_gtbf(metadata_df: pd.DataFrame, regions_df: pd.DataFrame, samples: list, groundtruth_dir: Path) -> pd.DataFrame:
    """Tạo ground truth GTBF (dựa trên BlueFuse ground truth)."""
    integrate_rows = []
    
    for sample_id in samples:
        sample_meta = metadata_df[metadata_df['sample'] == sample_id]
        if sample_meta.empty:
            continue
        
        bluefuse_file = groundtruth_dir / sample_id / f"{sample_id}_bluefuse_segments.bed"
        if not bluefuse_file.exists():
            continue
        bluefuse_df = pd.read_csv(bluefuse_file, sep='\t')
        
        row = {'sample': sample_id}
        for idx, region_row in regions_df.iterrows():
            region_id = idx + 1
            scale_ratio = float(sample_meta.iloc[0][str(region_id)])

            base_cn = utils.get_region_copy_number(
                bluefuse_df,
                region_row['chrom'],
                region_row['chromStart'],
                region_row['chromEnd']
            )
            expected_cn = scale_ratio * base_cn if base_cn is not None else None
            row[str(region_id)] = expected_cn
        
        integrate_rows.append(row)
    
    return pd.DataFrame(integrate_rows)

def run_integrate(experiment_id: str, metadata_dir: Path, merge_dir: Path,
                  integrate_dir: Path, gt_type: str, groundtruth_dir: Path):
    """Tạo bảng integrate cho ground truth và các thuật toán."""
    metadata_tsv = metadata_dir / f"{experiment_id}.tsv"
    regions_bed = metadata_dir / f"{experiment_id}.bed"
    if not metadata_tsv.exists() or not regions_bed.exists():
        return
    
    metadata_df = pd.read_csv(metadata_tsv, sep='\t')
    regions_df = pd.read_csv(regions_bed, sep='\s+', usecols=['chrom', 'chromStart', 'chromEnd', 'type'])
    
    # Lấy danh sách samples từ merge_dir
    samples = [d.name for d in merge_dir.iterdir() if d.is_dir()]
    if not samples:
        return
    
    # Tạo ground truth
    if gt_type == "GT2":
        gt_df = create_gt2(metadata_df, samples)
    else:  # GTBF
        gt_df = create_gtbf(metadata_df, regions_df, samples, groundtruth_dir)
    
    # Lưu ground truth integrate
    gt_integrate_file = integrate_dir / f"{gt_type}_integrate.tsv"
    cols = ['sample'] + [str(i+1) for i in range(len(regions_df))]
    gt_df = gt_df.reindex(columns=cols, fill_value=None)
    gt_df.to_csv(gt_integrate_file, sep='\t', index=False)
    
    # Xử lý từng thuật toán
    integrate_rows_per_algorithm = defaultdict(list)
    
    for sample_dir in sorted(merge_dir.iterdir()):
        if not sample_dir.is_dir():
            continue
        
        sample_id = sample_dir.name
        
        # Xử lý tất cả thuật toán
        algorithm_files = list(sample_dir.glob("*_segments.bed"))
        for algorithm_file in algorithm_files:
            algorithm_id = algorithm_file.name.replace(f"{sample_id}_", "").replace("_segments.bed", "")
            algorithm_df = pd.read_csv(algorithm_file, sep='\t')
            
            row_integrate = {'sample': sample_id}
            for idx, region_row in regions_df.iterrows():
                region_id = idx + 1
                region_cn = utils.get_region_copy_number(
                    algorithm_df,
                    region_row['chrom'],
                    region_row['chromStart'],
                    region_row['chromEnd']
                )
                row_integrate[str(region_id)] = region_cn
            
            integrate_rows_per_algorithm[algorithm_id].append(row_integrate)
    
    # Lưu bảng integrate cho từng thuật toán
    for algorithm_id, rows in integrate_rows_per_algorithm.items():
        integrate_df = pd.DataFrame(rows)
        cols = ['sample'] + [str(i+1) for i in range(len(regions_df))]
        integrate_df = integrate_df.reindex(columns=cols, fill_value=None)
        
        integrate_file = integrate_dir / f"{algorithm_id}_integrate.tsv"
        integrate_df.to_csv(integrate_file, sep='\t', index=False)
    

def run_deviation(experiment_id: str, metadata_dir: Path, integrate_dir: Path, 
                  deviation_dir: Path, gt_type: str):
    """Tính toán độ lệch từ các bảng integrate."""
    regions_bed = metadata_dir / f"{experiment_id}.bed"
    
    if not regions_bed.exists():
        return
    
    regions_df = pd.read_csv(regions_bed, sep='\s+', usecols=['chrom', 'chromStart', 'chromEnd', 'type'])
    
    # Đọc ground truth integrate
    gt_integrate_file = integrate_dir / f"{gt_type}_integrate.tsv"
    if not gt_integrate_file.exists():
        return
    gt_df = pd.read_csv(gt_integrate_file, sep='\t')
    
    # Tìm tất cả file integrate của thuật toán
    algorithm_integrate_files = [f for f in integrate_dir.glob("*_integrate.tsv") 
                                 if not f.name.startswith(('GT2', 'GTBF'))]
    
    # Tính deviation và relative cho từng thuật toán
    for algorithm_integrate_file in algorithm_integrate_files:
        algorithm_id = algorithm_integrate_file.name.replace("_integrate.tsv", "")
        algorithm_integrate_df = pd.read_csv(algorithm_integrate_file, sep='\t')
        
        deviation_rows = []
        relative_rows = []
        
        for _, algorithm_row in algorithm_integrate_df.iterrows():
            sample_id = algorithm_row['sample']
            
            # Lấy ground truth tương ứng
            gt_row = gt_df[gt_df['sample'] == sample_id]
            if gt_row.empty:
                continue
            gt_row = gt_row.iloc[0]
            
            dev_row = {'sample': sample_id}
            rel_row = {'sample': sample_id}
            
            for idx, region_row in regions_df.iterrows():
                region_id = str(idx + 1)
                region_type = region_row['type']  # 'G' hoặc 'L'
                
                algorithm_value = algorithm_row.get(region_id)
                gt_value = gt_row.get(region_id)
                
                if pd.isna(algorithm_value) or pd.isna(gt_value):
                    dev_row[region_id] = None
                    rel_row[region_id] = None
                    continue
                
                raw = algorithm_value - gt_value
                deviation = raw if region_type == 'G' else -raw
                if gt_value != 0:
                    relative = round((deviation / gt_value) * 100, 2)
                else:
                    relative = None
                
                dev_row[region_id] = deviation
                rel_row[region_id] = f"{relative}%" if relative is not None else None
            
            deviation_rows.append(dev_row)
            relative_rows.append(rel_row)
        
        # Lưu deviation và relative
        cols = ['sample'] + [str(i+1) for i in range(len(regions_df))]
        dev_dir = deviation_dir / gt_type
        dev_dir.mkdir(parents=True, exist_ok=True)
        
        dev_df = pd.DataFrame(deviation_rows)
        dev_df = dev_df.reindex(columns=cols, fill_value=None)
        dev_file = dev_dir / f"{algorithm_id}_deviation.tsv"
        dev_df.to_csv(dev_file, sep='\t', index=False)
        
        rel_df = pd.DataFrame(relative_rows)
        rel_df = rel_df.reindex(columns=cols, fill_value=None)
        rel_file = dev_dir / f"{algorithm_id}_relative.tsv"
        rel_df.to_csv(rel_file, sep='\t', index=False)