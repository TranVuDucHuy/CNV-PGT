from pathlib import Path
import numpy as np
import pysam

CHROMOSOME_LENGTHS_GRCh37 = {
    "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276,
    "5": 180915260, "6": 171115067, "7": 159138663, "8": 146364022,
    "9": 141213431, "10": 135534747, "11": 135006516, "12": 133851895,
    "13": 115169878, "14": 107349540, "15": 102531392, "16": 90354753,
    "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
    "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566,
}

class Estimator:
    def __init__(self, bin_size = 200000, chromosome_list = None):
        self.bin_size = int(bin_size)
        self.chromosome_list = (chromosome_list if chromosome_list is not None else [str(i) for i in range(1, 23)] + ["X", "Y"])

    def save_bin_coordinates(self, output_dir):
        """
        Generate bin coordinate file (NPZ) based on chromosome lengths and bin size
        Each chromosome -> Nx2 array [start, end]

        Args:
            output_dir (Path): Output directory to save NPZ file

        Returns:
            str: NPZ file path containing bin coordinates
        """
        bin_coordinate_file = output_dir / "binCoordinate.npz"
        if bin_coordinate_file.exists():
            print(f"Bin coordinate file already exists: {bin_coordinate_file}")
            return str(bin_coordinate_file)

        chromosome_bins = {}

        for chromosome in self.chromosome_list:
            chromosome_length = CHROMOSOME_LENGTHS_GRCh37[str(chromosome)]
            num_bins = chromosome_length // self.bin_size

            start_positions = np.arange(0, num_bins * self.bin_size, self.bin_size, dtype=np.int64)
            end_positions = np.minimum(start_positions + self.bin_size, chromosome_length)

            chromosome_bins[chromosome] = np.column_stack((start_positions, end_positions))

        np.savez_compressed(bin_coordinate_file, **chromosome_bins)
        return str(bin_coordinate_file)

    def count_read(self, bam_file, output_dir):
        """
        Count the number of reads in bins on each chromosome (raw counts only)

        Args:
            bam_file (str): BAM file path
            output_dir (Path): Output directory to save NPZ file

        Returns:
            str: NPZ file path containing raw read counts
        """
        print(f"Processing file: {bam_file}")

        bam_name = Path(bam_file).stem
        output_file = output_dir / f"{bam_name}_raw_readCount.npz"

        if output_file.exists():
            print(f"NPZ file already exists: {output_file}")
            return str(output_file)

        chromosome_data = {}

        bam = pysam.AlignmentFile(bam_file, "rb")

        for chromosome in self.chromosome_list:
            bam_chromosome_name = f"chr{chromosome}"

            chromosome_length = CHROMOSOME_LENGTHS_GRCh37[str(chromosome)]
            # Use floor division to exclude any trailing partial bin
            num_bins = chromosome_length // self.bin_size
            read_counts = np.zeros(num_bins)

            for bin_index in range(num_bins):
                start_pos = bin_index * self.bin_size
                end_pos = min((bin_index + 1) * self.bin_size, chromosome_length)

                count = bam.count(contig=bam_chromosome_name, start=start_pos, end=end_pos)
                read_counts[bin_index] = count

            chromosome_data[chromosome] = read_counts

            print(f"  Chromosome {chromosome} ({bam_chromosome_name}): {num_bins} bins, {np.sum(read_counts)} reads")

        bam.close()

        np.savez_compressed(output_file, **chromosome_data)

        print(f"Saved raw read counts to: {output_file}")

        return str(output_file)

    def build_mean_reference(self, train_dir, output_dir):
        """
        Build mean reference file from training read count samples.

        For each chromosome, this function loads all training NPZ files containing
        per-bin read counts, stacks them, and computes the mean read count per bin
        across all training samples. The result is saved as a compressed NPZ file.

        Args:
            train_dir (Path): Directory containing training NPZ files
                (each file named *_normalized_readCount.npz).
            output_dir (Path): Output directory to save the mean reference file.

        Returns:
            str: File path to the saved mean reference NPZ file.
        """
        mean_reference_file = output_dir / "mean_ref.npz"

        readcount_file_list = sorted(train_dir.glob("*_normalized_readCount.npz"))

        mean_dict = {}
        data_per_chromosome = {}

        for readcount_file in readcount_file_list:
            data = np.load(readcount_file)
            for chromosome in data.files:
                arr = data[chromosome].astype(float)
                data_per_chromosome.setdefault(chromosome, []).append(arr)

        for chromosome, arrs in data_per_chromosome.items():
            stacked = np.vstack(arrs)
            mean = np.nanmean(stacked, axis = 0)
            mean_dict[chromosome] = mean

        np.savez_compressed(mean_reference_file, **mean_dict)
        return str(mean_reference_file)

    def calculate_proportion(self, readcount_file, mean_reference_file, output_dir):
        """
        Calculate read proportion for each chromosome based on total read counts.

        This function computes normalized read proportions across all autosomes
        by adjusting for chromosomes with abnormal copy numbers (high mosaicism).
        Chromosomes with large deviations in estimated copy number (|CN - 2| ≥ 0.9)
        are temporarily excluded when calculating total reads, and their expected
        contribution is estimated from the mean reference.

        Args:
            readcount_file (str): Path to NPZ file containing per-bin raw read counts.
            mean_reference_file (str): Path to NPZ mean reference file
                (used to estimate expected reads for excluded chromosomes).
            output_dir (Path): Output directory to save the resulting NPZ file.

        Returns:
            str: File path to the saved NPZ file containing read proportions
                 per chromosome.
        """
        readcount_data = np.load(readcount_file)
        mean_reference_data = np.load(mean_reference_file)

        name = Path(readcount_file).stem
        proportion_file = output_dir / f"{name.replace('_readCount', '_proportion')}.npz"
        proportion_file.parent.mkdir(parents=True, exist_ok=True)

        autosome_list = [str(i) for i in range(1, 23)]
        total_reads_per_chromosome = {}
        for chromosome in autosome_list:
            if chromosome in readcount_data.files:
                total_reads_per_chromosome[chromosome] = np.sum(readcount_data[chromosome])

        high_mosaicism_chromosomes = []
        for chromosome, total_read in total_reads_per_chromosome.items():
            if chromosome in mean_reference_data:
                estimated_copy_number = (total_read / np.sum(mean_reference_data[chromosome])) * 2
                if abs(estimated_copy_number - 2) >= 0.9:
                    high_mosaicism_chromosomes.append(chromosome)

        proportion_result = {}
        for chromosome in autosome_list:
            if chromosome not in readcount_data.files:
                continue
            chromosome_counts = readcount_data[chromosome].astype(float)
            valid_mask = chromosome_counts != -1

            total_included = 0.0
            for other_chromosome, total_read in total_reads_per_chromosome.items():
                if other_chromosome not in high_mosaicism_chromosomes and other_chromosome != chromosome:
                    total_included += total_read

            expected_excluded = 0.0

            for high_chr in high_mosaicism_chromosomes:
                if high_chr in mean_reference_data.files and high_chr != chromosome:
                    expected_excluded += np.sum(mean_reference_data[high_chr])

            effective_total = total_included + expected_excluded
            if effective_total <= 0 or not np.isfinite(effective_total):
                effective_total = 1.0

            chromosome_proportion = np.full_like(chromosome_counts, -1.0)
            chromosome_proportion[valid_mask] = chromosome_counts[valid_mask] / effective_total

            proportion_result[chromosome] = chromosome_proportion

        np.savez_compressed(proportion_file, **proportion_result)

        print(f"Saved read proportion to: {output_dir}")

        return str(proportion_file)

    def statistics(self, control_npz_dir, output_dir):
        """
        Calculate statistics from train samples

        Args:
            control_npz_dir (str): Directory path containing NPZ files of train sample
            output_dir (Path): Output directory

        Returns:
            tuple(mean_file, std_file, cv_file) - path of 3 NPZ files containing mean, std and cv
        """
        print("Calculating statistics from train samples...")

        proportion_list = list(Path(control_npz_dir).glob("*_proportion.npz"))
        # proportion_list = list(Path(control_npz_dir).glob("*_readCount.npz"))

        print(f"Found {len(proportion_list)} sample files")

        all_data = {}

        for npz_file in proportion_list:
            data = np.load(npz_file)
            for chromosome in self.chromosome_list:
                if chromosome in data.files:
                    if chromosome not in all_data:
                        all_data[chromosome] = []
                    all_data[chromosome].append(data[chromosome])

        mean_dict = {}
        std_dict = {}
        cv_dict = {}

        for chromosome in self.chromosome_list:
            if chromosome in all_data and all_data[chromosome]:
                chromosome_data = np.array(all_data[chromosome])

                mean_dict[chromosome] = np.mean(chromosome_data, axis=0)
                std_dict[chromosome] = np.std(chromosome_data, axis=0)
                with np.errstate(divide='ignore', invalid='ignore'):
                    cv_dict[chromosome] = np.where(mean_dict[chromosome] != 0, std_dict[chromosome] / mean_dict[chromosome], 0)

                print(f"  Chromosome {chromosome}: {chromosome_data.shape[1]} bins, {chromosome_data.shape[0]} samples")

        mean_file = output_dir / "Mean.npz"
        cv_file = output_dir / "CoefficientVariation.npz"

        np.savez_compressed(mean_file, **mean_dict)
        np.savez_compressed(cv_file, **cv_dict)

        print(f"Statistics saved to: {output_dir}")

        return str(mean_file), str(cv_file)

    def calculate_ratio(self, test_file, mean_file, blacklist_file, output_dir):
        """
        Calculate log2 ratio between test and train samples

        Args:
            case_file (str): NPZ file path of test sample
            mean_file (str): NPZ file path containing mean
            blacklist_file (str): NPZ file path containing filter bins
            output_dir: Output directory

        Returns:
            str: NPZ file path containing log2 ratio
        """
        test_data = np.load(test_file)
        mean_data = np.load(mean_file)
        bin_data = np.load(blacklist_file)

        test_name = Path(test_file).stem.replace('_proportion', '_ratio')
        # case_name = Path(case_file).stem.replace('_readCount', '_ratio')
        ratio_file = output_dir / f"{test_name}.npz"

        ratio_dict = {}

        for chromosome in self.chromosome_list:
            if chromosome in test_data.files and chromosome in mean_data.files and chromosome in bin_data.files:
                case_ratios = test_data[chromosome]
                mean_ratios = mean_data[chromosome]
                bin_mask = bin_data[chromosome]

                log2_ratios = np.full_like(case_ratios, -2.0)

                valid_bins = bin_mask == True
                valid_case = case_ratios > 0
                valid_mean = mean_ratios > 0
                valid_mask = valid_bins & valid_case & valid_mean

                if np.any(valid_mask):
                    log2_ratios[valid_mask] = np.log2(case_ratios[valid_mask] / mean_ratios[valid_mask])

                ratio_dict[chromosome] = log2_ratios

                print(f" Chromosome {chromosome}: {np.sum(valid_mask)} stable bin")
            else:
                print(f"Warning: No data for chromosome {chromosome}")
                ratio_dict[chromosome] = np.array([])

        np.savez_compressed(ratio_file, **ratio_dict)

        print(f"Saved log2 ratio to: {ratio_file}")

        return str(ratio_file)