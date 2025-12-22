# WisecondorX Pipeline - Hướng dẫn sử dụng

## Tổng quan

Pipeline này được sử dụng để xử lý các tệp BAM (Binary Alignment Map) bằng WisecondorX, một công cụ phân tích dữ liệu WGS (Whole Genome Sequencing). `autorun.py` tự động chạy pipeline cho mỗi tập kiểm thử.

## Cấu trúc thư mục

Thư mục `Exe/` được chuẩn bị sẵn với cấu trúc sau:

```
Exe/
├── simulate_bam/              # Chứa các thư mục tệp BAM kiểm thử
│   ├── test_set_1/
│   │   ├── sample1.bam
│   │   ├── sample2.bam
│   │   └── ...
│   ├── test_set_2/
│   │   └── ...
│   └── ...
├── Run/                       # Thư mục làm việc chính
│   ├── Input/
│   │   ├── Test/              # (Sẽ được điền tự động bởi autorun.py)
│   │   └── Train/             # Chứa tệp BAM huấn luyện
│   ├── Output/                # Kết quả sau khi chạy (BED, Plot)
│   └── Temporary/             # Tệp trung gian
│       ├── Reference.npz      # Tệp tham chiếu được tạo
│       ├── Test/              # Tệp NPZ kiểm thử
│       └── Train/             # Tệp NPZ huấn luyện
└── Output/                    # Tập hợp kết quả cuối cùng
    ├── test_set_1/
    ├── test_set_2/
    └── ...
```

## Cách sử dụng

#### Chạy pipeline:

```bash
cd /mnt/d/lab/experiment/wisecondorx
python autorun.py ./Exe
```
