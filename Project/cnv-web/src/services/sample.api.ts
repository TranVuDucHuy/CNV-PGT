/**
 * Sample API Service
 * Tất cả API calls liên quan đến samples
 */

import { fetchAPI } from './api-client';

// TODO: Định nghĩa Sample types
export interface Sample {
  id: number;
  name: string;
  // ... thêm fields khác
}

export const sampleAPI = {
  /**
   * Lấy danh sách tất cả samples
   */
  async getAll(): Promise<Sample[]> {
    return fetchAPI<Sample[]>('/samples');
  },

  /**
   * Lấy chi tiết một sample
   */
  async getById(id: number): Promise<Sample> {
    return fetchAPI<Sample>(`/samples/${id}`);
  },

  /**
   * Tạo sample mới
   */
  async create(data: Partial<Sample>): Promise<Sample> {
    return fetchAPI<Sample>('/samples', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Cập nhật sample
   */
  async update(id: number, data: Partial<Sample>): Promise<Sample> {
    return fetchAPI<Sample>(`/samples/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Xóa sample
   */
  async delete(id: number): Promise<void> {
    return fetchAPI<void>(`/samples/${id}`, {
      method: 'DELETE',
    });
  },
};
