# Simulate CNV - BED-based Simulation

Script mô phỏng CNV (Copy Number Variation) dựa trên file BED để chỉ định các vùng CNV cụ thể.

## Mục đích

Tạo BAM files mô phỏng với CNV ở các vùng nhiễm sắc thể cụ thể được định nghĩa trong file BED, thay vì mô phỏng toàn bộ một nhiễm sắc thể.

## Cách sử dụng

```bash
python simulate.py <original_bam_dir> <experiment_name.bed>
```

### Ví dụ:

```bash
python simulate.py ../experiment_data/original_bam exp1.bed
```

## Input

### 1. BAM Directory

Thư mục chứa các file BAM gốc (ví dụ: `../experiment_data/original_bam/`)

### 2. BED File

File BED định nghĩa các vùng CNV với format:

```
chrom    chromStart    chromEnd    name    type    mosaicism
1        1000000       2000000     region1  G       0.3
2        5000000       8000000     region2  L       0.5
```

**Các cột:**

- `chrom`: Nhiễm sắc thể (1, 2, ..., 22 hoặc chr1, chr2, ...)
- `chromStart`: Vị trí bắt đầu (0-based)
- `chromEnd`: Vị trí kết thúc
- `name`: Tên vùng (unique identifier)
- `type`: Loại CNV (`G` = Gain, `L` = Loss)
- `mosaicism`: Mức độ mosaic (0.0-1.0), ví dụ: 0.3 = 30%

## Output

Tạo thư mục mới có tên theo file BED (ví dụ: `exp1/`) chứa:

1. **BAM files mô phỏng**: Các file BAM với CNV đã được mô phỏng
2. **BAM index files**: `.bam.bai` cho mỗi BAM
3. **metadata.json**: Thông tin về quá trình mô phỏng

### metadata.json

```json
{
  "denominator": 2.5,
  "samples": {
    "sample1.bam": {
      "region1": {
        "original_read": 10000,
        "keep_read": 9200
      },
      "region2": {
        "original_read": 8000,
        "keep_read": 4000
      },
      "0": {
        "original_read": 100000,
        "keep_read": 80000
      }
    }
  }
}
```

- `region1`, `region2`: Thống kê cho từng vùng trong BED
- `0`: Thống kê cho các vùng bình thường (không nằm trong BED)

## Cách hoạt động

### 1. Tính Expected Copy Number

- **Gain**: `CN = 2.0 + mosaicism`
  - Ví dụ: mosaicism = 0.3 → CN = 2.3
- **Loss**: `CN = 2.0 - mosaicism`
  - Ví dụ: mosaicism = 0.5 → CN = 1.5

### 2. Tính Keep Probability

```python
denominator = max(all_expected_CNs, 2.0)
keep_probability = expected_CN / denominator
```

### 3. Mô phỏng Reads

- Đọc từng read trong BAM gốc
- Kiểm tra read có overlap với vùng BED nào không
- Giữ lại read với xác suất = keep_probability
- Các vùng không trong BED được giữ với xác suất = 2.0 / denominator

## Ví dụ thực tế

### Tạo file BED (exp1.bed):

```
chrom    chromStart    chromEnd    name       type    mosaicism
1        10000000      50000000    chr1_gain   G       0.3
3        20000000      60000000    chr3_loss   L       0.5
```

### Chạy simulation:

```bash
python simulate.py ../experiment_data/original_bam exp1.bed
```

### Kết quả:

```
exp1/
├── sample1_S93.bam
├── sample1_S93.bam.bai
├── sample2_S93.bam
├── sample2_S93.bam.bai
├── ...
└── metadata.json
```
