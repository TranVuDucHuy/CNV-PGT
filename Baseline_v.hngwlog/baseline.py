import os
import sys
import argparse
from pathlib import Path
from estimate import (count_read, statistics, calculate_ratio)
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

        self.chromosomes = [str(i) for i in range(1, 23)] + ['X', 'Y']

        self.plotter = Plotter(self.chromosomes, self.bin_size, self.work_directory / "Output")

    def create_directories(self):
        directory_list = [
            self.work_directory / "Temporary",
            self.work_directory / "Temporary" / "Raw",
            self.work_directory / "Temporary" / "Raw" / "Train",
            self.work_directory / "Temporary" / "Raw" / "Train" / "Control",
            self.work_directory / "Temporary" / "Raw" / "Train" / "Case",
            self.work_directory / "Temporary" / "Normalized",
            self.work_directory / "Temporary" / "Normalized" / "Train",
            self.work_directory / "Temporary" / "Normalized" / "Train" / "Control",
            self.work_directory / "Temporary" / "Normalized" / "Train" / "Case"
        ]

        for directory in directory_list:
            directory.mkdir(parents = True, exist_ok = True)

    def run_pipeline(self):

        control_bam_files = list((self.work_directory / "Train" / "Control").glob('*.bam'))

        control_raw_files = []
        for bam_file in control_bam_files:
            raw_file = count_read(self, str(bam_file), self.work_directory / "Temporary" / "Raw" / "Train" / "Control")
            if raw_file:
                control_raw_files.append(raw_file)

        control_normalized_files = []
        for raw_file in control_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Train" / "Control")
            if normalized_file:
                control_normalized_files.append(normalized_file)

        case_bam_files = list((self.work_directory / "Train" / "Case").glob('*.bam'))

        case_raw_files = []
        for bam_file in case_bam_files:
            raw_file = count_read(self, str(bam_file), self.work_directory / "Temporary" / "Raw" / "Train" / "Case")
            if raw_file:
                case_raw_files.append(raw_file)

        case_normalized_files = []
        for raw_file in case_raw_files:
            normalized_file = normalize_readcount(self, raw_file, self.work_directory / "Temporary" / "Normalized" / "Train" / "Case")
            if normalized_file:
                case_normalized_files.append(normalized_file)

        mean_file, std_file, cv_file = statistics(self, self.work_directory / "Temporary" / "Normalized" / "Train" / "Control", self.work_directory / "Temporary" / "Normalized" / "Train")

        blacklist_file = filter_bins(cv_file, self.filter_ratio, self.work_directory / "Temporary" / "Normalized" / "Train")

        mean_filterd_file = create_filter_files(mean_file, blacklist_file, self.work_directory / "Temporary" / "Normalized" / "Train")

        # Will fix soon (filtered file) ------------------------------------------------------------------------------------------------------------ @@@@@@@@@@@@@@@
        ratio_files = []
        for case_file in case_normalized_files:
            ratio_file = calculate_ratio(self, case_file, mean_file, blacklist_file, self.work_directory / "Temporary" / "Normalized" / "Train" / "Case")
            if ratio_file:
                ratio_files.append(ratio_file)

        segments_files = []
        for ratio_file in ratio_files:
            segments_file = cbs(self, ratio_file, self.work_directory / "Temporary" / "Normalized" / "Train" / "Case" , self.bin_size, self.chromosomes)
            if segments_file:
                segments_files.append(segments_file)
            else:
                segments_files.append(None)

        plot_files = []
        for i, ratio_file in enumerate(ratio_files):
            segments_file = segments_files[i] if i < len(segments_files) else None
            plot_file = self.plotter.plot(ratio_file, mean_filterd_file, segments_file, pipeline_obj=self)
            if plot_file:
                plot_files.append(plot_file)

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