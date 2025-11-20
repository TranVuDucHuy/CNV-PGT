/**
 * Sample API Service
 * Tất cả API calls liên quan đến samples
 */

import { fetchAPI } from './api-client';
import { Sample, SampleSummary } from '@/types/sample';


export const sampleAPI = {
  /**
   * Lấy danh sách tất cả samples
   */
  async getAll(): Promise<SampleSummary[]> {
    return fetchAPI<SampleSummary[]>('/samples');
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
  async create(file: File, referenceGenome?: string): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);
    if (referenceGenome) {
      formData.append("reference_genome", referenceGenome);
    }

    const res = await fetchAPI<void>('/samples', {
      method: 'POST',
      body: formData, // browser tự set multipart/form-data
    });

    return res;
  },

  /**
   * Tạo sample mới
   */
  async createMany(files: File[], referenceGenome?: string): Promise<void> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file, file.name);
    });
    if (referenceGenome) {
      formData.append("reference_genome", referenceGenome);
    }
    

    const res = await fetchAPI<void>('/samples/many', {
      method: 'POST',
      body: formData, // browser tự set multipart/form-data
    });

    return res;
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
  async delete(id: string): Promise<void> {
    return fetchAPI<void>(`/samples/${id}`, {
      method: 'DELETE',
    });
  },
};

export type { Sample };