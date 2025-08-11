#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline phát hiện Copy Number Variation (CNV) từ dữ liệu sequencing
Sử dụng phương pháp baseline dựa trên tỷ lệ read count trong các bin

Mô tả:
Script này thực hiện phân tích CNV bằng cách:
1. Đếm số read trong các bin 200 KB trên từng chromosome
2. Tính toán thống kê từ các mẫu control bình thường
3. Lọc các bin không ổn định
4. Tính tỷ lệ log2 giữa mẫu case và control
5. Tạo biểu đồ visualization kết quả

Đầu vào:
- Thư mục chứa các file BAM của mẫu control bình thường
- Thư mục chứa các file BAM của mẫu cần kiểm tra

Đầu ra:
- Các file ảnh PNG chứa biểu đồ CNV cho từng mẫu case
"""

import os
import sys
import glob
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pysam
import warnings
warnings.filterwarnings('ignore')

# Thiết lập font cho matplotlib để hiển thị tiếng Việt
plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

class CNVPipeline:
    """
    Lớp chính để thực hiện pipeline phát hiện CNV
    """
    
    def __init__(self, control_dir, case_dir, output_dir, temp_dir, binsize=200000, threshold=5):
        """
        Khởi tạo pipeline CNV
        
        Args:
            control_dir (str): Đường dẫn thư mục chứa các file BAM của mẫu control
            case_dir (str): Đường dẫn thư mục chứa các file BAM của mẫu case
            output_dir (str): Đường dẫn thư mục đầu ra cho các file ảnh
            temp_dir (str): Đường dẫn thư mục tạm thời
            binsize (int): Kích thước bin tính bằng base pair (mặc định: 1MB)
            threshold (float): Ngưỡng độ lệch chuẩn để lọc bin (mặc định: 0.05)
        """
        self.control_dir = Path(control_dir)
        self.case_dir = Path(case_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.binsize = binsize
        self.threshold = threshold
        
        # Tạo các thư mục cần thiết
        self._create_directories()
        
        # Danh sách chromosome cần phân tích
        self.chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']
    
    def _create_directories(self):
        """
        Tạo các thư mục cần thiết cho pipeline
        """
        directories = [
            self.output_dir,
            self.temp_dir,
            self.temp_dir / 'control_npz',
            self.temp_dir / 'case_npz',
            self.temp_dir / 'ratio_npz'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Đã tạo thư mục: {directory}")
    
    def readcount(self, bam_file):
        """
        Đếm số read trong các bin trên từng chromosome
        
        Args:
            bam_file (str): Đường dẫn file BAM
            
        Returns:
            str: Đường dẫn file NPZ chứa kết quả đếm read
        """
        print(f"Đang xử lý file: {bam_file}")
        
        # Tạo tên file output dựa trên tên file BAM
        bam_name = Path(bam_file).stem
        output_file = self.temp_dir / f"{bam_name}_readcount.npz"
        
        # Dictionary để lưu kết quả đếm read cho từng chromosome
        chromosome_data = {}
        
        try:
            # Mở file BAM
            bam = pysam.AlignmentFile(bam_file, "rb")
            
            # Lấy danh sách chromosome thực tế từ file BAM
            bam_chromosomes = list(bam.references)
            
            # Tính tổng số read của toàn bộ file BAM bằng cách đếm thực tế
            total_bam_reads = 0
            for chrom in self.chromosomes:
                # Tìm chromosome trong BAM
                bam_chrom_name = None
                possible_names = [chrom, f"chr{chrom}"]
                
                for name in possible_names:
                    if name in bam_chromosomes:
                        bam_chrom_name = name
                        break
                
                if bam_chrom_name is None:
                    continue
                
                # Lấy index của chromosome trong BAM để tính length
                try:
                    chr_index = bam_chromosomes.index(bam_chrom_name)
                    chr_length = bam.lengths[chr_index]
                except (ValueError, IndexError):
                    continue
                
                # Đếm tổng read trên chromosome này
                try:
                    count = bam.count(contig=bam_chrom_name)
                    total_bam_reads += count
                except Exception as e:
                    print(f"Lỗi khi đếm read cho chromosome {chrom}: {e}")
            
            print(f"Tổng số read đã đếm: {total_bam_reads}")
            
            # Xử lý từng chromosome
            for chrom in self.chromosomes:
                # Tìm chromosome trong BAM
                bam_chrom_name = None
                possible_names = [chrom, f"chr{chrom}"]
                
                for name in possible_names:
                    if name in bam_chromosomes:
                        bam_chrom_name = name
                        break
                
                if bam_chrom_name is None:
                    print(f"Cảnh báo: Không tìm thấy chromosome {chrom} trong file BAM")
                    chromosome_data[chrom] = np.array([])
                    continue
                
                # Lấy index của chromosome trong BAM để tính length
                try:
                    chr_index = bam_chromosomes.index(bam_chrom_name)
                    chr_length = bam.lengths[chr_index]
                except (ValueError, IndexError):
                    print(f"Lỗi: Không thể lấy thông tin cho chromosome {chrom} ({bam_chrom_name})")
                    chromosome_data[chrom] = np.array([])
                    continue
                
                # Sử dụng length thực tế từ BAM thay vì hardcode
                chrom_size = chr_length
                
                # Tính số bin cho chromosome này
                num_bins = int(np.ceil(chrom_size / self.binsize))
                
                # Khởi tạo mảng đếm read cho từng bin
                read_counts = np.zeros(num_bins)
                
                # Đếm read trong từng bin (đơn giản)
                for bin_idx in range(num_bins):
                    start_pos = bin_idx * self.binsize
                    end_pos = min((bin_idx + 1) * self.binsize, chrom_size)
                    
                    # Đếm read trong khoảng này
                    try:
                        # Sử dụng pysam để đếm read trong region
                        count = bam.count(contig=bam_chrom_name, start=start_pos, end=end_pos)
                        read_counts[bin_idx] = count
                    except Exception as e:
                        print(f"Lỗi khi đếm read cho chromosome {chrom} ({bam_chrom_name}), bin {bin_idx}: {e}")
                        read_counts[bin_idx] = 0
                
                # Tính tỷ lệ read cho từng bin (dựa trên tổng read của toàn bộ file BAM)
                if total_bam_reads > 0:
                    read_ratios = read_counts / total_bam_reads
                else:
                    read_ratios = np.zeros_like(read_counts)
                
                # Lưu vào dictionary
                chromosome_data[chrom] = read_ratios
                
                print(f"  Chromosome {chrom} ({bam_chrom_name}): {num_bins} bins, {np.sum(read_counts)} reads")
            
            bam.close()
            
            # Lưu kết quả vào file NPZ
            np.savez_compressed(output_file, **chromosome_data)
            print(f"Đã lưu kết quả vào: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            print(f"Lỗi khi xử lý file {bam_file}: {e}")
            return None
    
    def statistics(self, control_npz_dir):
        """
        Tính toán thống kê từ các mẫu control
        
        Args:
            control_npz_dir (str): Đường dẫn thư mục chứa các file NPZ của mẫu control
            
        Returns:
            tuple: (mean_npz_path, std_npz_path) - đường dẫn 2 file NPZ chứa mean và std
        """
        print("Đang tính toán thống kê từ các mẫu control...")
        
        # Tìm tất cả file NPZ trong thư mục control
        npz_files = list(Path(control_npz_dir).glob("*.npz"))
        
        if not npz_files:
            raise ValueError(f"Không tìm thấy file NPZ nào trong thư mục {control_npz_dir}")
        
        print(f"Tìm thấy {len(npz_files)} file NPZ")
        
        # Dictionary để lưu dữ liệu từ tất cả mẫu control
        all_data = {}
        
        # Đọc dữ liệu từ tất cả file NPZ
        for npz_file in npz_files:
            try:
                data = np.load(npz_file)
                for chrom in self.chromosomes:
                    if chrom in data.files:
                        if chrom not in all_data:
                            all_data[chrom] = []
                        all_data[chrom].append(data[chrom])
            except Exception as e:
                print(f"Lỗi khi đọc file {npz_file}: {e}")
        
        # Tính mean và std cho từng chromosome
        mean_dict = {}
        std_dict = {}
        
        for chrom in self.chromosomes:
            if chrom in all_data and all_data[chrom]:
                # Kiểm tra kích thước của các array để đảm bảo chúng có cùng length
                lengths = [len(arr) for arr in all_data[chrom]]
                if len(set(lengths)) > 1:
                    print(f"Cảnh báo: Chromosome {chrom} có các array với kích thước khác nhau: {lengths}")
                    # Tìm kích thước tối thiểu
                    min_length = min(lengths)
                    print(f"  Cắt tất cả array về kích thước tối thiểu: {min_length}")
                    # Cắt tất cả array về cùng kích thước
                    all_data[chrom] = [arr[:min_length] for arr in all_data[chrom]]
                
                try:
                    # Chuyển list thành array 2D
                    chrom_data = np.array(all_data[chrom])
                    
                    # Tính mean và std cho từng bin
                    mean_dict[chrom] = np.mean(chrom_data, axis=0)
                    std_dict[chrom] = np.std(chrom_data, axis=0)
                    
                    print(f"  Chromosome {chrom}: {chrom_data.shape[1]} bins, {chrom_data.shape[0]} mẫu")
                except Exception as e:
                    print(f"Lỗi khi xử lý chromosome {chrom}: {e}")
                    mean_dict[chrom] = np.array([])
                    std_dict[chrom] = np.array([])
            else:
                print(f"Cảnh báo: Không có dữ liệu cho chromosome {chrom}")
                mean_dict[chrom] = np.array([])
                std_dict[chrom] = np.array([])
        
        # Lưu kết quả vào file NPZ
        mean_file = self.temp_dir / "mean_statistics.npz"
        std_file = self.temp_dir / "std_statistics.npz"
        
        np.savez_compressed(mean_file, **mean_dict)
        np.savez_compressed(std_file, **std_dict)
        
        print(f"Đã lưu thống kê mean vào: {mean_file}")
        print(f"Đã lưu thống kê std vào: {std_file}")
        
        return str(mean_file), str(std_file)
    
    def filter(self, mean_npz, std_npz, threshold=None):
        """
        Lọc các bin không ổn định dựa trên độ lệch chuẩn
        
        Args:
            mean_npz (str): Đường dẫn file NPZ chứa mean
            std_npz (str): Đường dẫn file NPZ chứa standard deviation
            threshold (float): Ngưỡng độ lệch chuẩn (mặc định: self.threshold)
            
        Returns:
            str: Đường dẫn file NPZ đã lọc
        """
        if threshold is None:
            threshold = self.threshold
            
        print(f"Đang lọc bin với ngưỡng độ lệch chuẩn: {threshold}")
        
        # Đọc dữ liệu mean và std
        mean_data = np.load(mean_npz)
        std_data = np.load(std_npz)
        
        # Tạo bản sao của mean_dict để lọc
        filtered_mean = {}
        
        for chrom in self.chromosomes:
            if chrom in mean_data.files and chrom in std_data.files:
                mean_values = mean_data[chrom].copy()
                std_values = std_data[chrom]
                
                # Lọc các bin có độ lệch chuẩn lớn hơn ngưỡng
                unstable_bins = std_values > threshold
                mean_values[unstable_bins] = -1
                
                filtered_mean[chrom] = mean_values
                
                num_unstable = np.sum(unstable_bins)
                total_bins = len(mean_values)
                print(f"  Chromosome {chrom}: {num_unstable}/{total_bins} bin không ổn định")
            else:
                print(f"Cảnh báo: Không có dữ liệu cho chromosome {chrom}")
                filtered_mean[chrom] = np.array([])
        
        # Lưu kết quả đã lọc
        filtered_file = self.temp_dir / "mean_filtered.npz"
        np.savez_compressed(filtered_file, **filtered_mean)
        
        print(f"Đã lưu mean đã lọc vào: {filtered_file}")
        return str(filtered_file)
    
    def ratio(self, case_npz, mean_filter_npz):
        """
        Tính log2 ratio giữa mẫu case và control
        
        Args:
            case_npz (str): Đường dẫn file NPZ của mẫu case
            mean_filter_npz (str): Đường dẫn file NPZ chứa mean đã lọc
            
        Returns:
            str: Đường dẫn file NPZ chứa log2 ratio
        """
        print(f"Đang tính log2 ratio cho: {case_npz}")
        
        # Đọc dữ liệu case và mean
        case_data = np.load(case_npz)
        mean_data = np.load(mean_filter_npz)
        
        # Tạo tên file output
        case_name = Path(case_npz).stem.replace('_readcount', '')
        ratio_file = self.temp_dir / 'ratio_npz' / f"{case_name}_ratio.npz"
        
        # Dictionary để lưu log2 ratio
        ratio_dict = {}
        
        for chrom in self.chromosomes:
            if chrom in case_data.files and chrom in mean_data.files:
                case_ratios = case_data[chrom]
                mean_ratios = mean_data[chrom]
                
                # Tính log2 ratio
                log2_ratios = np.full_like(case_ratios, -2.0)  # Giá trị mặc định
                
                # Chỉ tính ratio cho các bin có mean > 0 (bin ổn định)
                valid_bins = mean_ratios > 0
                
                # Tránh chia cho 0
                valid_case = case_ratios > 0
                valid_mask = valid_bins & valid_case
                
                if np.any(valid_mask):
                    log2_ratios[valid_mask] = np.log2(case_ratios[valid_mask] / mean_ratios[valid_mask])
                
                ratio_dict[chrom] = log2_ratios
                
                print(f"  Chromosome {chrom}: {np.sum(valid_bins)} bin ổn định")
            else:
                print(f"Cảnh báo: Không có dữ liệu cho chromosome {chrom}")
                ratio_dict[chrom] = np.array([])
        
        # Lưu kết quả
        np.savez_compressed(ratio_file, **ratio_dict)
        print(f"Đã lưu log2 ratio vào: {ratio_file}")
        
        return str(ratio_file)
    
    def plot(self, ratio_npz, mean_filter_npz):
        """
        Tạo biểu đồ CNV từ dữ liệu log2 ratio
        
        Args:
            ratio_npz (str): Đường dẫn file NPZ chứa log2 ratio
            mean_filter_npz (str): Đường dẫn file NPZ chứa mean đã lọc
            
        Returns:
            str: Đường dẫn file PNG chứa biểu đồ
        """
        print(f"Đang tạo biểu đồ cho: {ratio_npz}")
        
        # Đọc dữ liệu
        ratio_data = np.load(ratio_npz)
        mean_data = np.load(mean_filter_npz)
        
        # Tạo tên file output
        ratio_name = Path(ratio_npz).stem.replace('_ratio', '')
        plot_file = self.output_dir / f"{ratio_name}_cnv_plot.png"
        
        # Tạo figure với 2 subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
        
        # Chuẩn bị dữ liệu cho plotting
        all_positions = []
        all_ratios = []
        all_colors = []
        all_chroms = []
        
        # Đường giới hạn cho các trạng thái ploidy
        constitutional_3n = np.log2(3/2)  # ≈ 0.58
        constitutional_2n = 0.0
        constitutional_1n = np.log2(1/2)  # ≈ -1.0
        
        current_pos = 0
        
        for chrom in self.chromosomes:
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
                    
                    # Phân loại màu sắc
                    colors = []
                    for ratio in valid_ratios:
                        if ratio > 0.2:  # Gain
                            colors.append('#696969')  # Dark grey
                            # colors.append('#00CED1')  # Teal
                        elif ratio < -0.2:  # Loss
                            colors.append('#696969')  # Dark grey
                            # colors.append('#FFD700')  # Gold
                        else:  # Normal
                            colors.append('#696969')  # Dark grey
                    
                    all_positions.extend(valid_positions)
                    all_ratios.extend(valid_ratios)
                    all_colors.extend(colors)
                    all_chroms.extend([chrom] * len(valid_positions))
                
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
            # Vẽ scatter plot (subplot 1)
            ax1.scatter(all_positions, all_ratios, c=all_colors, alpha=0.6, s=20)
            
            # Vẽ đường giới hạn
            ax1.axhline(y=constitutional_3n, color='lightgreen', linestyle='--', alpha=0.7, label='Constitutional 3n')
            ax1.axhline(y=constitutional_2n, color='black', linestyle='--', alpha=0.7, label='Constitutional 2n')
            ax1.axhline(y=constitutional_1n, color='lightgoldenrodyellow', linestyle='--', alpha=0.7, label='Constitutional 1n')
        
        ax1.set_ylabel('log2(ratio)')
        ax1.set_title(f'Copy Number Variation Analysis - {ratio_name}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Vẽ box plot (subplot 2) - chỉ khi có dữ liệu hợp lệ
        if len(all_positions) > 0:
            box_data = []
            box_labels = []
            
            for chrom in self.chromosomes:
                if chrom in ratio_data.files and chrom in mean_data.files:
                    ratios = ratio_data[chrom]
                    means = mean_data[chrom]
                    
                    # Chỉ lấy các giá trị hợp lệ
                    valid_mask = ratios != -2
                    if np.any(valid_mask):
                        valid_ratios = ratios[valid_mask]
                        box_data.append(valid_ratios)
                        box_labels.append(f'chr{chrom}')
            
            if box_data:
                bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True)
                
                # Tô màu cho box plot
                for patch in bp['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
            
            # Vẽ đường giới hạn cho box plot
            ax2.axhline(y=constitutional_3n, color='lightgreen', linestyle='--', alpha=0.7)
            ax2.axhline(y=constitutional_2n, color='black', linestyle='--', alpha=0.7)
            ax2.axhline(y=constitutional_1n, color='lightgoldenrodyellow', linestyle='--', alpha=0.7)
        
        ax2.set_ylabel('log2(ratio)')
        ax2.set_xlabel('Chromosome')
        ax2.grid(True, alpha=0.3)
        
        # Xoay label cho box plot
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Đã lưu biểu đồ vào: {plot_file}")
        return str(plot_file)
    
    def run_pipeline(self):
        """
        Chạy toàn bộ pipeline CNV
        """
        print("=== BẮT ĐẦU PIPELINE PHÁT HIỆN CNV ===")
        
        # Bước 1: Xử lý các mẫu control
        print("\n1. Xử lý các mẫu control...")
        control_bam_files = list(self.control_dir.glob("*.bam"))
        if not control_bam_files:
            raise ValueError(f"Không tìm thấy file BAM nào trong thư mục {self.control_dir}")
        
        for bam_file in control_bam_files:
            npz_file = self.readcount(str(bam_file))
            if npz_file:
                # Di chuyển file NPZ vào thư mục control_npz
                target_file = self.temp_dir / 'control_npz' / Path(npz_file).name
                Path(npz_file).rename(target_file)
        
        # Bước 2: Xử lý các mẫu case
        print("\n2. Xử lý các mẫu case...")
        case_bam_files = list(self.case_dir.glob("*.bam"))
        if not case_bam_files:
            raise ValueError(f"Không tìm thấy file BAM nào trong thư mục {self.case_dir}")
        
        case_npz_files = []
        for bam_file in case_bam_files:
            npz_file = self.readcount(str(bam_file))
            if npz_file:
                # Di chuyển file NPZ vào thư mục case_npz
                target_file = self.temp_dir / 'case_npz' / Path(npz_file).name
                Path(npz_file).rename(target_file)
                case_npz_files.append(target_file)
        
        # Bước 3: Tính thống kê từ mẫu control
        print("\n3. Tính thống kê từ mẫu control...")
        mean_file, std_file = self.statistics(self.temp_dir / 'control_npz')
        
        # Bước 4: Lọc bin không ổn định
        print("\n4. Lọc bin không ổn định...")
        filtered_mean_file = self.filter(mean_file, std_file)
        
        # Bước 5: Tính ratio cho từng mẫu case
        print("\n5. Tính ratio cho các mẫu case...")
        ratio_files = []
        for case_npz in case_npz_files:
            ratio_file = self.ratio(str(case_npz), filtered_mean_file)
            if ratio_file:
                ratio_files.append(ratio_file)
        
        # Bước 6: Tạo biểu đồ
        print("\n6. Tạo biểu đồ...")
        plot_files = []
        for ratio_file in ratio_files:
            plot_file = self.plot(ratio_file, filtered_mean_file)
            if plot_file:
                plot_files.append(plot_file)
        
        print(f"\n=== HOÀN THÀNH PIPELINE ===")
        print(f"Đã tạo {len(plot_files)} biểu đồ CNV trong thư mục: {self.output_dir}")
        
        return plot_files


def main():
    """
    Hàm chính để chạy pipeline
    """
    parser = argparse.ArgumentParser(
        description="Pipeline phát hiện Copy Number Variation (CNV)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  python baseline.py -c /path/to/control/bams -t /path/to/case/bams -o /path/to/output

Tác giả: [Tên tác giả]
Phiên bản: 1.0
        """
    )
    
    parser.add_argument(
        '-c', '--control-dir',
        required=True,
        help='Đường dẫn thư mục chứa các file BAM của mẫu control bình thường'
    )
    
    parser.add_argument(
        '-t', '--case-dir',
        required=True,
        help='Đường dẫn thư mục chứa các file BAM của mẫu cần kiểm tra'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='./output',
        help='Đường dẫn thư mục đầu ra cho các file ảnh (mặc định: ./output)'
    )
    
    parser.add_argument(
        '--temp-dir',
        default='./temp',
        help='Đường dẫn thư mục tạm thời (mặc định: ./temp)'
    )
    
    parser.add_argument(
        '--binsize',
        type=int,
        default=200000,
        help='Kích thước bin tính bằng base pair (mặc định: 200000 = 200 KB)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=5,
        help='Ngưỡng độ lệch chuẩn để lọc bin (mặc định: 5)'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra thư mục đầu vào
    if not os.path.exists(args.control_dir):
        print(f"Lỗi: Thư mục control không tồn tại: {args.control_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.case_dir):
        print(f"Lỗi: Thư mục case không tồn tại: {args.case_dir}")
        sys.exit(1)
    
    # Tạo pipeline và chạy
    try:
        pipeline = CNVPipeline(
            control_dir=args.control_dir,
            case_dir=args.case_dir,
            output_dir=args.output_dir,
            temp_dir=args.temp_dir,
            binsize=args.binsize,
            threshold=args.threshold
        )
        
        plot_files = pipeline.run_pipeline()
        
        print(f"\nKết quả:")
        print(f"- Số biểu đồ đã tạo: {len(plot_files)}")
        print(f"- Thư mục chứa kết quả: {args.output_dir}")
        
    except Exception as e:
        print(f"Lỗi khi chạy pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 