import os
import sys
import argparse
from pathlib import Path
from estimate import Estimator
from normalize import normalize_readcount
from filter import (filter_bins, create_filter_files)
from segment import cbs
from plot import Plotter

class CNV:
    def __init__(self, work_directory, bin_size = 200000, filter_ratio = 0.8):
        self.work_directory = Path(work_directory)
        self.bin_size = bin_size
        self.filter_ratio = filter_ratio

        self.create_directories()

        self.chromosome_list = [str(i) for i in range(1, 23)] + ['X', 'Y']

        self.estimator = Estimator(
            bin_size = self.bin_size,
            chromosome_list = self.chromosome_list
        )

    def create_directories(self):
        directory_list = [
            self.work_directory / "Temporary",
            self.work_directory / "Temporary" / "Raw",
            self.work_directory / "Temporary" / "Raw" / "Test",
            self.work_directory / "Temporary" / "Raw" / "Train",
            self.work_directory / "Temporary" / "Normalized",
            self.work_directory / "Temporary" / "Normalized" / "Test",
            self.work_directory / "Temporary" / "Normalized" / "Train",
            self.work_directory / "Output",
            self.work_directory / "Output" / "Raw",
            self.work_directory / "Output" / "Raw" / "Data",
            self.work_directory / "Output" / "Raw" / "Plot",
            self.work_directory / "Output" / "Normalized",
            self.work_directory / "Output" / "Normalized" / "Data",
            self.work_directory / "Output" / "Normalized" / "Plot",
        ]

        for directory in directory_list:
            directory.mkdir(parents = True, exist_ok = True)

    def run_pipeline(self):

        print("=== START CNV DETECTION PIPELINE ===")

        print("\n1. Count reads train samples...")
        train_bam_list = list((self.work_directory / "Input" / "Train").glob('*.bam'))
        train_raw_list = []
        for bam_file in train_bam_list:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Raw" / "Train")
            train_raw_list.append(raw_file)

        print("\n2. Normalized and calculate proportion for train samples...")
        control_normalized_list = []
        for raw_file in train_raw_list:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Train")
            control_normalized_list.append(normalized_file)
            control_proportion_normalized_file = self.estimator.calculate_proportion(normalized_file, self.work_directory / "Temporary" / "Normalized" / "Train")


        print("\n3. Count reads for test samples...")
        test_bam_list = list((self.work_directory / "Input" / "Test").glob('*.bam'))
        test_raw_list = []
        for bam_file in test_bam_list:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Raw" / "Test")
            test_raw_list.append(raw_file)

        print("\n4. Normalize test and calculate proportion for samples...")
        test_normalized_list = []
        test_proportion_normalized_list = []
        for raw_file in test_raw_list:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Test")
            test_normalized_list.append(normalized_file)
            test_proportion_normalized_file = self.estimator.calculate_proportion(normalized_file, self.work_directory / "Temporary" / "Normalized" / "Test")
            test_proportion_normalized_list.append(test_proportion_normalized_file)

        print("\n5. Calculate statistics from train samples (raw & normalized) and filter out unstable bins...")
        mean_normalized, cv_normalized = self.estimator.statistics(self.work_directory / "Temporary" / "Normalized" / "Train", self.work_directory / "Temporary" / "Normalized")
        blacklist_normalized = filter_bins(cv_normalized, self.filter_ratio, self.work_directory / "Temporary" / "Normalized")
        mean_filtered_normalized = create_filter_files(mean_normalized, blacklist_normalized, self.work_directory / "Temporary" / "Normalized")

        print("\n6. Calculate ratio for test samples (raw & normalized)...")
        # # Will fix soon (filtered file) ------------------------------------------------------------------------------------------------------------ @@@@@@@@@@@@@@@
        # ratio_normalized_files = []
        # for case_file in case_proportion_normalized_files:
        #     ratio_file = self.estimator.calculate_ratio(case_file, mean_normalized_file, blacklist_normalized_file, self.work_directory / "Output" / "Normalized" / "Data")
        #     if ratio_file:
        #         ratio_normalized_files.append(ratio_file)

        ratio_normalized_list = []
        for test_proportion_normalized_file in test_proportion_normalized_list:
            ratio_normalized_file = self.estimator.calculate_ratio(test_proportion_normalized_file, mean_normalized, blacklist_normalized,
                                                        self.work_directory / "Output" / "Normalized" / "Data")
            ratio_normalized_list.append(ratio_normalized_file)

        print("\n7. Performing CBS segmentation...")
        segments_normalized_list = []
        for ratio_normalized_file in ratio_normalized_list:
            segments_file = cbs(self, ratio_normalized_file, self.work_directory / "Output" / "Normalized" / "Data", self.bin_size, self.chromosome_list)
            segments_normalized_list.append(segments_file)

        print("\n9. Create chart with segments (raw & normalized)...")

        plot_normalized_files = []
        for i, ratio_normalized_file in enumerate(ratio_normalized_list):
            segments_file = segments_normalized_list[i]

            plotter = Plotter(
                self.chromosome_list,
                self.bin_size,
                self.work_directory / "Output" / "Normalized" / "Plot"
            )

            plot_file = plotter.plot(ratio_normalized_file, mean_filtered_normalized, segments_file)
            plot_normalized_files.append(plot_file)

        print(f"\n=== COMPLETED PIPELINE ===")


def main():
    parser = argparse.ArgumentParser(
        description = "CNV Pipeline (modular)"
    )

    parser.add_argument(
        '-o', '--work-directory',
        required = True,
        help = 'Path to work directory'
    )

    parser.add_argument(
        '--bin-size',
        type = int,
        default = 200000,
        help = 'Size of bin'
    )

    parser.add_argument(
        '--filter-ratio',
        type = float,
        default = 0.8,
        help = 'Filter ratio'
    )

    args = parser.parse_args()

    pipeline = CNV(
        work_directory = args.work_directory,
        bin_size = args.bin_size,
        filter_ratio = args.filter_ratio
    )

    plot_files = pipeline.run_pipeline()

if __name__ == "__main__":
    main()