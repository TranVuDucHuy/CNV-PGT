# CNV-PGT: BWA Preprocessing và Baseline CNV Pipeline

## 1. Giới thiệu

Trong phân tích **Preimplantation Genetic Testing (PGT)** dựa trên dữ
liệu **Next-Generation Sequencing (NGS)**, việc phát hiện **Copy Number
Variation (CNV)** là bước quan trọng.\
Tài liệu này mô tả hai thành phần nhỏ trong một hệ thống phân tích lớn
hơn:

1.  **Tiền xử lý BWA**
    -   Chuyển đổi từ FASTQ → BAM chuẩn **BlueFuse**.
    -   Bao gồm bước align (BWA-MEM), lọc theo MAPQ, chọn lọc nhiễm sắc
        thể chuẩn (24 chr) và thêm header.
2.  **Pipeline CNV**
    -   Workflow phân tích CNV dạng module gồm:
        -   Đếm reads trên từng bin.
        -   Chuẩn hóa bằng GC/LOWESS.
        -   Lọc bin không ổn định bằng hệ số biến thiên (CV).
        -   Tính log2 ratio (test vs. train).
        -   Phân đoạn bằng **Circular Binary Segmentation (CBS)**.
        -   Vẽ biểu đồ CNV để đánh giá trực quan.
        
> Lưu ý: Đây chỉ là **các module phụ trợ**. Trong dự án tổng thể, chúng
> sẽ được tích hợp cùng nhiều bước xử lý khác.

------------------------------------------------------------------------
## 2. Yêu cầu hệ thống

-   Python ≥ 3.8

-   R (cần cài gói `DNAcopy`)

-   Công cụ dòng lệnh:

    -   [BWA](http://bio-bwa.sourceforge.net/) (≥ 0.7.17)
    -   [Samtools](http://www.htslib.org/) (≥ 1.10)

-   Thư viện Python:

    ``` bash
    pip install numpy pandas matplotlib pysam statsmodels
    ```

------------------------------------------------------------------------

## 3. Cấu trúc thư mục

### 3.1. BWA Preprocessing

    project_bwa/
    │
    ├── bwa.py                # Script FASTQ → BAM, đã chỉnh cho BlueFuse
    ├── header.txt            # File header mẫu (chứa @HD, @SQ, @RG…)
    │
    ├── fastq/                # FASTQ đầu vào
    │   ├── sample1.fastq.gz
    │   └── sample2.fastq.gz
    │
    ├── reference/            # Reference FASTA
    │   └── hg19.fa
    │
    └── bam/                  # BAM đầu ra (BlueFuse-compatible)
        ├── sample1_S93.bam
        └── sample2_S93.bam

### 3.2. CNV Baseline Pipeline

    project_baseline/
    │
    ├── Code/
    │   ├── baseline.py       # Pipeline CNV
    │   ├── estimate.py       # Đếm reads, tính proportion, thống kê
    │   ├── filter.py         # Lọc bin theo CV
    │   ├── normalize.py      # Chuẩn hóa GC/LOWESS
    │   ├── plot.py           # Vẽ CNV plots
    │   ├── CBS.R           
    │   └── segment.py        # Chạy CBS segmentation (R)
    │
    ├── Input/                # Dữ liệu đầu vào
    │   ├── Train/            # BAM train (control)
    │   ├── Test/             # BAM test (case)
    │   └── hg19.fa           # Reference genome (cho normalization)
    │
    ├── Temporary/            # Kết quả trung gian
    │   ├── Raw/              # Gốc
    │   │   ├── Train/
    │   │   └── Test/
    │   └── Normalized/       # Sau chuẩn hóa
    │       ├── Train/
    │       └── Test/
    │
    └── Output/               # Kết quả cuối
        ├── Raw/
        │   ├── Data/
        │   └── Plot/
        └── Normalized/
            ├── Data/
            └── Plot/

------------------------------------------------------------------------

## 4. Cách chạy

### 4.1. Tạo BAM từ FASTQ với `bwa.py`

``` bash
python bwa.py     -i fastq/     -r reference.fa     -o bam/     -t 8     -q 30     -F 0x4     -K 10000000     --sort-mem 4G	--cleanup
```

Tham số chính:
- `-i` : thư mục FASTQ đầu vào
- `-r` : reference genome (FASTA)
- `-o` : thư mục BAM đầu ra
- `-t` : số threads
- `-q` : ngưỡng MAPQ (mặc định: 30)
- `-F` : Samtools flags cần lọc (`0x4` = unmapped)
- `-K` : batch size BWA
- `--sort-mem` : bộ nhớ sort (vd: 4G)
- `--cleanup`  : xóa các file trung gian 

Kết quả: BAM `*_S93.bam` trong thư mục `bam/`, đã sẵn sàng cho BlueFuse
hoặc baseline pipeline.

------------------------------------------------------------------------

### 4.2. Phân tích CNV với `baseline.py`

``` bash
python Code/baseline.py     -o <thu_muc_work>     --bin-size 200000     --filter-ratio 0.8
```

Tham số chính:
- `-o` : thư mục làm việc
- `--bin-size` : kích thước bin (mặc định 200000)
- `--filter-ratio` : tỉ lệ giữ lại bin ổn định (mặc định 0.8)
------------------------------------------------------------------------

## 5. Quy trình phân tích CNV baseline

1.  **Đếm reads (Train/Test)** → `.npz` chứa read counts.
2.  **Chuẩn hóa (LOWESS/GC)** → loại bỏ bias theo GC, N-content.
3.  **Tính thống kê (Train)** → Mean + CV trên mỗi bin.
4.  **Lọc bin** → tạo `blacklist.npz` và `Mean_filtered.npz`.
5.  **Tính log2 ratio (Test/Train)** → `.npz` chứa log2 ratio.
6.  **CBS segmentation** → phân đoạn bất thường copy number.
7.  **Vẽ CNV plots** → scatter plot + boxplot cho toàn bộ genome.

------------------------------------------------------------------------

## 6. Kết quả đầu ra

-   `Output/Normalized/Data/` : normalized, ratio, segments CSV
-   `Output/Normalized/Plot/` : biểu đồ CNV `.png`

------------------------------------------------------------------------

## 7. Ghi chú

-   BAM đầu vào cho `baseline.py` nên được tạo bằng `bwa.py` để đảm bảo
    tương thích BlueFuse.
-   File reference genome (`hg19.fa`) phải có trong `Input/`.
-   CBS segmentation cần **R + DNAcopy**.
-   Các module này chỉ là **một phần nhỏ trong dự án phân tích PGT lớn
    hơn**.
