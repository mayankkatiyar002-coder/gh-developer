// Thin API layer: all business logic lives on the server.
const API = {
  async request(path, opts = {}) {
    const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail?.[0]?.msg || data.detail || `Request failed (${res.status})`);
    return data;
  },
  base: (u) => `/api/users/${encodeURIComponent(u)}`,
  profile: (u, r) => API.request(`${API.base(u)}/profile?refresh=${r}`),
  repos: (u, sort, r = false) => API.request(`${API.base(u)}/repos?sort=${sort}&refresh=${r}`),
  contributions: (u, r) => API.request(`${API.base(u)}/contributions?refresh=${r}`),
  match: (u, jd) => API.request(`${API.base(u)}/match`, { method: "POST", body: JSON.stringify({ job_description: jd }) }),
  insights: (u) => API.request(`${API.base(u)}/insights`),
  settings: (u) => API.request(`${API.base(u)}/settings`),
  chat: (u, m) => API.request(`${API.base(u)}/chat`, { method: "POST", body: JSON.stringify({ message: m }) }),
};
