import numpy as np
from pathlib import Path
from statsmodels.nonparametric.smoothers_lowess import lowess
import pysam

def base_content(pipeline_obj, fasta_file):
    """Compute per-bin GC and N contents using pysam and cache them to NPZ files.
    Returns two file paths: (GC-content.npz, N-content.npz).
    """
    gc_file = pipeline_obj.work_directory / "Prepare" / "GC-content.npz"
    n_file = pipeline_obj.work_directory / "Prepare" / "N-content.npz"

    if gc_file.exists() and n_file.exists():
        print(f"GC and N content files already exist: {gc_file}, {n_file}")
        return str(gc_file), str(n_file)

    fasta_path = Path(fasta_file)
    fasta = pysam.FastaFile(str(fasta_path))

    gc_counts = {}
    n_counts = {}

    for chromosome in pipeline_obj.chromosome_list:
        chrom_len = min(pipeline_obj.chromosome_lengths[chromosome], fasta.get_reference_length(chromosome))
        num_bins = chrom_len // pipeline_obj.bin_size

        # Fetch full chromosome sequence once, uppercase for stable counting
        seqU = fasta.fetch(chromosome, 0, chrom_len).upper()
        valid_len = num_bins * pipeline_obj.bin_size
        buf = memoryview(seqU.encode('ascii'))[:valid_len]
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(num_bins, pipeline_obj.bin_size)

        # Vectorized counting
        is_G = (arr == ord('G'))
        is_C = (arr == ord('C'))
        is_N = (arr == ord('N'))
        gc_counts[chromosome] = (is_G | is_C).sum(axis=1, dtype=np.int64).astype(np.int32)
        n_counts[chromosome] = is_N.sum(axis=1, dtype=np.int64).astype(np.int32)

    # Compute GC content and N ratio per bin
    gc_content = {}
    n_content = {}
    for chromosome in pipeline_obj.chromosome_list:
        counts_gc = gc_counts[chromosome]
        counts_n = n_counts[chromosome]

        n_content[chromosome] = counts_n.astype(float) / pipeline_obj.bin_size
        total_bases = pipeline_obj.bin_size - counts_n
        gc_frac = np.zeros_like(counts_gc, dtype=float)
        np.divide(counts_gc.astype(float), total_bases, out=gc_frac, where=total_bases > 0)
        gc_content[chromosome] = gc_frac
    
    # Save contents (fractions/ratios) to caches
    np.savez_compressed(gc_file, **gc_content)
    np.savez_compressed(n_file, **n_content)

    return str(gc_file), str(n_file)

def lowess_normalize(raw_data, gc_data, base_filter, min_rd=0.0001, frac=0.1):
    """
    Chuẩn hoá read count theo GC bằng LOWESS.
    """
    chromosome_list = list(raw_data.keys())
    length_list = [len(raw_data[chromosome]) for chromosome in chromosome_list]

    # Nối toàn bộ thành mảng 1D lớn để tạo một mask toàn cục rõ ràng
    all_reads = np.concatenate([raw_data[chromosome] for chromosome in chromosome_list])
    all_gc = np.concatenate([gc_data[chromosome] for chromosome in chromosome_list])
    all_base = np.concatenate([base_filter[chromosome] for chromosome in chromosome_list])

    # 2) Tạo mask hợp lệ toàn cục theo đúng quy tắc
    valid = (all_reads > min_rd) & (~all_base)
    corrected_full = np.zeros_like(all_reads, dtype=all_reads.dtype)

    # 3) Tính LOWESS trên các bin hợp lệ theo thứ tự đã gom (giữ nguyên thứ tự)
    try:
        smoothed = lowess(all_reads[valid], all_gc[valid], frac=frac, return_sorted=False)
    except Exception as e:
        print(f"Lỗi khi sử dụng statsmodels LOWESS: {e}")
        return raw_data.copy()

    # 4) Gán expected cho đúng vị trí hợp lệ (scatter)
    expected_full = np.zeros_like(all_reads, dtype=float)
    expected_full[valid] = smoothed
    corrected_valid = np.where(expected_full[valid] > 0, all_reads[valid] / expected_full[valid], all_reads[valid])
    corrected_full[valid] = corrected_valid.astype(corrected_full.dtype, copy=False)

    # 5) Chia lại theo từng chromosome (bin không hợp lệ đã là 0)
    corrected_data = {}
    start = 0
    for chromosome, length in zip(chromosome_list, length_list):
        sl = corrected_full[start:start+length]
        corrected_data[chromosome] = sl.astype(raw_data[chromosome].dtype, copy=False)
        start += length

    return corrected_data

def normalize_readcount(gc_file, raw_file, output_dir, filter_file):

    raw_name = Path(raw_file).stem
    normalized_file = output_dir / f"{raw_name.replace('_rawCount', '_normalized')}.npz"

    if normalized_file.exists():
        print(f"Normalized file already exists: {normalized_file}")
        return str(normalized_file)

    raw_data = np.load(raw_file)
    gc_data = np.load(gc_file)
    base_filter = np.load(filter_file)
    chromosome_data = lowess_normalize(raw_data, gc_data, base_filter)

    np.savez_compressed(normalized_file, **chromosome_data)

    return str(normalized_file)