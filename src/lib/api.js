const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Scanner
export const scannerApi = {
  getScans: () => request('/scanner/scans/'),
  getScan: (id) => request(`/scanner/scans/${id}/`),
  createScan: (data) => request('/scanner/scans/', { method: 'POST', body: JSON.stringify(data) }),
  getFindings: (id) => request(`/scanner/scans/${id}/findings/`),
};

// Threats
export const threatsApi = {
  getThreats: () => request('/threats/threats/'),
  createThreat: (data) => request('/threats/threats/', { method: 'POST', body: JSON.stringify(data) }),
  updateThreat: (id, data) => request(`/threats/threats/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteThreat: (id) => request(`/threats/threats/${id}/`, { method: 'DELETE' }),
};

// Audit
export const auditApi = {
  getEvents: (params = '') => request(`/audit/events/${params ? '?' + params : ''}`),
};

// Records
export const recordsApi = {
  getRecords: () => request('/records/records/'),
  createRecord: (data) => request('/records/records/', { method: 'POST', body: JSON.stringify(data) }),
  verifyChain: () => request('/records/records/verify/'),
};
