#!/usr/bin/env python3
import os
import sys
import random
import pysam
import glob
import shutil
from collections import defaultdict


def parse_bed_file(bed_path):
    """
    Parse BED file và trả về dict là danh sách regions.
    """
    regions = []
    with open(bed_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('chrom'):
                continue
            
            parts = line.split()
            if len(parts) < 6:
                print(f"Cảnh báo: bỏ qua dòng BED không đúng định dạng: {line}", file=sys.stderr)
                continue
            
            chrom = parts[0]            
            chromStart = int(parts[1])
            chromEnd = int(parts[2])
            region_id = int(parts[3])  # Region ID: 1, 2, ..., k
            region_type = parts[4].upper()  # G or L
            mosaic = float(parts[5])
            
            regions.append({
                'chrom': chrom,
                'start': chromStart,
                'end': chromEnd,
                'region': region_id,
                'type': region_type,
                'mosaic': mosaic
            })

    return regions
    
def standardize_chromosomes(chrom_name):
    """Chuẩn hóa chromosome: X -> 23, Y -> 24, loại bỏ 'chr' prefix, trả về string."""
    if chrom_name is None:
        return None
    chrom_str = str(chrom_name).replace('chr', '')
    replacements = {'X': '23', 'Y': '24'}
    chrom_str = replacements.get(chrom_str, chrom_str)
    return chrom_str


def read_overlaps_region(read, regions, ref_name):
    """Xác định region của read, trả về region_id (0 nếu không thuộc region nào)."""
    if read.is_unmapped:
        return 0
    
    for region in regions:
        norm_ref = standardize_chromosomes(ref_name)
        norm_region = standardize_chromosomes(region['chrom'])
        if norm_ref != norm_region:
            continue
        
        if read.reference_start < region['end'] and read.reference_end > region['start']:
            return region['region']
    
    return 0  # Không thuộc region nào


def calculate_expected_copy_number(regions):
    """
    Tính expected copy number cho tất cả k+1 vùng (0, 1, 2, ..., k).
    """
    expected_copy_number = {0: 2.0}  # Region 0 (normal) luôn có CN = 2.0
    
    for region in regions:
        region_id = region['region']
        
        if region['type'] == 'G':
            copy_number = 2.0 + region['mosaic']
        elif region['type'] == 'L':
            copy_number = 2.0 - region['mosaic']
        else:
            copy_number = 2.0
        
        expected_copy_number[region_id] = copy_number
        region['expected_cn'] = copy_number
    
    return expected_copy_number


def simulate_sample(bam_path, regions, keep_probs, exp_name):
    """
    Mô phỏng CNV cho một BAM file.
    """
    # Khởi tạo stats cho tất cả regions
    stats = defaultdict(lambda: {'original': 0, 'kept': 0})
    
    # Tạo đường dẫn output
    bam_filename = os.path.basename(bam_path)
    out_dir = f'Output/{exp_name}'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, bam_filename)
    
    # Mở BAM input và output
    with pysam.AlignmentFile(bam_path, "rb") as fin:
        with pysam.AlignmentFile(out_path, "wb", header=fin.header) as fout:
            for read in fin.fetch(until_eof=True):
                if read.is_unmapped:
                    region_id = 0
                else:
                    ref_name = fin.get_reference_name(read.reference_id)
                    region_id = read_overlaps_region(read, regions, ref_name)
                
                stats[region_id]['original'] += 1                
                if random.random() < keep_probs[region_id]:
                    fout.write(read)
                    stats[region_id]['kept'] += 1
    
    # Tạo index cho BAM output
    pysam.index(out_path)
    
    return dict(stats)


def calculate_scale_ratios(all_stats):
    """
    Tính scale_ratio cho tất cả samples.
    """
    scale_ratios = {}
    
    for sample_name, regions_data in all_stats.items():
        sample_ratios = {}

        region_0_data = regions_data.get(0, {'original': 0, 'kept': 0})
        for region_id, data in regions_data.items():
            if region_id == 0:
                continue  # Bỏ qua region 0
            
            if data['original'] == 0 or region_0_data['kept'] == 0:
                scale_ratio = 0.0
            else:
                scale_ratio = (data['kept'] * region_0_data['original']) / (data['original'] * region_0_data['kept'])   
            
            sample_ratios[region_id] = scale_ratio
        
        scale_ratios[sample_name] = sample_ratios
    
    return scale_ratios


def export_tsv(experiment_name, scale_ratios):
    """
    Xuất scale_ratio ra file TSV.
    """
    output_path = f'Output/Metadata/{experiment_name}.tsv'
    
    # Lấy tất cả region IDs và sắp xếp
    all_region_ids = set()
    for sample_ratios in scale_ratios.values():
        all_region_ids.update(sample_ratios.keys())
    
    region_ids = sorted(all_region_ids)
    
    # Ghi file TSV
    with open(output_path, 'w') as f:
        header = ['sample'] + [str(rid) for rid in region_ids]
        f.write('\t'.join(header) + '\n')
        
        for sample_name in sorted(scale_ratios.keys()):
            ratios = scale_ratios[sample_name]
            row = [sample_name]
            
            for rid in region_ids:
                ratio_value = ratios.get(rid, 0.0)
                row.append(f'{ratio_value:.6f}')
            
            f.write('\t'.join(row) + '\n')


def process_experiment(experiment_name, bed_path):
    """
    Xử lý một experiment.
    """
    # 1. Parse BED file
    regions = parse_bed_file(bed_path)    
    if len(regions) == 0:
        print(f"  Cảnh báo: Không tìm thấy regions trong {bed_path}, bỏ qua...")
        return
    
    # 2. Tính keep_probability cho k+1 vùng
    expected_copy_number = calculate_expected_copy_number(regions)
    denominator = max(expected_copy_number.values())
    keep_probs = {}
    for region_id, copy_number in sorted(expected_copy_number.items()):
        keep_probs[region_id] = copy_number / denominator
    
    # 3. Lấy danh sách BAM files
    bam_files = glob.glob('Input/Original/*.bam')
    bam_files.sort()
    if len(bam_files) == 0:
        print(f"  Lỗi: Không tìm thấy file BAM nào trong Input/Original/")
        return
    
    # 4. Xử lý từng BAM file
    all_stats = {}
    
    for i, bam_path in enumerate(bam_files, 1):
        bam_filename = os.path.basename(bam_path)
        sample_name = bam_filename.replace('.bam', '')
        if '_' in sample_name:
            sample_name = sample_name.split('_')[0]
        print(f"\n   Đang xử lý mẫu [{i}/{len(bam_files)}]: {bam_filename}")
        
        sample_stats = simulate_sample(bam_path, regions, keep_probs, experiment_name)
        all_stats[sample_name] = sample_stats
    
    # 5. Xuất metadata
    scale_ratios = calculate_scale_ratios(all_stats)
    export_tsv(experiment_name, scale_ratios)
    output_path = f'Output/Metadata/{experiment_name}.bed'
    shutil.copy2(bed_path, output_path)
    

def main():    
    # Đảm bảo cấu trúc thư mục tồn tại
    os.makedirs('Output/Metadata', exist_ok=True)
    
    # Lấy tất cả file BED
    bed_files = glob.glob('Input/Metadata/*.bed')
    if len(bed_files) == 0:
        sys.exit(1)
    
    # Xử lý từng experiment
    for i, bed_file in enumerate(bed_files, 1):
        experiment_name = os.path.splitext(os.path.basename(bed_file))[0]
        print(f"Đang xử lý experiment [{i}/{len(bed_files)}]: {experiment_name}")
        
        try:
            process_experiment(experiment_name, bed_file)
        except Exception as e:
            print(f"\nLỗi xử lý experiment '{experiment_name}': {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\nHoàn tất!")


if __name__ == "__main__":
    main()