````markdown
# WisecondorX CNV Plugin — README

Tài liệu này mô tả code hiện có trong thư mục và cách chạy thử local (không giả định backend cụ thể).

## Mục lục

- Giới thiệu
- Cấu trúc thư mục
- Cách plugin nhận dữ liệu (`WisecondorXInput`)
- Chạy thử local với `test_run.py`
- Cài đặt môi trường (micromamba / pip)

## Giới thiệu

Plugin này đóng gói pipeline CNV (WisecondorX) nằm trong `Exe/Code/` và cung cấp một lớp `WisecondorXPlugin` (định nghĩa trong `wrapper.py`) tuân theo interface giả lập `AlgorithmPlugin`.

Hai cách dùng chính trong repo này:
- `wrapper.py`: lớp `WisecondorXPlugin` + CLI `main()` để chạy như plugin độc lập.
- `test_run.py`: script giúp dev test nhanh `WisecondorXPlugin.run()` bằng cách lấy một BAM trong `Input/Test`.

## Cấu trúc thư mục (chú ý các file quan trọng)

- `wrapper.py` — entrypoint plugin hiện tại: định nghĩa `WisecondorXPlugin`, lớp input/output Pydantic fallback, và `main()` để gọi run() từ CLI.
- `test_run.py` — script test local: đọc BAM đầu tiên trong `Input/Test`, tạo `WisecondorXInput` và gọi `WisecondorXPlugin.run()`; kết quả ghi `Output/result_test.json`.
- `Exe/Code/` — mã pipeline chính (ví dụ: `wisecondorx.py`).
- `Input/Test`, `Input/Reference` — nơi đặt BAM test/reference cho dev local.
- `Output/` — nơi plugin ghi kết quả (ví dụ `result.json`, `result_test.json`, các artifact .bed/.tsv).

## Cách plugin nhận dữ liệu (`WisecondorXInput`)

Plugin hỗ trợ 3 chế độ nhận dữ liệu (đã được hiện thực trong `wrapper.py`):

1. Legacy / default: truyền `BaseInput.bam` (bytes) — plugin sẽ ghi bytes này thành file trong `Exe/Run/Input/Test` và gọi pipeline; plugin luôn cố gắng tạo index `.bai` bằng `pysam.index()`.

2. Inline multi-samples: truyền `WisecondorXInput.test` (và `WisecondorXInput.reference`) là danh sách các sample in-memory. Mỗi sample cần có ít nhất:
   - `name` (tên file mong muốn, ví dụ `sampleA.bam`)
   - `bam` (nội dung file, `bytes`)

3. Glob mode: đọc tất cả các file BAM từ `Input/Test` và `Input/Reference` trên đĩa.

`run()` sẽ ưu tiên dùng `WisecondorXInput.test`/`reference` -> dùng `BaseInput.bam` (legacy) -> fallback đọc các file sẵn có trong `Input/Test` và `Input/Reference` trên đĩa.

## Định dạng đầu ra WisecondorX

WisecondorX tạo ra các file đầu ra trong `Exe/Run/Output/<sample_id>/`:
- `<sample_id>_bins.bed`: chứa thông tin bins với các cột `chr`, `start`, `end`, `id`, `ratio`, `zscore`
- `<sample_id>_segments.bed`: chứa thông tin segments với các cột `chr`, `start`, `end`, `ratio`, `zscore`

Plugin sẽ đọc các file này và chuyển đổi sang định dạng chuẩn:
- `copy_number = 2^(ratio + 1)`
- `confidence = zscore` (cho segments)
- Bỏ qua các bins có `ratio = nan`

## Chạy thử local với `test_run.py`

Hành vi mặc định: lấy BAM đầu tiên trong `Input/Test`, đọc toàn bộ bytes và truyền vào `WisecondorXInput.bam` (legacy mode). Nếu muốn khai báo dùng `test` list thay vì `BaseInput.bam`, chạy với `--no-baseinput`.

Ví dụ run (đã cài dependencies):

```bash
# mặc định: dùng BaseInput.bam (plugin sẽ ghi file -> Exe/Run/Input/Test và tạo .bai)
python test_run.py

# hoặc, ép dùng sample list (không truyền bytes vào BaseInput)
python test_run.py --no-baseinput
```

Kết quả: `Output/result_test.json` sẽ được viết.


## Cài đặt môi trường (micromamba, pip)

Khuyến nghị dùng micromamba để tái tạo môi trường giống dev:

```bash
micromamba create -n wisecondorx-plugin \
  python=3.10 \
  wisecondorx=1.4.2 \
  r-base \
  r-jsonlite \
  bioconductor-dnacopy \
  -c conda-forge -c bioconda -y

# Cài các dependencies khác nếu cần
micromamba run -n wisecondorx-plugin pip install -r requirements.txt
```

## Chạy CLI trực tiếp (dev)

```bash
python wrapper.py --params '{}'  # params hiện không quan trọng cho test local
```

## Docker (tùy chọn)

Dockerfile trong repo có thể dùng để tạo container có môi trường sẵn sàng cho WisecondorX. Thao tác build/run mẫu:

```bash
docker build -t wisecondorx-plugin:local .
# mount Input/Output/Plugin nếu muốn test trong container
docker run --rm -v $PWD/Input:/Input -v $PWD/Output:/Output -v $PWD:/Plugin wisecondorx-plugin:local bash -c "python /Plugin/wrapper.py"
```

(Tùy cấu trúc Dockerfile trong repo, bạn có thể cần điều chỉnh lệnh trên.)
````
