const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const TOKEN_KEY = 'finsec_access_token';
const REFRESH_KEY = 'finsec_refresh_token';

export const tokenStorage = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access, refresh) => {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY),
};

async function refreshAccessToken() {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) throw new Error('No refresh token');
  const res = await fetch(`${BASE_URL}/auth/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    tokenStorage.clear();
    window.location.href = '/login';
    throw new Error('Session expired. Please log in again.');
  }
  const data = await res.json();
  tokenStorage.set(data.access, null);
  return data.access;
}

async function request(path, options = {}, retry = true) {
  const token = tokenStorage.getAccess();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // Token expired — attempt a silent refresh then retry once
  if (res.status === 401 && retry) {
    try {
      await refreshAccessToken();
      return request(path, options, false);
    } catch {
      throw new Error('Unauthorized. Please log in.');
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  // 204 No Content has no body
  if (res.status === 204) return null;
  return res.json();
}

// Auth
export const authApi = {
  login: async (username, password) => {
    const res = await fetch(`${BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || 'Login failed');
    }
    const data = await res.json();
    tokenStorage.set(data.access, data.refresh);
    return data;
  },
  logout: () => {
    tokenStorage.clear();
    window.location.href = '/login';
  },
  register: (username, email, password) =>
    fetch(`${BASE_URL}/scanner/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    }).then(res => {
      if (!res.ok) return res.json().then(e => { throw new Error(e.detail || 'Registration failed'); });
      return res.json();
    }),
};

// Scanner
export const scannerApi = {
  getScans: () => request('/scanner/scans/'),
  getScan: (id) => request(`/scanner/scans/${id}/`),
  createScan: (data) => request('/scanner/scans/', { method: 'POST', body: JSON.stringify(data) }),
  getFindings: (id) => request(`/scanner/scans/${id}/findings/`),
  getStatistics: (id) => request(`/scanner/scans/${id}/statistics/`),
  getRisk: (id) => request(`/scanner/scans/${id}/risk/`),
  getOnChainData: (id) => request(`/scanner/scans/${id}/`).then(s => s.metadata?.onchain_data || null),
  getDashboardScans: () => request('/scanner/scans/?ordering=-created_at&page_size=100'),
};

// Threats
export const threatsApi = {
  getThreats: () => request('/threats/threats/'),
  getThreat: (id) => request(`/threats/threats/${id}/`),
  createThreat: (data) => request('/threats/threats/', { method: 'POST', body: JSON.stringify(data) }),
  updateThreat: (id, data) => request(`/threats/threats/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteThreat: (id) => request(`/threats/threats/${id}/`, { method: 'DELETE' }),
};

// Audit
export const auditApi = {
  getEvents: (params = '') => request(`/audit/events/${params ? '?' + params : ''}`),
  getEvent: (id) => request(`/audit/events/${id}/`),
};

// Records
export const recordsApi = {
  getRecords: () => request('/records/records/'),
  createRecord: (data) => request('/records/records/', { method: 'POST', body: JSON.stringify(data) }),
  verifyChain: () => request('/records/records/verify/'),
};
