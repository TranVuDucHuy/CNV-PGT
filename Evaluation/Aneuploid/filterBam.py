#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path
from typing import Dict, List

def parse_args():
    p = argparse.ArgumentParser(description="Lọc & chọn các tệp BAM dựa trên thông tin Cycle-Embryo khớp với các tệp PNG")
    p.add_argument('--bam_root', '-a', required=True, help='Thư mục A: gốc chứa các thư mục con có *.bam')
    p.add_argument('--bam_copy_dir', '-b', required=True, help='Thư mục B: nơi sao chép toàn bộ BAM hợp lệ')
    p.add_argument('--png_root', '-c', required=True, help='Thư mục C: gốc chứa các thư mục con có *.png')
    p.add_argument('--bam_selected_dir', '-d', required=True, help='Thư mục D: nơi di chuyển các BAM có PNG tương ứng (theo Cycle-Embryo)')
    return p.parse_args()

def bam_key(filename: str) -> str:
    # Giả định chắc chắn kết thúc bằng _S93.bam
    base = filename[:-8]  # cắt '_S93.bam'
    parts = base.split('-', 1)
    return parts[1] if len(parts) == 2 else base

def main():
    args = parse_args()
    bam_root = Path(args.bam_root).resolve()
    bam_copy_dir = Path(args.bam_copy_dir).resolve()
    png_root = Path(args.png_root).resolve()
    bam_selected_dir = Path(args.bam_selected_dir).resolve()

    for p in [bam_copy_dir, bam_selected_dir]:
        p.mkdir(parents=True, exist_ok=True)

    # 1. Thu thập & sao chép toàn bộ BAM hợp lệ
    bam_files = [p for p in bam_root.rglob('*.bam') if p.is_file()]
    print(f"[INFO] Tìm thấy {len(bam_files)} tệp .bam trong {bam_root}")

    # Map key (cycle-embryo) -> list path (trong thư mục B sau copy)
    key_to_bams: Dict[str, List[Path]] = {}

    copied_count = 0
    for bam in bam_files:
        key = bam_key(bam.name)
        dest = bam_copy_dir / bam.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bam, dest)
        key_to_bams.setdefault(key, []).append(dest)
        copied_count += 1
    print(f"[INFO] Đã sao chép {copied_count} tệp BAM hợp lệ vào {bam_copy_dir}")

    # 2. Thu thập PNG & đối chiếu
    png_files = [p for p in png_root.rglob('*.png') if p.is_file()]
    print(f"[INFO] Tìm thấy {len(png_files)} tệp .png trong {png_root}")

    moved = 0
    missing_keys = []
    for png in png_files:
        key = png.name[:-4] if png.name.lower().endswith('.png') else png.name
        if not key:
            print(f"[WARN] Không lấy được key từ file PNG: {png.name}")
            continue
        bam_list = key_to_bams.get(key)
        if not bam_list:
            print(f"[MISS] {key}.png")
            missing_keys.append(key)
            continue
        for bam_path in bam_list:
            target = bam_selected_dir / bam_path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            shutil.move(str(bam_path), str(target))
            moved += 1
        del key_to_bams[key]
    print(f"[INFO] Đã di chuyển {moved} tệp BAM phù hợp sang {bam_selected_dir}")
    if missing_keys:
        print(f"[SUMMARY] Số key không tìm thấy BAM: {len(missing_keys)}")

    print("[DONE]")

if __name__ == '__main__':
    main()
