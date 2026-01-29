# Công cụ mô phỏng CNV

## Cài đặt Môi trường

```bash
# Cài đặt pysam
pip install pysam
```

## Cấu trúc Thư mục

```
Simulate/
├── simulate.py                     # Script chính
├── Input/
│   ├── Original/                   # BAM gốc (Input)
│   │   ├── {Sample ID}.bam
│   │   └── ...
│   └── Metadata/                   # BED định nghĩa experiment
│       ├── {Experiment ID}.bed
│       └── ...
├── Output/                         # Thư mục đầu ra (tạo tự động)
│   ├── {Experiment ID}/            # Chứa các file BAM đã mô phỏng
│   │   ├── {Sample ID}.bam
│   │   └── ...
│   └── Metadata/                   # Chứa kết quả phân tích
│       ├── {Experiment ID}.tsv     # Bảng tỷ lệ scale ratios
│       └── {Experiment ID}.bed     # File BED gốc được copy sang
└── README.md                       # Tệp này
```

## Định dạng File BED

File BED trong `Input/Metadata/` cần có đủ 6 cột sau:

1.  `chrom`: Tên nhiễm sắc thể (số nguyên thuộc [1, 24]).
2.  `chromStart`: Vị trí bắt đầu.
3.  `chromEnd`: Vị trí kết thúc.
4.  `region`: ID của vùng (số nguyên bắt đầu lần lượt: 1, 2, ...).
5.  `type`: Loại biến đổi ('G' cho Gain, 'L' cho Loss).
6.  `mosaic`: Tỷ lệ mosaic (số thực thuộc [0, 1]).

Ví dụ:

```
1    10000   20000   1   G   1.0
2    50000   60000   2   L   0.5
```

## Cách Sử dụng

1.  Chuẩn bị dữ liệu:

    - Đặt tất cả các file `{Sample ID}.bam` gốc cần mô phỏng vào thư mục `Input/Original/`.
    - Đặt các file `{Experiment ID}.bed` định nghĩa các vùng CNV vào `Input/Metadata/`. Tên file BED sẽ được dùng làm tên Experiment.

2.  Chạy script:

    ```bash
    python3 simulate.py
    ```

## Quy trình Thực thi

### Bước 1: Chuẩn bị dữ liệu

- Đọc file `{Experiment ID}.bed` để xác định các vùng CNV cần mô phỏng.
- Tính toán `expected_copy_number` cho từng vùng dựa trên loại (Gain/Loss) và tỷ lệ mosaic.

### Bước 2: Tính toán xác suất giữ lại reads

- Xác định vùng có copy number lớn nhất làm denominator.
- Tính `keep_prob` cho từng vùng bằng `copy_number / denominator`.

### Bước 3: Tạo mẫu mô phỏng

- Duyệt qua từng `{Experiment ID}` (từ file `{Experiment ID}.bed`):
  - Cho mỗi experiment, duyệt qua tất cả `{Sample ID}.bam` trong `Input/Original/`:
    - Xác định vùng của từng read.
    - Giữ lại read ngẫu nhiên dựa trên `keep_prob` của vùng.
    - Ghi các read được giữ lại vào file `{Sample ID}.bam` mới trong `Output/{Experiment ID}/`.

### Bước 4: Tính toán và xuất kết quả

- Tính `scale_ratio` thực tế dựa trên số lượng reads trước và sau xử lý, so sánh với vùng tham chiếu (region 0).
- Xuất bảng `scale_ratio` ra file `{Experiment ID}.tsv` trong `Output/Metadata/`.
- Sao chép file `{Experiment ID}.bed` gốc vào `Output/Metadata/` để lưu trữ.
