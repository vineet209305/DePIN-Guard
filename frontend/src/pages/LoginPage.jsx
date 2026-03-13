import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './AuthPages.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Email validation helper
  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    if (error) setError(''); // Type karte hi error hat jaye
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Step 1: Frontend Validation
    if (!isValidEmail(formData.email)) {
      setError('Please enter a valid email address.');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters.');
      setIsLoading(false);
      return;
    }

    try {
      // Step 2: Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Step 3: Login Logic (Ab ye aage jane dega)
      // Note: Asli project mein yahan backend check hota hai
      console.log("Logging in with:", formData.email);
      
      localStorage.setItem('isAuthenticated', 'true');
      localStorage.setItem('userEmail', formData.email);
      
      // Step 4: Redirect to Dashboard
      navigate('/dashboard'); 
      
    } catch (err) {
      setError('Connection failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Background with Particles */}
      <div className="auth-background">
        <div className="grid-overlay"></div>
        <div className="floating-particles">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="particle" style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${15 + Math.random() * 10}s`
            }}></div>
          ))}
        </div>
      </div>

      <div className="auth-content">
        {/* LEFT SIDE: LOGIN CARD */}
        <div className="auth-card">
          <div className="auth-header">
            <div className="logo-container">
              <svg className="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <h1 className="auth-title">Welcome Back</h1>
            </div>
            <p className="auth-subtitle">Login to manage your IoT network</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            {error && (
              <div className="error-message">
                <span>⚠️</span> {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className="input-wrapper">
                <input 
                  type="email" 
                  name="email" 
                  value={formData.email} 
                  onChange={handleChange} 
                  placeholder="Enter your email" 
                  className="form-input" 
                  required 
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="input-wrapper">
                <input 
                  type={showPassword ? "text" : "password"} 
                  name="password" 
                  value={formData.password} 
                  onChange={handleChange} 
                  placeholder="••••••••" 
                  className="form-input" 
                  required 
                />
                <button 
                  type="button" 
                  className="password-toggle-icon" 
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <div className="form-options">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  name="rememberMe" 
                  checked={formData.rememberMe} 
                  onChange={handleChange} 
                />
                <span>Remember me</span>
              </label>
              <Link to="/forgot-password" size="small" className="forgot-link">
                Forgot password?
              </Link>
            </div>

            <button type="submit" className="submit-button" disabled={isLoading}>
              {isLoading ? "Authenticating..." : "Login"}
            </button>
          </form>

          <div className="auth-footer">
            <p className="footer-text">
              Don't have an account? <Link to="/signup" className="footer-link">Sign up</Link>
            </p>
          </div>
        </div>

        {/* RIGHT SIDE: INFO SECTION */}
        <div className="auth-info">
          <div className="info-card">
            <div className="info-icon">🛡️</div>
            <h3>Secure Access</h3>
            <p>Your data is protected with industry-standard encryption.</p>
          </div>
          <div className="info-card">
            <div className="info-icon">📡</div>
            <h3>Real-time Monitoring</h3>
            <p>Get instant updates from all your connected IoT devices.</p>
          </div>
          <div className="info-card">
            <div className="info-icon">🚀</div>
            <h3>Fast Performance</h3>
            <p>Optimized dashboard for smooth experience.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;