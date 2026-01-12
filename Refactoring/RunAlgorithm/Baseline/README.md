# Tự động chạy thuật toán Baseline

## Cài đặt Môi trường Conda

```bash
# Tạo environment mới
conda create -n baseline-env python=3.11 -y

# Cài đặt các gói Python chính
conda install -n baseline-env -c conda-forge numpy pandas matplotlib statsmodels pydantic -y

# Cài pysam từ pip
conda run -n baseline-env pip install pysam

# Cài R base + packages cần thiết (optparse, DNAcopy)
conda install -n baseline-env -c conda-forge r-base r-optparse bioconductor-dnacopy -y

# Kích hoạt môi trường
conda activate baseline-env

```

## Cấu trúc Thư mục

```
Baseline/
├── wrapper.py                                        # Script wrapper chính
├── Input/                                            # Thư mục đầu vào
│   └── {Experiment ID}/                              # Thư mục cho mỗi thí nghiệm
│       └── {Sample ID}/                              # Thư mục cho mỗi mẫu
│           ├── {Sample ID}.bam                       # Tệp BAM của mẫu
│           └── {Sample ID}.bam.bai                   # Chỉ mục BAM của mẫu
├── Output/                                           # Thư mục đầu ra (tạo tự động)
│   └── {Experiment ID}/                              # Thư mục cho mỗi thí nghiệm
│       └── {Sample ID}/                              # Thư mục cho mỗi mẫu
│           ├── {Sample ID}_baseline_bins.bed         # Tệp BED chứa dữ liệu bins
│           ├── {Sample ID}_baseline_segments.bed     # Tệp BED chứa dữ liệu segments
│           └── {Sample ID}_baseline_scatterChart.png # Biểu đồ scatter plot
├── Exe/
│   ├── Code/                                         # Code thuật toán Baseline
│   │   ├── baseline.py                               # Script phân tích chính
│   │   └── ...                                       # Các script hỗ trợ khác
│   └── Run/                                          # Thư mục runtime
│       ├── Input/Test/                               # Lưu trữ BAM tạm thời
│       ├── Output/                                   # Lưu trữ đầu ra tạm thời
│       └── Temporary/                                # Tệp tạm thời
└── README.md                                         # Tệp này
```

## Cách Sử dụng

1. Đặt các tệp BAM vào các thư mục con trong `Input/`. Mỗi thư mục con đại diện cho một thí nghiệm.

2. Chạy script wrapper:

```bash
python wrapper.py
```

## Quy trình Thực thi

### Bước 1: Quét thư mục đầu vào

- Tìm kiếm các thư mục thí nghiệm (thư mục con trong `Input/`) chứa tệp BAM.

### Bước 2: Xử lý từng thí nghiệm tuần tự

- **Chuẩn bị dữ liệu**: Di chuyển tệp BAM từ thư mục thí nghiệm vào thư mục tạm thời `Exe/Run/Input/Test/` và tạo BAI nếu thiếu.
- **Phân tích CNV**: Chạy pipeline baseline cho dữ liệu trong `Exe/Run/Input/Test/`.
- **Xuất kết quả**: Chuyển đổi đầu ra phân tích sang định dạng BED lưu tại `Output/{Experiment ID}/{Sample ID}/`.
- **Khôi phục dữ liệu**: Trả lại tệp BAM và BAI về thư mục thí nghiệm gốc trong `Input/`.

### Bước 3: Dọn dẹp

- Xóa dữ liệu trong thư mục `Exe/Run/Temporary/Test/` và `Exe/Run/Output/` sau khi hoàn thành xử lý tất cả các mẫu trong thí nghiệm.
