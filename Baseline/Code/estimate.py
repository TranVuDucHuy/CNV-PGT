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

    def calculate_proportion(self, readcount_file, output_dir):
        """
        Calculate read proportion from read counts (read count / total reads across all bins)

        Args:
            readcount_file (str): NPZ file path containing read counts
            output_dir (Path): Output directory

        Returns:
            str: NPZ file path containing read proportions
        """
        data = np.load(readcount_file)

        name = Path(readcount_file).stem
        proportion_file = output_dir / f"{name.replace('_readCount', '_proportion')}.npz"

        proportion_file.parent.mkdir(parents=True, exist_ok=True)

        total_reads = 0
        for chromosome in self.chromosome_list:
            if chromosome in data.files:
                counts = data[chromosome]

                valid_counts = counts[counts != -1]
                total_reads += np.sum(valid_counts)

        print(f"Total reads: {total_reads:,}")

        if total_reads == 0:
            print(f"Warning: Total reads = 0!")
            return None

        proportion_dict = {}

        for chromosome in self.chromosome_list:
            if chromosome in data.files:
                counts = data[chromosome].astype(np.float32)

                read_proportion = counts / total_reads

                invalid_mask = (counts == -1)
                read_proportion[invalid_mask] = -1

                proportion_dict[chromosome] = read_proportion

                valid_mask = ~invalid_mask
                if np.any(valid_mask):
                    print(f"  Chr {chromosome}: {np.sum(valid_mask)} bins, "
                          f"ratio range: {np.min(read_proportion[valid_mask]):.6f} - {np.max(read_proportion[valid_mask]):.6f}")

        np.savez_compressed(proportion_file, **proportion_dict)

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