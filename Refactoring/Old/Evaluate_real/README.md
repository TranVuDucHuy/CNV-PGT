# Benchmark - Pipeline Đánh Giá Copy Number Variation

Pipeline này được sử dụng để chuẩn bị, đánh giá và so sánh các kết quả từ ba công cụ phân tích Copy Number Variation (CNV):

- **Baseline**
- **WisecondorX**
- **BlueFuse** (gold standard)

---

## 🔧 Cách Chạy Các Tệp

### 1️⃣ **prepare_eval.py** - Chuẩn Bị Dữ Liệu

**Mục đích:**

- Chuẩn hóa và chuẩn bị dữ liệu từ ba công cụ (Baseline, WisecondorX, BlueFuse)
- Chuyển đổi định dạng file từ các công cụ khác nhau sang định dạng TSV thống nhất
- Chuẩn hóa chromosome (X→23, Y→24; loại bỏ MT, M)
- Tính toán Copy Number từ log2 ratio
- Sao chép plot từ các công cụ

**Cách chạy:**

```bash
python prepare_eval.py <baseline_dir> <wisecondorx_dir> <bluefuse_dir> <output_dir>
```

**Tham số:**

- `<baseline_dir>`: Thư mục chứa kết quả Baseline (file `*_S93_segments.csv`)
- `<wisecondorx_dir>`: Thư mục chứa kết quả WisecondorX (subfolder với `*_segments.bed`)
- `<bluefuse_dir>`: Thư mục chứa kết quả BlueFuse (subfolder với file segments)
- `<output_dir>`: Thư mục output, sẽ tạo subfolder cho mỗi mẫu

**Output:**

```
output_dir/
├── sample_1/
│   ├── sample_1_baseline_segments.tsv
│   ├── sample_1_wisecondorx_segments.tsv
│   ├── sample_1_bluefuse_segments.tsv
│   ├── sample_1.png (baseline plot)
│   ├── sample_1_wisecondorx_scatterChart.png
│   └── sample_1.jpg (bluefuse plot)
├── sample_2/
│   └── ...
```

**Ví dụ:**

```bash
python prepare_eval.py ./Raw/Baseline ./Raw/WisecondorX ./Raw/BlueFuse ./Result
```

---

### 2️⃣ **chrEval.py** - Đánh Giá Theo Chromosome

**Mục đích:**

- Đánh giá hiệu suất của Baseline và WisecondorX so với BlueFuse (gold standard)
- Tính toán TP (True Positive), FP (False Positive), FN (False Negative), TN (True Negative)
- Tính toán các metric: Precision, Recall, Specificity, Accuracy
- So sánh loại chromosome (Gain, Loss, No Change) giữa các công cụ

**Cách chạy:**

```bash
python chrEval.py -i <input_dir> [--gain-thr GAIN_THR] [--loss-thr LOSS_THR]
```

**Tham số:**

- `-i, --input_dir`: Thư mục chứa các sample (output từ `prepare_eval.py`)
- `--gain-thr`: Ngưỡng Copy Number cho Gain (mặc định: 2.45)
- `--loss-thr`: Ngưỡng Copy Number cho Loss (mặc định: 1.55)

**Output:**

- `chr_eval_baseline.tsv`: Kết quả đánh giá Baseline vs BlueFuse
- `chr_eval_wisecondorx.tsv`: Kết quả đánh giá WisecondorX vs BlueFuse
- `chrEval.log`: Chi tiết các false positive/false negative

**Ví dụ:**

```bash
python chrEval.py -i ./Result --gain-thr 2.45 --loss-thr 1.55
```

**Output columns:**
| Column | Ý nghĩa |
|--------|---------|
| sample_id | Mã mẫu |
| TP | True Positives (22 chr) |
| FP | False Positives |
| FN | False Negatives |
| TN | True Negatives |
| Precision | TP / (TP + FP) |
| Recall | TP / (TP + FN) |
| Specificity | TN / (TN + FP) |
| Accuracy | (TP + TN) / (TP + FP + FN + TN) |

---

### 3️⃣ **integrate.py** - Tích Hợp Kết Quả

**Mục đích:**

- Tích hợp kết quả Copy Number từ các công cụ
- Trích xuất segment dài nhất cho mỗi chromosome
- Tạo bảng tóm tắt Copy Number cho tất cả mẫu và công cụ

**Cách chạy:**

```bash
python integrate.py <input_dir> <output_dir>
```

**Tham số:**

- `<input_dir>`: Thư mục chứa các sample (output từ `prepare_eval.py`)
- `<output_dir>`: Thư mục output

**Output:**

```
output_dir/
├── baseline_integrated.tsv
├── wisecondorx_integrated.tsv
└── bluefuse_integrated.tsv
```

**Cấu trúc output file:**
| sample_id | 1 | 2 | ... | 22 |
|-----------|---|---|-----|-----|
| sample_1 | 1.95 | 2.10 | ... | 2.05 |
| sample_2 | 2.45 | 1.55 | ... | 2.00 |

(Giá trị là Copy Number của segment dài nhất trên mỗi chromosome)

**Ví dụ:**

```bash
python integrate.py ./Result ./Integrated
```

---

### 4️⃣ **summary.py** - Tóm Tắt Và Phân Tích

**Mục đích:**

- Tạo bảng tóm tắt tất cả các chỉ số (deviation, relative deviation, integrated predictions)
- Phân tích phân bố deviation theo percentile
- Phân tích relative deviation theo bin (khoảng)

**Cách chạy:**

```bash
python summary.py <input_dir> <output_dir> <integrated_dir>
```

**Tham số:**

- `<input_dir>`: Thư mục chứa file deviation/relative (thường là `Deviation/`)
- `<output_dir>`: Thư mục output
- `<integrated_dir>`: Thư mục chứa file integrated (output từ `integrate.py`)

**Output:**

```
output_dir/
├── summary.tsv
│   ├── Sample: Mã mẫu
│   ├── Chromosome: Nhiễm sắc thể
│   ├── BlueFuse CN: Copy number từ BlueFuse
│   ├── Baseline CN: Copy number từ Baseline
│   ├── WisecondorX CN: Copy number từ WisecondorX
│   ├── Baseline Deviation: Độ lệch Baseline
│   ├── WisecondorX Deviation: Độ lệch WisecondorX
│   ├── Baseline Relative Deviation: Độ lệch tương đối Baseline
│   └── WisecondorX Relative Deviation: Độ lệch tương đối WisecondorX
│
├── deviation_thresholds.tsv
│   ├── Percentile (20%, 40%, 60%, 80%)
│   ├── Baseline Deviation Threshold
│   └── WisecondorX Deviation Threshold
│
└── relative_deviation_distribution.tsv
    ├── Bin: Khoảng giá trị (-0.12, -0.09], ...
    ├── Baseline Count, Baseline %
    └── WisecondorX Count, WisecondorX %
```

**Ví dụ:**

```bash
python summary.py ./Deviation ./Summary ./Integrated
```

---

### 5️⃣ **plot.py** - Vẽ Biểu Đồ

**Mục đích:**

- Vẽ các biểu đồ so sánh deviation và relative deviation giữa Baseline và WisecondorX
- Sử dụng violin plot và box plot để hiển thị phân bố
- Tạo plot để so sánh với các ngưỡng cố định

**Cách chạy:**

```bash
python plot.py <deviation_files_dir> <output_dir>
```

**Tham số:**

- `<deviation_files_dir>`: Thư mục chứa file deviation TSV
- `<output_dir>`: Thư mục lưu plot

**Output:**

- `deviation_boxplot.png`: Box plot so sánh deviation
- `relative_deviation_boxplot.png`: Box plot so sánh relative deviation
- Các file plot bổ sung khác

**Ví dụ:**

```bash
python plot.py ./Deviation ./Plot
```

---

## 📊 Quy Trình Hoàn Chỉnh

Chạy toàn bộ pipeline từ đầu:

```bash
# Bước 1: Chuẩn bị dữ liệu
python prepare_eval.py ./Raw/Baseline ./Raw/WisecondorX ./Raw/BlueFuse ./Result

# Bước 2: Đánh giá theo chromosome
python chrEval.py -i ./Result

# Bước 3: Tích hợp kết quả
python integrate.py ./Result ./Integrated

# Bước 4: Tóm tắt và phân tích
python summary.py ./Deviation ./Summary ./Integrated

# Bước 5: Vẽ biểu đồ
python plot.py ./Deviation ./Plot
```

---

## 📁 Cấu Trúc Thư Mục Mong Đợi

```
benchmark/
├── prepare_eval.py
├── chrEval.py
├── integrate.py
├── summary.py
├── plot.py
├── README.md
│
├── Raw/                          # Input dữ liệu gốc
│   ├── Baseline/                 # Kết quả Baseline
│   │   ├── sample1_S93_segments.csv
│   │   └── sample1_S93_scatterChart.png
│   ├── WisecondorX/              # Kết quả WisecondorX
│   │   ├── sample1/
│   │   │   ├── sample1_segments.bed
│   │   │   └── sample1.plots/
│   │   │       └── genome_wide.png
│   │   └── ...
│   └── BlueFuse/                 # Kết quả BlueFuse
│       ├── sample1/
│       │   ├── sample1_bluefuse_segments.tsv
│       │   └── sample1.jpg
│       └── ...
│
├── Result/                       # Output từ prepare_eval.py
│   ├── sample1/
│   ├── sample2/
│   └── ...
│
├── Integrated/                   # Output từ integrate.py
│   ├── baseline_integrated.tsv
│   ├── wisecondorx_integrated.tsv
│   └── bluefuse_integrated.tsv
│
├── Deviation/                    # File deviation gốc (nếu có)
│   ├── deviation-1-baseline-bluefuse.tsv
│   ├── relative-1-baseline-bluefuse.tsv
│   └── ...
│
├── Summary/                      # Output từ summary.py
│   ├── summary.tsv
│   ├── deviation_thresholds.tsv
│   └── relative_deviation_distribution.tsv
│
└── Plot/                         # Output từ plot.py
    ├── deviation_boxplot.png
    └── relative_deviation_boxplot.png
```

---

## 📝 Ghi Chú Quan Trọng

1. **File input phải có format chuẩn:**

   - Baseline: CSV với cột `chrom`, `loc.start`, `loc.end`, `seg.mean`
   - WisecondorX: BED với cột `chr`, `start`, `end`, `ratio`
   - BlueFuse: TSV với cột `Chromosome`, `Start`, `End`, `Copy Number`

2. **Chromosome được hỗ trợ:** 1-22 (Autosomes). Chromosome X, Y, MT sẽ bị chuyển đổi hoặc loại bỏ.

3. **Các file log:**

   - `chrEval.log`: Chi tiết False Positive/False Negative theo sample

---
