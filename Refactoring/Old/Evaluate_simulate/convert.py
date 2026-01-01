#!/usr/bin/env python3
from argparse import ArgumentParser
import os, sys, shutil, re
from pathlib import Path
import pandas as pd

RAW_BLUE = os.path.join("raw", "bluefuse")
RAW_BASE = os.path.join("raw", "baseline")
RAW_SIM = os.path.join("raw", "simulate_bam")
RAW_WISE = os.path.join("raw", "wisecondorx")
RAW_GROUNDTRUTH = os.path.join("raw", "groundtruth")
OUT_BASE = "norm"

NEW_EXPERIMENTS = [
    "1-G-30", "1-L-30",
    "2-G-30", "2-L-30",
    "3-G-30", "3-L-30",
    "4-G-30", "4-L-30",
    "5-G-30", "5-L-30",
    "6-G-30", "6-L-30",
    "7-G-30", "7-L-30",
    "8-G-30", "8-L-30",
    "9-G-30", "9-L-30",
    "10-G-30", "10-L-30",
    "11-G-30", "11-L-30",
    "12-G-30", "12-L-30",
    "13-G-30", "13-L-30",
    "14-G-30", "14-L-30",
    "15-G-30", "15-L-30",
    "16-G-30", "16-L-30",
    "17-G-30", "17-L-30",
    "18-G-30", "18-L-30",
    "19-G-30", "19-L-30",
    "20-G-30", "20-L-30",
    "21-G-30", "21-L-30",
    "22-G-30", "22-L-30"
]

def get_ratio_from_stats(sample_id, exp_name):
    stats_path = os.path.join(RAW_SIM, exp_name, "stats.tsv")
    ratio = None
    if os.path.exists(stats_path):
        try:
            stats_df = pd.read_csv(stats_path, sep="\t")
            sample_col = 'sample'
            if sample_col in stats_df.columns and 'ratio_kept_on_deleted_chrom' in stats_df.columns:
                for _, r in stats_df.iterrows():
                    if sample_id in str(r[sample_col]):
                        try:
                            ratio = float(r['ratio_kept_on_deleted_chrom'])
                        except (ValueError, TypeError):
                            ratio = None
                        break
        except Exception as e:
            print(f"  Failed reading stats for {exp_name}: {e}")
            ratio = None
    if ratio is None:
        print(f"  No ratio found for sample {sample_id} in stats of {exp_name}. Using 0.0 (no adjustment).")
        ratio = 0.0
    return ratio

# A. sample_list
def read_sample_ids(file_path: Path) -> list[str]:
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        raise SystemExit(f"Sample list file not found: {file_path}")
    except OSError as e:
        raise SystemExit(f"Error reading sample list file '{file_path}': {e}")
    out = []
    pattern = r"^([A-Z0-9]+)-([A-Z0-9-]+)-([A-Z0-9]+)$"

    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        match = re.match(pattern, s)
        flowcell_id, cycle_id, embryo_id = match.groups()
        out.append((s, flowcell_id, cycle_id, embryo_id))
    return out


# B1. convert groundtruth
def convert_segment_groundtruth_bf(sample_id, exp_name):
    parts = exp_name.split("-")
    chrom, types = parts[0], parts[1]
    ratio = get_ratio_from_stats(sample_id, exp_name)

    src = os.path.join(RAW_GROUNDTRUTH, sample_id, f"{sample_id}_segments.txt")
    if not os.path.isfile(src):
        print(f"  No source file found for sample {sample_id} at {src}. Skipping.")
        return
    df = pd.read_csv(src, sep="\t", dtype=str)

    df2 = df[["Chromosome", "Start", "End", "Copy #"]].copy()
    df2.columns = ["Chromosome", "Start", "End", "Copy#"]
    df2['Chromosome'] = df2['Chromosome'].astype(int)
    df2 = df2[df2['Chromosome'].between(1,22)]

    def adjust(row):
        c = int(row["Chromosome"])
        orig = float(row["Copy#"])
        try:
            targ = int(chrom) if chrom != "34" else None
        except ValueError:
            return orig

        if chrom == "34":
            if c == 3:
                return orig / ratio if types[0] == "G" else orig * ratio
            elif c == 4:
                return orig / ratio if types[-1] == "G" else orig * ratio
        elif c == targ:
            return orig / ratio if types == "G" else orig * ratio
        return orig

    df2["Copy Number"] = df2.apply(adjust, axis=1)
    out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sample_id}_groundtruth_bf_segments.tsv")
    df2_out = df2[["Chromosome", "Start", "End", "Copy Number"]]
    df2_out.to_csv(out_path, sep="\t", index=False)

def convert_segment_groundtruth_2(sample_id, exp_name):
    parts = exp_name.split("-")
    chrom_part, types = parts[0], parts[1]
    ratio = get_ratio_from_stats(sample_id, exp_name)

    hg19_lengths = {
        1: 249250621, 2: 243199373, 3: 198022430, 4: 191154276, 5: 180915260,
        6: 171115067, 7: 159138663, 8: 146364022, 9: 141213431, 10: 135534747,
        11: 135006516, 12: 133851895, 13: 115169878, 14: 107349540, 15: 102531392,
        16: 90354753, 17: 81195210, 18: 78077248, 19: 59128983, 20: 63025520,
        21: 48129895, 22: 51304566
    }

    data = []
    if chrom_part == "34":
        if len(types) != 2:
            raise ValueError(f"For '34' experiments, expected two type letters, got: {types}")
        for c in range(1, 23):
            if c == 3:
                cn = 2.0 / ratio if types[0] == 'G' else 2.0 * ratio
            elif c == 4:
                cn = 2.0 / ratio if types[1] == 'G' else 2.0 * ratio
            else:
                cn = 2.0
            data.append({"Chromosome": c, "Start": 1, "End": hg19_lengths[c], "Copy Number": cn})
    else:
        targ = int(chrom_part)
        for c in range(1, 23):
            cn = (2.0 / ratio if types == 'G' else 2.0 * ratio) if c == targ else 2.0
            data.append({"Chromosome": c, "Start": 1, "End": hg19_lengths[c], "Copy Number": cn})

    df_out = pd.DataFrame(data, columns=["Chromosome", "Start", "End", "Copy Number"])
    out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sample_id}_groundtruth_2_segments.tsv")
    df_out.to_csv(out_path, sep="\t", index=False)
    return df_out

# B2. convert segment
def convert_segment_bluefuse(sample_id, exp_name):
    src_dir = os.path.join(RAW_BLUE, exp_name)
    if not os.path.isdir(src_dir):
        return
    candidates = [f for f in os.listdir(src_dir) if sample_id in f and f.endswith("bluefuse.tsv")]
    if not candidates:
        return
    src = os.path.join(src_dir, candidates[0])
    df = pd.read_csv(src, sep="\t", dtype=str)

    df2 = df[["Chromosome", "Start", "End", "Copy #"]].copy()
    df2.columns = ["Chromosome", "Start", "End", "Copy Number"]
    df2['Chromosome'] = df2['Chromosome'].astype(int)
    df2 = df2[df2['Chromosome'].between(1,22)]

    out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sample_id}_bluefuse_segments.tsv")
    df2.to_csv(out_path, sep="\t", index=False)

def convert_segment_baseline(sample_id, exp_name):
    src_dir = os.path.join(RAW_BASE, exp_name)
    if not os.path.isdir(src_dir):
        return
    candidates = [f for f in os.listdir(src_dir) if sample_id in f and f.endswith("_S93_segments.csv")]
    if not candidates:
        return
    src = os.path.join(src_dir, candidates[0])
    df = pd.read_csv(src, sep=",", dtype=str)

    df2 = df[["chrom", "loc.start", "loc.end", "seg.mean"]].copy()
    df2.columns = ["Chromosome", "Start", "End", "seg.mean"]
    df2['Chromosome'] = df2['Chromosome'].astype(int)
    df2 = df2[df2['Chromosome'].between(1,22)]
    
    df2["Copy Number"] = df2["seg.mean"].astype(float).apply(lambda x: 2 ** (x + 1))

    out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sample_id}_baseline_segments.tsv")
    df2_out = df2[["Chromosome", "Start", "End", "Copy Number"]]
    df2_out.to_csv(out_path, sep="\t", index=False)

def convert_segment_wisecondorx(sample_id, exp_name):
    src_dir = os.path.join(RAW_WISE, exp_name, sample_id)
    bed_path = os.path.join(src_dir, f"{sample_id}_segments.bed")

    if not os.path.isfile(bed_path):
        return
    df = pd.read_csv(bed_path, sep='\t', dtype=str)
    if not set(['chr','start','end','ratio']).issubset(df.columns):
        return
    df2 = df[['chr','start','end','ratio']].copy()
    
    def _norm_chr(x):
        if str(x) == 'X':
            return 23
        if str(x) == 'Y':
            return 24
        return int(str(x))
    
    df2['Chromosome'] = df2['chr'].apply(_norm_chr)
    df2 = df2[df2['Chromosome'].between(1,22)]
    df2['Copy Number'] = (2 ** (df2['ratio'].astype(float) + 1))

    out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{sample_id}_wisecondorx_segments.tsv")
    df_out = df2[['Chromosome','start','end','Copy Number']].copy()
    df_out.columns = ['Chromosome','Start','End','Copy Number']
    df_out.to_csv(out_path, sep='\t', index=False)

# B3. convert chart
def convert_chart_bluefuse(sample_id, flow_cell_id, cycle_id, embryo_id, exp_name):
    src_dir = os.path.join(RAW_BLUE, exp_name)
    if not os.path.isdir(src_dir):
        return
    # find jpg containing -{embryo_id}-
    for f in os.listdir(src_dir):
        if embryo_id in f and flow_cell_id in f and cycle_id in f and f.lower().endswith('.jpg'):
            src = os.path.join(src_dir, f)
            out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
            os.makedirs(out_dir, exist_ok=True)
            dst = os.path.join(out_dir, f"{sample_id}_bluefuse_scatterChart.jpg")
            shutil.copyfile(src, dst)
            return

def convert_chart_baseline(sample_id, exp_name):
    src_dir = os.path.join(RAW_BASE, exp_name)
    if not os.path.isdir(src_dir):
        return
    for f in os.listdir(src_dir):
        if sample_id in f and (f.endswith('_S93_scatterChart.png') or f.endswith('_S93_scatterChart.jpg')):
            src = os.path.join(src_dir, f)
            out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
            os.makedirs(out_dir, exist_ok=True)
            # preserve extension
            ext = os.path.splitext(f)[1]
            dst = os.path.join(out_dir, f"{sample_id}_baseline_scatterChart{ext}")
            shutil.copyfile(src, dst)
            return

def convert_chart_wisecondorx(sample_id, exp_name):
    src_dir = Path(RAW_WISE) / exp_name / sample_id
    if not src_dir.exists():
        return
    for p in src_dir.rglob('genome_wide.png'):
        out_dir = os.path.join(OUT_BASE, exp_name, f"{sample_id}")
        os.makedirs(out_dir, exist_ok=True)
        dst = os.path.join(out_dir, f"{sample_id}_wisecondorx_scatterChart.png")
        shutil.copyfile(str(p), dst)
        break

# C. Main flow: process experiments sequentially
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("sample_list", help="Path to a text file containing Sample IDs, one per line")
    args = parser.parse_args()
    sample_ids = read_sample_ids(Path(args.sample_list))

    exps = NEW_EXPERIMENTS
    for exp in exps:
        for sample_id, flowcell_id, cycle_id, embryo_id in sample_ids:
            convert_segment_groundtruth_bf(sample_id, exp)
            convert_segment_groundtruth_2(sample_id, exp)
            # convert_segment_bluefuse(sample_id, exp)
            convert_segment_baseline(sample_id, exp)
            convert_segment_wisecondorx(sample_id, exp)
            # convert_chart_bluefuse(sample_id, flowcell_id, cycle_id, embryo_id, exp)
            convert_chart_baseline(sample_id, exp)
            convert_chart_wisecondorx(sample_id, exp)
    print('Done.')
