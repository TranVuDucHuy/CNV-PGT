// src/types/models.ts

/**
 * TypeScript interfaces tương ứng với các model trong backend (SQLAlchemy + Pydantic).
 * Gồm:
 * - Result
 * - SampleSegment
 * - SampleBin
 * - ResultSummary
 * - ResultDto
 */

export type Chromosome =
  | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10'
  | '11' | '12' | '13' | '14' | '15' | '16' | '17' | '18' | '19' | '20'
  | '21' | '22' | 'X' | 'Y' | 'MT'
  | string;

export type ReferenceGenome = 'HG19' | 'HG38' | string;

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
  sample_id: string;
  algorithm_name: string;
  reference_genome: ReferenceGenome | string;
  created_at: string; // ISO format datetime
}

/** Tương ứng với lớp `ResultDto` trong backend */
export interface ResultDto extends ResultSummary {
  segments: SampleSegment[];
  bins: SampleBin[];
}

/* -------------------- Helper -------------------- */
export function parseResultCreatedAt(
  r: Result | ResultMinimal | ResultSummary
): Date | null {
  if (!r?.created_at) return null;
  const d = new Date(r.created_at);
  return isNaN(d.getTime()) ? null : d;
}
