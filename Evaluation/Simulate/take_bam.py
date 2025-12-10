from pathlib import Path
from shutil import copy2
from argparse import ArgumentParser

# Usage:
#   python take_bam.py <sample_list.txt> <input_dir> <output_dir>

def read_sample_ids(file_path: Path) -> list[str]:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise SystemExit(f"Sample list file not found: {file_path}")
    except OSError as e:
        raise SystemExit(f"Error reading sample list file '{file_path}': {e}")

    sample_ids = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        sample_ids.append(s)
    return sample_ids


def main():
    parser = ArgumentParser()
    parser.add_argument("sample_list", help="Path to a text file containing Sample IDs, one per line")
    parser.add_argument("input_dir", help="Root directory to search for BAM files")
    parser.add_argument("out_dir", help="Output directory to copy BAM files into")

    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    sample_ids = read_sample_ids(Path(args.sample_list))
    out_dir.mkdir(parents=True, exist_ok=True)

    for sid in sample_ids:
        for bam_path in input_dir.rglob(f"{sid}_S93.bam"):
            copy2(bam_path, out_dir / bam_path.name)
            print(f"Copied {bam_path} -> {out_dir / bam_path.name}")

if __name__ == "__main__":
    main()
