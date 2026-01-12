# Đánh giá dữ liệu SimulatedData

## Cài đặt Môi trường

```bash
# Tạo environment mới
conda create -n simulateddata-env python=3.11 -y

# Cài đặt các gói phân tích
conda install -n simulateddata-env -c conda-forge pandas numpy matplotlib -y

# Kích hoạt môi trường
conda activate simulateddata-env
```

## Cấu trúc Thư mục

```
SimulatedData/
├── main.py                           # Script điều phối chính
├── Code/                             # Các bước xử lý
│   ├── merge.py                      # Gom dữ liệu từ các thuật toán
│   ├── deviation.py                  # Tạo ground truth và tính độ lệch
│   ├── statistic.py                  # Thống kê deviation/relative/mean
│   ├── plot.py                       # Vẽ biểu đồ phân phối
│   └── utils.py                      # Hàm tiện ích
├── Input/
│   ├── Metadata/                     # File BED và TSV từ Simulate
│   │   ├── {Experiment ID}.bed       # Định nghĩa regions
│   │   └── {Experiment ID}.tsv       # Scale ratios
│   ├── GroundTruth/                  # BlueFuse segments của mẫu gốc
│   │   └── {Sample ID}/
│   │       └── {Sample ID}_bluefuse_segments.bed
│   └── {Algorithm ID}/               # Kết quả từ các thuật toán
│       └── {Experiment ID}/
│           └── {Sample ID}/
│               ├── {Sample ID}_{Algorithm ID}_segments.bed
│               └── {Sample ID}_{Algorithm ID}_scatterChart.*
├── Temporary/
│   └── {Experiment ID}/
│       ├── Merge/                    # Dữ liệu segments/scatter đã gom
│       │   └── {Sample ID}/
│       │       ├── {Sample ID}_{Algorithm ID}_segments.bed
│       │       └── {Sample ID}_{Algorithm ID}_scatterChart.*
│       ├── Integrate/                # Bảng copy number cho mỗi region
│       │   ├── GT2_integrate.tsv     # Ground truth dựa trên baseline=2
│       │   ├── GTBF_integrate.tsv    # Ground truth dựa trên BlueFuse
│       │   └── {Algorithm ID}_integrate.tsv
│       └── Deviation/
│           ├── GT2/                  # Kết quả so với GT2
│           │   ├── {Algorithm ID}_deviation.tsv
│           │   └── {Algorithm ID}_relative.tsv
│           └── GTBF/                 # Kết quả so với GTBF
├── Output/
│   └── {Experiment ID}/
│       ├── GT2/                      # Kết quả so với GT2
│       │   ├── {Experiment ID}_mean.tsv
│       │   ├── {Experiment ID}_deviation.tsv
│       │   ├── {Experiment ID}_relative.tsv
│       │   └── region_{Region ID}_relative.png
│       └── GTBF/                     # Kết quả so với GTBF
└── README.md
```

## Cách Sử dụng

1. Chuẩn bị dữ liệu:

   - Sao chép tệp `.bed` và `.tsv` trong `Simulate/Output/Metadata/` vào `SimulatedData/Input/Metadata/`.
   - Sao chép các thư mục `{Sample ID}/` của mẫu gốc (chưa mô phỏng) từ `BlueFuse/Output/` vào `Input/GroundTruth/`.
   - Sao chép toàn bộ thư mục `Output` từ mỗi Algorithm (Baseline, WisecondorX, ...) vào `Input/{Algorithm ID}/` (giữ nguyên cấu trúc bên trong).

2. Chạy script:

```bash
python3 main.py
```

## Quy trình Thực thi

### Bước 1: Quét thí nghiệm

`main.py` quét tất cả các thí nghiệm có cặp file `.bed` và `.tsv` trong `Input/Metadata/`.

### Bước 2: Gộp dữ liệu

`merge.py` sao chép `*_segments.bed` và `*_scatterChart.*` của mọi Algorithm cho cùng một Sample vào `Temporary/{Experiment ID}/Merge/{Sample ID}/`.

### Bước 3: Tạo bảng integrate

`deviation.py` tạo các bảng `integrate.tsv` chứa CN của từng region lưu vào `Temporary/{Experiment ID}/Integrate/`:

1. Ground Truth GT2

- Giả định CN của mỗi region là 2.0.
- Tính `expected_cn = scale_ratio * 2.0` cho từng region, trong đó `scale_ratio` lấy từ file `.tsv` do `Simulate` tạo ra.

2. Ground Truth GTBF

- Lấy CN từ BlueFuse segments của **mẫu gốc** (chưa mô phỏng) trong `Input/GroundTruth/`.
- Tính `expected_cn = scale_ratio * base_cn` cho từng region, trong đó `base_cn` là CN của segment overlap nhiều nhất với region đó.

3. Các Algorithm

- Đọc tệp `*_segments.bed` của từng Algorithm.
- Với mỗi region, lấy CN của segment overlap nhiều nhất với region đó.

### Bước 4: Tính độ lệch

`deviation.py` tính độ lệch giữa Algorithm và ground truth cho từng region:

- **Deviation**:
  - Nếu region là Gain (`type = 'G'`): `deviation = algorithm_cn - groundtruth_cn`
  - Nếu region là Loss (`type = 'L'`): `deviation = groundtruth_cn - algorithm_cn`
- **Relative**: `relative = (deviation / groundtruth_cn) * 100%`

Kết quả lưu trong `Temporary/{Experiment ID}/Deviation/{GT Type}/`:

- `{Algorithm ID}_deviation.tsv`: Giá trị lệch tuyệt đối
- `{Algorithm ID}_relative.tsv`: Tỉ lệ % lệch

### Bước 5: Thống kê

`statistic.py` tạo 3 bảng thống kê:

1. Mean Statistics (`*_mean.tsv`)

Cho mỗi thuật toán và từng region:

- `meanAbsoluteDeviation`: Trung bình độ lệch tuyệt đối
- `meanAbsoluteRelative`: Trung bình tỉ lệ % lệch tương đối
- `meanSquaredDeviation`: Trung bình bình phương độ lệch

2. Deviation Statistics (`*_deviation.tsv`)

Cho mỗi thuật toán và từng region:

- `mean`: Giá trị trung bình của deviation
- `20%`, `40%`, `60%`, `80%`: Các khoảng phân phối dựa trên percentiles 10-90

3. Relative Statistics (`*_relative.tsv`)

Cho mỗi thuật toán và từng region, đếm tỉ lệ mẫu có độ lệch tương đối nằm trong các khoảng:

- `[-10%, -5%)`
- `[-5%, 0%)`
- `[0%, 5%)`
- `[5%, 10%]`

### Bước 6: Vẽ biểu đồ

`plot.py` tạo biểu đồ kết hợp half-violin + boxplot cho từng region:

- File output: `region_{Region ID}_relative.png`
- Hiển thị phân phối độ lệch tương đối (%) của từng thuật toán
- Violin plot ở bên trái (phân phối), boxplot ở bên phải (thống kê tứ phân vị)
