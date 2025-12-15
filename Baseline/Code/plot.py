import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import shutil
import argparse

plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

class Plotter:
    def __init__(self, chromosome_list, bin_size, output_dir):
        self.chromosome_list = chromosome_list
        self.bin_size = bin_size
        self.output_dir = Path(output_dir)

    def _prepare_ratio_data(self, ratio_data):
        """Chuẩn bị dữ liệu ratio: positions, copy numbers, colors, chrom mapping"""
        all_positions = []
        all_copy_numbers = []
        all_colors = []
        chromosome_boundaries = []
        chromosome_centers = []
        chromosome_labels = []
        chrom_bin_mapping = {}
        current_pos = 0

        for chrom in self.chromosome_list:
            if chrom in ratio_data.files:
                ratios = ratio_data[chrom]
                num_bins = len(ratios)
                bin_positions = np.arange(num_bins) + current_pos
                
                chrom_bin_mapping[chrom] = {
                    'start_bin': current_pos,
                    'end_bin': current_pos + num_bins - 1,
                    'num_bins': num_bins
                }

                valid_mask = ratios > -10
                if np.any(valid_mask):
                    valid_positions = bin_positions[valid_mask]
                    valid_ratios = ratios[valid_mask]
                    valid_copy_numbers = np.power(2.0, valid_ratios + 1.0)

                    all_positions.extend(valid_positions)
                    all_copy_numbers.extend(valid_copy_numbers)
                    all_colors.extend(['#888888'] * len(valid_positions))

                if current_pos > 0:
                    chromosome_boundaries.append(current_pos)

                chromosome_centers.append(current_pos + num_bins / 2.0)
                chromosome_labels.append(chrom)
                current_pos += num_bins

        return {
            'positions': np.array(all_positions),
            'copy_numbers': np.array(all_copy_numbers),
            'colors': np.array(all_colors),
            'chrom_bin_mapping': chrom_bin_mapping,
            'boundaries': chromosome_boundaries,
            'centers': chromosome_centers,
            'labels': chromosome_labels,
            'max_pos': current_pos
        }

    def _calculate_segment_info(self, segment, chrom_bin_mapping, gender='female'):
        """Tính toán thông tin vị trí và màu sắc cho một segment"""
        chrom = str(segment['chrom_original']) if 'chrom_original' in segment.index else str(segment['chrom'])
        if chrom not in chrom_bin_mapping:
            return None
        chrom_info = chrom_bin_mapping[chrom]
        
        start_maploc = segment['loc.start'] if 'loc.start' in segment.index else 0
        end_maploc = segment['loc.end'] if 'loc.end' in segment.index else self.bin_size
        start_bin_idx, end_bin_idx = int(start_maploc // self.bin_size), int(end_maploc // self.bin_size)
        plot_start = chrom_info['start_bin'] + max(start_bin_idx, 0)
        plot_end = chrom_info['start_bin'] + min(end_bin_idx, chrom_info['num_bins'] - 1)
        seg_value = float(np.power(2.0, segment['seg.mean'] + 1.0))
        
        # Thresholds: male X/Y uses 0.55-1.45, others use 1.55-2.45
        high_thresh, low_thresh = (1.45, 0.55) if (gender == 'male' and chrom in ['X', 'Y']) else (2.45, 1.55)
        
        if seg_value > high_thresh:
            point_color, line_color, linewidth, alpha = "#F97E7E", '#FF0000', 4, 0.9
        elif seg_value < low_thresh:
            point_color, line_color, linewidth, alpha = "#65C3E3", '#0000FF', 4, 0.9
        else:
            point_color, line_color, linewidth, alpha = '#888888', '#000000', 3, 0.7
        
        return {
            'plot_start': plot_start, 'plot_end': plot_end, 'seg_value': seg_value,
            'point_color': point_color, 'line_color': line_color, 'linewidth': linewidth, 'alpha': alpha
        }

    def _prepare_segment_data(self, segments_df, chrom_bin_mapping, gender='female'):
        """Chuẩn bị dữ liệu segment: parse và tính toán vị trí, màu sắc"""
        if segments_df is None:
            return []
        
        segment_infos = []
        for _, segment in segments_df.iterrows():
            info = self._calculate_segment_info(segment, chrom_bin_mapping, gender)
            if info:
                segment_infos.append(info)
        
        return segment_infos

    def _plot_ratio_points(self, ax, ratio_data_dict, segment_infos):
        """Vẽ các điểm ratio với màu được áp dụng từ segments"""
        positions = ratio_data_dict['positions']
        copy_numbers = ratio_data_dict['copy_numbers']
        colors = ratio_data_dict['colors'].copy()
        
        # Áp dụng màu segment cho các điểm
        segment_bin_colors = {}
        for info in segment_infos:
            for bin_pos in range(int(info['plot_start']), int(info['plot_end']) + 1):
                segment_bin_colors[bin_pos] = info['point_color']
        
        for i, pos in enumerate(positions):
            if int(pos) in segment_bin_colors:
                colors[i] = segment_bin_colors[int(pos)]
        
        ax.scatter(positions, copy_numbers, c=colors, alpha=0.7, s=15, edgecolors='none')

    def _plot_segment_lines(self, ax, segment_infos):
        """Vẽ đường segments"""
        for info in segment_infos:
            ax.plot([info['plot_start'], info['plot_end']], 
                   [info['seg_value'], info['seg_value']],
                   color=info['line_color'], 
                   linewidth=info['linewidth'], 
                   alpha=info['alpha'], 
                   solid_capstyle='round')

    def plot(self, log2_ratio_file, segments_csv=None):
        """
        Tạo biểu đồ CNV từ dữ liệu log2 ratio với segments
        """
        ratio_data = np.load(log2_ratio_file)
        segments_df = pd.read_csv(segments_csv) if segments_csv else None
        ratio_name = Path(log2_ratio_file).stem.replace('_log2Ratio', '')
        
        # Detect gender from proportion.npz in Temporary/Test
        gender = 'female'  # default
        proportion_file = self.output_dir.parent / 'Temporary' / 'Test' / f"{ratio_name}_proportion.npz"
        if proportion_file.exists():
            try:
                prop_data = np.load(proportion_file, allow_pickle=True)
                if 'gender' in prop_data.files:
                    gender = str(prop_data['gender'])
                    print(f"Detected gender: {gender} for {ratio_name}")
            except Exception as e:
                print(f"Warning: Could not read gender from {proportion_file}: {e}")
        
        plot_file = self.output_dir / f"{ratio_name}_scatterChart.png"

        fig, ax1 = plt.subplots(1, 1, figsize=(20, 10))

        ratio_data_dict = self._prepare_ratio_data(ratio_data)
        segment_infos = self._prepare_segment_data(segments_df, ratio_data_dict['chrom_bin_mapping'], gender)

        if len(ratio_data_dict['positions']) == 0:
            print("Cảnh báo: Không có dữ liệu hợp lệ để vẽ biểu đồ!")
            ax1.text(0.5, 0.5, 'Không có dữ liệu hợp lệ', transform=ax1.transAxes, ha='center', va='center', fontsize=14)
        else:
            self._plot_ratio_points(ax1, ratio_data_dict, segment_infos)

            ax1.axhline(y=3.0, color='lightcoral', linestyle='--', alpha=0.8, linewidth=1.5)
            ax1.axhline(y=1.0, color='lightblue', linestyle='--', alpha=0.8, linewidth=1.5)
            ax1.axhline(y=2.0, color='darkgray', linestyle='-', alpha=0.8, linewidth=1.5)

            for boundary in ratio_data_dict['boundaries']:
                ax1.axvline(x=boundary, color='darkgray', linestyle='-', alpha=0.5, linewidth=0.8)

            self._plot_segment_lines(ax1, segment_infos)

        # Định dạng trục
        ax1.set_title(f'{ratio_name}', fontsize=14, fontweight='bold')
        ax1.grid(True, axis='y', alpha=0.3)
        ax1.xaxis.grid(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        ax1.tick_params(axis='x', which='both', length=0)
        ax1.set_ylim(0, 4)
        ax1.set_yticks(np.arange(0, 4.1, 0.2))

        if len(ratio_data_dict['centers']) > 0:
            ax1.set_xlim(0, ratio_data_dict['max_pos'])
            ax1.set_xticks(ratio_data_dict['centers'])
            ax1.set_xticklabels(ratio_data_dict['labels'], fontsize=10)

        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Đã lưu biểu đồ vào: {plot_file}")
        return str(plot_file)