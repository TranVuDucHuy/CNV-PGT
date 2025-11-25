/**
 * Types cho Algorithm Management (phù hợp backend hiện tại)
 */

export interface AlgorithmParameterDto {
  id: string;
  value: Record<string, any>;
}

// Thuật toán trả về dạng tóm tắt từ backend
export interface Algorithm {
  id: string; // ví dụ: "Name_Version"
  name: string;
  version: string;
  description?: string;
  references_required?: number;
  parameters: AlgorithmParameterDto[];
  last_parameter_id?: string; // ID của parameter set mới nhất
}

// Upload response cơ bản
export interface BasicResponse {
  message: string;
}

// Backend input types for creating/registering algorithms
export interface AlgorithmParameterCreateRequest {
  name: string;
  type: string;
  default: any;
  value: any;
}

export interface AlgorithmMetadata {
  name: string;
  version: string;
  description?: string;
  references_required?: number;
  parameters?: AlgorithmParameterCreateRequest[];
  url?: string; // optional field for algorithm source URL
}

export interface RegisterAlgorithmResponse extends BasicResponse {
  algorithm_id: string;
  algorithm_parameter_id: string;
}
