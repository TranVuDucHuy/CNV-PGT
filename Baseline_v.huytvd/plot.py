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
        ratio_name = Path(ratio_npz).stem.replace('_ratio', '')
        plot_file = Path(output_dir) / f"{ratio_name}_cnv_plot.png"

        # Tạo figure với 2 subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 14))

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
            ax2.text(0.5, 0.5, 'Không có dữ liệu hợp lệ',
                     transform=ax2.transAxes, ha='center', va='center', fontsize=14)
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

        # Vẽ box plot theo chromosome (subplot 2)
        if len(all_positions) > 0:
            box_data = []
            box_labels = []
            box_colors = []

            for chrom in chromosome_list:
                if chrom in ratio_data.files and chrom in mean_data.files:
                    ratios = ratio_data[chrom]
                    means = mean_data[chrom]

                    # Chỉ lấy các giá trị hợp lệ
                    valid_mask = ratios != -2
                    if np.any(valid_mask):
                        valid_ratios = ratios[valid_mask]
                        box_data.append(valid_ratios)
                        box_labels.append(f'chr{chrom}')

                        # Định màu cho box dựa trên median
                        median_ratio = np.median(valid_ratios)
                        if median_ratio > 0.2:
                            box_colors.append('#FF4444')  # Đỏ cho gain
                        elif median_ratio < -0.2:
                            box_colors.append('#4444FF')  # Xanh cho loss
                        else:
                            box_colors.append('#888888')  # Xám cho normal

            if box_data:
                bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True,
                                 boxprops=dict(alpha=0.7), medianprops=dict(linewidth=2))

                # Tô màu cho box plot
                for patch, color in zip(bp['boxes'], box_colors):
                    patch.set_facecolor(color)

            # Vẽ đường giới hạn cho box plot
            ax2.axhline(y=constitutional_3n, color='lightcoral', linestyle='--', alpha=0.8, linewidth=1.5)
            ax2.axhline(y=constitutional_2n, color='black', linestyle='-', alpha=0.8, linewidth=1.5)
            ax2.axhline(y=constitutional_1n, color='lightblue', linestyle='--', alpha=0.8, linewidth=1.5)

        ax2.set_ylabel('log2(ratio)', fontsize=12)
        ax2.set_xlabel('Chromosome', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-2, 2)

        # Xoay label cho box plot
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

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

    def plot_readcount_per_bin(self, case_dir, output_name="readcount_per_bin", use_normalized=False):
        """
        Vẽ biểu đồ readcount trên từng bin của mỗi mẫu test

        Args:
            case_dir (str): Thư mục chứa file NPZ của các mẫu test
            output_name (str): Tên file output
            use_normalized (bool): True nếu dùng file normalized, False dùng raw counts
        """
        plot_type = "normalized readcount" if use_normalized else "raw readcount"
        print(f"Đang tạo biểu đồ {plot_type} per bin...")

        # Tìm file NPZ theo loại - TÌM FILE NORMALIZED (nhưng KHÔNG phải ratio)
        case_files = []
        for file_path in glob.glob(f"{case_dir}/*.npz"):
            filename = Path(file_path).name
            if use_normalized:
                # Tìm file normalized nhưng KHÔNG phải ratio và chắc chắn có "_normalized"
                if '_normalized' in filename and '_ratio' not in filename:
                    case_files.append(file_path)
            else:
                # Tìm file raw readcount
                if '_normalized' not in filename and '_ratio' not in filename and 'readcount' in filename:
                    case_files.append(file_path)

        if not case_files:
            print(f"Không tìm thấy file NPZ {plot_type} nào trong {case_dir}")
            return

        # Tạo figure
        fig, axes = plt.subplots(len(case_files), 1, figsize=(20, 5 * len(case_files)))
        if len(case_files) == 1:
            axes = [axes]

        for idx, case_file in enumerate(case_files):
            sample_name = Path(case_file).stem
            print(f"Đang xử lý: {sample_name}")

            data = np.load(case_file)

            # Chuẩn bị dữ liệu cho plotting
            all_positions = []
            all_counts = []
            current_pos = 0
            chromosome_boundaries = []
            chr_ticks = []
            chr_labels = []

            for chrom in self.chromosome_list:
                if chrom in data.files:
                    counts = data[chrom]
                    num_bins = len(counts)
                    bin_positions = np.arange(num_bins) + current_pos

                    # Lọc các điểm hợp lệ
                    if use_normalized:
                        valid_mask = ~np.isnan(counts) & (counts >= 0)
                    else:
                        valid_mask = (counts != -1) & (counts >= 0)

                    if np.any(valid_mask):
                        valid_positions = bin_positions[valid_mask]
                        valid_counts = counts[valid_mask]

                        all_positions.extend(valid_positions)
                        all_counts.extend(valid_counts)

                    # Lưu boundary của chromosome
                    if current_pos > 0:
                        chromosome_boundaries.append(current_pos)

                    # Tick giữa chromosome để ghi tên
                    chr_ticks.append(current_pos + num_bins // 2)
                    chr_labels.append(f'chr{chrom}')

                    current_pos += num_bins

            # Vẽ scatter plot
            if all_positions:
                color = 'green' if use_normalized else 'blue'
                axes[idx].scatter(all_positions, all_counts, alpha=0.6, s=8, color=color)

                # Vẽ đường phân chia chromosome - ĐỎ ĐẬM
                for boundary in chromosome_boundaries:
                    axes[idx].axvline(x=boundary, color='red', linestyle='-', alpha=0.8, linewidth=2)

                ylabel = 'Normalized Read Count' if use_normalized else 'Raw Read Count'
                title = f'{ylabel} per Bin - {sample_name}'

                axes[idx].set_ylabel(ylabel, fontsize=10)
                axes[idx].set_title(title, fontsize=12)
                axes[idx].grid(True, alpha=0.3)
                axes[idx].set_ylim(0, 200)  # Giới hạn 0-200

                # Thêm tên chromosome dưới trục x
                if chr_ticks:
                    axes[idx].set_xticks(chr_ticks)
                    axes[idx].set_xticklabels(chr_labels, rotation=45, fontsize=8)

        plt.xlabel('Bin Position', fontsize=10)
        plt.tight_layout()

        plot_file = self.output_dir / f"{output_name}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Đã lưu biểu đồ vào: {plot_file}")
        return str(plot_file)

    def plot_gccount_per_bin(self, gc_file, output_name="gccount_per_bin"):
        """
        Vẽ biểu đồ GC percentage trên từng bin của reference genome

        Args:
            gc_file (str): Đường dẫn file NPZ chứa GC count
            output_name (str): Tên file output
        """
        print(f"Đang tạo biểu đồ GC percentage per bin...")

        if not Path(gc_file).exists():
            print(f"File GC không tồn tại: {gc_file}")
            return

        data = np.load(gc_file)

        # Tạo figure - chỉ 1 subplot cho GC percentage
        fig, ax = plt.subplots(1, 1, figsize=(20, 6))

        # Chuẩn bị dữ liệu cho plotting
        all_positions = []
        all_gc_percentages = []
        current_pos = 0
        chromosome_boundaries = []
        chr_ticks = []
        chr_labels = []

        for chrom in self.chromosome_list:
            if chrom in data.files:
                gc_counts = data[chrom]
                num_bins = len(gc_counts)
                bin_positions = np.arange(num_bins) + current_pos

                # Tính GC percentage
                gc_percentages = (gc_counts / self.bin_size) * 100

                all_positions.extend(bin_positions)
                all_gc_percentages.extend(gc_percentages)

                # Lưu boundary của chromosome
                if current_pos > 0:
                    chromosome_boundaries.append(current_pos)

                # Tick giữa chromosome để ghi tên
                chr_ticks.append(current_pos + num_bins // 2)
                chr_labels.append(f'chr{chrom}')

                current_pos += num_bins

        # Vẽ GC Percentage
        ax.scatter(all_positions, all_gc_percentages, alpha=0.6, s=8, color='purple')

        # Vẽ đường phân chia chromosome - ĐỎ ĐẬM
        for boundary in chromosome_boundaries:
            ax.axvline(x=boundary, color='red', linestyle='-', alpha=0.8, linewidth=2)

        ax.set_ylabel('GC Percentage (%)', fontsize=12)
        ax.set_ylim(0, 100)
        ax.set_title('GC Percentage per Bin', fontsize=14)
        ax.grid(True, alpha=0.3)

        # Thêm tên chromosome dưới trục x
        if chr_ticks:
            ax.set_xticks(chr_ticks)
            ax.set_xticklabels(chr_labels, rotation=45, fontsize=8)

        plt.tight_layout()

        plot_file = self.output_dir / f"{output_name}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Đã lưu biểu đồ vào: {plot_file}")
        return str(plot_file)

    def plot_readcount_vs_gc(self, case_dir, control_dir, gc_file, output_name="readcount_vs_gc"):
        """
        Vẽ biểu đồ readcount vs GC percentage cho từng mẫu riêng biệt (như hình S2 trong paper)

        Args:
            case_dir (str): Thư mục chứa file NPZ của các mẫu test
            control_dir (str): Thư mục chứa file NPZ của các mẫu control
            gc_file (str): Đường dẫn file NPZ chứa GC content
            output_name (str): Tên file output
        """
        print(f"Đang tạo biểu đồ readcount vs GC percentage...")

        if not Path(gc_file).exists():
            print(f"File GC không tồn tại: {gc_file}")
            return

        # Đọc GC data
        gc_data = np.load(gc_file)

        # Tìm tất cả file mẫu RAW READCOUNT (không có _normalized, _ratio)
        case_files = []
        control_files = []

        for file_path in glob.glob(f"{case_dir}/*.npz"):
            filename = Path(file_path).name
            if '_normalized' not in filename and '_ratio' not in filename and 'readcount' in filename:
                case_files.append(file_path)

        for file_path in glob.glob(f"{control_dir}/*.npz"):
            filename = Path(file_path).name
            if '_normalized' not in filename and '_ratio' not in filename and 'readcount' in filename:
                control_files.append(file_path)

        all_files = case_files + control_files
        if not all_files:
            print("Không tìm thấy file mẫu raw readcount nào")
            return

        # Debug: In ra số lượng file tìm được
        print(f"Tìm được {len(case_files)} case files và {len(control_files)} control files")

        # Tạo một biểu đồ riêng cho từng mẫu
        created_plots = 0
        for sample_file in all_files:
            sample_name = Path(sample_file).stem
            sample_data = np.load(sample_file)

            print(f"Đang xử lý: {sample_name}")

            # Tập hợp tất cả dữ liệu từ các chromosome
            all_gc_percentages = []
            all_read_counts = []

            for chrom in self.chromosome_list:
                if chrom in sample_data.files and chrom in gc_data.files:
                    read_counts = sample_data[chrom]
                    gc_counts = gc_data[chrom]

                    # Tính GC percentage
                    gc_percentages = (gc_counts / self.bin_size) * 100

                    # Lọc dữ liệu hợp lệ
                    valid_mask = (read_counts != -1) & (gc_counts > 0)
                    if np.any(valid_mask):
                        all_read_counts.extend(read_counts[valid_mask])
                        all_gc_percentages.extend(gc_percentages[valid_mask])

            print(f"Mẫu {sample_name}: {len(all_gc_percentages)} điểm dữ liệu")

            if all_gc_percentages and all_read_counts:
                # Tạo figure cho mẫu này
                fig, ax = plt.subplots(1, 1, figsize=(8, 6))

                # Chuyển thành array để dễ xử lý
                all_gc_percentages = np.array(all_gc_percentages)
                all_read_counts = np.array(all_read_counts)

                # Lọc GC từ 20-60% như yêu cầu và read count hợp lý
                mask_gc = (all_gc_percentages >= 20) & (all_gc_percentages <= 60)
                mask_count = all_read_counts <= 200
                mask_combined = mask_gc & mask_count
                filtered_gc = all_gc_percentages[mask_combined]
                filtered_counts = all_read_counts[mask_combined]

                print(f"Sau khi lọc GC 20-60% và read count <=200: {len(filtered_gc)} điểm")

                if len(filtered_gc) > 0:
                    # Vẽ scatter plot
                    ax.scatter(filtered_gc, filtered_counts,
                               alpha=0.5, s=1, color='blue')

                    ax.set_xlabel('GC Content (%)', fontsize=12)
                    ax.set_ylabel('Read Count', fontsize=12)
                    ax.set_title(f'{sample_name}', fontsize=14)
                    ax.grid(True, alpha=0.3)
                    ax.set_xlim(20, 60)  # GC range 20-60%
                    ax.set_ylim(0, 200)  # Read count 0-200

                    # Lưu biểu đồ riêng cho mỗi mẫu
                    individual_plot_file = self.output_dir / f"{sample_name}_readcount_vs_gc.png"
                    plt.tight_layout()
                    plt.savefig(individual_plot_file, dpi=300, bbox_inches='tight')
                    plt.close()

                    print(f"Đã lưu biểu đồ: {individual_plot_file}")
                    created_plots += 1
                else:
                    print(f"Không có dữ liệu GC <= 60% cho mẫu {sample_name}")
                    plt.close()
            else:
                print(f"Không có dữ liệu hợp lệ cho mẫu {sample_name}")

        print(f"Hoàn thành tạo {created_plots} biểu đồ readcount vs GC")
        return f"Đã tạo biểu đồ riêng cho {created_plots} mẫu"

    def create_additional_plots(self, pipeline_obj):
        """
        Tạo các biểu đồ bổ sung cho phân tích chi tiết

        Args:
            pipeline_obj: Object CNVPipeline để truy cập các thuộc tính

        Returns:
            list: Danh sách đường dẫn các file biểu đồ đã tạo
        """
        print("\n=== CREATING ADDITIONAL PLOTS ===")

        additional_plots = []

        # 1. Biểu đồ readcount per bin (raw)
        print("\n1. Tạo biểu đồ readcount per bin...")
        try:
            plot_file = self.plot_readcount_per_bin(
                str(pipeline_obj.temp_dir / 'case_npz'),
                "readcount_per_bin"
            )
            if plot_file:
                additional_plots.append(plot_file)
        except Exception as e:
            print(f"Lỗi khi tạo biểu đồ readcount per bin: {e}")

        # 2. Biểu đồ normalized readcount per bin
        print("\n2. Tạo biểu đồ normalized readcount per bin...")
        try:
            plot_file = self.plot_readcount_per_bin(
                str(pipeline_obj.temp_dir / 'case_npz'),
                "normalized_readcount_per_bin",
                use_normalized=True
            )
            if plot_file:
                additional_plots.append(plot_file)
        except Exception as e:
            print(f"Lỗi khi tạo biểu đồ normalized readcount per bin: {e}")

        # 3. Biểu đồ GC count per bin
        print("\n3. Tạo biểu đồ GC count per bin...")
        try:
            gc_file = str(pipeline_obj.temp_dir / f"gc_content_bin_size_{pipeline_obj.bin_size}.npz")
            plot_file = self.plot_gccount_per_bin(gc_file, "gccount_per_bin")
            if plot_file:
                additional_plots.append(plot_file)
        except Exception as e:
            print(f"Lỗi khi tạo biểu đồ GC count per bin: {e}")

        # 4. Biểu đồ readcount vs GC (như Figure S2)
        print("\n4. Tạo biểu đồ readcount vs GC percentage...")
        try:
            gc_file = str(pipeline_obj.temp_dir / f"gc_content_bin_size_{pipeline_obj.bin_size}.npz")
            plot_file = self.plot_readcount_vs_gc(
                str(pipeline_obj.temp_dir / 'case_npz'),
                str(pipeline_obj.temp_dir / 'control_npz'),
                gc_file,
                "readcount_vs_gc"
            )
            if plot_file:
                additional_plots.append(plot_file)
        except Exception as e:
            print(f"Lỗi khi tạo biểu đồ readcount vs GC: {e}")

        # 5. Tạo biểu đồ segments without normalization...
        print("\n5. Tạo biểu đồ segments without normalization...")
        try:
            # Import các module cần thiết
            import glob
            import shutil
            from normalize import calculate_raw_statistics, calculate_read_ratios
            from filter import filter
            from segment import cbs

            # Tìm file raw case và control
            case_raw_files = []
            for file_path in glob.glob(f"{pipeline_obj.temp_dir}/case_npz/*.npz"):
                filename = Path(file_path).name
                if '_normalized' not in filename and '_ratio' not in filename and 'readcount' in filename:
                    case_raw_files.append(file_path)

            control_raw_files = []
            for file_path in glob.glob(f"{pipeline_obj.temp_dir}/control_npz/*.npz"):
                filename = Path(file_path).name
                if '_normalized' not in filename and '_ratio' not in filename and 'readcount' in filename:
                    control_raw_files.append(file_path)

            if case_raw_files and control_raw_files:
                print(f"Tìm được {len(case_raw_files)} case raw files và {len(control_raw_files)} control raw files")

                # Bước 1: Chuyển đổi raw read count sang ratio cho tất cả files
                print("Chuyển đổi raw read count sang ratio...")
                control_ratio_files = []
                case_ratio_files = []

                # Chuyển đổi control files
                for control_file in control_raw_files:
                    ratio_file = calculate_read_ratios(pipeline_obj, control_file,
                                                       pipeline_obj.temp_dir / 'control_npz')
                    if ratio_file:
                        control_ratio_files.append(ratio_file)

                # Chuyển đổi case files
                for case_file in case_raw_files:
                    ratio_file = calculate_read_ratios(pipeline_obj, case_file, pipeline_obj.temp_dir / 'case_npz')
                    if ratio_file:
                        case_ratio_files.append(ratio_file)

                print(
                    f"Chuyển đổi được {len(control_ratio_files)} control ratio files và {len(case_ratio_files)} case ratio files")

                # Bước 2: Tính thống kê từ control ratio files
                print("Tính thống kê từ control ratio files...")

                # Tính mean và std từ control ratio files
                mean_raw_file, std_raw_file = calculate_raw_statistics(pipeline_obj, control_ratio_files)
                filtered_raw_mean_file = filter(mean_raw_file, std_raw_file, pipeline_obj=pipeline_obj)

                # Bước 3: Tính raw ratio và chạy CBS cho từng case
                for case_ratio_file in case_ratio_files:
                    sample_name = Path(case_ratio_file).stem
                    print(f"Xử lý mẫu ratio: {sample_name}")

                    # Tính raw ratio (sử dụng hàm ratio từ pipeline_obj)
                    raw_ratio_file = pipeline_obj.ratio(case_ratio_file, filtered_raw_mean_file)

                    if raw_ratio_file:
                        # Chạy CBS trên raw ratio
                        raw_segments_file = cbs(raw_ratio_file, pipeline_obj=pipeline_obj)

                        # Tạo biểu đồ với raw segments
                        plot_file = self.plot(raw_ratio_file, filtered_raw_mean_file, raw_segments_file,
                                              pipeline_obj=pipeline_obj)

                        if plot_file:
                            # Đổi tên để phân biệt với normalized plot
                            new_name = Path(plot_file).stem.replace('_cnv_plot',
                                                                    '_cnv_plot_without_normalization') + '.png'
                            new_plot_file = pipeline_obj.output_dir / new_name
                            shutil.move(plot_file, new_plot_file)
                            additional_plots.append(str(new_plot_file))
                            print(f"Đã tạo biểu đồ raw với segments: {new_plot_file}")
            else:
                print("Không tìm thấy đủ file raw case hoặc control")

        except Exception as e:
            print(f"Lỗi khi tạo biểu đồ segments without normalization: {e}")

        print(f"\n=== HOÀN THÀNH TẠO {len(additional_plots)} BIỂU ĐỒ BỔ SUNG ===")
        return additional_plots