import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './AuthPages.css';

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
      await new Promise(resolve => setTimeout(resolve, 1500));
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', formData.email);
      navigate('/dashboard');
    } catch (err) {
      setError('Connection failed. Please try again.');
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

        {/* ── MAIN CARD ── */}
        <div className="auth-card">

          {/* Header */}
          <div className="auth-header">
            <div className="logo-container">
              <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <div className="brand-name-tag">DePIN-Guard</div>
            </div>
            <h1 className="auth-title">Welcome Back 👋</h1>
            <p className="auth-subtitle">
              Login to monitor your <span className="highlight-text">IoT devices</span>,
              view <span className="highlight-text">AI anomaly alerts</span>, and check your
              <span className="highlight-text"> blockchain audit trail</span>.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {error && <div className="error-message"><span>⚠️</span> {error}</div>}

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className="input-wrapper">
                <input
                  type="email" name="email"
                  value={formData.email} onChange={handleChange}
                  placeholder="Enter your email"
                  className={`form-input ${fieldErrors.email ? 'input-error' : ''}`}
                />
              </div>
              {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password} onChange={handleChange}
                  placeholder="Min. 8 characters"
                  className={`form-input ${fieldErrors.password ? 'input-error' : ''}`}
                />
                <button type="button" className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
              {formData.password && (
                <div className="password-strength">
                  <div className={`strength-bar ${formData.password.length >= 8 ? 'strong' : formData.password.length >= 4 ? 'medium' : 'weak'}`} />
                  <span className="strength-label">
                    {formData.password.length >= 8 ? '✅ Strong' : formData.password.length >= 4 ? '⚠️ Medium' : '❌ Too short (min 8)'}
                  </span>
                </div>
              )}
            </div>

            <div className="form-options">
              <label className="checkbox-label">
                <input type="checkbox" name="rememberMe" checked={formData.rememberMe} onChange={handleChange} />
                <span>Remember me</span>
              </label>
              <Link to="/forgot-password" className="forgot-link">Forgot password?</Link>
            </div>

            <button type="submit" className="submit-button" disabled={isLoading}>
              {isLoading ? '🔐 Authenticating...' : 'Login to Dashboard →'}
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

        {/* ── INFO CARDS — BELOW ── */}
        <div className="auth-info-bottom">
          <div className="info-card-bottom">
            <div className="info-icon">🛡️</div>
            <div>
              <h3>Secure Access</h3>
              <p>JWT auth + bcrypt passwords + TLS encryption</p>
            </div>
          </div>
          <div className="info-card-bottom">
            <div className="info-icon">📡</div>
            <div>
              <h3>Live IoT Dashboard</h3>
              <p>Real-time sensor data + anomaly alerts</p>
            </div>
          </div>
          <div className="info-card-bottom">
            <div className="info-icon">🔗</div>
            <div>
              <h3>Blockchain Verified</h3>
              <p>Every event hashed on Hyperledger Fabric</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LoginPage;