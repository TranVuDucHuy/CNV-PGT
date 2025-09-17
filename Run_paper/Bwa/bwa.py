import subprocess
import sys
import time
import os
import glob
import argparse

FASTQ_PATTERN = "*.fastq*"

def run_command(command):
    print(f"Current command: {' '.join(map(str, command))}")
    try:
        subprocess.run(command, check=True, stderr=subprocess.STDOUT, stdout=sys.stdout)
        print(f"--- DONE ---\n")
    except FileNotFoundError:
        print(f"'{command[0]}' doesn't exist.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed, exit code: {e.returncode}")
        sys.exit(1)

def find_fastq_files(input_dir):
    pattern_path = os.path.join(input_dir, FASTQ_PATTERN)
    fastq_files = glob.glob(pattern_path)
    fastq_files.sort()
    return fastq_files

def run_bwa_mem(command, output_sam_file):
    try:
        with open(output_sam_file, 'w') as f_out:
            process = subprocess.run(command, check=True, stdout=f_out, stderr=subprocess.PIPE, text=True)
            if process.stderr:
                print("BWA-MEM INFO:")
                print(process.stderr, file=sys.stderr)
    except FileNotFoundError:
        print(f"{command[0]} doesn't exist!")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"BWA-MEM failed, exit code: {e.returncode}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)

def format_bam(input_bam, output_bam, base_name, output_dir_bam, cleanup):
    with open("header.txt", "r", encoding="utf-8") as f:
        header = f.read()
    header = header.replace("SAMPLE", base_name)

    header_file = os.path.join(output_dir_bam, f"{base_name}_header.txt")
    with open(header_file, "w", encoding="utf-8") as f:
        f.write(header)

    cmd = f"samtools reheader -P {header_file} {input_bam} > {output_bam}"
    subprocess.run(cmd, shell=True, check=True)

    if cleanup:
        try:
            if os.path.exists(header_file):
                os.remove(header_file)
        except OSError as e:
            print(f"Can't delete temp files: {e}")

def process_single_fastq(input_fastq, output_dir, reference_fasta, threads, min_mapq, filter_flags, bwa_batch, sort_mem, cleanup):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_fastq))[0]

    sam_file = os.path.join(output_dir, f"{base_name}.sam")
    fixmate_bam_file = os.path.join(output_dir, f"{base_name}.fixmate.bam")
    final_bam_file = os.path.join(output_dir, f"{base_name}_S93.bam")
    temp_sort_prefix = os.path.join(output_dir, f"{base_name}_temp_sort")
    sorted_bam_file = os.path.join(output_dir, f"{base_name}.sorted.bam")
    filtered_bam_file = os.path.join(output_dir, f"{base_name}.sorted.q{min_mapq}.bam")
    filtered_bam_index_file = os.path.join(output_dir, f"{base_name}.sorted.q{min_mapq}.bam.bai")

    try:
        index_file_check = f"{reference_fasta}.bwt"
        if not os.path.exists(index_file_check):
            cmd = ["bwa", "index", "-p", reference_fasta, reference_fasta]
            run_command(cmd)

        rg_header = f"@RG\\tID:{base_name}\\tPL:ILLUMINA\\tSM:{base_name}"
        cmd = ["bwa", "mem", "-M", "-K", str(bwa_batch), "-t", str(threads), "-R", rg_header, reference_fasta, input_fastq]
        run_bwa_mem(cmd, sam_file)

        cmd = ["samtools", "fixmate", "-O", "bam", sam_file, fixmate_bam_file]
        run_command(cmd)

        cmd = ["samtools", "sort",
               "-T", temp_sort_prefix,
               "-O", "bam",
               "-@", str(threads),
               "-m", sort_mem,
               "-o", sorted_bam_file,
               fixmate_bam_file]
        run_command(cmd)

        cmd = ["samtools", "view",
               "-b",
               "-@", str(threads),
               "-q", str(min_mapq),
               "-F", str(filter_flags),
               sorted_bam_file]
        with open(filtered_bam_file, "wb") as fout:
            subprocess.run(cmd, check=True, stdout=fout)

        cmd = ["samtools", "index", filtered_bam_file]
        run_command(cmd)

        primary24_bam = os.path.join(output_dir, f"{base_name}.primary24.bam")

        keep_chrs = ["chrMT"] + ["chr" + str(i) for i in range(1, 23)] + ["chrX", "chrY"]
        cmd = ["samtools", "view", "-b", filtered_bam_file] + keep_chrs
        with open(primary24_bam, "wb") as fout:
            subprocess.run(cmd, check=True, stdout=fout)

        format_bam(primary24_bam, final_bam_file, base_name, output_dir, cleanup)

        cmd = ["samtools", "index", final_bam_file]
        run_command(cmd)

        if cleanup:
            try:
                for file in (sam_file, fixmate_bam_file, sorted_bam_file, filtered_bam_file, filtered_bam_index_file, primary24_bam):
                    if os.path.exists(file):
                        os.remove(file)
            except OSError as e:
                print(f"Can't delete temp files: {e}")

        return True
    except Exception as e:
        print(f"ERROR! {base_name}: {e}")
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Create BlueFuse-friendly BAM with MAPQ filter & low-RAM options")
    parser.add_argument("-i", "--input-fastq-dir", help="FASTQ folder")
    parser.add_argument("-r", "--reference-fasta", help="Refer FASTA)")
    parser.add_argument("-o", "--output-dir-bam", help="Output dir")
    parser.add_argument("-t", "--threads", type=int, help="Threads")
    parser.add_argument("-q", "--min-mapq", type=int, help="MAPQ")
    parser.add_argument("-F", "--filter-flags", type=lambda x: int(x, 0), help="Samtools -F flags")
    parser.add_argument("-K", "--bwa-batch", type=int, help="Batch size")
    parser.add_argument("--sort-mem", help="samtools sort -m")
    parser.add_argument("--cleanup", dest="cleanup", action="store_true", default=True, help="Delete temp file")
    parser.add_argument("--no-cleanup", dest="cleanup", action="store_false", help="Don't delete temp file")
    return parser.parse_args()

def main_pipeline():
    start_time = time.time()
    total_time = 0

    args = parse_args()
    if not os.path.exists(args.input_fastq_dir):
        print(f"Folder FASTQ doesn't exist: {args.input_fastqMIN_MAPQ_dir}")
        sys.exit(1)
    if not os.path.exists(args.reference_fasta):
        print(f"File FASTA doesn't exist: {args.reference_fasta}")
        sys.exit(1)
    os.makedirs(args.output_dir_bam, exist_ok=True)

    fastq_files = find_fastq_files(args.input_fastq_dir)
    if not fastq_files:
        print(f"ERROR! Can't find any files in folder FASTQ: {args.input_fastq_dir}")
        sys.exit(1)

    successful_count = 0
    failed_files = []
    for i, fastq_file in enumerate(fastq_files, 1):
        success = process_single_fastq(
            input_fastq = fastq_file,
            output_dir = args.output_dir_bam,
            reference_fasta = args.reference_fasta,
            threads = args.threads,
            min_mapq = args.min_mapq,
            filter_flags = args.filter_flags,
            bwa_batch = args.bwa_batch,
            sort_mem = args.sort_mem,
            cleanup = args.cleanup
        )
        if success:
            successful_count += 1
        else:
            failed_files.append(os.path.basename(fastq_file))

        single_time = time.time() - start_time
        print(f"#{i}: {single_time:.2f} giây ({single_time / 60:.2f} phút)")
        total_time += single_time
        start_time = time.time()

    print(f"TIME: {total_time:.2f} giây ({total_time / 60:.2f} phút)")
    print(f"Total files: {len(fastq_files)} | Failed: {len(failed_files)}")

if __name__ == "__main__":
    main_pipeline()