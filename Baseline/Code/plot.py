import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import shutil

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

    def plot(self, ratio_npz, mean_filter_npz, segments_csv=None):
        """
        Tạo biểu đồ CNV từ dữ liệu log2 ratio với segments

        Args:
            ratio_npz (str): Đường dẫn file NPZ chứa log2 ratio
            mean_filter_npz (str): Đường dẫn file NPZ chứa mean đã lọc
            segments_csv (str): Đường dẫn file CSV chứa segments (tùy chọn)
            pipeline_obj (optional): Object CNVPipeline để truy cập các thuộc tính

        Returns:
            str: Đường dẫn file PNG chứa biểu đồ
        """
        # Sử dụng pipeline_obj nếu có để lấy các thuộc tính
        chromosome_list = self.chromosome_list
        bin_size = self.bin_size
        output_dir = self.output_dir

        print(f"Đang tạo biểu đồ cho: {ratio_npz}")

        # Đọc dữ liệu
        ratio_data = np.load(ratio_npz)
        mean_data = np.load(mean_filter_npz)

        # Đọc segments nếu có
        segments_df = None
        if segments_csv and Path(segments_csv).exists():
            try:
                segments_df = pd.read_csv(segments_csv)
                print(f"Đã đọc {len(segments_df)} segments từ {segments_csv}")
            except Exception as e:
                print(f"Lỗi khi đọc segments: {e}")

        # Tạo tên file output
        ratio_name = Path(ratio_npz).stem.replace('_ratio_2', '')
        plot_file = Path(output_dir) / f"{ratio_name}_cnv_plot.png"

        # Tạo figure chỉ với 1 subplot (loại bỏ boxplot)
        fig, ax1 = plt.subplots(1, 1, figsize=(20, 10))

        # Chuẩn bị dữ liệu cho plotting
        all_positions = []
        all_ratios = []
        all_colors = []
        all_chroms = []
        chromosome_boundaries = []

        # Đường giới hạn cho các trạng thái ploidy
        constitutional_3n = np.log2(3 / 2)  # ≈ 0.58
        constitutional_2n = 0.0
        constitutional_1n = np.log2(1 / 2)  # ≈ -1.0

        current_pos = 0

        for chrom in chromosome_list:
            if chrom in ratio_data.files and chrom in mean_data.files:
                ratios = ratio_data[chrom]
                means = mean_data[chrom]

                # Tạo vị trí cho các bin
                num_bins = len(ratios)
                bin_positions = np.arange(num_bins) + current_pos

                # Lọc các điểm hợp lệ (không phải -2)
                valid_mask = ratios != -2

                if np.any(valid_mask):
                    valid_positions = bin_positions[valid_mask]
                    valid_ratios = ratios[valid_mask]

                    # Phân loại màu sắc theo giá trị log2 ratio
                    colors = []
                    for ratio in valid_ratios:
                        colors.append('#888888')  # Xám cho normal

                    all_positions.extend(valid_positions)
                    all_ratios.extend(valid_ratios)
                    all_colors.extend(colors)
                    all_chroms.extend([chrom] * len(valid_positions))

                # Lưu boundary của chromosome
                if current_pos > 0:
                    chromosome_boundaries.append(current_pos)

                current_pos += num_bins

        # Chuyển thành array
        all_positions = np.array(all_positions)
        all_ratios = np.array(all_ratios)
        all_colors = np.array(all_colors)

        # Kiểm tra xem có dữ liệu hợp lệ không
        if len(all_positions) == 0:
            print("Cảnh báo: Không có dữ liệu hợp lệ để vẽ biểu đồ!")
            # Tạo biểu đồ trống với thông báo
            ax1.text(0.5, 0.5, 'Không có dữ liệu hợp lệ',
                     transform=ax1.transAxes, ha='center', va='center', fontsize=14)
        else:
            # Vẽ scatter plot (subplot 1) - theo style WisecondorX
            ax1.scatter(all_positions, all_ratios, c=all_colors, alpha=0.7, s=15, edgecolors='none')

            # Vẽ đường segments nếu có
            if segments_df is not None:
                self._plot_segments(ax1, segments_df, ratio_data, bin_size)

            # Vẽ đường giới hạn
            ax1.axhline(y=constitutional_3n, color='lightcoral', linestyle='--', alpha=0.8, linewidth=1.5,
                        label='Constitutional 3n')
            ax1.axhline(y=constitutional_1n, color='lightblue', linestyle='--', alpha=0.8, linewidth=1.5,
                        label='Constitutional 1n')

            # Vẽ đường phân chia chromosome
            for boundary in chromosome_boundaries:
                ax1.axvline(x=boundary, color='lightgray', linestyle='-', alpha=0.5, linewidth=0.8)

        ax1.set_ylabel('log2(ratio)', fontsize=12)
        ax1.set_title(f'Copy Number Variation Analysis - {ratio_name}', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-2, 2)  # Giới hạn trục y như WisecondorX

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

        print(f"Vẽ {len(segments_df)} segments...")

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

                # Màu sắc segment
                seg_mean = segment['seg.mean']
                if seg_mean > 0.2:
                    color = '#FF0000'  # Đỏ đậm cho gain
                    linewidth = 4
                    alpha = 0.9
                elif seg_mean < -0.2:
                    color = '#0000FF'  # Xanh đậm cho loss
                    linewidth = 4
                    alpha = 0.9
                else:
                    color = '#000000'  # Đen cho normal
                    linewidth = 2
                    alpha = 0.7

                # Vẽ đường segment
                ax.plot([plot_start, plot_end], [seg_mean, seg_mean],
                        color=color, linewidth=linewidth, alpha=alpha, solid_capstyle='round')