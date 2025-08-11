import numpy as np
import warnings
import pysam
from pathlib import Path

# Import thư viện cho GC normalization
try:
    from scipy.interpolate import interp1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from statsmodels.nonparametric.smoothers_lowess import lowess
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

def readcount(pipeline_obj, bam_file, output_dir):
    """
    Đếm số read trong các bin trên từng chromosome (chỉ raw counts)
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        bam_file (str): Đường dẫn file BAM
        output_dir (Path): Thư mục đầu ra để lưu file NPZ
        
    Returns:
        str: Đường dẫn file NPZ chứa raw read counts
    """
    print(f"Đang xử lý file: {bam_file}")
    
    # Tạo tên file output dựa trên tên file BAM
    bam_name = Path(bam_file).stem
    output_file = output_dir / f"{bam_name}_readcount.npz"
    
    # Kiểm tra xem file NPZ đã tồn tại hay chưa
    if output_file.exists():
        print(f"File NPZ đã tồn tại: {output_file}")
        print("Bỏ qua việc xử lý lại file BAM")
        return str(output_file)
    
    # Dictionary để lưu kết quả đếm read cho từng chromosome
    chromosome_data = {}
    
    try:
        # Mở file BAM
        bam = pysam.AlignmentFile(bam_file, "rb")
        
        # Lấy danh sách chromosome thực tế từ file BAM
        bam_chromosomes = list(bam.references)
        
        # Tính tổng số read của toàn bộ file BAM bằng cách đếm thực tế
        total_bam_reads = 0
        for chrom in pipeline_obj.chromosomes:
            # BAM file sử dụng định dạng chr1, chr2, ..., chrX, chrY
            bam_chrom_name = f"chr{chrom}"
            
            if bam_chrom_name not in bam_chromosomes:
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
        for chrom in pipeline_obj.chromosomes:
            # BAM file sử dụng định dạng chr1, chr2, ..., chrX, chrY
            bam_chrom_name = f"chr{chrom}"
            
            if bam_chrom_name not in bam_chromosomes:
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
            num_bins = int(np.ceil(chrom_size / pipeline_obj.binsize))
            
            # Khởi tạo mảng đếm read cho từng bin
            read_counts = np.zeros(num_bins)
            
            # Đếm read trong từng bin (đơn giản)
            for bin_idx in range(num_bins):
                start_pos = bin_idx * pipeline_obj.binsize
                end_pos = min((bin_idx + 1) * pipeline_obj.binsize, chrom_size)
                
                # Đếm read trong khoảng này
                try:
                    # Sử dụng pysam để đếm read trong region
                    count = bam.count(contig=bam_chrom_name, start=start_pos, end=end_pos)
                    read_counts[bin_idx] = count
                except Exception as e:
                    print(f"Lỗi khi đếm read cho chromosome {chrom} ({bam_chrom_name}), bin {bin_idx}: {e}")
                    read_counts[bin_idx] = 0
            
            # Lưu raw read counts vào dictionary (chưa normalize)
            chromosome_data[chrom] = read_counts
            
            print(f"  Chromosome {chrom} ({bam_chrom_name}): {num_bins} bins, {np.sum(read_counts)} reads")
        
        bam.close()
        
        # Lưu raw read counts vào file NPZ
        np.savez_compressed(output_file, **chromosome_data)
        print(f"Đã lưu raw read counts vào: {output_file}")
        
        return str(output_file)
        
    except Exception as e:
        print(f"Lỗi khi xử lý file {bam_file}: {e}")
        return None

def gccount(pipeline_obj, fasta_file):
    """
    Tính toán GC count cho từng bin trong file reference FASTA
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        fasta_file (str): Đường dẫn file FASTA reference
        
    Returns:
        dict: Dictionary chứa GC count và N count cho từng chromosome
    """
    print(f"Đang tính GC content từ file: {fasta_file}")
    
    # Kiểm tra file cache
    gc_cache_file = pipeline_obj.temp_dir / f"gc_content_binsize_{pipeline_obj.binsize}.npz"
    if gc_cache_file.exists():
        print(f"File GC content đã tồn tại: {gc_cache_file}")
        print("Bỏ qua việc tính toán lại GC content")
        data = np.load(gc_cache_file)
        return {key: data[key] for key in data.files}
    
    # Initialize dictionaries for GC and N counts
    gc_counts = {}
    n_counts = {}
    
    for chrom in pipeline_obj.chromosomes:
        gc_counts[chrom] = []
        n_counts[chrom] = []
    
    current_chrom = None
    current_pos = 0
    gc_count = 0
    n_count = 0
    bin_total_count = 0  # Count for current bin only
    
    def finish_bin(bin_number):
        nonlocal gc_count, n_count, bin_total_count, current_chrom
        if current_chrom and current_chrom in gc_counts:
            # Extend arrays if necessary
            while len(gc_counts[current_chrom]) <= bin_number:
                gc_counts[current_chrom].append(0)
                n_counts[current_chrom].append(0)
            
            # Store GC count for this bin (not percentage)
            gc_counts[current_chrom][bin_number] = gc_count
            n_counts[current_chrom][bin_number] = n_count
            
            # Calculate and print GC percentage for logging (based on actual bin content)
            gc_percentage = (gc_count / bin_total_count * 100) if bin_total_count > 0 else 0
            print(f"\tChr: {current_chrom}\tBin: {bin_number}\t-\tGC: {gc_count}\tGC%: {gc_percentage:.2f}\tN: {n_count}\tBin_size: {bin_total_count}")
        
        # Reset for next bin
        gc_count = 0
        n_count = 0
        bin_total_count = 0
    
    try:
        with open(fasta_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    # Finish previous bin if exists
                    if current_chrom and bin_total_count > 0:
                        current_bin = current_pos // pipeline_obj.binsize
                        finish_bin(current_bin)
                    
                    # Parse chromosome name
                    current_pos = 0
                    header_parts = line.split()
                    chrom_name = header_parts[0][1:]  # Remove '>'
                    
                    # Normalize chromosome name
                    if chrom_name.startswith('chr'):
                        chrom_name = chrom_name[3:]
                    
                    current_chrom = chrom_name if chrom_name in pipeline_obj.chromosomes else None
                    
                    if current_chrom:
                        print(f"\nWorking on chromosome: {current_chrom}")
                
                elif current_chrom and current_chrom in gc_counts:
                    # Process sequence data
                    for char in line:
                        # Check for GC (both uppercase and lowercase)
                        if char in 'GCgc':
                            gc_count += 1
                        elif char.upper() == 'N':
                            n_count += 1
                        
                        bin_total_count += 1
                        current_pos += 1
                        
                        # Check if bin is complete
                        if current_pos % pipeline_obj.binsize == 0:
                            current_bin = (current_pos - 1) // pipeline_obj.binsize
                            finish_bin(current_bin)
            
            # Finish last bin if incomplete
            if current_chrom and bin_total_count > 0:
                current_bin = current_pos // pipeline_obj.binsize
                finish_bin(current_bin)
    
    except Exception as e:
        print(f"Lỗi khi đọc file FASTA: {e}")
        return None
    
    # Combine GC and N counts into single dictionary
    result = {}
    for chrom in pipeline_obj.chromosomes:
        if chrom in gc_counts:
            result[chrom] = np.array(gc_counts[chrom])
            result[f'N{chrom}'] = np.array(n_counts[chrom])
    
    # Save to cache
    np.savez_compressed(gc_cache_file, **result)
    print(f"Đã lưu GC content vào cache: {gc_cache_file}")
    
    return result

def lowess_normalize(pipeline_obj, sample_data, gc_data, max_n=0.1, min_rd=0.0001, frac=0.1):
    """
    Chuẩn hóa read count theo GC content sử dụng LOWESS regression
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        sample_data (dict): Dictionary chứa read count data cho từng chromosome
        gc_data (dict): Dictionary chứa GC content data
        max_n (float): Tỷ lệ tối đa bases N trong bin (mặc định: 0.1)
        min_rd (float): Read depth tối thiểu tương đối (mặc định: 0.0001)
        frac (float): Fraction of data used in LOWESS (mặc định: 0.1)
        
    Returns:
        dict: Dictionary chứa read count đã được chuẩn hóa
    """
    print("Đang thực hiện LOWESS normalization cho GC content...")
    
    # Collect all valid data points for LOWESS fitting
    all_gc = []
    all_reads = []
    
    for chrom in sample_data.keys():
        if chrom in gc_data and f'N{chrom}' in gc_data:
            sample_counts = sample_data[chrom]
            gc_counts = gc_data[chrom]  # Now contains GC counts, not percentages
            n_content = gc_data[f'N{chrom}']
            
            min_len = min(len(sample_counts), len(gc_counts), len(n_content))
            
            for i in range(min_len):
                # Tính tỷ lệ bases N trong bin (N ratio)
                n_ratio = n_content[i] / pipeline_obj.binsize if pipeline_obj.binsize > 0 else 0
                read_count = sample_counts[i]
                
                # Tính GC content từ GC count
                total_bases = pipeline_obj.binsize - n_content[i]  # Tổng số bases hợp lệ (loại trừ N)
                gc_content = gc_counts[i] / total_bases if total_bases > 0 else 0  # GC content = GC count / total valid bases
                
                # Áp dụng các tiêu chí lọc để chọn bin hợp lệ
                if (n_ratio < max_n and                              # Tỷ lệ N < ngưỡng tối đa
                    read_count > min_rd and                          # Read count > ngưỡng tối thiểu
                    gc_content > 0 and                               # GC content > 0
                    total_bases > pipeline_obj.binsize * 0.5):      # Ít nhất 50% bases hợp lệ trong bin
                    # Thêm điểm dữ liệu hợp lệ vào danh sách để fit LOWESS
                    all_gc.append(gc_content)       # Thêm GC content
                    all_reads.append(sample_counts[i])  # Thêm read count tương ứng
    
    # Kiểm tra xem có đủ điểm dữ liệu để thực hiện LOWESS không
    if len(all_gc) < 10:
        print("Cảnh báo: Không đủ điểm dữ liệu để thực hiện LOWESS normalization")
        return sample_data.copy()  # Trả về dữ liệu gốc nếu không đủ điểm
    
    # Chuyển đổi list thành numpy arrays để xử lý
    all_gc = np.array(all_gc)      # Array chứa GC content
    all_reads = np.array(all_reads)  # Array chứa read count
    
    print(f"Sử dụng {len(all_gc)} điểm dữ liệu cho LOWESS fitting")
    
    # Sử dụng statsmodels LOWESS nếu có, nếu không sẽ fallback về phương pháp đơn giản
    if HAS_STATSMODELS:
        try:
            # statsmodels lowess với return_sorted=False để giữ nguyên thứ tự
            # Trả về mảng smoothed values có cùng thứ tự với input
            smoothed_reads = lowess(all_reads, all_gc, frac=frac, return_sorted=False)
            print("Sử dụng statsmodels LOWESS với return_sorted=False")
        except Exception as e:
            print(f"Lỗi khi sử dụng statsmodels LOWESS: {e}")
            print("Không thể thực hiện LOWESS normalization")
            return sample_data.copy()  # Trả về dữ liệu gốc nếu lỗi
    else:
        print("Cảnh báo: statsmodels không có sẵn, không thể thực hiện LOWESS normalization")
        return sample_data.copy()  # Trả về dữ liệu gốc nếu không có statsmodels
    
    # Áp dụng correction cho sample data sử dụng smoothed values
    corrected_sample = {}
    
    # Index để theo dõi vị trí trong mảng all_gc và smoothed_reads
    global_index = 0
    
    # Duyệt qua tất cả chromosome để áp dụng normalization
    for chrom in sample_data.keys():
        # Kiểm tra xem chromosome này có dữ liệu GC và N content không
        if chrom in gc_data and f'N{chrom}' in gc_data:
            # Lấy dữ liệu cho chromosome hiện tại
            sample_counts = sample_data[chrom]              # Read count data
            gc_counts = gc_data[chrom]                      # GC count data (không phải phần trăm)
            n_content = gc_data[f'N{chrom}']               # N content data
            
            # Tìm độ dài tối thiểu để đảm bảo index không vượt quá
            min_len = min(len(sample_counts), len(gc_counts), len(n_content))
            # Khởi tạo array để lưu kết quả đã correction
            corrected_counts = np.zeros(len(sample_counts))
            
            # Duyệt qua từng bin để áp dụng correction
            for i in range(min_len):
                # Tính tỷ lệ N trong bin
                n_ratio = n_content[i] / pipeline_obj.binsize if pipeline_obj.binsize > 0 else 0
                # Lấy read count trong bin này
                read_count = sample_counts[i]
                
                # Tính GC content từ GC count
                total_bases = pipeline_obj.binsize - n_content[i]  # Tổng số bases hợp lệ (loại trừ N)
                gc_content = gc_counts[i] / total_bases if total_bases > 0 else 0  # GC content
                
                # Kiểm tra bin có hợp lệ để áp dụng correction không
                if (n_ratio < max_n and                              # Tỷ lệ N < ngưỡng tối đa
                    read_count > min_rd and                          # Read count > ngưỡng tối thiểu  
                    gc_content > 0 and                               # GC content > 0
                    total_bases > pipeline_obj.binsize * 0.5):      # Ít nhất 50% bases hợp lệ
                    
                    # Lấy giá trị expected từ smoothed values tại vị trí global_index
                    try:
                        # Kiểm tra xem global_index có hợp lệ không
                        if global_index < len(smoothed_reads):
                            expected_value = float(smoothed_reads[global_index])
                            
                            if expected_value > 0:
                                # Chuẩn hóa: observed / expected (loại bỏ bias do GC)
                                corrected_value = sample_counts[i] / expected_value
                            else:
                                corrected_value = sample_counts[i]
                                
                            corrected_counts[i] = corrected_value
                            # Tăng global_index để chuyển sang điểm dữ liệu tiếp theo
                            global_index += 1
                        else:
                            # Nếu vượt quá số lượng smoothed values, giữ nguyên giá trị gốc
                            corrected_counts[i] = sample_counts[i]
                    except Exception as e:
                        # Nếu có lỗi, giữ nguyên giá trị gốc
                        corrected_counts[i] = sample_counts[i]
                else:
                    # Bin không hợp lệ thì giữ nguyên giá trị gốc
                    corrected_counts[i] = sample_counts[i]
            
            # Điền các vị trí còn lại với giá trị gốc (nếu có)
            for i in range(min_len, len(sample_counts)):
                corrected_counts[i] = sample_counts[i]
                
            # Lưu kết quả đã correction cho chromosome này
            corrected_sample[chrom] = corrected_counts
        else:
            # Chromosome không có dữ liệu GC thì copy nguyên dữ liệu gốc
            corrected_sample[chrom] = sample_data[chrom].copy()
    
    print("Hoàn thành LOWESS normalization")
    return corrected_sample

def normalize_readcount(pipeline_obj, raw_readcount_npz, output_dir):
    """
    Chuẩn hóa raw read count với GC content và tính ratio
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        raw_readcount_npz (str): Đường dẫn file NPZ chứa raw read counts
        output_dir (Path): Thư mục đầu ra để lưu file NPZ đã chuẩn hóa
        
    Returns:
        str: Đường dẫn file NPZ chứa read ratios đã chuẩn hóa
    """
    print(f"Đang chuẩn hóa file: {raw_readcount_npz}")
    
    # Tạo tên file output
    raw_name = Path(raw_readcount_npz).stem
    normalized_file = output_dir / f"{raw_name.replace('_readcount', '_normalized')}.npz"
    
    # Kiểm tra xem file đã tồn tại hay chưa
    if normalized_file.exists():
        print(f"File đã chuẩn hóa đã tồn tại: {normalized_file}")
        print("Bỏ qua việc chuẩn hóa lại")
        return str(normalized_file)
    
    try:
        # Đọc raw read counts
        raw_data = np.load(raw_readcount_npz)
        chromosome_data = {}
        
        # Copy dữ liệu từ file NPZ
        for chrom in pipeline_obj.chromosomes:
            if chrom in raw_data.files:
                chromosome_data[chrom] = raw_data[chrom].copy()
            else:
                chromosome_data[chrom] = np.array([])
        
        # Áp dụng GC normalization (BẮT BUỘC)
        print("Áp dụng GC content normalization...")
        try:
            chromosome_data = lowess_normalize(pipeline_obj, chromosome_data, pipeline_obj.gc_data)
            print("Hoàn thành GC normalization")
        except Exception as e:
            print(f"Lỗi khi áp dụng GC normalization: {e}")
            raise ValueError("GC normalization thất bại - không thể tiếp tục")
        
        # Tính tỷ lệ read cho từng bin sau khi GC normalize
        print("Tính tỷ lệ read sau GC normalization...")
        
        # Tính tổng read sau normalize cho toàn bộ file
        total_normalized_reads = 0
        for chrom in pipeline_obj.chromosomes:
            if chrom in chromosome_data:
                total_normalized_reads += np.sum(chromosome_data[chrom])
        
        print(f"Tổng số read sau GC normalization: {total_normalized_reads}")
        print("Giữ nguyên normalized counts (không chuyển thành ratio)")
        
        # Lưu kết quả đã chuẩn hóa vào file NPZ
        np.savez_compressed(normalized_file, **chromosome_data)
        print(f"Đã lưu kết quả chuẩn hóa vào: {normalized_file}")
        
        return str(normalized_file)
        
    except Exception as e:
        print(f"Lỗi khi chuẩn hóa file {raw_readcount_npz}: {e}")
        return None

def calculate_read_ratios(pipeline_obj, raw_npz_file, output_dir):
    """
    Tính tỷ lệ read từ raw read counts (raw read count / total reads across all bins)
    Đây KHÔNG phải là chuẩn hóa GC, chỉ là tính tỷ lệ đơn thuần
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        raw_npz_file (str): Đường dẫn file NPZ chứa raw read count
        output_dir (Path): Thư mục đầu ra
        
    Returns:
        str: Đường dẫn file NPZ chứa read ratios (không chuẩn hóa GC)
    """
    raw_data = np.load(raw_npz_file)
    
    # Tạo tên file output
    raw_name = Path(raw_npz_file).stem
    ratio_file = output_dir / f"{raw_name}_ratios.npz"
    ratio_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Tính tổng số reads trên tất cả chromosome và bins
    total_reads = 0
    for chrom in pipeline_obj.chromosomes:
        if chrom in raw_data.files:
            counts = raw_data[chrom]
            # Chỉ tính các bin hợp lệ (không phải -1)
            valid_counts = counts[counts != -1]
            total_reads += np.sum(valid_counts)
    
    print(f"Tổng số reads: {total_reads:,}")
    
    if total_reads == 0:
        print("Cảnh báo: Tổng số reads = 0!")
        return None
    
    # Chuẩn hóa từng chromosome
    ratio_dict = {}
    
    for chrom in pipeline_obj.chromosomes:
        if chrom in raw_data.files:
            counts = raw_data[chrom].astype(np.float32)
            
            # Tính tỷ lệ: ratio = count / total_reads
            read_ratios = counts / total_reads
            
            # Giữ nguyên các bin không hợp lệ
            invalid_mask = (counts == -1)
            read_ratios[invalid_mask] = -1
            
            ratio_dict[chrom] = read_ratios
            
            valid_mask = ~invalid_mask
            if np.any(valid_mask):
                print(f"Chr {chrom}: {np.sum(valid_mask)} bins, "
                      f"ratio range: {np.min(read_ratios[valid_mask]):.6f} - {np.max(read_ratios[valid_mask]):.6f}")
    
    # Lưu file
    np.savez_compressed(ratio_file, **ratio_dict)
    print(f"Đã lưu file read ratios: {ratio_file}")
    
    return str(ratio_file)

def statistics(pipeline_obj, control_npz_dir):
    """
    Tính toán thống kê từ các mẫu control
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        control_npz_dir (str): Đường dẫn thư mục chứa các file NPZ của mẫu control
        
    Returns:
        tuple: (mean_npz_path, std_npz_path) - đường dẫn 2 file NPZ chứa mean và std
    """
    print("Đang tính toán thống kê từ các mẫu control...")
    
    # Tìm tất cả file NPZ normalized trong thư mục control
    # Tìm cả file có '_normalized' và '_ratios' (cho trường hợp không có GC normalization)
    npz_files = list(Path(control_npz_dir).glob("*_normalized.npz"))
    if not npz_files:
        npz_files = list(Path(control_npz_dir).glob("*_ratios.npz"))
    
    if not npz_files:
        raise ValueError(f"Không tìm thấy file NPZ nào trong thư mục {control_npz_dir}")
    
    print(f"Tìm thấy {len(npz_files)} file NPZ")
    
    # Dictionary để lưu dữ liệu từ tất cả mẫu control
    all_data = {}
    
    # Đọc dữ liệu từ tất cả file NPZ
    for npz_file in npz_files:
        try:
            data = np.load(npz_file)
            for chrom in pipeline_obj.chromosomes:
                if chrom in data.files:
                    if chrom not in all_data:
                        all_data[chrom] = []
                    all_data[chrom].append(data[chrom])
        except Exception as e:
            print(f"Lỗi khi đọc file {npz_file}: {e}")
    
    # Tính mean và std cho từng chromosome
    mean_dict = {}
    std_dict = {}
    
    for chrom in pipeline_obj.chromosomes:
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
    mean_file = pipeline_obj.temp_dir / "mean_statistics.npz"
    std_file = pipeline_obj.temp_dir / "std_statistics.npz"
    
    np.savez_compressed(mean_file, **mean_dict)
    np.savez_compressed(std_file, **std_dict)
    
    print(f"Đã lưu thống kê mean vào: {mean_file}")
    print(f"Đã lưu thống kê std vào: {std_file}")
    
    return str(mean_file), str(std_file)

def calculate_raw_statistics(pipeline_obj, control_raw_files):
    """
    Tính mean và std statistics từ danh sách raw control files
    
    Args:
        pipeline_obj: Object CNVPipeline để truy cập các thuộc tính
        control_raw_files (list): Danh sách đường dẫn file raw control NPZ
        
    Returns:
        tuple: (mean_file_path, std_file_path)
    """
    print("Đang tính toán thống kê từ các mẫu control raw...")
    
    # Tập hợp dữ liệu từ tất cả control files
    all_data = {}
    sample_count = 0
    
    for file_path in control_raw_files:
        print(f"Đọc file: {Path(file_path).name}")
        data = np.load(file_path)
        
        for chrom in pipeline_obj.chromosomes:
            if chrom in data.files:
                counts = data[chrom]
                
                if chrom not in all_data:
                    all_data[chrom] = []
                
                # Lọc các bin hợp lệ (không phải -1)
                valid_mask = counts != -1
                filtered_counts = counts.copy()
                filtered_counts[~valid_mask] = np.nan
                
                all_data[chrom].append(filtered_counts)
        
        sample_count += 1
    
    print(f"Tìm thấy {sample_count} file NPZ")
    
    # Tính mean và std cho từng chromosome
    mean_data = {}
    std_data = {}
    
    for chrom in pipeline_obj.chromosomes:
        if chrom in all_data and all_data[chrom]:
            # Stack thành matrix (samples x bins)
            matrix = np.stack(all_data[chrom], axis=0)
            
            # Tính mean và std, bỏ qua NaN
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                mean_values = np.nanmean(matrix, axis=0)
                std_values = np.nanstd(matrix, axis=0)
            
            mean_data[chrom] = mean_values
            std_data[chrom] = std_values
            
            num_bins = len(mean_values)
            print(f"  Chromosome {chrom}: {num_bins} bins, {sample_count} mẫu")
    
    # Lưu kết quả
    mean_output_file = pipeline_obj.temp_dir / 'mean_raw_statistics.npz'
    std_output_file = pipeline_obj.temp_dir / 'std_raw_statistics.npz'
    
    np.savez_compressed(mean_output_file, **mean_data)
    np.savez_compressed(std_output_file, **std_data)
    
    print(f"Đã lưu thống kê raw mean vào: {mean_output_file}")
    print(f"Đã lưu thống kê raw std vào: {std_output_file}")
    
    return str(mean_output_file), str(std_output_file)
