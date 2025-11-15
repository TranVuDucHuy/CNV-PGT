/**
 * Generic API Client
 * Dùng chung cho tất cả API services
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Generic fetch wrapper với improved error handling
 */
export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const headers: Record<string, string> = {};

    // Nếu body là FormData thì không set Content-Type (fetch tự set boundary)
    if (!(options?.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (options?.headers) {
      // options.headers có thể là object; merge vào headers
      try {
        Object.assign(headers, options.headers as Record<string, string>);
      } catch {
        // ignore if headers is not plain object
      }
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    // Try to parse response body (json if possible, otherwise text)
    const contentType = response.headers.get("content-type") || "";
    let parsedBody: any = null;
    try {
      if (contentType.includes("application/json")) {
        parsedBody = await response.json();
      } else {
        parsedBody = await response.text();
      }
    } catch (parseErr) {
      parsedBody = `<<unable to parse response body: ${String(parseErr)}>>`;
    }

    if (!response.ok) {
      // Build an Error that contains status and parsed body for caller to inspect
      const err = new Error(
        `API Error ${response.status} ${response.statusText} - ${typeof parsedBody === "string" ? parsedBody : JSON.stringify(parsedBody)}`
      ) as Error & { status?: number; body?: any };
      err.status = response.status;
      err.body = parsedBody;
      throw err;
    }

    // Success: return parsed body (cast to T)
    return parsedBody as T;
  } catch (error) {
    // Ensure we log helpful diagnostic info
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
