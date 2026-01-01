# Tự động chuyển đổi dữ liệu BlueFuse

## Cài đặt môi trường

```bash
pip install pandas
```

## Cấu trúc thư mục

```
BlueFuse/
├── wrapper.py                                        # Script wrapper chính
├── Input/                                            # Thư mục đầu vào
│   └── {Experiment ID}/                              # Thư mục cho mỗi thí nghiệm
│       └── {Sample ID}/                              # Thư mục cho mỗi mẫu
│           ├── *_processed.xls                       # Tệp dữ liệu bins (tab-separated)
│           ├── {Sample ID}_segments.txt              # Tệp dữ liệu segments (tab-separated)
│           └── *.jpg                                 # Biểu đồ scatter plot (tìm động)
├── Output/                                           # Thư mục đầu ra (tạo tự động)
│   └── {Experiment ID}/                              # Thư mục cho mỗi thí nghiệm
│       └── {Sample ID}/                              # Thư mục cho mỗi mẫu
│           ├── {Sample ID}_bluefuse_bins.bed         # Tệp BED chứa dữ liệu bins
│           ├── {Sample ID}_bluefuse_segments.bed     # Tệp BED chứa dữ liệu segments
│           └── {Sample ID}_bluefuse_scatterChart.jpg # Biểu đồ scatter plot
└── README.md                                         # Tệp này
```

## Cách sử dụng

1. Đặt các tệp dữ liệu BlueFuse vào thư mục `Input/` theo cấu trúc trên. Script sẽ tự động tìm tệp dựa trên pattern (không cần tên chính xác, chỉ cần đuôi phù hợp).

2. Chạy script:

```bash
python wrapper.py
```

Script sẽ xử lý tuần tự từng thí nghiệm và mẫu, xuất kết quả vào `Output/`.

## Quy trình thực thi

### Bước 1: Quét thư mục đầu vào

- Duyệt qua các thư mục con trong `Input/` (mỗi thư mục là một thí nghiệm).
- Trong mỗi thí nghiệm, duyệt các thư mục mẫu.

### Bước 2: Xử lý từng mẫu

- **Tệp bins**: Đọc `{Sample ID}_processed.xls`, bỏ qua 49 hàng đầu (metadata + header), lọc NST 1-24, tính chromEnd dựa trên vị trí tiếp theo hoặc độ dài chromosome, xuất BED với header.
- **Tệp segments**: Đọc `{Sample ID}_segments.txt`, lọc NST 1-24, xuất BED với header.
- **Ảnh**: Sao chép tệp `.jpg` đầu tiên tìm được, đổi tên thành `{Sample ID}_bluefuse_scatterChart.jpg`.
