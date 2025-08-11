import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import argparse
import numpy as np
from pathlib import Path

# --- CẤU HÌNH BIỂU ĐỒ ---
# Màu sắc tương tự WisecondorX
GAIN_COLOR = '#44B8A3'  # Teal
LOSS_COLOR = '#E4C479'  # Gold
NEUTRAL_COLOR = '#666666' # Dark gray

# Ngưỡng để xác định Gain/Loss từ log2.copyRatio
GAIN_THRESHOLD = 0
LOSS_THRESHOLD = 0

# Kích thước bộ gen hg19 (sử dụng để tạo trục X)
HG19_CHROMS = {
    'chr1': 249250621, 'chr2': 243199373, 'chr3': 198022430, 'chr4': 191154276,
    'chr5': 180915260, 'chr6': 171115067, 'chr7': 159138663, 'chr8': 146364022,
    'chr9': 141213431, 'chr10': 135534747, 'chr11': 135006516, 'chr12': 133851895,
    'chr13': 115169878, 'chr14': 107349540, 'chr15': 102531392, 'chr16': 90354753,
    'chr17': 81195210, 'chr18': 78077248, 'chr19': 59128983, 'chr20': 63025520,
    'chr21': 48129895, 'chr22': 51304566, 'chrX': 155270560, 'chrY': 59373566
}

def plot_cnv(seg_file_path, output_file_path):
    """
    Hàm chính để đọc file .seg và vẽ biểu đồ CNV toàn bộ bộ gen.
    """
    # 1. Đọc và xử lý dữ liệu đầu vào
    try:
        df = pd.read_csv(seg_file_path, sep='\t')
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{seg_file_path}'")
        return

    # Sắp xếp các nhiễm sắc thể theo thứ tự tự nhiên
    chrom_order = [f'chr{i}' for i in range(1, 23)] + ['chrX', 'chrY']
    df['chrom'] = pd.Categorical(df['chrom'], categories=chrom_order, ordered=True)
    df = df.sort_values('chrom')
    df = df[df['chrom'].isin(HG19_CHROMS.keys())].copy() # Lọc ra các NST chuẩn

    # 2. Tạo hệ tọa độ bộ gen
    chrom_offsets = {}
    current_offset = 0
    for chrom in chrom_order:
        if chrom in HG19_CHROMS:
            chrom_offsets[chrom] = current_offset
            current_offset += HG19_CHROMS[chrom]
    total_genome_length = current_offset

    # 3. Bắt đầu vẽ
    fig, ax = plt.subplots(figsize=(20, 7))

    # Vẽ nền xen kẽ
    for i, chrom in enumerate(chrom_order):
        if chrom in chrom_offsets:
            start_pos = chrom_offsets[chrom]
            end_pos = start_pos + HG19_CHROMS[chrom]
            if i % 2 == 1: # Các nhiễm sắc thể chẵn (1, 3, 5...)
                ax.axvspan(start_pos, end_pos, facecolor='#F0F0F0', zorder=-10)

    # 4. Vẽ các đoạn CNV
    for _, row in df.iterrows():
        chrom, start, end = row['chrom'], row['start'], row['end']
        log2_ratio = row['log2.copyRatio']
        
        abs_start = chrom_offsets[chrom] + start
        abs_end = chrom_offsets[chrom] + end
        
        color = NEUTRAL_COLOR
        if log2_ratio > GAIN_THRESHOLD:
            color = GAIN_COLOR
        elif log2_ratio < LOSS_THRESHOLD:
            color = LOSS_COLOR
            
        # Chỉ vẽ các đoạn có thay đổi (không phải neutral)
        if color != NEUTRAL_COLOR:
            # Vẽ một đường ngang dày để thể hiện segment
            ax.hlines(y=log2_ratio, xmin=abs_start, xmax=abs_end, color=color, linewidth=4)

    # 5. Tùy chỉnh giao diện biểu đồ
    # Vẽ các đường tham chiếu
    ax.axhline(y=np.log2(3/2), color=GAIN_COLOR, linestyle=':', linewidth=1.5, zorder=0) # 3n
    ax.axhline(y=0, color=NEUTRAL_COLOR, linestyle='--', linewidth=1.5, zorder=0)      # 2n
    ax.axhline(y=np.log2(1/2), color=LOSS_COLOR, linestyle=':', linewidth=1.5, zorder=0)  # 1n

    # Vẽ đường phân cách và nhãn nhiễm sắc thể
    chrom_label_y = -2.4 # Vị trí của nhãn 'chr1', 'chr2'...
    ax.axhline(y=-2.0, color='black', linewidth=1.5) # Đường cơ sở cho nhãn

    for chrom in chrom_order:
        if chrom in chrom_offsets:
            start_pos = chrom_offsets[chrom]
            end_pos = start_pos + HG19_CHROMS[chrom]
            label_pos = start_pos + (end_pos - start_pos) / 2
            
            ax.axvline(x=end_pos, linestyle=':', color='black', linewidth=0.8)
            ax.text(label_pos, chrom_label_y, chrom.replace("chr", ""), ha='center', va='center', fontsize=12)

    # Cài đặt trục và tiêu đề
    ax.set_xlim(0, total_genome_length)
    ax.set_ylim(-2.0, 2.0)
    ax.set_ylabel('log₂(ratio)', fontsize=14)
    ax.set_xticks([]) # Bỏ các tick số trên trục x
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # 6. Tạo Legends
    # Chú thích cho Gain/Loss
    legend_elements_1 = [
        Patch(facecolor=GAIN_COLOR, edgecolor=GAIN_COLOR, label='Gain'),
        Patch(facecolor=LOSS_COLOR, edgecolor=LOSS_COLOR, label='Loss')
    ]
    leg1 = ax.legend(handles=legend_elements_1, loc='upper left',
                     bbox_to_anchor=(0.01, 1.15), frameon=False, fontsize=14)
    ax.add_artist(leg1)

    # Chú thích cho các trạng thái
    legend_elements_2 = [
        Line2D([0], [0], color=GAIN_COLOR, linestyle=':', lw=2, label='Constitutional 3n'),
        Line2D([0], [0], color=NEUTRAL_COLOR, linestyle='--', lw=2, label='Constitutional 2n'),
        Line2D([0], [0], color=LOSS_COLOR, linestyle=':', lw=2, label='Constitutional 1n')
    ]
    ax.legend(handles=legend_elements_2, loc='upper left',
              bbox_to_anchor=(0.2, 1.15), frameon=False, fontsize=14)
              
    fig.tight_layout(rect=[0, 0.05, 1, 0.95]) # Điều chỉnh layout để nhãn không bị cắt

    # 7. Lưu file kết quả
    plt.savefig(output_file_path, dpi=300, bbox_inches='tight')
    print(f"Biểu đồ đã được lưu tại: {output_file_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Vẽ biểu đồ CNV toàn bộ bộ gen từ file .seg của BIC-seq2.")
    parser.add_argument("seg_file", help="Đường dẫn đến file .seg đầu vào.")
    parser.add_argument("output_file", help="Đường dẫn đến file ảnh .png hoặc .pdf đầu ra.")
    args = parser.parse_args()
    
    plot_cnv(args.seg_file, args.output_file)