export const getStoredToken = () => (
  localStorage.getItem('token') || sessionStorage.getItem('token') || ''
);

export const storeAuthToken = (token, rememberMe) => {
  if (rememberMe) {
    localStorage.setItem('token', token);
    sessionStorage.removeItem('token');
  } else {
    sessionStorage.setItem('token', token);
    localStorage.removeItem('token');
  }
};

export const clearAuthStorage = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('isAuthenticated');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('userName');
  localStorage.removeItem('userPhone');
  localStorage.removeItem('savedEmail');
  localStorage.removeItem('rememberMe');
  sessionStorage.removeItem('token');
};

export const storeUserProfile = (profile = {}) => {
  if (profile.email) {
    localStorage.setItem('userEmail', profile.email);
    localStorage.setItem('savedEmail', profile.email);
  }
  if (profile.full_name) {
    localStorage.setItem('userName', profile.full_name);
  }
  if (profile.phone) {
    localStorage.setItem('userPhone', profile.phone);
  }
};