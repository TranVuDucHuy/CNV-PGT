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

# Đọc dữ liệu CSV đã được chuẩn bị từ Python
cat("Đang đọc dữ liệu từ file CSV...\n")

if (!file.exists(opt$input)) {
  stop(paste("File input không tồn tại:", opt$input))
}

ratio_df <- read.csv(opt$input)

if (nrow(ratio_df) == 0) {
  stop("Không có dữ liệu hợp lệ để phân tích")
}

# Tạo đối tượng CNA
CNA_object <- CNA(genomdat = ratio_df$log2_ratio,
                  chrom = ratio_df$chrom_numeric,
                  maploc = ratio_df$maploc,
                  data.type = "logratio",
                  sampleid = opt$sample)

# Smooth the data (tùy chọn)
smoothed_CNA_object <- smooth.CNA(CNA_object)

# Thực hiện segmentation
segment_result <- segment(smoothed_CNA_object, 
                         alpha = opt$alpha,
                         nperm = opt$nperm,
                         p.method = opt$p.method,
                         verbose = 1)

# Lấy kết quả segmentation
segments_df <- segment_result$output

# Thay thế trực tiếp giá trị 23/24 thành X/Y trong cột chrom
segments_df$chrom <- ifelse(segments_df$chrom == 23, "X",
        ifelse(segments_df$chrom == 24, "Y",
          as.character(segments_df$chrom)))

# Lưu kết quả
write.csv(segments_df, opt$output, row.names = FALSE)
