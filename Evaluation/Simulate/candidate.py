#!/usr/bin/env python3
"""
Parse BlueFuse bin files for multiple samples and compute deviation statistics using pandas.
Usage: python candidate.py /path/to/A [--output candidate.tsv]
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Union

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute deviation stats from BlueFuse bin files")
    p.add_argument("input_dir", help="Directory A containing sample subdirectories")
    p.add_argument("--output", "-o", default=None, help="Output TSV path (default: candidate.tsv in current working directory)")
    return p.parse_args()


def compute_stats_series(dev_s: pd.Series) -> Dict[str, float]:
    max_abs = float(dev_s.abs().max())
    sumsq = float(dev_s.pow(2).sum())
    abs_mean = float(abs(dev_s.mean()))
    return {"max_abs": max_abs, "sumsq": sumsq, "abs_mean": abs_mean}


def process_file_df(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", usecols=["BIN COPY #", "CHROMOSOME"], dtype={"BIN COPY #": float, "CHROMOSOME": int})
    df = df.rename(columns={"BIN COPY #": "copy", "CHROMOSOME": "chrom"})
    df["dev"] = df["copy"] - 2.0
    return df[["chrom", "dev"]]


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(2)

    # Default output in current working directory
    out_path = args.output if args.output else os.path.join(os.getcwd(), "candidate.tsv")

    header = [
        "SampleID",
        "MAX AUTOSOME",
        "SUM AUTOSOME",
        "MEAN AUTOSOME",
    ]
    for i in [1, 2, 3, 4]:
        header.extend([f"MAX CHR{i}", f"SUM CHR{i}", f"MEAN CHR{i}"])

    records: List[Dict[str, Union[float, str]]] = []

    for entry in sorted(os.listdir(input_dir)):
        sample_dir = os.path.join(input_dir, entry)
        if not os.path.isdir(sample_dir):
            continue
        sample_id = entry
        # strictly require file named '<SampleID>_bluefuse_bins.tsv'
        fname = f"{sample_id}_bluefuse_bins.tsv"
        bluefuse_file = os.path.join(sample_dir, fname)
        if not os.path.isfile(bluefuse_file):
            # skip directories without file
            continue
        try:
            df = process_file_df(bluefuse_file)
        except Exception as e:
            print(f"Warning: failed to process {bluefuse_file}: {e}", file=sys.stderr)
            continue

        # autosomes 1..22 combined
        autosome_df = df[(df["chrom"] >= 1) & (df["chrom"] <= 22)]
        autosome_stats = compute_stats_series(autosome_df["dev"])

        rec: Dict[str, Union[float, str]] = {
            "SampleID": sample_id,
            "MAX AUTOSOME": autosome_stats["max_abs"],
            "SUM AUTOSOME": autosome_stats["sumsq"],
            "MEAN AUTOSOME": autosome_stats["abs_mean"],
        }

        for c in [1, 2, 3, 4]:
            sub = df[df["chrom"] == c]
            stats = compute_stats_series(sub["dev"])
            rec[f"MAX CHR{c}"] = stats["max_abs"]
            rec[f"SUM CHR{c}"] = stats["sumsq"]
            rec[f"MEAN CHR{c}"] = stats["abs_mean"]

        records.append(rec)

    # write output
    if records:
        out_df = pd.DataFrame.from_records(records)
        # enforce column order
        out_df = out_df.reindex(columns=header)
    else:
        out_df = pd.DataFrame(columns=header)

    out_df.to_csv(out_path, sep="\t", index=False, float_format="%.6f")
    print(f"Wrote {len(records)} samples to {out_path}")


if __name__ == "__main__":
    main()
