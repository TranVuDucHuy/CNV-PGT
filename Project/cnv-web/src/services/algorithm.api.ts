/**
 * Algorithm API Service
 * Tất cả API calls liên quan đến algorithms
 */

import { fetchAPI } from './api-client';
import { Algorithm, AlgorithmFormData, ValidationResult } from '@/types/algorithm';

export const algorithmAPI = {
  /**
   * Lấy danh sách tất cả algorithms
   */
  async getAll(): Promise<Algorithm[]> {
    return fetchAPI<Algorithm[]>('/algorithms');
  },

  /**
   * Lấy chi tiết một algorithm
   */
  async getById(id: number): Promise<Algorithm> {
    return fetchAPI<Algorithm>(`/algorithms/${id}`);
  },

  /**
   * Tạo algorithm mới
   */
  async create(data: AlgorithmFormData): Promise<Algorithm> {
    return fetchAPI<Algorithm>('/algorithms', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Cập nhật algorithm
   */
  async update(id: number, data: Partial<AlgorithmFormData>): Promise<Algorithm> {
    return fetchAPI<Algorithm>(`/algorithms/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Xóa algorithm
   */
  async delete(id: number): Promise<void> {
    return fetchAPI<void>(`/algorithms/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Validate module path
   * Kiểm tra xem đường dẫn module có hợp lệ không
   */
  async validateModule(modulePath: string): Promise<ValidationResult> {
    try {
      return await fetchAPI<ValidationResult>('/algorithms/validate-module', {
        method: 'POST',
        body: JSON.stringify({ module_path: modulePath }),
      });
    } catch (error) {
      return {
        valid: false,
        message: error instanceof Error ? error.message : 'Validation failed',
      };
    }
  },
};
