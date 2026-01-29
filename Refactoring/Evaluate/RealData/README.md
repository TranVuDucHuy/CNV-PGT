# Đánh giá dữ liệu RealData

## Cài đặt Môi trường

```bash
# Tạo environment mới
conda create -n realdata-env python=3.11 -y

# Cài đặt các gói phân tích
conda install -n realdata-env -c conda-forge pandas numpy matplotlib -y

# Kích hoạt môi trường
conda activate realdata-env
```

## Cấu trúc Thư mục

```
RealData/
├── main.py                      # Script điều phối chính
├── Code/                        # Các bước xử lý
│   ├── merge.py                 # Gom dữ liệu từ các thuật toán
│   ├── evaluate.py              # So sánh với BlueFuse
│   ├── deviation.py             # Tính độ lệch copy number
│   ├── statistic.py             # Thống kê deviation/relative
│   └── plot.py                  # Vẽ biểu đồ phân phối
├── Input/
│   └── {Algorithm ID}/          # Ví dụ: Baseline, BlueFuse, WisecondorX...
│       └── {Experiment ID}/
│           └── {Sample ID}/
│               ├── {Sample ID}_{Algorithm ID}_segments.bed
│               └── {Sample ID}_{Algorithm ID}_scatterChart.*
├── Temporary/
│   └── {Experiment ID}/
│       ├── Merge/               # Dữ liệu segments/scatter đã gom
│       │   └── {Sample ID}/
│       │       ├── {Sample ID}_{Algorithm ID}_segments.bed
│       │       └── {Sample ID}_{Algorithm ID}_scatterChart.*
│       └── Integrate/           # Bảng integrate mỗi thuật toán
│           ├── {Algorithm ID}_autosome_integrate.tsv
│           └── {Algorithm ID}_gonosome_integrate.tsv
├── Output/
│   └── {Experiment ID}/
│       ├── Autosome/
│       │   ├── {Experiment ID}_chrEval_summary.tsv
│       │   ├── {Experiment ID}_chrEval_FP.tsv
│       │   ├── {Experiment ID}_chrEval_FN.tsv
│       │   ├── {Experiment ID}_summary.tsv
│       │   ├── {Experiment ID}_deviation.tsv
│       │   ├── {Experiment ID}_relative.tsv
│       │   └── {Experiment ID}_relative.png
│       └── Gonosome/
└── README.md
```

## Cách Sử Dụng

1. Sao chép toàn bộ thư mục `Output` từ mỗi Algorithm vào `RealData/Input/{Algorithm ID}/` (giữ nguyên cấu trúc bên trong).
2. Tại thư mục `RealData/`, chạy:

```bash
python3 main.py
```

## Quy trình Thực thi

### Bước 1: Quét thí nghiệm

`main.py` thống kê toàn bộ `Experiment ID` xuất hiện trong mọi Algorithm trong `Input/`.

### Bước 2: Gộp dữ liệu

`merge.py` sao chép `*_segments.bed` và `*_scatterChart.*` của mọi Algorithm đối với cùng một Sample vào `Temporary/{Experiment ID}/Merge/{Sample ID}/`

### Bước 3: Đánh giá so với BlueFuse

`evaluate.py`:

- BlueFuse được chọn là ground-truth. Script xác định giới tính dựa trên NST Y và chỉ giữ mẫu nam khi phân tích Gonosome.
- Với từng NST, xác định loại `Gain/Loss/No Change` theo CN và `MOSAIC_THRESHOLD` (0.45):
  - Tính `expected_copy_number` dựa trên NST và giới tính (ví dụ: Autosome = 2.0).
  - Tính tỷ lệ độ dài phân đoạn thuộc mỗi loại và chọn loại có tỷ lệ độ dài cao nhất.
- Xuất các bảng `*_chrEval_summary.tsv`, `*_chrEval_FP.tsv`, `*_chrEval_FN.tsv` theo từng nhóm Autosome/Gonosome.

### Bước 4: Tính độ lệch CN

`deviation.py`:

- Lấy CN của phân đoạn dài nhất cho mỗi NST của từng Algorithm vào `Temporary/{Experiment ID}/Integrate/{Algorithm ID}_{autosome|gonosome}_integrate.tsv`.
- Với mọi Algorithm khác BlueFuse, chỉ tính khi BlueFuse khác expected:
  - `raw = algorithm_value - bluefuse_value`
  - Nếu BlueFuse > expected (Gain): `deviation = raw`
  - Nếu BlueFuse < expected (Loss): `deviation = -raw`
  - `relative = (deviation / bluefuse_value) * 100%`
- Lưu kết quả vào `Output/{Experiment ID}/{ChromosomeType}/{Experiment ID}_summary.tsv`.

### Bước 5: Thống kê

`statistic.py` tạo các bảng:

- `*_deviation.tsv`: Thống kê độ lệch CN cho từng Algorithm (mean, và các dải percentile 20%, 40%, 60%, 80% dựa trên percentiles 10-90%).
- `*_relative.tsv`: Tỉ lệ % độ lệch tương đối nằm trong các khoảng [-10%, -5%), [-5%, 0%), [0%, 5%), [5%, 10%].

### Bước 6: Vẽ biểu đồ

`plot.py` tạo violin + box plot `*_relative.png` cho phân phối độ lệch tương đối của từng thuật toán.
