from pathlib import Path
from Code import merge
from Code import deviation
from Code import statistic
from Code import plot

def get_all_experiments(metadata_dir: Path):
    """Quét tất cả các thí nghiệm có trong thư mục Metadata."""
    experiments = []
    for tsv_file in metadata_dir.glob("*.tsv"):
        experiment_id = tsv_file.stem
        bed_file = metadata_dir / f"{experiment_id}.bed"
        if bed_file.exists():
            experiments.append(experiment_id)
    return sorted(experiments)

def process_experiment(experiment_id: str, root_dir: Path):
    """Xử lý một thí nghiệm."""    
    input_dir = root_dir / "Input"
    metadata_dir = input_dir / "Metadata"
    groundtruth_dir = input_dir / "GroundTruth"
    experiment_temp_dir = root_dir / "Temporary" / experiment_id
    experiment_out_dir = root_dir / "Output" / experiment_id
    merge_dir = experiment_temp_dir / "Merge"
    integrate_dir = experiment_temp_dir / "Integrate"
    deviation_dir = experiment_temp_dir / "Deviation"
    
    merge_dir.mkdir(parents=True, exist_ok=True)
    integrate_dir.mkdir(parents=True, exist_ok=True)
    deviation_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Gộp dữ liệu
    print(f"    [1/5] Gộp dữ liệu từ các thuật toán...")
    merge.run_merge(experiment_id, input_dir, merge_dir)
    
    # Xử lý cho cả GT2 và GTBF
    for gt_type in ["GT2", "GTBF"]:
        output_dir = experiment_out_dir / gt_type
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Tạo bảng integrate
        print(f"    [2/5] Tạo bảng integrate cho {gt_type}...")
        deviation.run_integrate(experiment_id, metadata_dir, merge_dir, integrate_dir, gt_type, groundtruth_dir)
        
        # 3. Tính độ lệch
        print(f"    [3/5] Tính độ lệch cho {gt_type}...")
        deviation.run_deviation(experiment_id, metadata_dir, integrate_dir, deviation_dir, gt_type)
        
        # 4. Thống kê
        print(f"    [4/5] Tổng hợp thống kê cho {gt_type}...")
        statistic.run_statistic(experiment_id, deviation_dir, output_dir, gt_type)
        
        # 5. Vẽ biểu đồ
        print(f"    [5/5] Vẽ biểu đồ cho {gt_type}...")
        plot.run_plot(experiment_id, deviation_dir, output_dir, gt_type)
    

def main():
    root_dir = Path(__file__).resolve().parent
    metadata_dir = root_dir / "Input" / "Metadata"
    if not metadata_dir.exists():
        print(f"Không tìm thấy thư mục Metadata: {metadata_dir}")
        return
    
    # Xử lý tất cả thí nghiệm
    experiments = get_all_experiments(metadata_dir)
    if not experiments:
        print("Không tìm thấy thí nghiệm nào trong thư mục Metadata")
        return
    
    for i, experiment_id in enumerate(experiments, 1):
        print(f"\033[1m\n=== XỬ LÝ THÍ NGHIỆM [{i}/{len(experiments)}]: {experiment_id} ===\033[0m")
        process_experiment(experiment_id, root_dir)
    
    print("Hoàn thành!")

if __name__ == "__main__":
    main()
