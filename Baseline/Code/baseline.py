import argparse
from pathlib import Path

from estimate import Estimator
from normalize import base_content, normalize_readcount
from filter import (
    combine_filters,
    create_blacklist,
    filter_base,
    filter_bins,
    filter_import,
)
from plot import Plotter
from segment import cbs

CHROMOSOME_LENGTHS_GRCh37 = {
    "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276,
    "5": 180915260, "6": 171115067, "7": 159138663, "8": 146364022,
    "9": 141213431, "10": 135534747, "11": 135006516, "12": 133851895,
    "13": 115169878, "14": 107349540, "15": 102531392, "16": 90354753,
    "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
    "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566,
}

class CNV:
    def __init__(self, work_directory, bin_size = 400000, filter_ratio = 0.8):
        self.work_directory = Path(work_directory)
        self.bin_size = bin_size
        self.filter_ratio = filter_ratio

        self.create_directories()

        self.chromosome_list = [str(i) for i in range(1, 23)] + ['X', 'Y']
        self.chromosome_lengths = CHROMOSOME_LENGTHS_GRCh37

        self.estimator = Estimator(
            bin_size = self.bin_size,
            chromosome_list = self.chromosome_list,
            chromosome_lengths = CHROMOSOME_LENGTHS_GRCh37,
        )

    def create_directories(self):
        directory_list = [
            self.work_directory / "Temporary",
            self.work_directory / "Temporary" / "Test",
            self.work_directory / "Temporary" / "Train",
            self.work_directory / "Prepare",
            self.work_directory / "Output"
        ]

        for directory in directory_list:
            directory.mkdir(parents = True, exist_ok = True)

    def run_pipeline(self):

        print("=== START CNV DETECTION PIPELINE ===")

        # Precompute base content caches and base filter
        gc_file, n_file = base_content(self, self.work_directory / "Input" / "hg19.fa")
        base_filter_file = filter_base(gc_file, n_file)
        _ = filter_import(self.work_directory / "Input" / "consensusBlacklist.bed", self)
        combined_filter_file = combine_filters(self.work_directory / "Prepare")

        print("\n1. Count reads train samples...")
        train_bam_list = list((self.work_directory / "Input" / "Train").glob('*.bam'))
        train_raw_list = []
        for bam_file in train_bam_list:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Train")
            train_raw_list.append(raw_file)

        print("\n2. Count reads for test samples...")
        test_bam_list = list((self.work_directory / "Input" / "Test").glob('*.bam'))
        test_raw_list = []
        for bam_file in test_bam_list:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Test")
            test_raw_list.append(raw_file)

        print("\n3. Normalized and calculate frequency for train samples...")
        train_normalized_list = []
        for raw_file in train_raw_list:
            normalized_file = normalize_readcount(gc_file, raw_file, self.work_directory / "Temporary" / "Train", combined_filter_file)
            train_normalized_list.append(normalized_file)
            control_frequency_file = self.estimator.calculate_frequency(normalized_file, self.work_directory / "Temporary" / "Train")

        print("\n4. Create blacklist...")
        blacklist = create_blacklist(self.work_directory / "Temporary" / "Train", combined_filter_file)

        print("\n5. Calculate proportion for train samples...")
        for normalized_file in train_normalized_list:
            control_proportion_file = self.estimator.calculate_proportion(
                normalized_file,
                self.work_directory / "Temporary" / "Train",
                blacklist,
            )

        print("\n6. Normalize test and calculate proportion for samples...")
        test_normalized_list = []
        test_proportion_list = []
        for raw_file in test_raw_list:
            normalized_file = normalize_readcount(gc_file, raw_file, self.work_directory / "Temporary" / "Test", combined_filter_file)
            test_normalized_list.append(normalized_file)
            test_proportion_file = self.estimator.calculate_proportion(
                normalized_file,
                self.work_directory / "Temporary" / "Test",
                blacklist,
            )
            test_proportion_list.append(test_proportion_file)

        print("\n7. Calculate statistics from train samples and filter out unstable bins...")
        reference = self.estimator.create_reference(self.work_directory / "Temporary" / "Train", self.work_directory / "Temporary")

        print("\n8. Calculate ratio for test samples ...")
        ratio_list = []
        for test_proportion_file in test_proportion_list:
            ratio_file = self.estimator.calculate_ratio(test_proportion_file, reference, self.work_directory / "Temporary" / "Test")
            ratio_list.append(ratio_file)

        print("\n9. Recalculate ratio using aberration masking and scaling...")
        recalculated_ratio_list = []
        for i, ratio_file in enumerate(ratio_list):
            normalized_file = test_normalized_list[i]
            refined_ratio_file = self.estimator.recalculate_ratio(normalized_file, ratio_file, reference, self.work_directory / "Output", 0.35)
            recalculated_ratio_list.append(refined_ratio_file)

        print("\n10. Performing CBS segmentation...")
        segments_list = []
        for refined_ratio_file in recalculated_ratio_list:
            segments_file = cbs(refined_ratio_file, self.work_directory / "Output", self.bin_size, self.chromosome_list)
            segments_list.append(segments_file)

        print("\n11. Create chart with segments ...")

        for i, refined_ratio_file in enumerate(recalculated_ratio_list):
            segments_file = segments_list[i]
            plotter = Plotter(self.chromosome_list, self.bin_size, self.work_directory / "Output")
            plot_file = plotter.plot(refined_ratio_file, segments_file)

        print(f"\n=== COMPLETED PIPELINE ===")


def main():
    parser = argparse.ArgumentParser(description = "CNV Pipeline (modular)")
    parser.add_argument('-o', '--work-directory', required = True, help = 'Path to work directory')
    parser.add_argument('--bin-size', type = int, default = 400000, help = 'Size of bin')
    parser.add_argument('--filter-ratio', type = float, default = 0.9, help = 'Filter ratio')

    args = parser.parse_args()

    pipeline = CNV(args.work_directory, args.bin_size, args.filter_ratio)

    pipeline.run_pipeline()

if __name__ == "__main__":
    main()