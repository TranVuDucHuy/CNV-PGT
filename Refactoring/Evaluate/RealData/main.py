from pathlib import Path
from Code import merge
from Code import evaluate
from Code import deviation
from Code import statistic
from Code import plot

def get_all_experiments(input_dir: Path):
    """Quét tất cả các thí nghiệm có trong các thư mục thuật toán."""
    experiments = set()
    for algorithm_dir in input_dir.iterdir():
        if not algorithm_dir.is_dir():
            continue

        for experiment_dir in algorithm_dir.iterdir():
            if experiment_dir.is_dir():
                experiments.add(experiment_dir.name)
    
    return sorted(experiments)

def process_experiment(experiment_id: str, root_dir: Path):
    """Xử lý một thí nghiệm."""
    input_dir = root_dir / "Input"
    experiment_temp_dir = root_dir / "Temporary" / experiment_id
    experiment_out_dir = root_dir / "Output" / experiment_id
    merge_dir = experiment_temp_dir / "Merge"
    integrate_dir = experiment_temp_dir / "Integrate"
    
    integrate_dir.mkdir(parents=True, exist_ok=True)

    # 1. Gộp dữ liệu
    merge.run_merge(experiment_id, str(input_dir), str(merge_dir))
    
    for chromosome_type in ["Autosome", "Gonosome"]:
        output_dir = experiment_out_dir / chromosome_type
        output_dir.mkdir(parents=True, exist_ok=True)
                
        # 2. Đánh giá (TP/FP/FN/TN)
        evaluate.run_evaluate(experiment_id, str(merge_dir), str(output_dir), chromosome_type)
        
        # 3. Độ lệch
        deviation.run_deviation(experiment_id, str(merge_dir), str(integrate_dir), str(output_dir), chromosome_type)
        
        # 4. Thống kê
        summary_file = output_dir / f"{experiment_id}_summary.tsv"
        statistic.run_statistic(experiment_id, str(summary_file), str(output_dir))
        
        # 5. Vẽ biểu đồ
        plot.run_plot(experiment_id, str(summary_file), str(output_dir))
    

def main():
    root_dir = Path(__file__).resolve().parent
    input_dir = root_dir / "Input"
    if not input_dir.exists():
        print(f"Không tìm thấy thư mục Input: {input_dir}")
        return
    
    # Xử lý tất cả thí nghiệm
    experiments = get_all_experiments(input_dir)
    if not experiments:
        print("Không tìm thấy thí nghiệm nào trong thư mục Input")
        return
        
    for i, experiment_id in enumerate(experiments, 1):
        print(f"\033[1m\n=== XỬ LÝ THÍ NGHIỆM [{i}/{len(experiments)}]: {experiment_id} ===\033[0m")
        process_experiment(experiment_id, root_dir)
    
    print("Hoàn thành!")

if __name__ == "__main__":
    main()
