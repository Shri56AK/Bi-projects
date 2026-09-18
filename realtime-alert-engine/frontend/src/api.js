const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

async function req(path, opts = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  return res.json();
}

export const api = {
  rules: () => req("/api/rules"),
  createRule: (rule) => req("/api/rules", { method: "POST", body: JSON.stringify(rule) }),
  toggleRule: (id) => req(`/api/rules/${id}/toggle`, { method: "PATCH" }),
  deleteRule: (id) => req(`/api/rules/${id}`, { method: "DELETE" }),
  events: (limit = 50) => req(`/api/events?limit=${limit}`),
  metrics: () => req("/api/metrics"),
  metricHistory: (name, minutes = 120) => req(`/api/metrics/${name}?minutes=${minutes}`),
};
