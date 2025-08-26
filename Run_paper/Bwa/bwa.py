import multiprocessing
import subprocess
import sys
import time
import os
import glob

INPUT_FASTQ_DIR = "/mnt/g/Lab/SelfDevelop/BWA/Fastq"
REFERENCE_FASTA = "/mnt/g/Lab/SelfDevelop/BWA/Reference/hg19.p13.plusMT.no_alt_analysis_set.fa"
OUTPUT_DIR_BAM = "/mnt/g/Lab/SelfDevelop/BWA/Bam"
CLEANUP_INTERMEDIATE_FILES = True

THREADS = multiprocessing.cpu_count()

def run_command(command):
    print(f"Current command: {' '.join(command)}")
    try:
        subprocess.run(command, check = True, stderr = subprocess.STDOUT, stdout = sys.stdout)
        print(f"--- DONE ---\n")
    except FileNotFoundError:
        print(f"'{command[0]}' doesn't exist.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed, exit code: {e.returncode}")
        sys.exit(1)

def find_fastq_files(input_dir):
    fastq_pattern = "*.fastq"
    pattern_path = os.path.join(input_dir, fastq_pattern)
    fastq_files = glob.glob(pattern_path)
    fastq_files.sort()
    return fastq_files

def run_bwa_mem(command, output_sam_file):
    try:
        with open(output_sam_file, 'w') as f_out:
            process = subprocess.run(command, check = True, stdout = f_out, stderr = subprocess.PIPE, text = True)
            if process.stderr:
                print("BWA-MEM INFO:")
                print(process.stderr, file = sys.stderr)
    except FileNotFoundError:
        print(f"{command[0]} doesn't exist!")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"BWA-MEM failed, exit code: {e.returncode}")
        if e.stderr:
            print(e.stderr, file = sys.stderr)
        sys.exit(1)

def format_bam(input_bam, output_bam, base_name, cleanup):
    head_file = os.path.join(OUTPUT_DIR_BAM, f"{base_name}_head.txt")
    cmd = f"samtools view -H {input_bam} | head -n 26 > {head_file}"
    subprocess.run(cmd, shell=True, check=True)

    with open("tail.txt", "r", encoding="utf-8") as f:
        data = f.read()

    data = data.replace("SAMPLE", base_name)

    tail_file = os.path.join(OUTPUT_DIR_BAM, f"{base_name}_tail.txt")

    with open(tail_file, "w", encoding="utf-8") as f:
        f.write(data)

    header_file = os.path.join(OUTPUT_DIR_BAM, f"{base_name}_header.txt")
    with open(header_file, "w", encoding="utf-8") as fout:
        with open(head_file, "r", encoding="utf-8") as f1:
            fout.write(f1.read())
        with open(tail_file, "r", encoding="utf-8") as f2:
            fout.write(f2.read())

    cmd = f"samtools reheader -P {header_file} {input_bam} > {output_bam}"
    subprocess.run(cmd, shell=True, check=True)

    if cleanup:
        try:
            if os.path.exists(head_file):
                os.remove(head_file)
            if os.path.exists(tail_file):
                os.remove(tail_file)
            if os.path.exists(header_file):
                os.remove(header_file)

        except OSError as e:
            print(f"Can't delete temp files: {e}")

def process_single_fastq(input_fastq, output_dir, reference_fasta, threads, cleanup):
    os.makedirs(output_dir, exist_ok = True)
    base_name = os.path.splitext(os.path.basename(input_fastq))[0]

    sam_file = os.path.join(output_dir, f"{base_name}.sam")
    fixmate_bam_file = os.path.join(output_dir, f"{base_name}.fixmate.bam")
    final_bam_file = os.path.join(output_dir, f"{base_name}.bam")
    temp_sort_prefix = os.path.join(output_dir, f"{base_name}_temp_sort")
    sorted_bam_file = os.path.join(output_dir, f"{base_name}.sorted.bam")
    sorted_index_bam_file = os.path.join(output_dir, f"{base_name}.sorted.bam.bai")

    try:
        index_file_check = f"{reference_fasta}.bwt"
        if not os.path.exists(index_file_check):
            cmd = ["bwa", "index", "-p", reference_fasta, reference_fasta]
            run_command(cmd)

        rg_header = f"@RG\\tID:{base_name}\\tPL:ILLUMINA\\tSM:{base_name}"
        cmd = ["bwa", "mem", "-M", "-t", str(threads), "-R", rg_header, reference_fasta, input_fastq]
        run_bwa_mem(cmd, sam_file)

        cmd = ["samtools", "fixmate", "-O", "bam", sam_file, fixmate_bam_file]
        run_command(cmd)

        cmd = ["samtools", "sort",
               "-T", temp_sort_prefix,
               "-O", "bam",
               "-@", str(threads),
               "-o", sorted_bam_file,
               fixmate_bam_file]
        run_command(cmd)

        cmd = ["samtools", "index", sorted_bam_file]
        run_command(cmd)

        primary24_bam = os.path.join(output_dir, f"{base_name}.primary24.bam")

        keep_chrs = ["chrMT"] + ["chr" + str(i) for i in range(1, 23)] + ["chrX", "chrY"]
        cmd = ["samtools", "view", "-b", sorted_bam_file] + keep_chrs
        with open(primary24_bam, "wb") as fout:
            subprocess.run(cmd, check=True, stdout=fout)

        raw_hdr = subprocess.check_output(["samtools", "view", "-H", primary24_bam], text=True)
        allowed = set(keep_chrs)
        new_lines = []
        for ln in raw_hdr.splitlines():
            if ln.startswith("@SQ"):
                sn = None
                for f in ln.split("\t"):
                    if f.startswith("SN:"):
                        sn = f[3:]
                        break
                if sn not in allowed:
                    continue
                ln = ln.replace("SN:chrMT", "SN:chrM")
                if "AS:" not in ln:
                    ln = ln + "\tAS:hg19"
                new_lines.append(ln)
            else:
                new_lines.append(ln)
        hdr = "\n".join(new_lines) + "\n"

        with open(final_bam_file, "wb") as fout:
            proc = subprocess.Popen(
                ["samtools", "reheader", "-", primary24_bam],
                stdin=subprocess.PIPE, stdout=fout, text=True
            )
            proc.communicate(hdr)

        final_format_bam_file = os.path.join(OUTPUT_DIR_BAM, f"{base_name}_S93.bam")

        format_bam(final_bam_file, final_format_bam_file, base_name, cleanup = CLEANUP_INTERMEDIATE_FILES)

        cmd = ["samtools", "index", final_format_bam_file]
        run_command(cmd)

        if cleanup:
            try:
                if os.path.exists(sam_file):
                    os.remove(sam_file)
                if os.path.exists(fixmate_bam_file):
                    os.remove(fixmate_bam_file)
                if os.path.exists(sorted_bam_file):
                    os.remove(sorted_bam_file)
                if os.path.exists(primary24_bam):
                    os.remove(primary24_bam)
                if os.path.exists(sorted_index_bam_file):
                    os.remove(sorted_index_bam_file)
                if os.path.exists(final_bam_file):
                    os.remove(final_bam_file)
            except OSError as e:
                print(f"Can't delete temp files: {e}")

        return True
    except Exception as e:
        print(f"ERROR! {base_name}: {e}")
        return False

def main_pipeline():
    start_time = time.time()
    total_time = 0

    if not os.path.exists(INPUT_FASTQ_DIR):
        print(f"Folder FASTQ doesn't exist: {INPUT_FASTQ_DIR}")
        sys.exit(1)
    if not os.path.exists(REFERENCE_FASTA):
        print(f"File FASTA doesn't exist: {REFERENCE_FASTA}")
        sys.exit(1)

    fastq_files = find_fastq_files(INPUT_FASTQ_DIR)
    if not fastq_files:
        print(f"ERROR! Can't find any files in folder FASTQ: {INPUT_FASTQ_DIR}")
        sys.exit(1)

    successful_count = 0
    failed_files = []
    for i, fastq_file in enumerate(fastq_files, 1):
        success = process_single_fastq(input_fastq = fastq_file,
                                       output_dir = OUTPUT_DIR_BAM,
                                       reference_fasta = REFERENCE_FASTA,
                                       threads = THREADS,
                                       cleanup = CLEANUP_INTERMEDIATE_FILES)
        if success:
            successful_count += 1
        else:
            failed_files.append(os.path.basename(fastq_file))

        single_time = time.time() - start_time
        print(f"#{i}: {single_time:.2f} giây ({single_time / 60:.2f} phút)")

        total_time += single_time
        start_time = time.time()

    print(f"TIME: {total_time:.2f} giây ({total_time / 60:.2f} phút)")

    print(f"Total files: {len(fastq_files)}")
    print(f"Failed files: {len(failed_files)}")

if (__name__ == "__main__"):
    main_pipeline()