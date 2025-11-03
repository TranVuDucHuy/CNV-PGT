/**
 * Result API Service
 * Tất cả API calls liên quan đến results
 */

import { fetchAPI } from './api-client';

// TODO: Định nghĩa Result types
export interface Result {
  id: number;
  name: string;
  // ... thêm fields khác
}

export const resultAPI = {
  /**
   * Lấy danh sách tất cả results
   */
  async getAll(): Promise<Result[]> {
    return fetchAPI<Result[]>('/results');
  },

  /**
   * Lấy chi tiết một result
   */
  async getById(id: number): Promise<Result> {
    return fetchAPI<Result>(`/results/${id}`);
  },

  /**
   * Tạo result mới
   */
  async create(data: Partial<Result>): Promise<Result> {
    return fetchAPI<Result>('/results', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Cập nhật result
   */
  async update(id: number, data: Partial<Result>): Promise<Result> {
    return fetchAPI<Result>(`/results/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Xóa result
   */
  async delete(id: number): Promise<void> {
    return fetchAPI<void>(`/results/${id}`, {
      method: 'DELETE',
    });
  },
};
