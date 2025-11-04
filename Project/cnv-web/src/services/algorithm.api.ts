/**
 * Algorithm API Service
 * Tất cả API calls liên quan đến algorithms (đồng bộ với backend hiện tại)
 */

import { fetchAPI, getApiUrl } from './api-client';
import { Algorithm, BasicResponse } from '@/types/algorithm';

export const algorithmAPI = {
  /**
   * Lấy danh sách tất cả algorithms
   */
  async getAll(): Promise<Algorithm[]> {
    return fetchAPI<Algorithm[]>('/algorithms');
  },

  /**
   * Upload algorithm mới (file .zip chứa metadata.json và mã)
   */
  async upload(file: File): Promise<BasicResponse> {
    const form = new FormData();
    form.append('file', file);

    const res = await fetch(getApiUrl('/algorithms'), {
      method: 'POST',
      body: form,
      // Không set Content-Type để trình duyệt tự thêm boundary cho multipart/form-data
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Xóa algorithm
   */
  async delete(id: string): Promise<BasicResponse> {
    return fetchAPI<BasicResponse>(`/algorithms/${id}`, {
      method: 'DELETE',
    });
  },
};
