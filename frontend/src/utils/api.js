// frontend/src/utils/api.js
// In local dev: uses Vite proxy (relative paths → localhost:8000)
// In production/localtunnel: set VITE_API_URL in .env to override

const BACKEND_URL = import.meta.env.VITE_API_URL || '';

export const authenticatedFetch = async (path, options = {}) => {
  const url = path.startsWith('http') ? path : `${BACKEND_URL}${path}`;

  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': import.meta.env.VITE_API_KEY || 'Depin_Project_Secret_Key_999',
    'bypass-tunnel-reminder': 'true',
    'User-Agent': 'depin-guard-bot',
    ...options.headers,
  };

  if (token && token !== 'null') {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('isAuthenticated');
      window.location.href = '/login';
      return null;
    }

    return response;
  } catch (err) {
    console.error(`[authenticatedFetch] Failed to reach ${url}:`, err.message);
    throw err;
  }
};

export const apiGet = (path) => authenticatedFetch(path);

export const apiPost = (path, body) =>
  authenticatedFetch(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });

export { BACKEND_URL };