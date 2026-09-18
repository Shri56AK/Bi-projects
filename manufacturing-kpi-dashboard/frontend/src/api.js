const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  return res.json();
}

export const api = {
  lines: () => get("/api/lines"),
  kpis: (params) => get(`/api/kpis?${new URLSearchParams(params)}`),
  trend: (params) => get(`/api/trend?${new URLSearchParams(params)}`),
  machineRanking: (params) => get(`/api/machines/ranking?${new URLSearchParams(params)}`),
  downtimeBreakdown: (params) => get(`/api/downtime/breakdown?${new URLSearchParams(params)}`),
};
