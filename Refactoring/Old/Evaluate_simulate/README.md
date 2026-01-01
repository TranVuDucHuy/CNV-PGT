# Hướng Dẫn Sử Dụng Pipeline Mô Phỏng và Đánh Giá CNV

Tài liệu này mô tả cách sử dụng các script Python để mô phỏng dữ liệu CNV (Copy Number Variation) và đánh giá kết quả từ các thuật toán khác nhau.

## 📁 Cấu Trúc Thư Mục

```
simulate/                          # Thư mục gốc (workspace root)
├── simulate_1chr.py               # Script mô phỏng
├── convert.py                     # Script chuẩn hóa dữ liệu
├── eval_2.py                      # Script đánh giá kết quả
├── summary.py                     # Script tổng hợp thống kê
├── plot_2.py                      # Script vẽ violin plots
├── line_chart.py                  # Script vẽ line charts
├── samplesList.txt                # Danh sách mẫu
│
├── experiment_data/
│   ├── original_bam/              # BAM gốc (input cho simulate_1chr.py)
│   │   └── *.bam                  # Các file BAM gốc
│   │
│   ├── 30/, 50/, 100/             # Kết quả thí nghiệm với % mosaic khác nhau
│   │   ├── raw/                   # Dữ liệu thô (input cho convert.py)
│   │   │   ├── bluefuse/
│   │   │   │   └── <exp>/         # Kết quả BlueFuse cho mỗi thí nghiệm
│   │   │   ├── baseline/
│   │   │   │   └── <exp>/         # Kết quả Baseline cho mỗi thí nghiệm
│   │   │   ├── wisecondorx/
│   │   │   │   └── <exp>/         # Kết quả WisecondorX cho mỗi thí nghiệm
│   │   │   ├── simulate_bam/
│   │   │   │   └── <exp>/         # BAM đã mô phỏng và stats.tsv
│   │   │   └── groundtruth/       # Ground truth gốc
│   │   │       └── <sample_id>/
│   │   │
│   │   ├── norm/                  # Dữ liệu đã chuẩn hóa (output của convert.py)
│   │   │   └── <exp>/
│   │   │       └── <sample_id>/   # Tất cả segments chuẩn hóa
│   │   │
│   │   ├── result/                # Kết quả đánh giá (output của eval_2.py)
│   │   │   └── <exp>-<algo>-<gt>.tsv
│   │   │
│   │   ├── summary/               # Thống kê tổng hợp (output của summary.py)
│   │   │   ├── mean.tsv
│   │   │   ├── absolute.tsv
│   │   │   └── relative.tsv
│   │   │
│   │   └── plot/                  # Biểu đồ violin (output của plot_2.py)
│   │       └── <exp>-<field>.png
│
└── line_chart/                    # Line charts (output của line_chart.py)
    └── *.png
```

## 🔧 Các Script và Chức Năng

### 1. simulate_1chr.py - Mô Phỏng CNV

**Mục đích**: Tạo BAM file mô phỏng với CNV (Gain/Loss) trên từng NST riêng biệt.

**Chức năng**:

- Lấy BAM gốc từ `experiment_data/original_bam/`
- Tạo mô phỏng Loss (L) hoặc Gain (G) với % mosaic cụ thể
- Xóa/giữ reads ngẫu nhiên trên nhiễm sắc thể đích
- Tạo các thư mục output: `<chr>-<type>-<mosaic>` (ví dụ: `1-L-30`, `2-G-30`)
- Mỗi thư mục chứa BAM đã mô phỏng và file `stats.tsv`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TẠI thư mục gốc /simulate/
# Chạy với đường dẫn đến thư mục chứa BAM gốc
python simulate_1chr.py experiment_data/original_bam
```

**Output**:

- Tạo thư mục: `1-L-30/`, `1-G-30/`, `2-L-30/`, ... `22-G-30/`
- Mỗi thư mục chứa:
  - `*.bam`: BAM files đã mô phỏng
  - `*.bam.bai`: Index files
  - `stats.tsv`: Thống kê tỷ lệ reads giữ lại

**Lưu ý**:

- Script xử lý song song 7 chromosomes cùng lúc
- Mỗi chromosome tạo 2 scenarios: Loss (30%) và Gain (30%)
- Tổng cộng tạo 44 thư mục (22 chromosomes × 2 types)

---

### 2. convert.py - Chuẩn Hóa Dữ Liệu

**Mục đích**: Chuyển đổi segments từ các thuật toán khác nhau về định dạng thống nhất.

**Chức năng**:

- Đọc kết quả từ `raw/bluefuse/`, `raw/baseline/`, `raw/wisecondorx/`, `raw/groundtruth/`
- Tạo ground truth điều chỉnh dựa trên `stats.tsv` từ `raw/simulate_bam/`
- Chuẩn hóa định dạng về: `Chromosome, Start, End, Copy Number`
- Copy scatter charts từ các thuật toán
- Lưu tất cả vào `norm/<exp>/<sample_id>/`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TRONG thư mục experiment_data/<mosaic>/
# Ví dụ: để convert dữ liệu 30%

cd /mnt/d/lab/experiment/simulate/experiment_data/30

# Chạy convert với file danh sách mẫu
python ../../convert.py ../../samplesList.txt

# KHÔNG chạy từ thư mục gốc, vì script cần thư mục raw/ ở cùng cấp
```

**Vị trí tương đối quan trọng**:

```
experiment_data/30/           # <-- Phải chạy TẠI ĐÂY
├── raw/                      # Script tìm ./raw/
│   ├── bluefuse/
│   ├── baseline/
│   ├── wisecondorx/
│   ├── simulate_bam/         # Chứa stats.tsv
│   └── groundtruth/
└── norm/                     # Script tạo ./norm/
```

**Output**:

- `norm/<exp>/<sample_id>/`
  - `<sample_id>_groundtruth_bf_segments.tsv`
  - `<sample_id>_groundtruth_2_segments.tsv`
  - `<sample_id>_baseline_segments.tsv`
  - `<sample_id>_wisecondorx_segments.tsv`
  - `<sample_id>_*_scatterChart.png/jpg`

---

### 3. eval_2.py - Đánh Giá Kết Quả

**Mục đích**: So sánh kết quả của các thuật toán với ground truth.

**Chức năng**:

- Đọc segments từ `norm/<exp>/<sample_id>/`
- Tính Deviation, Squared Deviation, Relative Deviation
- So sánh cho từng thuật toán (baseline, wisecondorx) với từng ground truth
- Lưu kết quả vào `result/`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TRONG thư mục experiment_data/<mosaic>/
cd /mnt/d/lab/experiment/simulate/experiment_data/30

# Chạy eval cho tất cả experiments
python ../../eval_2.py

# Hoặc chỉ đánh giá một số experiments cụ thể
python ../../eval_2.py 1-L-30 1-G-30 2-L-30
```

**Vị trí tương đối**:

```
experiment_data/30/           # <-- Phải chạy TẠI ĐÂY
├── norm/                     # Script đọc từ ./norm/
│   └── <exp>/<sample_id>/
└── result/                   # Script tạo ./result/
```

**Output**:

- `result/<exp>-<algo>-<gt>.tsv` (ví dụ: `1-L-30-baseline-groundtruth_2.tsv`)
- Mỗi file chứa: Sample, Deviation, Squared Deviation, Relative Deviation

**Metrics**:

- **Deviation**: `algo_value - gt_value` (cho Gain) hoặc `-algo_value + gt_value` (cho Loss)
- **Squared Deviation**: `Deviation²`
- **Relative Deviation**: `Deviation / gt_value`

---

### 4. summary.py - Tổng Hợp Thống Kê

**Mục đích**: Tính toán các chỉ số thống kê tổng hợp từ kết quả đánh giá.

**Chức năng**:

- Đọc kết quả từ `result/`
- Tính Mean Absolute Deviation, Mean Squared Deviation, Mean Absolute Relative Deviation
- Tính quantiles (20%, 40%, 60%, 80%) của Absolute Deviation
- Phân bố Relative Deviation theo các khoảng giá trị
- Lưu thống kê vào `summary/`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TRONG thư mục experiment_data/<mosaic>/
cd /mnt/d/lab/experiment/simulate/experiment_data/30

# Chạy summary
python ../../summary.py
```

**Vị trí tương đối**:

```
experiment_data/30/           # <-- Phải chạy TẠI ĐÂY
├── result/                   # Script đọc từ ./result/
│   └── *.tsv
└── summary/                  # Script tạo ./summary/
```

**Output**:

- `summary/mean.tsv`: Giá trị trung bình các metrics
- `summary/absolute.tsv`: Quantiles của Absolute Deviation
- `summary/relative.tsv`: Phân bố samples theo khoảng Relative Deviation

---

### 5. plot_2.py - Vẽ Violin Plots

**Mục đích**: Tạo biểu đồ violin-box kết hợp để trực quan hóa phân bố metrics.

**Chức năng**:

- Đọc dữ liệu từ `result/`
- Vẽ half-violin (bên trái) + half-box (bên phải)
- So sánh 4 tổ hợp: (baseline+GT_2, wisecondorx+GT_2, baseline+GT_BF, wisecondorx+GT_BF)
- Màu sắc: lightblue (baseline), lightgreen (wisecondorx)
- Lưu plots vào `plot/`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TRONG thư mục experiment_data/<mosaic>/
cd /mnt/d/lab/experiment/simulate/experiment_data/30

# Chạy plotting
python ../../plot_2.py
```

**Vị trí tương đối**:

```
experiment_data/30/           # <-- Phải chạy TẠI ĐÂY
├── result/                   # Script đọc từ ./result/
│   └── *.tsv
└── plot/                     # Script tạo ./plot/
```

**Output**:

- `plot/<exp>-Relative Deviation.png`
- Một biểu đồ cho mỗi experiment với Relative Deviation field

---

### 6. line_chart.py - Vẽ Line Charts So Sánh

**Mục đích**: Tạo line charts so sánh kết quả giữa các mức độ mosaic (30%, 50%, 100%).

**Chức năng**:

- Đọc `summary/mean.tsv` từ cả 3 thư mục (30/, 50/, 100/)
- Vẽ line charts theo chromosome (1-22)
- So sánh 6 đường: 3 mức mosaic × 2 thuật toán
- Màu sắc: red/cyan (100%), orange/blue (50%), yellow/purple (30%)
- Lưu charts vào `line_chart/`

**Cách sử dụng**:

```bash
# ⚠️ QUAN TRỌNG: Phải chạy TẠI thư mục gốc /simulate/
cd /mnt/d/lab/experiment/simulate

# Chạy line chart
python line_chart.py
```

**Vị trí tương đối**:

```
simulate/                     # <-- Phải chạy TẠI ĐÂY
├── line_chart.py
├── experiment_data/          # Script đọc từ ./experiment_data/
│   ├── 30/summary/mean.tsv
│   ├── 50/summary/mean.tsv
│   └── 100/summary/mean.tsv
└── line_chart/               # Script tạo ./line_chart/
```

**Output**:

- `line_chart/GT_2_G_Absolute_Relative.png`
- `line_chart/GT_2_L_Absolute_Relative.png`
- `line_chart/GT_BF_G_Absolute_Relative.png`
- `line_chart/GT_BF_L_Absolute_Relative.png`

---

## 🔄 Workflow Hoàn Chỉnh

### Bước 1: Mô phỏng dữ liệu

```bash
cd /mnt/d/lab/experiment/simulate
python simulate_1chr.py experiment_data/original_bam
```

→ Tạo thư mục `1-L-30/`, `1-G-30/`, ..., `22-G-30/` với BAM files và stats.tsv

### Bước 2: Di chuyển dữ liệu mô phỏng

```bash
# Di chuyển output của simulate_1chr.py vào raw/simulate_bam/
# Ví dụ cho mosaic 30%
mkdir -p experiment_data/30/raw/simulate_bam/
mv 1-L-30/ experiment_data/30/raw/simulate_bam/
mv 1-G-30/ experiment_data/30/raw/simulate_bam/
# ... (lặp lại cho tất cả experiments)
```

### Bước 3: Chuẩn bị raw data

```bash
# Đảm bảo cấu trúc thư mục đúng:
# experiment_data/30/raw/
#   ├── bluefuse/<exp>/       # Kết quả BlueFuse
#   ├── baseline/<exp>/       # Kết quả Baseline
#   ├── wisecondorx/<exp>/    # Kết quả WisecondorX
#   ├── simulate_bam/<exp>/   # Từ bước 1
#   └── groundtruth/<sample>/ # Ground truth gốc
```

### Bước 4: Chuẩn hóa dữ liệu

```bash
cd /mnt/d/lab/experiment/simulate/experiment_data/30
python ../../convert.py ../../samplesList.txt
```

→ Tạo thư mục `norm/` với segments chuẩn hóa

### Bước 5: Đánh giá kết quả

```bash
cd /mnt/d/lab/experiment/simulate/experiment_data/30
python ../../eval_2.py
```

→ Tạo thư mục `result/` với các file TSV chứa metrics

### Bước 6: Tổng hợp thống kê

```bash
cd /mnt/d/lab/experiment/simulate/experiment_data/30
python ../../summary.py
```

→ Tạo thư mục `summary/` với mean.tsv, absolute.tsv, relative.tsv

### Bước 7: Vẽ violin plots

```bash
cd /mnt/d/lab/experiment/simulate/experiment_data/30
python ../../plot_2.py
```

→ Tạo thư mục `plot/` với các biểu đồ PNG

### Bước 8: Vẽ line charts (sau khi có data từ 3 mức mosaic)

```bash
# Lặp lại bước 4-7 cho experiment_data/50/ và experiment_data/100/
# Sau đó chạy line chart
cd /mnt/d/lab/experiment/simulate
python line_chart.py
```

→ Tạo thư mục `line_chart/` với các line charts so sánh

---
