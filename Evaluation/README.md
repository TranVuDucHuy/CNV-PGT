## 1. `convert.py`
### Mục đích
Chuẩn hoá các tệp segment đầu ra từ nhiều thuật toán khác nhau về cùng một schema TSV:
Chromosome (1,2,...,23,24); Start; End; Copy Number

### Thuật toán hỗ trợ
| Thuật toán | Đầu vào mong đợi 
|------------|------------------
| BlueFuse   | `<sample>/BlueFuse/<sample>_segments.tsv` 
| Bicseq2    | `<sample>/Bicseq2/<sample>_S93.bicseq2.seg` 
| Baseline   | `<sample>/Baseline/<sample>_S93_normalized_segments.csv` 
| WisecondorX| `<sample>/WisecondorX/<sample>_S93_segments.bed` 

### Đầu ra
Mỗi mẫu được ghi dưới thư mục output tương ứng:  
`<output>/<sample>/<sample>_<Algo>_segments.tsv`

### Cách chạy
```bash
python convert.py -i /path/to/input_root -o /path/to/output_root
```
Trong đó cây thư mục đầu vào cần có dạng:
```
input_root/
  SAMPLE_001/
    BlueFuse/SAMPLE_001_segments.tsv
    Bicseq2/SAMPLE_001_S93.bicseq2.seg
    Baseline/SAMPLE_001_S93_normalized_segments.csv
    WisecondorX/SAMPLE_001_S93_segments.bed
  SAMPLE_002/
    ...
```

---
## 2. `eval.py`
### Mục đích
Tính các chỉ số TP/FP/TN/FN và các metric: Precision, Recall, Specificity, Accuracy, F1-Score cho mỗi thuật toán so với ground truth. Loại bỏ chromosome 23 (X) và 24 (Y) khỏi đánh giá.

### Tham số
| Tham số | Mặc định | Ý nghĩa |
|---------|----------|---------|
| `--mosaicism` | 0.5 | Ngưỡng lệch khỏi 2 để xác định CNV |
| `--overlap` | 0.5 | Ngưỡng phần trăm độ dài trùng loại giữa segment và ground truth |
| `--min_length` | 5000000 | Độ dài tối thiểu (bp) để xét |

### Cách chạy
Giả sử thư mục đầu vào là kết quả từ bước convert:
```bash
python eval.py -i /path/to/normalized_segments \
  --mosaicism 0.5 --overlap 0.5 --min_length 5000000
```
---
## 3. `Statistics/cnv_size.py`
### Mục đích
Tạo bảng đếm số lượng segment (từ file BlueFuse chuẩn hoá) theo các bins chiều dài và mức copy number đã được làm tròn half-up 1 chữ số, clamp trong [1.0, 3.0].

### Đầu ra
Một bảng TSV với cột đầu tiên `Sample`, tiếp theo là các cột kết hợp `<SizeBin>_CN<value>` chứa số lượng segment. Các ô không có giá trị được điền 0.

### Cách chạy
```bash
python Statistics/cnv_size.py -i /path/to/normalized_segments -o cnv_size_counts.tsv
```

---
## 4. `Statistics/summary.py`
### Mục đích
Tính copy number trung bình theo mỗi chromosome (1..24) có trọng số độ dài segment và suy luận giới tính dựa trên CN trung bình của chr23 (X) và chr24 (Y).

### Cách chạy
```bash
python Statistics/summary.py -i /path/to/normalized_segments -o summary.tsv
```

---
## Yêu cầu môi trường
Python 3.8+ và các thư viện:
- pandas
- numpy (dùng trong `convert.py`)

Cài đặt nhanh:
```bash
pip install pandas numpy
```