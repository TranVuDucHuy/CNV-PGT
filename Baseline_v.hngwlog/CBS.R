#!/usr/bin/env Rscript
# CBS.R - Circular Binary Segmentation for CNV analysis
# Sử dụng gói DNAcopy để phân đoạn dữ liệu log2 ratio

library(DNAcopy)
library(optparse)

# Định nghĩa các tham số dòng lệnh
option_list = list(
  make_option(c("-i", "--input"), type="character", default=NULL, 
              help="File CSV chứa log2 ratio data đã được chuẩn bị", metavar="character"),
  make_option(c("-o", "--output"), type="character", default=NULL, 
              help="File output để lưu kết quả segmentation", metavar="character"),
  make_option(c("-s", "--sample"), type="character", default="Sample", 
              help="Tên mẫu", metavar="character"),
  make_option(c("--alpha"), type="double", default=0.001, 
              help="Alpha cho CBS [default= %default]", metavar="number"),
  make_option(c("--nperm"), type="integer", default=10000, 
              help="Số permutations cho CBS [default= %default]", metavar="number"),
  make_option(c("--p.method"), type="character", default="hybrid", 
              help="P-value method [default= %default]", metavar="character")
)

opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

if (is.null(opt$input)){
  print_help(opt_parser)
  stop("Cần chỉ định file input CSV.", call.=FALSE)
}

if (is.null(opt$output)){
  print_help(opt_parser)
  stop("Cần chỉ định file output.", call.=FALSE)
}

cat("=== CBS Segmentation ===\n")
cat("Input file:", opt$input, "\n")
cat("Output file:", opt$output, "\n")
cat("Sample name:", opt$sample, "\n")

# Đọc dữ liệu CSV đã được chuẩn bị từ Python
cat("Đang đọc dữ liệu từ file CSV...\n")

if (!file.exists(opt$input)) {
  stop(paste("File input không tồn tại:", opt$input))
}

cnv_data <- read.csv(opt$input)

if (nrow(cnv_data) == 0) {
  stop("Không có dữ liệu hợp lệ để phân tích")
}

cat("Số điểm dữ liệu:", nrow(cnv_data), "\n")

# Kiểm tra các cột cần thiết
required_cols <- c("sample.name", "chrom_numeric", "maploc", "log2_ratio")
missing_cols <- setdiff(required_cols, colnames(cnv_data))
if (length(missing_cols) > 0) {
  stop(paste("Thiếu các cột cần thiết:", paste(missing_cols, collapse=", ")))
}

# Tạo đối tượng CNA
cat("Tạo đối tượng CNA...\n")
CNA.object <- CNA(genomdat = cnv_data$log2_ratio,
                  chrom = cnv_data$chrom_numeric,
                  maploc = cnv_data$maploc,
                  data.type = "logratio",
                  sampleid = opt$sample)

# Smooth the data (tùy chọn)
cat("Smoothing dữ liệu...\n")
smoothed.CNA.object <- smooth.CNA(CNA.object)

# Thực hiện segmentation
cat("Thực hiện CBS segmentation...\n")
cat("  Alpha:", opt$alpha, "\n")
cat("  Nperm:", opt$nperm, "\n")
cat("  P-method:", opt$p.method, "\n")

segment.result <- segment(smoothed.CNA.object, 
                         alpha = opt$alpha,
                         nperm = opt$nperm,
                         p.method = opt$p.method,
                         verbose = 1)

# Lấy kết quả segmentation
segments_df <- segment.result$output

# Thêm thông tin chromosome gốc
segments_df$chrom_original <- ifelse(segments_df$chrom == 23, "X",
                                   ifelse(segments_df$chrom == 24, "Y", 
                                         as.character(segments_df$chrom)))

# Lưu kết quả
cat("Lưu kết quả segmentation...\n")
write.csv(segments_df, opt$output, row.names = FALSE)

# In thống kê tóm tắt
cat("\n=== Thống kê Segmentation ===\n")
cat("Số segments:", nrow(segments_df), "\n")
cat("Segments có gain (>0.2):", sum(segments_df$seg.mean > 0.2), "\n")
cat("Segments có loss (<-0.2):", sum(segments_df$seg.mean < -0.2), "\n")
cat("Segments normal:", sum(abs(segments_df$seg.mean) <= 0.2), "\n")

cat("\nHoàn thành CBS segmentation!\n")
