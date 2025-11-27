/**
 * Types cho Algorithm Management (phù hợp backend hiện tại)
 */

export interface AlgorithmParameterDto {
  id: string;
  value: Record<string, any>;
}

// Thuật toán trả về dạng tóm tắt từ backend
export interface Algorithm {
  id: string; 
  name: string;
  version: string;
  description?: string;
  references_required?: number;
  parameters: AlgorithmParameterDto[];
  last_parameter_id?: string;
  exe_class?: string | null; 
}

// Upload response cơ bản
export interface BasicResponse {
  message: string;
}

// Upload ZIP response với exe_class
export interface UploadZipResponse extends BasicResponse {
  exe_class?: string | null;
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
}

export interface RegisterAlgorithmResponse extends BasicResponse {
  algorithm_id: string;
  algorithm_parameter_id: string;
}
