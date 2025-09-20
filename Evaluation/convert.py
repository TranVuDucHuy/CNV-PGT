import os
import pandas as pd
import numpy as np
import argparse

def standardize_chromosomes(df, chromosome_col):
    """
    Chuẩn hóa cột nhiễm sắc thể trong một DataFrame.
    - Chuyển đổi X -> 23, Y -> 24
    - Lọc bỏ các nhiễm sắc thể 'M', 'MT', '25'
    """
    # Đảm bảo cột là kiểu string để xử lý
    df_copy = df.copy() # Tạo một bản sao tường minh để tránh cảnh báo
    df_copy[chromosome_col] = df_copy[chromosome_col].astype(str)
    
    # Loại bỏ tiền tố 'chr' (nếu có)
    df_copy[chromosome_col] = df_copy[chromosome_col].str.replace('chr', '', regex=False)

    # Lọc bỏ các hàng không mong muốn
    unwanted_chroms = ['M', 'MT', '25']
    df_filtered = df_copy[~df_copy[chromosome_col].isin(unwanted_chroms)]
    
    # Thay thế X và Y. Dùng .loc để đảm bảo gán giá trị an toàn.
    replacements = {'X': '23', 'Y': '24'}
    df_final = df_filtered.copy() # Tạo bản sao mới để thực hiện replace
    df_final.loc[:, chromosome_col] = df_final[chromosome_col].replace(replacements)
    
    return df_final

def process_bluefuse(input_dir, output_dir, sample_id):
    input_file = os.path.join(input_dir, 'BlueFuse', f'{sample_id}_segments.tsv')
    output_file = os.path.join(output_dir, f'{sample_id}_BlueFuse_segments.tsv')

    print(f"  -> Đang xử lý BlueFuse cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep='\t')

        required_cols = ['Chromosome', 'Start', 'End', 'Copy #']

        df = standardize_chromosomes(df, 'Chromosome')

        df_out = df[required_cols]
        df_out = df_out.rename(columns={'Copy #': 'Copy Number'})

        df_out.to_csv(output_file, sep='\t', index=False)

    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")

def process_bicseq2(input_dir, output_dir, sample_id):
    input_file = os.path.join(input_dir, 'Bicseq2', f'{sample_id}_S93.bicseq2.seg')
    output_file = os.path.join(output_dir, f'{sample_id}_Bicseq2_segments.tsv')

    print(f"  -> Đang xử lý Bicseq2 cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep='\t')

        df = standardize_chromosomes(df, 'chrom')
        
        df['log2.copyRatio'] = pd.to_numeric(df['log2.copyRatio'], errors='coerce')
        df['Copy Number'] = 2**(df['log2.copyRatio'] + 1)
        
        df_out = df[['chrom', 'start', 'end', 'Copy Number']]
        df_out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

        df_out.to_csv(output_file, sep='\t', index=False)

    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")

def process_baseline(input_dir, output_dir, sample_id):
    input_file = os.path.join(input_dir, 'Baseline', f'{sample_id}_S93_normalized_segments.csv')
    output_file = os.path.join(output_dir, f'{sample_id}_Baseline_segments.tsv')

    print(f"  -> Đang xử lý Baseline cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep=',')

        df = standardize_chromosomes(df, 'chrom')
        
        df['seg.mean'] = pd.to_numeric(df['seg.mean'], errors='coerce')
        df['Copy Number'] = 2**(df['seg.mean'] + 1)
        
        df_out = df[['chrom', 'loc.start', 'loc.end', 'Copy Number']]
        df_out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

        df_out.to_csv(output_file, sep='\t', index=False)

    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")

def process_wisecondorx(input_dir, output_dir, sample_id):
    input_file = os.path.join(input_dir, 'WisecondorX', f'{sample_id}_S93_segments.bed')
    output_file = os.path.join(output_dir, f'{sample_id}_WisecondorX_segments.tsv')

    print(f"  -> Đang xử lý WisecondorX cho mẫu {sample_id}...")

    if not os.path.exists(input_file):
        print(f"    [CẢNH BÁO] Không tìm thấy tệp: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep='\t')

        df = standardize_chromosomes(df, 'chr')
        
        df['ratio'] = pd.to_numeric(df['ratio'], errors='coerce')
        df['Copy Number'] = 2**(df['ratio'] + 1)
        
        df_out = df[['chr', 'start', 'end', 'Copy Number']]
        df_out.columns = ['Chromosome', 'Start', 'End', 'Copy Number']

        df_out.to_csv(output_file, sep='\t', index=False)

    except Exception as e:
        print(f"    [LỖI] Đã xảy ra lỗi khi xử lý tệp {input_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Chuẩn hóa dữ liệu segment từ các thuật toán phát hiện CNV.")
    parser.add_argument('-i', '--input_dir', required=True, help="Đường dẫn đến thư mục đầu vào.")
    parser.add_argument('-o', '--output_dir', required=True, help="Đường dẫn đến thư mục đầu ra.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.isdir(input_dir):
        print(f"[LỖI] Thư mục đầu vào không tồn tại: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        sample_ids = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    except OSError as e:
        print(f"[LỖI] Không thể đọc thư mục đầu vào: {e}")
        return

    print(f"Tìm thấy {len(sample_ids)} mẫu")

    for sample_id in sample_ids:
        print(f"\nBắt đầu xử lý mẫu: {sample_id}")
        input_sample_dir = os.path.join(input_dir, sample_id)
        output_sample_dir = os.path.join(output_dir, sample_id)

        os.makedirs(output_sample_dir, exist_ok=True)

        process_bluefuse(input_sample_dir, output_sample_dir, sample_id)
        process_bicseq2(input_sample_dir, output_sample_dir, sample_id)
        process_baseline(input_sample_dir, output_sample_dir, sample_id)
        process_wisecondorx(input_sample_dir, output_sample_dir, sample_id)

    print("\nHoàn tất quá trình chuẩn hóa dữ liệu!")

if __name__ == '__main__':
    main()