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
from pathlib import Path
import pysam
import subprocess
import warnings
import pickle
import shutil
from plot import CNVPlotter
from filter import filter_bins, filter
from segment import cbs, prepare_cbs_data
from normalize import (gccount, lowess_normalize, readcount, 
                      normalize_readcount, calculate_read_ratios, 
                      statistics, calculate_raw_statistics)
warnings.filterwarnings('ignore')

class CNVPipeline:
    """
    Lớp chính để thực hiện pipeline phát hiện CNV
    """
    
    def __init__(self, control_dir, case_dir, output_dir, temp_dir, binsize=200000, threshold=5, reference_fasta=None):
        """
        Khởi tạo pipeline CNV
        
        Args:
            control_dir (str): Đường dẫn thư mục chứa các file BAM của mẫu control
            case_dir (str): Đường dẫn thư mục chứa các file BAM của mẫu case
            output_dir (str): Đường dẫn thư mục đầu ra cho các file ảnh
            temp_dir (str): Đường dẫn thư mục tạm thời
            binsize (int): Kích thước bin tính bằng base pair (mặc định: 200KB)
            threshold (float): Ngưỡng độ lệch chuẩn để lọc bin (mặc định: 5)
            reference_fasta (str): Đường dẫn file FASTA reference cho GC normalization (BẮT BUỘC)
        """
        self.control_dir = Path(control_dir)
        self.case_dir = Path(case_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.binsize = binsize
        self.threshold = threshold
        self.reference_fasta = reference_fasta
        
        # Kiểm tra file reference FASTA bắt buộc
        if not self.reference_fasta or not Path(self.reference_fasta).exists():
            raise ValueError(f"File reference FASTA là bắt buộc và phải tồn tại: {self.reference_fasta}")
        
        # Tạo các thư mục cần thiết
        self._create_directories()
        
        # Danh sách chromosome cần phân tích
        self.chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']
        
        # Tính GC content ngay khi khởi tạo
        print("Tính toán GC content cho reference genome...")
        self.gc_data = gccount(self, self.reference_fasta)
        if not self.gc_data:
            raise ValueError("Không thể tính toán GC content từ file reference")
        
        # Khởi tạo plotter
        self.plotter = CNVPlotter(self.chromosomes, self.binsize, self.output_dir)
    
    def _create_directories(self):
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
        
        # Tạo tên file output
        case_name = Path(case_npz).stem.replace('_readcount', '')
        ratio_file = self.temp_dir / 'ratio_npz' / f"{case_name}_ratio.npz"
        
        # Đọc dữ liệu case và mean
        case_data = np.load(case_npz)
        mean_data = np.load(mean_filter_npz)
        
        # Dictionary để lưu log2 ratio
        ratio_dict = {}
        
        for chrom in self.chromosomes:
            if chrom in case_data.files and chrom in mean_data.files:
                case_counts = case_data[chrom]  # Bây giờ là counts, không phải ratios
                mean_counts = mean_data[chrom]  # Bây giờ là counts, không phải ratios
                
                # Tính log2 ratio
                log2_ratios = np.full_like(case_counts, -2.0)  # Giá trị mặc định
                
                # Chỉ tính ratio cho các bin có mean > 0 (bin ổn định)
                valid_bins = mean_counts > 0
                
                # Tránh chia cho 0
                valid_case = case_counts > 0
                valid_mask = valid_bins & valid_case
                
                if np.any(valid_mask):
                    # Chuyển từ counts sang ratio (copy number) trước khi tính log2
                    log2_ratios[valid_mask] = np.log2(case_counts[valid_mask] / mean_counts[valid_mask])
                
                ratio_dict[chrom] = log2_ratios
                
                print(f"  Chromosome {chrom}: {np.sum(valid_bins)} bin ổn định")
            else:
                print(f"Cảnh báo: Không có dữ liệu cho chromosome {chrom}")
                ratio_dict[chrom] = np.array([])
        
        # Lưu kết quả
        np.savez_compressed(ratio_file, **ratio_dict)
        print(f"Đã lưu log2 ratio vào: {ratio_file}")
        
        return str(ratio_file)
    
    def run_pipeline(self):
        """
        Chạy toàn bộ pipeline CNV
        """
        print("=== BẮT ĐẦU PIPELINE PHÁT HIỆN CNV ===")
        
        # Bước 1: Đếm read cho các mẫu control
        print("\n1. Đếm read cho các mẫu control...")
        control_bam_files = list(self.control_dir.glob("*.bam"))
        if not control_bam_files:
            raise ValueError(f"Không tìm thấy file BAM nào trong thư mục {self.control_dir}")
        
        control_raw_files = []
        for bam_file in control_bam_files:
            raw_file = readcount(self, str(bam_file), self.temp_dir / 'control_npz')
            if raw_file:
                control_raw_files.append(raw_file)
        
        # Bước 2: Chuẩn hóa các mẫu control
        print("\n2. Chuẩn hóa các mẫu control...")
        control_normalized_files = []
        for raw_file in control_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.temp_dir / 'control_npz')
            if normalized_file:
                control_normalized_files.append(normalized_file)
        
        # Bước 3: Đếm read cho các mẫu case
        print("\n3. Đếm read cho các mẫu case...")
        case_bam_files = list(self.case_dir.glob("*.bam"))
        if not case_bam_files:
            raise ValueError(f"Không tìm thấy file BAM nào trong thư mục {self.case_dir}")
        
        case_raw_files = []
        for bam_file in case_bam_files:
            raw_file = readcount(self, str(bam_file), self.temp_dir / 'case_npz')
            if raw_file:
                case_raw_files.append(raw_file)
        
        # Bước 4: Chuẩn hóa các mẫu case
        print("\n4. Chuẩn hóa các mẫu case...")
        case_normalized_files = []
        for raw_file in case_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.temp_dir / 'case_npz')
            if normalized_file:
                case_normalized_files.append(normalized_file)
        
        # Bước 5: Tính thống kê từ mẫu control đã chuẩn hóa
        print("\n5. Tính thống kê từ mẫu control đã chuẩn hóa...")
        mean_file, std_file = statistics(self, self.temp_dir / 'control_npz')
        
        # Bước 6: Lọc bin không ổn định
        print("\n6. Lọc bin không ổn định...")
        filtered_mean_file = filter(mean_file, std_file, pipeline_obj=self)
        
        # Bước 7: Tính ratio cho từng mẫu case
        print("\n7. Tính ratio cho các mẫu case...")
        ratio_files = []
        for case_npz in case_normalized_files:
            ratio_file = self.ratio(str(case_npz), filtered_mean_file)
            if ratio_file:
                ratio_files.append(ratio_file)
        
        # Bước 8: Thực hiện CBS segmentation
        print("\n8. Thực hiện CBS segmentation...")
        segments_files = []
        for ratio_file in ratio_files:
            segments_file = cbs(ratio_file, pipeline_obj=self)
            if segments_file:
                segments_files.append(segments_file)
            else:
                segments_files.append(None)
        
        # Bước 9: Tạo biểu đồ với segments
        print("\n9. Tạo biểu đồ với segments...")
        plot_files = []
        for i, ratio_file in enumerate(ratio_files):
            segments_file = segments_files[i] if i < len(segments_files) else None
            plot_file = self.plotter.plot(ratio_file, filtered_mean_file, segments_file, pipeline_obj=self)
            if plot_file:
                plot_files.append(plot_file)
        
        print(f"\n=== HOÀN THÀNH PIPELINE ===")
        print(f"Đã tạo {len(plot_files)} biểu đồ CNV trong thư mục: {self.output_dir}")
        
        return plot_files


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline phát hiện Copy Number Variation (CNV)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Chạy pipeline với GC content normalization (BẮT BUỘC)
  python baseline.py -c control/ -t case/ -o output/ -r reference.fasta
  
  # Chạy với tham số tùy chỉnh
  python baseline.py -c control/ -t case/ -o output/ -r reference.fasta --binsize 100000 --threshold 3
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
    
    parser.add_argument(
        '-r', '--reference',
        type=str,
        required=True,
        help='Đường dẫn file FASTA reference cho GC content normalization (BẮT BUỘC)'
    )
    
    parser.add_argument(
        '--additional-plots',
        action='store_true',
        help='Tạo các biểu đồ bổ sung chi tiết (readcount per bin, GC analysis, etc.)'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra thư mục đầu vào
    if not os.path.exists(args.control_dir):
        print(f"Lỗi: Thư mục control không tồn tại: {args.control_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.case_dir):
        print(f"Lỗi: Thư mục case không tồn tại: {args.case_dir}")
        sys.exit(1)
    
    if not os.path.exists(args.reference):
        print(f"Lỗi: File reference FASTA không tồn tại: {args.reference}")
        sys.exit(1)
    
    # Tạo pipeline và chạy
    try:
        pipeline = CNVPipeline(
            control_dir=args.control_dir,
            case_dir=args.case_dir,
            output_dir=args.output_dir,
            temp_dir=args.temp_dir,
            binsize=args.binsize,
            threshold=args.threshold,
            reference_fasta=args.reference
        )
        
        plot_files = pipeline.run_pipeline()
        
        # Tạo biểu đồ bổ sung nếu được yêu cầu
        additional_plots = []
        if args.additional_plots:
            additional_plots = pipeline.plotter.create_additional_plots(pipeline)
        
        print(f"\nKết quả:")
        print(f"- Số biểu đồ CNV chính: {len(plot_files)}")
        if additional_plots:
            print(f"- Số biểu đồ bổ sung: {len(additional_plots)}")
        print(f"- Thư mục chứa kết quả: {args.output_dir}")
        
    except Exception as e:
        print(f"Lỗi khi chạy pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 