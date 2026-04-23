// Utility to get the JWT access token from localStorage
export function getAccessToken() {
  return localStorage.getItem('access_token');
}

// Utility to add Authorization header to fetch requests
export function authFetch(url, options = {}) {
  const token = getAccessToken();
  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  return fetch(url, { ...options, headers });
}
