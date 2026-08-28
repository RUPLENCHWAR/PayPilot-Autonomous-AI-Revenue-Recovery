const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
      if (Array.isArray(detail)) detail = detail.map((d) => d.msg || d).join("; ");
    } catch {
      detail = await response.text();
    }
    throw new ApiError(detail, response.status);
  }
  return response.json();
}

export const api = {
  dashboard: () => request("/api/dashboard"),
  health: () => request("/api/health"),
  settings: () => request("/api/settings"),
  transactions: (query = "") => request(`/api/transactions${query}`),
  transaction: (id: number) => request(`/api/transactions/${id}`),
  customers: () => request("/api/customers"),
  customer: (id: number) => request(`/api/customers/${id}`),
  opportunities: (query = "") => request(`/api/recovery/opportunities${query}`),
  opportunity: (id: number) => request(`/api/recovery/opportunities/${id}`),
  analyze: (id: number) => request(`/api/recovery/${id}/analyze`, { method: "POST" }),
  execute: (id: number) => request(`/api/recovery/${id}/execute`, { method: "POST" }),
  approve: (id: number) => request(`/api/recovery/${id}/approve`, { method: "POST" }),
  simulateSuccess: (id: number) => request(`/api/recovery/${id}/simulate-success`, { method: "POST" }),
  simulateFailure: (id: number) => request(`/api/recovery/${id}/simulate-failure`, { method: "POST" }),
  activity: () => request("/api/agent/activity"),
  scan: () => request("/api/recovery/scan", { method: "POST" }),
  simulator: (limit = 10000) => request(`/api/recovery/simulator?limit=${limit}`),
  updateAutonomy: (autonomous_amount_limit: number, enabled: boolean) => request("/api/settings/autonomy", { method: "PATCH", body: JSON.stringify({ autonomous_amount_limit, enabled }) }),
  command: (query: string, confirm = false) =>
    request("/api/command", { method: "POST", body: JSON.stringify({ query, confirm }) }),
};

export { API_URL };
