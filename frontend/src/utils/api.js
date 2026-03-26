// frontend/src/utils/api.js
// Har fetch call mein automatically token add ho jayega

export const authenticatedFetch = async (url, options = {}) => {
  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'Depin_Project_Secret_Key_999',
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  const response = await fetch(url, { ...options, headers });

  // Agar token expire ho gaya to login pe bhej do
  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('isAuthenticated');
    window.location.href = '/login';
    return null;
  }

  return response;
};