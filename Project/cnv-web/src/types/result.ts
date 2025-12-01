// src/types/models.ts

/**
 * TypeScript interfaces tương ứng với các model trong backend (SQLAlchemy + Pydantic).
 * Gồm:
 * - Result
 * - SampleSegment
 * - SampleBin
 * - ResultSummary
 * - ResultDto
 * - ResultReportResponse and its dependencies
 */

export type Chromosome =
  | "1"
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "7"
  | "8"
  | "9"
  | "10"
  | "11"
  | "12"
  | "13"
  | "14"
  | "15"
  | "16"
  | "17"
  | "18"
  | "19"
  | "20"
  | "21"
  | "22"
  | "X"
  | "Y"
  | "MT"
  | string;

export type ReferenceGenome = "GRCh37/hg19" | "GRCh38/hg38" | string;

/* -------------------- SAMPLE BIN -------------------- */
export interface SampleBin {
  id: string;
  result_id: string;
  chromosome: Chromosome;
  start: number;
  end: number;
  copy_number: number;
  read_count: number;
  gc_content: number;
  result?: ResultMinimal;
}

/* -------------------- SAMPLE SEGMENT -------------------- */
export interface SampleSegment {
  id: string;
  result_id: string;
  chromosome: Chromosome;
  start: number;
  end: number;
  copy_number: number;
  confidence?: number | null;
  man_change: boolean;
  result?: ResultMinimal;
}

/* -------------------- RESULT MODELS -------------------- */
export interface ResultMinimal {
  id: string;
  sample_id?: string;
  algorithm_id?: string;
  reference_genome?: ReferenceGenome;
  created_at?: string;
}

export interface Result {
  id: string;
  sample_id: string;
  algorithm_id: string;
  reference_genome: ReferenceGenome;
  created_at: string;
  segments?: SampleSegment[];
  bins?: SampleBin[];
  sample?: any;
  algorithm?: any;
}

/* -------------------- Pydantic-based Models -------------------- */

/** Tương ứng với lớp `ResultSummary` trong backend */
export interface ResultSummary {
  id: string;
  sample_name: string;
  algorithm_name: string;
  reference_genome: ReferenceGenome | string;
  created_at: string; // ISO format datetime
}

/** Tương ứng với lớp `ResultDto` trong backend */
export interface ResultDto extends ResultSummary {
  segments: SampleSegment[];
  bins: SampleBin[];
}

/* -------------------- RESULT REPORT RESPONSE -------------------- */

/** Tương ứng với lớp `SampleInfo` trong backend */
export interface SampleInfo {
  flowcell_id: string;
  cycle_id: string;
  embryo_id: string;
  cell_type: string;
  reference_genome: string;
  date: string; // ISO format date
}

/** Tương ứng với lớp `AlgorithmParameterInfo` trong backend */
export interface AlgorithmParameterInfo {
  name: string;
  type: string;
  default: any;
  value: any;
}

/** Tương ứng với lớp `AlgorithmInfo` trong backend */
export interface AlgorithmInfo {
  name: string;
  version: string;
  parameters: AlgorithmParameterInfo[];
}

/** Tương ứng với lớp `AberrationSegmentInfo` trong backend */
export interface AberrationSegmentInfo {
  chromosome: string;
  start: number;
  end: number;
  copy_number: number;
  confidence?: number | null;
  size: number;
  type: string;
  mosaicism: number;
  aberration_code: string;
  assessment: string;
  annotation_for_segment?: string | null;
  man_change?: boolean | null;
}

/** Tương ứng với lớp `AberrationInfo` trong backend */
export interface AberrationInfo {
  aberration_summary?: string[] | null;
  aberration_segments: AberrationSegmentInfo[];
}

/** Tương ứng với lớp `ResultReportResponse` trong backend */
export interface ResultReportResponse {
  result_id: string;
  sample: SampleInfo;
  algorithm: AlgorithmInfo;
  aberration: AberrationInfo;
}

/* -------------------- Helper -------------------- */
export function parseResultCreatedAt(
  r: Result | ResultMinimal | ResultSummary
): Date | null {
  if (!r?.created_at) return null;
  const d = new Date(r.created_at);
  return isNaN(d.getTime()) ? null : d;
}

/* -------------------- CYCLE REPORT -------------------- */

/** Tương ứng với lớp `CycleReportRequest` trong backend */
export interface CycleReportRequest {
  report_ids: string[];
}

/** Tương ứng với lớp `AberrationSummary` trong backend */
export interface AberrationSummary {
  code: string;
  mosaic: number;
  size?: number | null; // in Mbp
  diseases?: string[] | null;
  assessment?: string | null;
}

/** Tương ứng với lớp `EmbryoInfo` trong backend */
export interface EmbryoInfo {
  embryo_id: string;
  cell_type: string;
  call: string;
  abberations: AberrationSummary[];
}

/** Tương ứng với lớp `CycleReportResponse` trong backend */
export interface CycleReportResponse {
  cycle_id: string;
  flowcell_id: string;
  embryos: EmbryoInfo[];
}
