from pathlib import Path
import numpy as np
import pysam

def count_read(pipeline_obj, bam_file, output_dir):
    bam_name = Path(bam_file).stem
    output_file = output_dir / f"{bam_name}_raw_readCount.npz"

    if output_file.exists():
        return str(output_file)

    chromosome_data = {}

    bam = pysam.AlignmentFile(bam_file, "rb")

    bam_chromosomes = list(bam.references)

    for chromosome in pipeline_obj.chromosomes:
        bam_chromosome_name = f"chr{chromosome}"

        chr_index = bam_chromosomes.index(bam_chromosome_name)
        chr_length = bam.lengths[chr_index]

        chromosome_size = chr_length

        num_bins = int(np.ceil(chromosome_size / pipeline_obj.bin_size))

        read_counts = np.zeros(num_bins)

        for bin_index in range(num_bins):
            start_pos = bin_index * pipeline_obj.bin_size
            end_pos = min((bin_index + 1) * pipeline_obj.bin_size, chromosome_size)

            count = bam.count(contig=bam_chromosome_name, start=start_pos, end=end_pos)
            read_counts[bin_index] = count

        chromosome_data[chromosome] = read_counts

    bam.close()

    np.savez_compressed(output_file, **chromosome_data)

    return str(output_file)

def statistics(pipeline_obj, control_npz_dir, output_dir):

    proportion_list = list(Path(control_npz_dir).glob("*_readCount.npz"))

    all_data = {}

    for npz_file in proportion_list:
        data = np.load(npz_file)
        for chromosome in pipeline_obj.chromosomes:
            if chromosome in data.files:
                if chromosome not in all_data:
                    all_data[chromosome] = []
                all_data[chromosome].append(data[chromosome])

    mean_dict = {}
    std_dict = {}
    cv_dict = {}

    for chromosome in pipeline_obj.chromosomes:
        if chromosome in all_data and all_data[chromosome]:
            chromosome_data = np.array(all_data[chromosome])

            mean_dict[chromosome] = np.mean(chromosome_data, axis=0)
            std_dict[chromosome] = np.std(chromosome_data, axis=0)
            with np.errstate(divide='ignore', invalid='ignore'):
                cv_dict[chromosome] = np.where(mean_dict[chromosome] != 0, std_dict[chromosome] / mean_dict[chromosome], 0)

    mean_file = output_dir / "Mean.npz"
    std_file = output_dir / "StandardDeviation.npz"
    cv_file = output_dir / "CoefficientVariation.npz"

    np.savez_compressed(mean_file, **mean_dict)
    np.savez_compressed(std_file, **std_dict)
    np.savez_compressed(cv_file, **cv_dict)

    return str(mean_file), str(std_file), str(cv_file)

def calculate_ratio(pipeline_obj, case_file, mean_file, blacklist_file, output_dir):

    case_data = np.load(case_file)
    mean_data = np.load(mean_file)
    bin_data = np.load(blacklist_file)

    case_name = Path(case_file).stem.replace('_readCount', '_ratio')
    ratio_file = output_dir / f"{case_name}.npz"

    ratio_dict = {}

    for chromosome in pipeline_obj.chromosomes:
        if chromosome in case_data.files and chromosome in mean_data.files and chromosome in bin_data.files:
            case_ratios = case_data[chromosome]
            mean_ratios = mean_data[chromosome]
            bin_mask = bin_data[chromosome]

            log2_ratios = np.full_like(case_ratios, -2.0)

            valid_bins = bin_mask == True

            valid_case = case_ratios > 0
            valid_mask = valid_bins & valid_case

            if np.any(valid_mask):
                log2_ratios[valid_mask] = np.log2(case_ratios[valid_mask] / mean_ratios[valid_mask])

            ratio_dict[chromosome] = log2_ratios
        else:
            ratio_dict[chromosome] = np.array([])

    np.savez_compressed(ratio_file, **ratio_dict)

    return str(ratio_file)