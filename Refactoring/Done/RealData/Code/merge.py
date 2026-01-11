import shutil
from pathlib import Path

def run_merge(experiment_id: str, input_dir: str, merge_dir: str):
    """Sao chép các tệp segments.bed và scatterChart của các thuật toán."""
    input_dir = Path(input_dir)
    if not input_dir.exists():
        return

    # Quét tất cả các thư mục Thuật toán trong Input/
    algorithm_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    for algorithm_dir in algorithm_dirs:
        algorithm_id = algorithm_dir.name.lower()
        
        experiment_dir = algorithm_dir / experiment_id
        if not experiment_dir.exists():
            continue
        
        # Duyệt qua các sample trong thí nghiệm
        for sample_dir in experiment_dir.iterdir():
            if not sample_dir.is_dir():
                continue
                
            sample_id = sample_dir.name
            target_sample_dir = Path(merge_dir) / sample_id
            target_sample_dir.mkdir(parents=True, exist_ok=True)
            
            # Sao chép file segments
            segment_src = sample_dir / f"{sample_id}_{algorithm_id}_segments.bed"
            segment_dst = target_sample_dir / f"{sample_id}_{algorithm_id}_segments.bed"
            shutil.copy2(segment_src, segment_dst)

            # Sao chép biểu đồ scatter
            scatter_files = list(sample_dir.glob(f"{sample_id}_{algorithm_id}_scatterChart.*"))
            if scatter_files:
                plot_src = scatter_files[0]
                ext = plot_src.suffix
                plot_dst = target_sample_dir / f"{sample_id}_{algorithm_id}_scatterChart{ext}"
                shutil.copy2(plot_src, plot_dst)
