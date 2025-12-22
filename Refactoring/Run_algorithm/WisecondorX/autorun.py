#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description="Automate WisecondorX runs for multiple test sets.")
    p.add_argument("job_dir", type=Path, help="Job directory containing simulate_bam, Run, and Output subdirectories")
    args = p.parse_args()

    job_dir = args.job_dir.resolve()
    project_root = Path(__file__).resolve().parent

    simulate_root = job_dir / "simulate_bam"
    output_root = job_dir / "Output"
    input_test = job_dir / "Run" / "Input" / "Test"
    tmp_test = job_dir / "Run" / "Temporary" / "Test"
    run_output = job_dir / "Run" / "Output"

    if not (project_root / "wisecondorx.py").exists():
        print(f"[ERROR] Could not find wisecondorx.py in {project_root}")
        sys.exit(1)

    run_times_tsv = job_dir / "run_times.tsv"
    run_times_tsv.parent.mkdir(parents=True, exist_ok=True)
    run_times_tsv.write_text("Experiment\tRuntime (second)\n")

    subs = [p for p in sorted(simulate_root.iterdir()) if p.is_dir()]
    print(f"[INFO] Found {len(subs)} test set(s) in {simulate_root}")

    for i, sub in enumerate(subs, start=1):
        tag = sub.name
        print(f"\n[STEP {i}/{len(subs)}] Processing: {tag}")

        if tmp_test.exists():
            shutil.rmtree(tmp_test)

        moved_files = []
        for f in sorted(sub.iterdir()):
            if f.is_file():
                print(f"  - Moving {f.name} to input test directory")
                shutil.move(str(f), str(input_test / f.name))
                moved_files.append(f.name)

        print(f"  - Running WisecondorX with -o {job_dir / 'Run'}")
        cmd = [sys.executable or "python3", str(project_root / "wisecondorx.py"), "-o", str(job_dir / "Run")]
        start_ns = time.time_ns()
        subprocess.run(cmd, cwd=str(project_root), check=True)
        end_ns = time.time_ns()
        duration_s = (end_ns - start_ns) / 1e9
        with open(run_times_tsv, "a") as fh:
            fh.write(f"{tag}\t{duration_s:.6f}\n")
        print("  - WisecondorX run completed")

        dest = output_root / tag
        dest.mkdir(parents=True, exist_ok=True)
        if run_output.exists():
            for child in sorted(run_output.iterdir()):
                shutil.move(str(child), str(dest / child.name))
        print(f"  - Moved outputs into {dest}")

        for name in moved_files:
            shutil.move(str(input_test / name), str(sub / name))
        print(f"  - Restored {len(moved_files)} input file(s) to {sub}")

    print("\n[DONE] All test sets processed.")


if __name__ == "__main__":
    main()
