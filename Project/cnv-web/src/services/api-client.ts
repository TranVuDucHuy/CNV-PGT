/**
 * Generic API Client
 * Dùng chung cho tất cả API services
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper với error handling
 */
export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const headers: Record<string, string> = {};

    if (!(options?.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (options?.headers) {
      Object.assign(headers, options.headers as Record<string, string>);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}


/**
 * Helper để build full URL
 */
export function getApiUrl(endpoint: string): string {
  return `${API_BASE}${endpoint}`;
}

/**
 * Export API_BASE để dùng ở nơi khác nếu cần
 */
export { API_BASE };
