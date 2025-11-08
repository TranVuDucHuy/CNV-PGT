/** Kiểu tế bào tương ứng với enum CellType bên backend */
export enum CellType {
  POLAR_BODY_1 = "Polar body 1",
  POLAR_BODY_2 = "Polar body 2",
  BLASTOMERE = "Blastomere",
  TROPHOECTODERM = "Trophectoderm",
  GENOMIC_DNA = "GenomicDNA",
  OTHER = "Other"
}

/** Mẫu sample đầy đủ (dùng khi get theo id) */
export interface Sample {
  id: string;
  flowcell_id: string;
  cycle_id: string;
  embryo_id: string;
  bam_url: string;
  cell_type: CellType;
  date: string; // ISO string, ví dụ "2025-11-05"
}

/** Mẫu sample rút gọn, dùng trong get_all */
export interface SampleSummary {
  id: string;
  bam_url: string;
  cell_type: string; // backend trả về .value (string)
  date: string;
}

/** Request body khi cập nhật sample */
export interface EditRequest {
  cell_type: CellType | string;
  date: string; // "YYYY-MM-DD"
}

/** Response đơn giản cho các thao tác upload, delete, update */
export interface BasicResponse {
  message: string;
}