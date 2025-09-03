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

        print("\n1. Count reads and calculate proportion for train samples...")

        control_bam_files = list((self.work_directory / "Input" / "Train").glob('*.bam'))

        control_raw_files = []
        control_proportion_raw_files = []
        for bam_file in control_bam_files:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Raw" / "Train")
            if raw_file:
                control_raw_files.append(raw_file)
                control_proportion_raw_file = self.estimator.calculate_proportion(raw_file, self.work_directory / "Temporary" / "Raw" / "Train")
                if control_proportion_raw_file:
                    control_proportion_raw_files.append(control_proportion_raw_file)

        print("\n2. Normalized train samples...")

        control_normalized_files = []
        control_proportion_normalized_files = []
        for raw_file in control_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Train")
            if normalized_file:
                control_normalized_files.append(normalized_file)
                control_proportion_normalized_file = self.estimator.calculate_proportion(normalized_file, self.work_directory / "Temporary" / "Normalized" / "Train")
                if control_proportion_normalized_file:
                    control_proportion_normalized_files.append(control_proportion_normalized_file)

        print("\n3. Count reads and calculate proportion for test samples...")

        case_bam_files = list((self.work_directory / "Input" / "Test").glob('*.bam'))

        case_raw_files = []
        case_proportion_raw_files = []
        for bam_file in case_bam_files:
            raw_file = self.estimator.count_read(str(bam_file), self.work_directory / "Temporary" / "Raw" / "Test")
            if raw_file:
                case_raw_files.append(raw_file)
                case_proportion_raw_file = self.estimator.calculate_proportion(raw_file, self.work_directory / "Temporary" / "Raw" / "Test")
                if case_proportion_raw_file:
                    case_proportion_raw_files.append(case_proportion_raw_file)

        print("\n4. Normalize test samples...")

        case_normalized_files = []
        case_proportion_normalized_files = []
        for raw_file in case_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Test")
            if normalized_file:
                case_normalized_files.append(normalized_file)
                case_proportion_normalized_file = self.estimator.calculate_proportion(normalized_file, self.work_directory / "Temporary" / "Normalized" / "Test")
                if case_proportion_normalized_file:
                    case_proportion_normalized_files.append(case_proportion_normalized_file)

        print("\n5. Calculate statistics from train samples (raw & normalized) and filter out unstable bins...")

        mean_raw_file, std_raw_file, cv_raw_file = self.estimator.statistics(self.work_directory / "Temporary" / "Raw" / "Train", self.work_directory / "Temporary" / "Raw")
        blacklist_raw_file = filter_bins(cv_raw_file, self.filter_ratio, self.work_directory / "Temporary" / "Raw")
        mean_filtered_raw_file = create_filter_files(mean_raw_file, blacklist_raw_file, self.work_directory / "Temporary" / "Raw")

        mean_normalized_file, std_normalized_file, cv_normalized_file = self.estimator.statistics(self.work_directory / "Temporary" / "Normalized" / "Train", self.work_directory / "Temporary" / "Normalized")
        blacklist_normalized_file = filter_bins(cv_normalized_file, self.filter_ratio, self.work_directory / "Temporary" / "Normalized")
        mean_filtered_normalized_file = create_filter_files(mean_normalized_file, blacklist_normalized_file, self.work_directory / "Temporary" / "Normalized")

        print("\n6. Calculate ratio for test samples (raw & normalized)...")

        # # Will fix soon (filtered file) ------------------------------------------------------------------------------------------------------------ @@@@@@@@@@@@@@@
        # ratio_raw_files = []
        # for case_file in case_proportion_raw_files:
        #     ratio_file = self.estimator.calculate_ratio(case_file, mean_raw_file, blacklist_raw_file, self.work_directory / "Output" / "Raw" / "Data")
        #     if ratio_file:
        #         ratio_raw_files.append(ratio_file)
        #
        # ratio_normalized_files = []
        # for case_file in case_proportion_normalized_files:
        #     ratio_file = self.estimator.calculate_ratio(case_file, mean_normalized_file, blacklist_normalized_file, self.work_directory / "Output" / "Normalized" / "Data")
        #     if ratio_file:
        #         ratio_normalized_files.append(ratio_file)
        ratio_raw_files = []
        for case_file in case_raw_files:
            ratio_file = self.estimator.calculate_ratio(case_file, mean_raw_file, blacklist_raw_file,
                                                        self.work_directory / "Output" / "Raw" / "Data")
            if ratio_file:
                ratio_raw_files.append(ratio_file)

        ratio_normalized_files = []
        for case_file in case_normalized_files:
            ratio_file = self.estimator.calculate_ratio(case_file, mean_normalized_file, blacklist_normalized_file,
                                                        self.work_directory / "Output" / "Normalized" / "Data")
            if ratio_file:
                ratio_normalized_files.append(ratio_file)

        print("\n7. Performing CBS segmentation...")

        segments_raw_files = []
        for ratio_file in ratio_raw_files:
            segments_file = cbs(self, ratio_file, self.work_directory / "Output" / "Raw" / "Data", self.bin_size, self.chromosome_list)
            if segments_file:
                segments_raw_files.append(segments_file)
            else:
                segments_raw_files.append(None)

        segments_normalized_files = []
        for ratio_file in ratio_normalized_files:
            segments_file = cbs(self, ratio_file, self.work_directory / "Output" / "Normalized" / "Data", self.bin_size, self.chromosome_list)
            if segments_file:
                segments_normalized_files.append(segments_file)
            else:
                segments_normalized_files.append(None)

        print("\n9. Create chart with segments (raw & normalized)...")

        plot_raw_files = []
        for i, ratio_file in enumerate(ratio_raw_files):
            segments_file = segments_raw_files[i] if i < len(segments_raw_files) else None

            plotter = Plotter(
                self.chromosome_list,
                self.bin_size,
                self.work_directory / "Output" / "Raw" / "Plot"
            )

            plot_file = plotter.plot(ratio_file, mean_filtered_raw_file, segments_file)

            if plot_file:
                plot_raw_files.append(plot_file)

        plot_normalized_files = []
        for i, ratio_file in enumerate(ratio_normalized_files):
            segments_file = segments_normalized_files[i] if i < len(segments_normalized_files) else None

            plotter = Plotter(
                self.chromosome_list,
                self.bin_size,
                self.work_directory / "Output" / "Normalized" / "Plot"
            )

            plot_file = plotter.plot(ratio_file, mean_filtered_normalized_file, segments_file)

            if plot_file:
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