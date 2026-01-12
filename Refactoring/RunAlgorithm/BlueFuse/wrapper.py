import os
import shutil
import pandas as pd
from pathlib import Path

# Độ dài chromosome cho GRCh37
CHROMOSOME_LENGTHS_GRCh37 = {
    "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276,
    "5": 180915260, "6": 171115067, "7": 159138663, "8": 146364022,
    "9": 141213431, "10": 135534747, "11": 135006516, "12": 133851895,
    "13": 115169878, "14": 107349540, "15": 102531392, "16": 90354753,
    "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
    "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566,
}

def convert_bins_file(input_path, output_path):
    """Chuyển đổi processed.xls thành bluefuse_bins.bed"""
    df = pd.read_csv(input_path, sep='\t', header=None, skiprows=49)
    df = df.iloc[:, [2, 3, 1]]  # chrom, start, copyNumber
    df.columns = ['chrom', 'chromStart', 'copyNumber']
    df['chrom'] = df['chrom'].astype(str)
    df = df[df['chrom'].astype(int).between(1, 24)]
    
    # Thêm chromEnd
    chromEnd_list = []
    for i, row in df.iterrows():
        chrom = row['chrom']
        if i + 1 < len(df) and df.iloc[i+1]['chrom'] == chrom:
            chromEnd_list.append(df.iloc[i+1]['chromStart'])
        else:
            chromEnd_list.append(CHROMOSOME_LENGTHS_GRCh37.get(chrom, row['chromStart'] + 1))  # Mặc định nếu không biết
    df['chromEnd'] = chromEnd_list
    df = df[['chrom', 'chromStart', 'chromEnd', 'copyNumber']]
    
    # Ghi tệp BED (tab-separated, với header)
    df.to_csv(output_path, sep='\t', index=False, header=True)
    print("Đã chuyển đổi tệp bins")

def convert_segments_file(input_path, output_path):
    """Chuyển đổi segments.txt thành bluefuse_segments.bed"""
    df = pd.read_csv(input_path, sep='\t')
    df = df[['Chromosome', 'Start', 'End', 'Copy #']]
    df.columns = ['chrom', 'chromStart', 'chromEnd', 'copyNumber']
    df['chrom'] = df['chrom'].astype(str)
    df = df[df['chrom'].astype(int).between(1, 24)]
    
    # Ghi tệp BED
    df.to_csv(output_path, sep='\t', index=False, header=True)
    print("Đã chuyển đổi tệp segments")

def main():
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'Input'
    output_dir = base_dir / 'Output'
    
    if not input_dir.exists():
        print("Thư mục Input không tồn tại.")
        return
    
    # Đảm bảo thư mục đầu ra tồn tại
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Quét các thí nghiệm
    for experiment_dir in input_dir.iterdir():
        if not experiment_dir.is_dir():
            continue
        experiment_name = experiment_dir.name
        print(f"Đang xử lý thí nghiệm: {experiment_name}")
        
        for sample_dir in experiment_dir.iterdir():
            if not sample_dir.is_dir():
                continue
            sample_id = sample_dir.name
            print(f"  Đang xử lý mẫu: {sample_id}")
            
            # Tạo thư mục đầu ra
            experiment_output_directory = output_dir / experiment_name
            sample_output_dir = experiment_output_directory / sample_id
            sample_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Xác định đường dẫn tệp - tìm tệp động
            bins_files = list(sample_dir.glob("*_processed.xls"))
            bins_input = bins_files[0] if bins_files else None
            bins_output = sample_output_dir / f"{sample_id}_bluefuse_bins.bed"
            
            segments_input = sample_dir / f"{sample_id}_segments.txt"
            segments_output = sample_output_dir / f"{sample_id}_bluefuse_segments.bed"
            
            image_files = list(sample_dir.glob("*.jpg"))
            image_input = image_files[0] if image_files else None
            image_output = sample_output_dir / f"{sample_id}_bluefuse_scatterChart.jpg"
            
            # Chuyển đổi tệp
            if bins_input and bins_input.exists():
                convert_bins_file(bins_input, bins_output)
            else:
                print("Không tìm thấy tệp bins")
            
            if segments_input.exists():
                convert_segments_file(segments_input, segments_output)
            else:
                print("Không tìm thấy tệp segments")
            
            if image_input and image_input.exists():
                shutil.copy2(image_input, image_output)
                print("Đã sao chép và đổi tên ảnh")
            else:
                print("Không tìm thấy tệp ảnh")

if __name__ == "__main__":
    main()