#!/usr/bin/env python3
import os, sys, random
import pysam
import multiprocessing

# Usage: python simulate_1chr.py <input_dir>
# Example: python simulate_1chr.py BAM      # will run for autosomes 1..22
# Creates folders: <chr>-L-50, <chr>-G-50

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simulate_1chr.py <input_dir>", file=sys.stderr)
        sys.exit(1)

    in_dir = sys.argv[1]
    chromosomes = [str(i) for i in range(1, 23)]
    scenarios = [("L", 30), ("G", 30)]
    bam_files = [f for f in os.listdir(in_dir) if f.endswith("_S93.bam")]
    bam_files.sort()

    # Process chromosomes in parallel using a pool of workers.
    # We distribute chromosomes evenly across `n_workers` groups and run each group in a separate process.
    n_workers = 7

    def process_group(group, in_dir, bam_files, scenarios):
        """Process a list of chromosome labels sequentially (runs inside a worker process)."""
        for chr_label in group:
            # Accept both "1" and "chr1" in BAMs by checking ref names once per file
            def is_target(ref_name):
                if ref_name is None:
                    return False
                rn = ref_name.lower()
                cl = chr_label.lower()
                return rn == cl or rn == f"chr{cl}" or (cl.startswith("chr") and rn == cl.replace("chr", "", 1))

            for typ, mosaic in scenarios:
                out_dir = os.path.join(os.getcwd(), f"{chr_label}-{typ}-{mosaic}")
                os.makedirs(out_dir, exist_ok=True)
                m = mosaic / 100.0
                p_keep_L = (2.0 - m) / 2.0
                p_keep_G = 2.0 / (2.0 + m)

                stats_rows = []  # (sample, total_reads, deleted_on_chr)

                for bf in bam_files:
                    in_path = os.path.join(in_dir, bf)
                    base = os.path.basename(bf)
                    out_path = os.path.join(out_dir, base)
                    total_reads = 0
                    orig_target = 0
                    kept_target = 0
                    orig_off = 0
                    kept_off = 0

                    with pysam.AlignmentFile(in_path, "rb") as fin:
                        with pysam.AlignmentFile(out_path, "wb", header=fin.header) as fout:
                            for read in fin.fetch(until_eof=True):
                                total_reads += 1
                                if read.is_unmapped:
                                    fout.write(read)
                                    continue
                                ref_name = fin.get_reference_name(read.reference_id)

                                if typ == "L":
                                    target = is_target(ref_name)
                                    if target:
                                        orig_target += 1
                                        if random.random() < p_keep_L:
                                            kept_target += 1
                                            fout.write(read)
                                        else:
                                            continue
                                    else:
                                        orig_off += 1
                                        kept_off += 1
                                        fout.write(read)
                                else:  # typ == "G"
                                    target = is_target(ref_name)
                                    if not target:
                                        orig_off += 1
                                        if random.random() < p_keep_G:
                                            kept_off += 1
                                            fout.write(read)
                                        else:
                                            continue
                                    else:
                                        # target chromosome is kept in Gain
                                        orig_target += 1
                                        kept_target += 1
                                        fout.write(read)

                    # Create BAM index for the output
                    pysam.index(out_path)
                    if typ == "L":
                        denom = orig_target
                        numer = kept_target
                    else:
                        denom = orig_off
                        numer = kept_off
                    ratio = (numer / denom) if denom > 0 else 0.0
                    stats_rows.append((base, total_reads, ratio))

                # Write per-scenario TSV summary
                stats_path = os.path.join(out_dir, "stats.tsv")
                with open(stats_path, "w") as sf:
                    sf.write("sample\ttotal_reads\tratio_kept_on_deleted_chrom\n")
                    for s, t, r in stats_rows:
                        sf.write(f"{s}\t{t}\t{r:.6f}\n")

    # Build groups of chromosomes distributed across workers
    groups = [[] for _ in range(n_workers)]
    for i, ch in enumerate(chromosomes):
        groups[i % n_workers].append(ch)

    # Filter out any empty groups
    tasks = [(g, in_dir, bam_files, scenarios) for g in groups if g]

    if len(tasks) == 1:
        # Single task: run inline (avoid multiprocessing overhead)
        process_group(*tasks[0])
    else:
        with multiprocessing.Pool(processes=min(n_workers, len(tasks))) as pool:
            pool.starmap(process_group, tasks)
