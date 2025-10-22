import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import shutil
import argparse

plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

class Plotter:
    """
    Lớp chứa các phương thức để vẽ biểu đồ CNV
    """

    def __init__(self, chromosome_list, bin_size, output_dir):
        """
        Khởi tạo Plotter

        Args:
            chromosome_list (list): Danh sách chromosome cần phân tích
            bin_size (int): Kích thước bin
            output_dir (Path): Thư mục đầu ra
        """
        self.chromosome_list = chromosome_list
        self.bin_size = bin_size
        self.output_dir = Path(output_dir)

    def plot(self, log2_ratio_file, segments_csv=None):
        """
        Tạo biểu đồ CNV từ dữ liệu log2 ratio với segments
        """
        # Sử dụng pipeline_obj nếu có để lấy các thuộc tính
        chromosome_list = self.chromosome_list
        bin_size = self.bin_size
        output_dir = self.output_dir
        ratio_data = np.load(log2_ratio_file)
        segments_df = pd.read_csv(segments_csv) if segments_csv else None
        ratio_name = Path(log2_ratio_file).stem.replace('_log2Ratio', '')
        # Đặt tên file:
        # - Trường hợp bình thường: vẽ tất cả chromosome => dùng tên rút gọn "{ratio_name}_scatterChart.png"
        # - Nếu chỉ vẽ 1 NST trong nhóm 1..22 thì thêm nhãn chromosome để phân biệt
        if len(chromosome_list) == 1:
            plot_file = Path(output_dir) / f"{ratio_name}_chr{str(chromosome_list[0])}_scatterChart.png"
        else:
            plot_file = Path(output_dir) / f"{ratio_name}_scatterChart.png"

        # Tạo figure chỉ với 1 subplot (loại bỏ boxplot)
        fig, ax1 = plt.subplots(1, 1, figsize=(20, 10))

        # Chuẩn bị dữ liệu cho plotting
        all_positions = []
        all_copy_numbers = []
        all_colors = []
        all_chroms = []
        chromosome_boundaries = []
        chromosome_centers = []
        chromosome_labels = []

        # Đường giới hạn cho các trạng thái ploidy (thang copy number)
        constitutional_3n_cn = 3.0
        constitutional_2n_cn = 2.0
        constitutional_1n_cn = 1.0

        current_pos = 0

        for chrom in chromosome_list:
            if chrom in ratio_data.files:
                ratios = ratio_data[chrom]

                # Tạo vị trí cho các bin
                num_bins = len(ratios)
                bin_positions = np.arange(num_bins) + current_pos

                # Lọc các điểm hợp lệ: không phải -2 và không bị đánh dấu lọc (<= -10)
                valid_mask = ratios > -10

                if np.any(valid_mask):
                    valid_positions = bin_positions[valid_mask]
                    valid_ratios = ratios[valid_mask]
                    valid_copy_numbers = np.power(2.0, valid_ratios + 1.0)

                    colors = []
                    for ratio in valid_ratios:
                        colors.append('#888888')

                    all_positions.extend(valid_positions)
                    all_copy_numbers.extend(valid_copy_numbers)
                    all_colors.extend(colors)
                    all_chroms.extend([chrom] * len(valid_positions))

                # Lưu boundary của chromosome
                if current_pos > 0:
                    chromosome_boundaries.append(current_pos)

                # Tính center cho nhãn chromosome trên trục X
                chromosome_centers.append(current_pos + num_bins / 2.0)
                chromosome_labels.append(chrom)

                current_pos += num_bins

        # Chuyển thành array
        all_positions = np.array(all_positions)
        all_copy_numbers = np.array(all_copy_numbers)
        all_colors = np.array(all_colors)

        # Kiểm tra xem có dữ liệu hợp lệ không
        if len(all_positions) == 0:
            print("Cảnh báo: Không có dữ liệu hợp lệ để vẽ biểu đồ!")
            # Tạo biểu đồ trống với thông báo
            ax1.text(0.5, 0.5, 'Không có dữ liệu hợp lệ',
                     transform=ax1.transAxes, ha='center', va='center', fontsize=14)
        else:
            # Vẽ scatter plot (subplot 1) theo thang copy number
            ax1.scatter(all_positions, all_copy_numbers, c=all_colors, alpha=0.7, s=15, edgecolors='none')

            # Vẽ đường segments nếu có
            if segments_df is not None:
                self._plot_segments(ax1, segments_df, ratio_data, bin_size)

            # Vẽ đường giới hạn (copy number)
            ax1.axhline(y=constitutional_3n_cn, color='lightcoral', linestyle='--', alpha=0.8, linewidth=1.5,
                        label='Constitutional 3n (CN=3)')
            ax1.axhline(y=constitutional_1n_cn, color='lightblue', linestyle='--', alpha=0.8, linewidth=1.5,
                        label='Constitutional 1n (CN=1)')
            ax1.axhline(y=constitutional_2n_cn, color='darkgray', linestyle='-', alpha=0.8, linewidth=1.5,
                        label='Diploid baseline (CN=2)')

            # Vẽ đường phân chia chromosome
            for boundary in chromosome_boundaries:
                ax1.axvline(x=boundary, color='darkgray', linestyle='-', alpha=0.5, linewidth=0.8)

        ax1.set_ylabel('Copy number', fontsize=12)
        ax1.set_title(f'Copy Number Variation Analysis - {ratio_name}', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right')
        # Chỉ hiển thị grid theo trục Y
        ax1.grid(True, axis='y', alpha=0.3)
        # Ẩn spine (đường trục) của trục X và tắt grid trục X
        ax1.xaxis.grid(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        # Ẩn vạch tick của trục X nhưng giữ nhãn NST
        ax1.tick_params(axis='x', which='both', length=0)
        ax1.set_ylim(0, 4)  # Giới hạn trục y cho copy number
        # Thiết lập các mức trên trục Y mỗi 0.2 để hiển thị đường mức dày hơn
        ax1.set_yticks(np.arange(0, 4.1, 0.2))

        # Thiết lập nhãn trục X theo chromosome (1..22, X, Y) thay cho số
        if len(chromosome_centers) > 0:
            ax1.set_xlim(0, current_pos)
            ax1.set_xticks(chromosome_centers)
            ax1.set_xticklabels(chromosome_labels, fontsize=10)

        # Đã loại bỏ phần vẽ boxplot (subplot 2)

        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Đã lưu biểu đồ vào: {plot_file}")
        return str(plot_file)

    def _plot_segments(self, ax, segments_df, ratio_data, bin_size=None):
        """
        Vẽ đường segments lên biểu đồ

        Args:
            ax: Matplotlib axis object
            segments_df: DataFrame chứa thông tin segments
            ratio_data: Dữ liệu ratio NPZ để map positions
            bin_size: Kích thước bin (nếu None sẽ dùng self.bin_size)
        """
        if bin_size is None:
            bin_size = self.bin_size

        # Tạo mapping từ chromosome position thực tế sang bin index
        chrom_bin_mapping = {}
        current_bin = 0

        for chrom in self.chromosome_list:
            if chrom in ratio_data.files:
                ratios = ratio_data[chrom]
                num_bins = len(ratios)

                # Map từ position thực tế sang bin index
                chrom_bin_mapping[chrom] = {
                    'start_bin': current_bin,
                    'end_bin': current_bin + num_bins - 1,
                    'num_bins': num_bins
                }
                current_bin += num_bins

        # Vẽ từng segment
        for _, segment in segments_df.iterrows():
            chrom = str(segment['chrom_original']) if 'chrom_original' in segment.index else str(segment['chrom'])

            if chrom in chrom_bin_mapping:
                chrom_info = chrom_bin_mapping[chrom]

                # Chuyển đổi từ map location thực tế sang bin index
                start_maploc = segment['loc.start'] if 'loc.start' in segment.index else 0
                end_maploc = segment['loc.end'] if 'loc.end' in segment.index else bin_size

                # Tính bin index từ map location
                start_bin_idx = int(start_maploc // bin_size)
                end_bin_idx = int(end_maploc // bin_size)

                # Chuyển sang plot position
                plot_start = chrom_info['start_bin'] + start_bin_idx
                plot_end = chrom_info['start_bin'] + min(end_bin_idx, chrom_info['num_bins'] - 1)

                # Đảm bảo positions hợp lệ
                plot_start = max(chrom_info['start_bin'], plot_start)
                plot_end = min(chrom_info['end_bin'], plot_end)

                # Xác định giá trị y vẽ segment theo scale
                seg_value = float(np.power(2.0, segment['seg.mean'] + 1.0))

                # Màu sắc segment dựa trên seg.mean ở thang log2
                if seg_value > 2.45:
                    color = '#FF0000'  # Đỏ đậm cho gain
                    linewidth = 4
                    alpha = 0.9
                elif seg_value < 1.55:
                    color = '#0000FF'  # Xanh đậm cho loss
                    linewidth = 4
                    alpha = 0.9
                else:
                    color = '#000000'  # Đen cho normal
                    linewidth = 2
                    alpha = 0.7

                # Vẽ đường segment
                ax.plot([plot_start, plot_end], [seg_value, seg_value],
                        color=color, linewidth=linewidth, alpha=alpha, solid_capstyle='round')


def _build_arg_parser():
    parser = argparse.ArgumentParser(description='Vẽ biểu đồ CNV cho 1 chromosome từ log2Ratio.npz và segments.tsv')
    parser.add_argument('--ratio', required=True, help='Đường dẫn tới tệp log2Ratio.npz')
    parser.add_argument('--segments', required=False, help='Đường dẫn tới tệp segments (TSV/CSV)')
    parser.add_argument('--chrom', required=True, help='Chromosome cần vẽ (ví dụ: 1..22, X, Y)')
    parser.add_argument('--bin-size', type=int, required=True, help='Kích thước bin (bp) dùng để quy đổi vị trí')
    return parser


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    ratio_path = Path(args.ratio)
    if not ratio_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp ratio: {ratio_path}")

    out_dir = ratio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Khởi tạo Plotter với chỉ 1 chromosome
    plotter = Plotter(chromosome_list=[str(args.chrom)], bin_size=int(args.bin_size), output_dir=out_dir)

    # Vẽ và in đường dẫn file ảnh
    img_path = plotter.plot(str(ratio_path), segments_csv=args.segments)
    print(img_path)


if __name__ == '__main__':
    main()