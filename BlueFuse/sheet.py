import os
import shutil
import argparse
import re, pandas as pd
from pathlib import Path

def load_bam(work_directory):
    bam_dir = Path(work_directory) / "Bam"
    bam_file_list = sorted([str(p.name) for p in bam_dir.glob("*.bam")])
    return bam_file_list

def split_name(bam_file_name):
    base_name = os.path.splitext(bam_file_name)[0]
    base_name_wo_S = re.match(r"(.+?)(?:_S\d+)?$", base_name).group(1)
    first, last = base_name_wo_S.find("-"), base_name_wo_S.rfind("-")
    flowcell = base_name_wo_S[:first]
    cycle    = base_name_wo_S[first+1:last]
    embryo   = base_name_wo_S[last+1:]
    return flowcell, cycle, embryo, base_name_wo_S

def create_sample_sheet(work_directory, flowcell_list, cycle_list, embryo_list, name_list, index):
    template_path = Path(work_directory) / "template.csv"
    lines = template_path.read_text(encoding="utf-8").splitlines()
    data_idx = next(i for i, line in enumerate(lines) if line.strip().startswith("[Data]"))
    df = pd.read_csv(template_path, skiprows=data_idx + 1)

    for i in range(data_idx):
        if lines[i].startswith("Flowcell ID"):
            parts = lines[i].split(",")
            parts[1] = flowcell_list[0]
            lines[i] = ",".join(parts)
            break

    output_dir = Path(work_directory) / "Output" / str(index)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = df[df["Sample_ID"].astype(str).str.fullmatch(r"SAMPLE_\d{2}")].index.tolist()
    for name, cycle, embryo, row_index in zip(name_list, cycle_list, embryo_list, rows):
        df.at[row_index, "Sample_ID"] = name
        df.at[row_index, "Cycle_ID"] = cycle
        df.at[row_index, "Embryo_ID"] = embryo
        source_file_path = Path(f"{work_directory}/Bam/{name}_S93.bam")
        shutil.move(str(source_file_path), str(output_dir / source_file_path.name))

    sample_sheet_path = output_dir / "Sample_Sheet.csv"

    with open(sample_sheet_path, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines[:data_idx + 1]) + "\n")
        df.to_csv(f, index=False)

def main():
    parser = argparse.ArgumentParser(
        description = "Create BlueFuse sample sheet"
    )

    parser.add_argument(
        '-w', '--work-directory',
        required = True,
        help = 'Path to work directory'
    )

    parser.add_argument(
        '-t', '--template',
        required = True,
        help = 'Path to template sample sheet'
    )

    args = parser.parse_args()

    bam_file_list = load_bam(work_directory = args.work_directory)

    flowcell_list = []
    cycle_list = []
    embryo_list = []
    name_list = []
    index = 0

    for bam_file in bam_file_list:
        flowcell, cycle, embryo, name = split_name(bam_file)
        if (len(flowcell_list) < 12 and (flowcell in flowcell_list or len(flowcell_list) == 0)):
            flowcell_list.append(flowcell)
            cycle_list.append(cycle)
            embryo_list.append(embryo)
            name_list.append(name)
        else:
            create_sample_sheet(args.work_directory, flowcell_list, cycle_list, embryo_list, name_list, index)
            flowcell_list = []
            cycle_list = []
            embryo_list = []
            name_list = []
            flowcell_list.append(flowcell)
            cycle_list.append(cycle)
            embryo_list.append(embryo)
            name_list.append(name)
            index += 1

    if (len(flowcell_list) > 0):
        create_sample_sheet(args.work_directory, flowcell_list, cycle_list, embryo_list, name_list, index)

if __name__ == "__main__":
    main()