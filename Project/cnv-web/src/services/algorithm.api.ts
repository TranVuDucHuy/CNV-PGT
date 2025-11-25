/**
 * Algorithm API Service
 * Tất cả API calls liên quan đến algorithms (đồng bộ với backend hiện tại)
 */

import { fetchAPI, getApiUrl } from './api-client';
import { Algorithm, BasicResponse, AlgorithmMetadata, RegisterAlgorithmResponse } from '@/types/algorithm';

export const algorithmAPI = {
  /**
   * Lấy danh sách tất cả algorithms
   */
  async getAll(): Promise<Algorithm[]> {
    return fetchAPI<Algorithm[]>('/algorithms/');
  },

  /**
   * Đăng ký thuật toán (metadata only) → trả về algorithm_id, algorithm_parameter_id
   */
  async register(metadata: AlgorithmMetadata): Promise<RegisterAlgorithmResponse> {
    const response = await fetch(getApiUrl('/algorithms/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metadata),
    });
    console.log('API Response [/algorithms/]:', response);
    const data = await response.json() as RegisterAlgorithmResponse;
    console.log('RegisterAlgorithmResponse:', {
      algorithm_id: data.algorithm_id,
      algorithm_parameter_id: data.algorithm_parameter_id,
      message: data.message,
    });
    return data;       
  },

  /**
   * Upload ZIP cho thuật toán đã đăng ký
   */
  async uploadZip(algorithmId: string, file: File): Promise<BasicResponse> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(getApiUrl(`/algorithms/${algorithmId}/upload`), {
      method: 'POST',
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  },

  // Note: `upload(file)` removed. Use `register(metadata)` then `uploadZip(id, file)`.

  /**
   * Cập nhật parameters cho algorithm
   */
  async updateParameters(algorithmId: string, parameters: Record<string, any>): Promise<{ message: string; algorithm_parameter_id: string }> {
    const response = await fetch(getApiUrl(`/algorithms/${algorithmId}/parameters`), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters }),
    });
    console.log(`API Response [/algorithms/${algorithmId}/parameters]:`, response);
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Xóa algorithm
   */
  async delete(id: string): Promise<BasicResponse> {
    const response = await fetch(getApiUrl(`/algorithms/${id}`), {
      method: 'DELETE',
    });
    console.log(`API Response [/algorithms/${id}]:`, response);
    return response.json();
  },
};
