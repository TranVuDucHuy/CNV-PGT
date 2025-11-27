/**
 * Result API Service
 * Tất cả API calls liên quan đến results
 */

import { fetchAPI } from "./api-client";
import {
  Result,
  ResultSummary,
  ResultDto,
  ResultReportResponse,
} from "@/types/result";

export const resultAPI = {
  /**
   * Lấy danh sách tất cả results
   */
  async getAll(): Promise<ResultSummary[]> {
    return fetchAPI<ResultSummary[]>("/results/");
  },

  /**
   * Lấy chi tiết một result
   */
  async getById(id: string): Promise<ResultDto> {
    return fetchAPI<ResultDto>(`/results/${id}`);
  },

  /**
   * Tạo result mới
   */
  async create(
    bins_tsv: File,
    segments_tsv: File,
    algorithm_id: string,
    algorithm_parameter_id: string,
    created_at?: string
  ): Promise<void> {
    const formData = new FormData();
    formData.append("bins_tsv", bins_tsv);
    formData.append("segments_tsv", segments_tsv);
    formData.append("algorithm_id", algorithm_id);
    formData.append("algorithm_parameter_id", algorithm_parameter_id);
    if (created_at) {
      formData.append("created_at", created_at);
    }

    const res = await fetchAPI<void>("/results", {
      method: "POST",
      body: formData, // browser tự set multipart/form-data
    });

    return res;
  },

  /**
   * Cập nhật result
   */
  async update(id: string, data: Partial<Result>): Promise<Result> {
    return fetchAPI<Result>(`/results/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /**
   * Xóa result
   */
  async delete(id: string): Promise<void> {
    return fetchAPI<void>(`/results/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * Lấy report chi tiết của một result
   */
  async getReport(id: string): Promise<ResultReportResponse> {
    return fetchAPI<ResultReportResponse>(`/results/${id}/report`);
  },
};
