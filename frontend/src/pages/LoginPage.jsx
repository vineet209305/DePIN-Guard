import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './AuthPages.css';

const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'https://depin-auth.loca.lt';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '', rememberMe: false });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    if (fieldErrors[name]) setFieldErrors(prev => ({ ...prev, [name]: '' }));
    if (error) setError('');
  };

  const validate = () => {
    const errors = {};
    if (!formData.email) errors.email = 'Email is required.';
    else if (!isValidEmail(formData.email)) errors.email = 'Please enter a valid email address.';
    if (!formData.password) errors.password = 'Password is required.';
    else if (formData.password.length < 8) errors.password = 'Password must be at least 8 characters.';
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validate();
    if (Object.keys(errors).length > 0) { setFieldErrors(errors); return; }

    setIsLoading(true);
    setError('');

    try {
      // ✅ Step 1: Check if user has signed up with this email
      const registeredUsersRaw = localStorage.getItem('registeredUsers');
      const registeredUsers = registeredUsersRaw ? JSON.parse(registeredUsersRaw) : [];

      const matchedUser = registeredUsers.find(
        (u) => u.email.toLowerCase() === formData.email.toLowerCase()
      );

      if (!matchedUser) {
      
        setError('No account found with this email. Please sign up first.');
        setIsLoading(false);
        return;
      }

     
      let token = null;
      try {
        const response = await fetch(`${AUTH_URL}/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'bypass-tunnel-reminder': 'true',
            'User-Agent': 'depin-guard-bot',
          },
          body: JSON.stringify({
            username: matchedUser.email,
            password: formData.password,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          token = data.access_token;
        } else {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || 'Invalid credentials');
        }
      } catch (authErr) {
        // ✅ Step 3: Auth service offline — check password locally
        if (matchedUser.password !== formData.password) {
          setError('Incorrect password. Please try again.');
          setIsLoading(false);
          return;
        }
        token = 'local-token-' + Date.now();
        console.warn('⚠️ Auth service unreachable — using local validation');
      }

      // ✅ Step 4: Login successful
      localStorage.setItem('token', token);
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', formData.email);
      localStorage.setItem('userName', matchedUser.fullName || '');

      navigate('/dashboard');

    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-background">
        <div className="grid-overlay" />
        <div className="floating-particles">
          {[...Array(15)].map((_, i) => (
            <div key={i} className="particle" style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${15 + Math.random() * 10}s`
            }} />
          ))}
        </div>
      </div>

      <div className="auth-wrapper">
        <div className="auth-card">

          <div className="auth-header">
            <div className="logo-container">
              <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 17L12 22L22 17" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 12L12 17L22 12" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="brand-name-tag">DePIN-Guard</div>
            </div>
            <h1 className="auth-title">Welcome Back </h1>
            <p className="auth-subtitle">
              Login to monitor your <span className="highlight-text">IoT devices</span>,
              view <span className="highlight-text">AI anomaly alerts</span>, and check your
              <span className="highlight-text"> blockchain audit trail</span>.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {error && <div className="error-message"><span>⚠️</span> {error}</div>}

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email" name="email"
                value={formData.email} onChange={handleChange}
                placeholder="your@email.com"
                className={`form-input ${fieldErrors.email ? 'input-error' : ''}`}
              />
              {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password} onChange={handleChange}
                  placeholder="Enter your password"
                  className={`form-input ${fieldErrors.password ? 'input-error' : ''}`}
                />
                <button type="button" className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
            </div>

            <div className="form-options">
              <label className="checkbox-label">
                <input type="checkbox" name="rememberMe" checked={formData.rememberMe} onChange={handleChange} />
                <span>Remember me</span>
              </label>
            </div>

            <button type="submit" className="submit-button" disabled={isLoading}>
              {isLoading ? '🔐 Signing in...' : 'Login to Dashboard →'}
            </button>
          </form>

          <div className="auth-footer">
            <p className="footer-text">
              Don't have an account? <Link to="/signup" className="footer-link">Sign up free</Link>
            </p>
            <p className="footer-text" style={{ marginTop: '0.5rem' }}>
              <Link to="/" className="footer-link">← Back to Home</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;