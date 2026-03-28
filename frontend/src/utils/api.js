// frontend/src/utils/api.js
// Permanent backend URL — never changes (localtunnel subdomain)
const BACKEND_URL = import.meta.env.VITE_API_URL || 'https://depin-backend.loca.lt';

export const authenticatedFetch = async (path, options = {}) => {
  // Accept either a full URL or just a path like /api/dashboard
  const url = path.startsWith('http') ? path : `${BACKEND_URL}${path}`;

  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'Depin_Project_Secret_Key_999',
    // LocalTunnel bypass — prevents the "click to continue" warning page
    'bypass-tunnel-reminder': 'true',
    'User-Agent': 'depin-guard-bot',
    ...options.headers,
  };

  // Only add Authorization if we actually have a token
  if (token && token !== 'null') {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // If token expired, clear auth and redirect to login
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

// Helper: GET request shorthand
export const apiGet = (path) => authenticatedFetch(path);

// Helper: POST request shorthand
export const apiPost = (path, body) =>
  authenticatedFetch(path, {
    method: 'POST',
    body: JSON.stringify(body),
  });

export { BACKEND_URL };