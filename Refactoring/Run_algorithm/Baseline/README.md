# Autorun - Baseline Pipeline Automation

## Mô tả

`autorun.py` là công cụ tự động hóa để chạy pipeline Baseline trên nhiều bộ dữ liệu test. Script này sẽ tự động:
- Xử lý tuần tự các test set trong thư mục `simulate_bam`
- Chạy `baseline.py` cho từng test set
- Ghi lại thời gian chạy của mỗi experiment
- Tổ chức outputs vào các thư mục riêng biệt

## Cấu trúc thư mục yêu cầu

```
baseline_parallel/
├── autorun.py          # Script tự động hóa
├── Code/
│   ├── baseline.py     # Pipeline chính (REQUIRED)
│   ├── estimate.py
│   ├── filter.py
│   ├── normalize.py
│   ├── segment.py
│   └── ...
└── Job<N>/             # Thư mục job (ví dụ: Job1, Job2, ...)
    ├── simulate_bam/   # Chứa các test set (thư mục con)
    │   ├── test1/      # Mỗi thư mục là một test set
    │   ├── test2/
    │   └── ...
    ├── Run/
    │   ├── Input/
    │   │   └── Test/   # Dữ liệu test tạm thời
    │   ├── Output/     # Output tạm thời
    │   ├── Prepare/    # Dữ liệu chuẩn bị (filter, GC-content, ...)
    │   └── Temporary/
    └── Output/         # Kết quả cuối cùng (được tạo tự động)
        ├── test1/
        ├── test2/
        └── ...
```

## Cách chạy

### 1. Chuẩn bị thư mục Job

Đảm bảo thư mục Job đã có:
- `simulate_bam/`: Chứa các thư mục con, mỗi thư mục là một test set
- `Run/Input/Test/`: Thư mục trống (sẽ được sử dụng tạm thời)
- `Run/Prepare/`: Chứa các file chuẩn bị (Base_filter.npz, GC-content.npz, ...)
- `Run/Temporary/`: Thư mục tạm

### 2. Chạy autorun

```bash
python3 autorun.py <job_directory>
```

**Ví dụ:**

```bash
# Chạy với Exe
python3 autorun.py Exe
```
## Output

### 1. Kết quả phân tích

Mỗi test set sẽ có thư mục riêng trong `<job_dir>/Output/`:

```
Output/
├── test1/
│   ├── sample1_log2Ratio.npz
│   ├── sample1_segments.csv
│   └── ...
├── test2/
│   └── ...
└── ...
```

### 2. Thời gian chạy

File `run_times.tsv` ghi lại thời gian xử lý:

```
Experiment      Runtime (second)
test1           125.456789
test2           138.234567
test3           142.891234
```

## Lưu ý quan trọng

1. **File baseline.py bắt buộc**: Script yêu cầu `Code/baseline.py` phải tồn tại
2. **Dữ liệu được di chuyển**: Files trong `simulate_bam/<test_set>` sẽ được di chuyển tạm thời vào `Run/Input/Test/`, sau đó được khôi phục lại
3. **Xử lý tuần tự**: Các test set được xử lý lần lượt, không song song
4. **Thư mục Temporary/Test**: Được xóa trước khi xử lý mỗi test set mới
5. **Output được di chuyển**: Kết quả từ `Run/Output/` được di chuyển vào `Output/<test_set>/`