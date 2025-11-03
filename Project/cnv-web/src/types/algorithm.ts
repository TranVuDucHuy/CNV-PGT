/**
 * Types cho Algorithm Management
 */

export interface AlgorithmParam {
  id?: number;
  name: string;
  type: 'string' | 'integer' | 'float' | 'boolean';
  default_value?: string | number | boolean;
  required: boolean;
  description?: string;
}

export interface Algorithm {
  id?: number;
  name: string;
  description?: string;
  module_path?: string;
  is_usable: boolean;
  parameters: AlgorithmParam[];
  created_at?: string;
  updated_at?: string;
}

export interface AlgorithmFormData {
  name: string;
  description: string;
  module_path: string;
  parameters: AlgorithmParam[];
}

export interface ValidationResult {
  valid: boolean;
  message: string;
}
