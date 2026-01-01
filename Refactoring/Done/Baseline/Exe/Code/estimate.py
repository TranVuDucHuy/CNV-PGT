from pathlib import Path
import numpy as np
import pysam

class Estimator:
    def __init__(self, bin_size = 400000, chromosome_list = None, chromosome_lengths = None):
        self.bin_size = int(bin_size)
        self.chromosome_list = (chromosome_list if chromosome_list is not None else [str(i) for i in range(1, 23)] + ["X", "Y"])
        if chromosome_lengths is None:
            raise ValueError("chromosome_lengths must be provided to Estimator")
        self.chromosome_lengths = chromosome_lengths

    def count_read(self, bam_file, output_dir):
        """
        Count the number of reads in bins on each chromosome (raw counts only)
        """
        print(f"Processing file: {bam_file}")
        bam_name = Path(bam_file).stem
        raw_file = output_dir / f"{bam_name}_rawCount.npz"

        if raw_file.exists():
            print(f"Raw count file already exists: {raw_file}")
            return str(raw_file)

        chromosome_data = {}
        bam = pysam.AlignmentFile(bam_file, "rb")

        for chromosome in self.chromosome_list:
            bam_chromosome_name = f"chr{chromosome}"
            chromosome_length = self.chromosome_lengths[str(chromosome)]
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
        np.savez_compressed(raw_file, **chromosome_data)
        print(f"Saved raw read counts to: {raw_file}")
        return str(raw_file)

    def calculate_frequency(self, normalized_file, output_dir):
        """
        Calculate read frequency from read counts (read count / total reads across all bins)
        """
        data = np.load(normalized_file)
        name = Path(normalized_file).stem
        frequency_file = output_dir / f"{name.replace('_normalized', '_frequency')}.npz"
        frequency_file.parent.mkdir(parents=True, exist_ok=True)

        if frequency_file.exists():
            print(f"Frequency file already exists: {frequency_file}")
            return str(frequency_file)

        # Only count total reads from autosomes (1-22), excluding X and Y
        autosome_list = [str(i) for i in range(1, 23)]
        total_reads = 0.0
        for chromosome in autosome_list:
            total_reads += np.sum(data[chromosome])

        print(f"Total reads (autosomes only): {int(total_reads):,}")

        if total_reads == 0:
            print(f"Warning: Total reads = 0!")
            return None

        frequency_dict = {}
        for chromosome in self.chromosome_list:
            counts = data[chromosome]
            read_frequency = counts / total_reads
            frequency_dict[chromosome] = read_frequency * self.bin_size

        # Calculate XY_ratio and determine gender
        sum_freq_X = np.sum(frequency_dict['X'])
        sum_freq_Y = np.sum(frequency_dict['Y'])
        num_bins_X = len(frequency_dict['X'])
        num_bins_Y = len(frequency_dict['Y'])
        
        XY_ratio = (sum_freq_Y * num_bins_X) / (sum_freq_X * num_bins_Y) if (sum_freq_X > 0 and num_bins_Y > 0) else 0.0
        gender = "male" if XY_ratio > 0.1 else "female"
        
        frequency_dict['XY_ratio'] = np.array(XY_ratio)
        frequency_dict['gender'] = np.array(gender)

        np.savez_compressed(frequency_file, **frequency_dict)
        print(f"Saved read frequency to: {output_dir}")
        return str(frequency_file)

    def calculate_proportion(self, normalized_file, output_dir, blacklist_file):
        """
        Calculate read proportion from normalized read counts.
        Blacklisted bins are set to 0 and excluded from totals by using an in-memory masked copy.
        """
        name = Path(normalized_file).stem
        proportion_file = output_dir / f"{name.replace('_normalized', '_proportion')}.npz"
        data = np.load(normalized_file)
        blacklist_data = np.load(blacklist_file)

        if proportion_file.exists():
            print(f"Proportion file already exists: {proportion_file}")
            return str(proportion_file)

        # Build a masked copy with blacklist bins zeroed
        masked = {}
        for chromosome in self.chromosome_list:
            arr = data[chromosome].copy()
            arr[blacklist_data[chromosome]] = 0
            masked[chromosome] = arr

        # Only count total reads from autosomes (1-22), excluding X and Y
        autosome_list = [str(i) for i in range(1, 23)]
        total_reads = 0.0
        total_counts_per_chromosome = {chromosome: 0.0 for chromosome in autosome_list}

        # Sum totals on masked data
        for chromosome in autosome_list:
            counts = masked[chromosome]
            chromosome_read_total = np.sum(counts)
            total_counts_per_chromosome[chromosome] = chromosome_read_total
            total_reads += chromosome_read_total
        print(f"Total reads (autosomes only): {int(total_reads):,}")

        total_exclude = {chr_name: total_reads - total_counts_per_chromosome.get(chr_name, 0.0) for chr_name in autosome_list}
        total_exclude["X"] = total_reads
        total_exclude["Y"] = total_reads

        proportion_dict = {}
        for chromosome in self.chromosome_list:
            counts = masked[chromosome]
            denom = total_exclude.get(chromosome, total_reads)
            read_proportion = (counts / denom * self.bin_size) if denom > 0 else np.zeros_like(counts)
            proportion_dict[chromosome] = read_proportion

        # Calculate XY_ratio and determine gender
        sum_prop_X = np.sum(proportion_dict['X'])
        sum_prop_Y = np.sum(proportion_dict['Y'])
        num_bins_X = len(proportion_dict['X'])
        num_bins_Y = len(proportion_dict['Y'])
        
        XY_ratio = (sum_prop_Y * num_bins_X) / (sum_prop_X * num_bins_Y) if (sum_prop_X > 0 and num_bins_Y > 0) else 0.0
        gender = "male" if XY_ratio > 0.1 else "female"
        
        proportion_dict['XY_ratio'] = np.array(XY_ratio)
        proportion_dict['gender'] = np.array(gender)

        np.savez_compressed(proportion_file, **proportion_dict)
        print(f"Saved read proportion to: {output_dir}")
        return str(proportion_file)

    def create_reference(self, train_dir, output_dir):
        """Compute only the per-chromosome mean across train proportion files."""
        proportion_list = list(Path(train_dir).glob("*_proportion.npz"))
        print(f"Found {len(proportion_list)} sample files")
        reference_file = output_dir / "Reference.npz"

        if reference_file.exists():
            print(f"Reference file already exists: {reference_file}")
            return str(reference_file)
        
        autosome_list = [str(i) for i in range(1, 23)]
        autosome_data = {chromosome: [] for chromosome in autosome_list}
        female_data = []
        male_data = []
        
        for proportion_file in proportion_list:
            data = np.load(proportion_file, allow_pickle=True)
            gender = str(data['gender'])
            
            # Autosomes from all samples
            for chromosome in autosome_list:
                autosome_data[chromosome].append(data[chromosome])
            
            # X from female samples only
            if gender == 'female':
                female_data.append(data['X'])
            
            # Y from male samples only
            if gender == 'male':
                male_data.append(data['Y'])

        reference_dict = {}
        
        # Autosomes: mean from all samples
        for chromosome in autosome_list:
            if autosome_data[chromosome]:
                reference_dict[chromosome] = np.mean(np.stack(autosome_data[chromosome], axis=0), axis=0)
        
        # X: mean from female samples
        if female_data:
            reference_dict['X'] = np.mean(np.stack(female_data, axis=0), axis=0)
        
        # Y: mean from male samples
        if male_data:
            reference_dict['Y'] = np.mean(np.stack(male_data, axis=0), axis=0)

        np.savez_compressed(reference_file, **reference_dict)
        print(f"Saved reference mean to: {reference_file}")
        return str(reference_file)

    def calculate_ratio(self, test_file, reference_file, output_dir):
        """Calculate linear ratio (test/reference) using only bins where reference > 0."""
        test_data = np.load(test_file)
        reference_data = np.load(reference_file)
        test_name = Path(test_file).stem.replace('_proportion', '_ratio')
        ratio_file = output_dir / f"{test_name}.npz"

        if ratio_file.exists():
            print(f"Ratio file already exists: {ratio_file}")
            return str(ratio_file)
        
        ratio_dict = {}
        for chromosome in self.chromosome_list:
            test_ratios = test_data[chromosome]
            reference_ratios = reference_data[chromosome]

            ratios_out = np.full_like(test_ratios, 0.0)
            valid_mask = reference_ratios > 0
            ratios_out[valid_mask] = (test_ratios[valid_mask] / reference_ratios[valid_mask])
            ratio_dict[chromosome] = ratios_out

        np.savez_compressed(ratio_file, **ratio_dict)
        print(f"Saved ratio to: {ratio_file}")
        return str(ratio_file)

    def recalculate_ratio(self, normalized_file, ratio_file, reference_file, output_dir, aberration_threshold):
        """Recalculate log2 ratio using aberration masking and scaling, aligning with new masking semantics.
        """
        normalized_data = np.load(normalized_file)
        ratio_data = np.load(ratio_file)
        reference_data = np.load(reference_file)
        name = Path(normalized_file).stem
        out_file = Path(output_dir) / f"{name.replace('_normalized', '_log2Ratio')}.npz"

        if out_file.exists():
            print(f"Recalculated ratio file already exists: {out_file}")
            return str(out_file)
        
        autosome_list = [str(i) for i in range(1, 23)]
        # 1) Aberration masks from linear ratios; only for autosomes
        aberration_mask = {}
        for chromosome in autosome_list:
            valid_bins = reference_data[chromosome] > 0
            aberration_bins = np.abs(ratio_data[chromosome] - 1.0) > aberration_threshold
            if np.count_nonzero(valid_bins) == 0:
                aberration_mask[chromosome] = np.zeros_like(aberration_bins, dtype=bool)
                continue
            fraction = np.count_nonzero(aberration_bins & valid_bins) / np.count_nonzero(valid_bins)
            if fraction > 0.5:
                aberration_bins[:] = True
            aberration_mask[chromosome] = aberration_bins

        # 2) Global scale across autosomes using valid (reference>0) and non-aberrant bins
        sum_test = 0.0
        sum_reference = 0.0
        for chromosome in autosome_list:
            include = (reference_data[chromosome] > 0) & (~aberration_mask[chromosome])
            sum_test += np.sum(normalized_data[chromosome][include])
            sum_reference += np.sum(reference_data[chromosome][include])
        scale = (sum_test / sum_reference) if sum_reference > 0 else 1.0

        # 3) Totals per chromosome (autosomes): replace aberrant bins with mean*scale
        total_normalized = 0.0
        total_per_chromosome = {chromosome: 0.0 for chromosome in autosome_list}
        for chromosome in autosome_list:
            reference_proportion = reference_data[chromosome]
            aberration_bins = aberration_mask[chromosome]

            adjusted = normalized_data[chromosome].copy()
            adjusted[aberration_bins] = reference_proportion[aberration_bins] * scale
            chromosome_total = np.sum(adjusted[adjusted >= 0])
            total_per_chromosome[chromosome] = chromosome_total
            total_normalized += chromosome_total

        total_exclude = {chromosome: total_normalized - total_per_chromosome.get(chromosome, 0.0) for chromosome in autosome_list}
        total_exclude["X"], total_exclude["Y"] = total_normalized, total_normalized

        # 4) Recompute test proportions using adjusted totals (denominators)
        proportion_dict = {}
        for chromosome in self.chromosome_list:
            denom = total_exclude.get(chromosome, total_normalized)
            proportion_dict[chromosome] = (normalized_data[chromosome] / denom * self.bin_size)

        # 5) Compute log2 ratio against reference; invalid -> -10.0
        ratio_dict = {}
        for chromosome in self.chromosome_list:
            test_proportion = proportion_dict[chromosome]
            reference_proportion = reference_data[chromosome]
            out = np.full_like(test_proportion, -10.0)
            valid = (test_proportion > 0) & (reference_proportion > 0)
            out[valid] = np.log2(test_proportion[valid] / reference_proportion[valid])
            
            # Y chromosome: subtract 1 (equivalent to dividing by 2)
            if chromosome == 'Y':
                out[valid] -= 1.0
            
            ratio_dict[chromosome] = out

        np.savez_compressed(out_file, **ratio_dict)
        print(f"Saved recalculated log2 ratio to: {out_file}")
        return str(out_file)