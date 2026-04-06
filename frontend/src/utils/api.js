const BACKEND_URL = import.meta.env.VITE_API_URL || '';
const API_KEY     = import.meta.env.VITE_API_KEY  || '';

export const authenticatedFetch = async (path, options = {}) => {
  // If path is already absolute use it directly, otherwise prepend BACKEND_URL
  // When BACKEND_URL is empty (local dev), path must be relative e.g. /api/dashboard
  const url = path.startsWith('http') ? path : `${BACKEND_URL}${path}`;

  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

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

export const apiGet  = (path)       => authenticatedFetch(path);
export const apiPost = (path, body) => authenticatedFetch(path, {
  method: 'POST',
  body: JSON.stringify(body),
});

export { BACKEND_URL };