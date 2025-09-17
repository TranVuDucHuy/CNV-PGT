import subprocess
import pandas as pd
import numpy as np
from pathlib import Path


def cbs(ratio_file, temp_dir, bin_size, chromosome_list):

    ratio_name = Path(ratio_file).stem.replace('_ratio', '')
    segments_file = Path(temp_dir) / f"{ratio_name}_segments.csv"
    temp_csv = prepare_cbs_data(ratio_file, ratio_name, temp_dir, bin_size, chromosome_list)
    cbs_script = Path(__file__).parent / "CBS.R"
    command = [
        "Rscript", str(cbs_script),
        "--input", temp_csv,
        "--output", str(segments_file),
        "--sample", ratio_name,
        "--alpha", "0.001",
        "--nperm", "10000"
    ]
    result = subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=True
    )
    print(result.stdout)
    if temp_csv and Path(temp_csv).exists():
        Path(temp_csv).unlink()
    if segments_file.exists():
        return str(segments_file)
    else:
        return None


def prepare_cbs_data(ratio_file, sample_name, temp_dir, bin_size, chromosome_list):

    data = np.load(ratio_file)
    all_data = []
    for chromosome in chromosome_list:
        if chromosome in data.files:
            ratios = data[chromosome]
            num_bins = len(ratios)
            bin_positions = [i * bin_size + bin_size // 2 for i in range(num_bins)]
            for i, ratio in enumerate(ratios):
                if ratio != -2:
                    all_data.append({
                        "sample.name": sample_name,
                        "chrom": chromosome,
                        "maploc": bin_positions[i],
                        "log2_ratio": ratio
                    })
    if not all_data:
        return None
    df = pd.DataFrame(all_data)
    df['chrom_numeric'] = df['chrom'].apply(lambda x: 23 if x == 'X' else (24 if x == 'Y' else int(x)))
    df = df.sort_values(['chrom_numeric', 'maploc']).reset_index(drop=True)
    temp_csv = Path(temp_dir) / f"{sample_name}_cbs_input.csv"
    df.to_csv(temp_csv, index=False)
    return str(temp_csv)