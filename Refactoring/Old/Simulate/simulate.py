#!/usr/bin/env python3
import os
import sys
import random
import pysam
import json
from collections import defaultdict

# Usage: python simulate.py <original_bam_dir> <experiment_name.bed>
# Example: python simulate.py experiment_data/original_bam experiment1.bed
# Creates folder: <experiment_name> with simulated BAM files and metadata

def parse_bed_file(bed_path):
    """
    Parse BED file and return list of regions.
    Format: chrom, chromStart, chromEnd, name, type, mosaicism
    """
    regions = []
    with open(bed_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Skip header line
            if line.startswith('chrom'):
                continue
            # Split by any whitespace (tabs or spaces)
            parts = line.split()
            if len(parts) < 6:
                print(f"Warning: skipping malformed BED line: {line}", file=sys.stderr)
                continue
            
            chrom = parts[0]
            # Normalize chromosome: ensure it has 'chr' prefix
            if not chrom.startswith('chr'):
                chrom = f'chr{chrom}'
            
            chromStart = int(parts[1])
            chromEnd = int(parts[2])
            name = parts[3]
            region_type = parts[4].upper()  # G or L
            mosaicism = float(parts[5])
            
            regions.append({
                'chrom': chrom,
                'start': chromStart,
                'end': chromEnd,
                'name': name,
                'type': region_type,
                'mosaicism': mosaicism
            })

            print(f"Loaded region: {chrom}:{chromStart}-{chromEnd} "
                  f"name={name}, type={region_type}, mosaicism={mosaicism}")
    
    return regions


def normalize_chrom(chrom_name):
    """Normalize chromosome name to handle both 'chr1' and '1' formats."""
    if chrom_name is None:
        return None
    chrom_lower = chrom_name.lower()
    if chrom_lower.startswith('chr'):
        return chrom_lower
    else:
        return f'chr{chrom_lower}'


def read_overlaps_region(read, region_chrom, region_start, region_end, ref_name):
    """Check if a read overlaps with a region."""
    if read.is_unmapped:
        return False
    
    # Normalize reference name
    norm_ref = normalize_chrom(ref_name)
    norm_region = normalize_chrom(region_chrom)
    
    if norm_ref != norm_region:
        return False
    
    # Check overlap: read range is [read.reference_start, read.reference_end)
    # region range is [region_start, region_end)
    read_start = read.reference_start
    read_end = read.reference_end
    
    # Check if ranges overlap
    return not (read_end <= region_start or read_start >= region_end)


def calculate_expected_copy_numbers(regions):
    """
    Calculate expected copy number for each region.
    - Gain: 2 + m
    - Loss: 2 - m
    """
    for region in regions:
        m = region['mosaicism']
        if region['type'] == 'G':
            region['expected_cn'] = 2.0 + m
        elif region['type'] == 'L':
            region['expected_cn'] = 2.0 - m
        else:
            raise ValueError(f"Unknown type: {region['type']}")

        print(f"Region {region['name']} ({region['chrom']}:{region['start']}-{region['end']}): "
              f"type={region['type']}, m={m}, expected_cn={region['expected_cn']:.3f}") 
    
    return regions


def simulate_sample(bam_path, regions, denominator, out_path):
    """
    Simulate CNV for a single BAM file.
    Returns dict with statistics for each region.
    """
    stats = {}
    
    # Initialize stats for each region
    for region in regions:
        stats[region['name']] = {
            'original_read': 0,
            'keep_read': 0
        }
    
    # Stats for regions not in BED (name = '0')
    stats['0'] = {
        'original_read': 0,
        'keep_read': 0
    }
    
    with pysam.AlignmentFile(bam_path, "rb") as fin:
        with pysam.AlignmentFile(out_path, "wb", header=fin.header) as fout:
            for read in fin.fetch(until_eof=True):
                # Handle unmapped reads
                if read.is_unmapped:
                    fout.write(read)
                    stats['0']['original_read'] += 1
                    stats['0']['keep_read'] += 1
                    continue
                
                ref_name = fin.get_reference_name(read.reference_id)
                
                # Check which region this read belongs to
                found_region = None
                for region in regions:
                    if read_overlaps_region(read, region['chrom'], region['start'], 
                                           region['end'], ref_name):
                        found_region = region
                        break
                
                if found_region:
                    # Read is in a BED region
                    region_name = found_region['name']
                    stats[region_name]['original_read'] += 1
                    
                    # Calculate keep probability
                    keep_probability = found_region['expected_cn'] / denominator
                    
                    # Randomly decide to keep or discard
                    if random.random() < keep_probability:
                        fout.write(read)
                        stats[region_name]['keep_read'] += 1
                else:
                    # Read is not in any BED region (normal region)
                    stats['0']['original_read'] += 1
                    
                    # Normal regions have expected_cn = 2
                    keep_probability = 2.0 / denominator
                    
                    if random.random() < keep_probability:
                        fout.write(read)
                        stats['0']['keep_read'] += 1
    
    # Index the output BAM file
    pysam.index(out_path)
    
    return stats


def main():
    if len(sys.argv) < 3:
        print("Usage: python simulate.py <original_bam_dir> <experiment_name.bed>", file=sys.stderr)
        print("Example: python simulate.py experiment_data/original_bam experiment1.bed", file=sys.stderr)
        sys.exit(1)
    
    bam_dir = sys.argv[1]
    bed_file = sys.argv[2]
    
    # Extract experiment name from BED file
    experiment_name = os.path.splitext(os.path.basename(bed_file))[0]
    
    # Create output directory
    out_dir = os.path.join(os.getcwd(), experiment_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # Parse BED file
    print(f"Parsing BED file: {bed_file}")
    regions = parse_bed_file(bed_file)
    print(f"Found {len(regions)} regions")
    
    # Calculate expected copy numbers
    regions = calculate_expected_copy_numbers(regions)
    
    # Calculate denominator (max expected copy number, but should be at least 2)
    expected_cns = [region['expected_cn'] for region in regions]
    expected_cns.append(2.0)  # Include normal regions
    denominator = max(expected_cns)
    print(f"Denominator: {denominator}")
    
    # Calculate keep probabilities for each region
    for region in regions:
        region['keep_probability'] = region['expected_cn'] / denominator
        print(f"Region {region['name']} ({region['chrom']}:{region['start']}-{region['end']}): "
              f"type={region['type']}, m={region['mosaicism']}, "
              f"expected_cn={region['expected_cn']:.3f}, "
              f"keep_prob={region['keep_probability']:.3f}")
    
    # Get list of BAM files
    bam_files = [f for f in os.listdir(bam_dir) if f.endswith('.bam')]
    bam_files.sort()
    print(f"Found {len(bam_files)} BAM files")
    
    # Process each BAM file
    all_stats = {}
    for i, bam_file in enumerate(bam_files, 1):
        print(f"\nProcessing [{i}/{len(bam_files)}]: {bam_file}")
        
        in_path = os.path.join(bam_dir, bam_file)
        out_path = os.path.join(out_dir, bam_file)
        
        # Simulate
        sample_stats = simulate_sample(in_path, regions, denominator, out_path)
        all_stats[bam_file] = sample_stats
        
        # Print summary for this sample
        print(f"  Sample {bam_file}:")
        for region_name in sorted(sample_stats.keys()):
            orig = sample_stats[region_name]['original_read']
            kept = sample_stats[region_name]['keep_read']
            ratio = (kept / orig * 100) if orig > 0 else 0
            print(f"    Region {region_name}: {kept}/{orig} reads kept ({ratio:.1f}%)")
    
    # Save metadata
    metadata = {
        'denominator': denominator,
        'samples': all_stats
    }
    
    metadata_path = os.path.join(out_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Simulation complete!")
    print(f"  Output directory: {out_dir}")
    print(f"  Metadata file: {metadata_path}")
    print(f"  Processed {len(bam_files)} BAM files")


if __name__ == "__main__":
    main()
