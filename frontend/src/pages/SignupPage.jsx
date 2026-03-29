import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './AuthPages.css';

const SignupPage = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ fullName: '', email: '', password: '', confirmPassword: '', agreeToTerms: false });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const getPasswordStrength = (password) => {
    if (!password) return 0;
    let s = 0;
    if (password.length >= 8) s++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) s++;
    if (/\d/.test(password)) s++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) s++;
    return s;
  };

  const strength = getPasswordStrength(formData.password);
  const getStrengthInfo = () => {
    if (strength <= 1) return { label: '❌ Weak (min 8 chars)', cls: 'weak' };
    if (strength === 2) return { label: '⚠️ Medium', cls: 'medium' };
    return { label: '✅ Strong', cls: 'strong' };
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    if (fieldErrors[name]) setFieldErrors(prev => ({ ...prev, [name]: '' }));
    if (error) setError('');
  };

  const validate = () => {
    const errors = {};
    if (!formData.fullName.trim()) errors.fullName = 'Full name is required.';
    if (!formData.email) errors.email = 'Email is required.';
    else if (!isValidEmail(formData.email)) errors.email = 'Please enter a valid email address.';
    if (!formData.password) errors.password = 'Password is required.';
    else if (formData.password.length < 8) errors.password = 'Password must be at least 8 characters.';
    if (!formData.confirmPassword) errors.confirmPassword = 'Please confirm your password.';
    else if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match.';
    if (!formData.agreeToTerms) errors.agreeToTerms = 'Please agree to the terms.';
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validate();
    if (Object.keys(errors).length > 0) { setFieldErrors(errors); return; }

    setIsLoading(true);
    setError('');

    try {
      
      const registeredUsersRaw = localStorage.getItem('registeredUsers');
      const registeredUsers = registeredUsersRaw ? JSON.parse(registeredUsersRaw) : [];

      const alreadyExists = registeredUsers.find(
        (u) => u.email.toLowerCase() === formData.email.toLowerCase()
      );

      if (alreadyExists) {
        setError('An account with this email already exists. Please login.');
        setIsLoading(false);
        return;
      }

     
      const newUser = {
        fullName: formData.fullName.trim(),
        email: formData.email.toLowerCase(),
        password: formData.password,
        createdAt: new Date().toISOString(),
      };

      registeredUsers.push(newUser);
      localStorage.setItem('registeredUsers', JSON.stringify(registeredUsers));

    
      await new Promise(resolve => setTimeout(resolve, 1000));

      alert(`✅ Account created successfully!\nWelcome, ${newUser.fullName}!\nPlease login to continue.`);
      navigate('/login');

    } catch (err) {
      setError('Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const { label: strengthLabel, cls: strengthCls } = getStrengthInfo();

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
                <path d="M12 2L2 7L12 12L22 7L12 2Z" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <div className="brand-name-tag">DePIN-Guard</div>
            </div>
            <h1 className="auth-title">Create Your Account </h1>
            <p className="auth-subtitle">
              Join DePIN-Guard to monitor your <span className="highlight-text">IoT devices</span>,
              detect <span className="highlight-text">AI anomalies</span>, and secure data with
              <span className="highlight-text"> blockchain technology</span>.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            {error && <div className="error-message"><span>⚠️</span> {error}</div>}

            <div className="form-group">
              <label className="form-label">Full Name</label>
              <div className="input-wrapper">
                <input type="text" name="fullName" value={formData.fullName} onChange={handleChange}
                  placeholder="Enter your full name"
                  className={`form-input ${fieldErrors.fullName ? 'input-error' : ''}`} />
              </div>
              {fieldErrors.fullName && <span className="field-error">{fieldErrors.fullName}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <div className="input-wrapper">
                <input type="email" name="email" value={formData.email} onChange={handleChange}
                  placeholder="your@email.com"
                  className={`form-input ${fieldErrors.email ? 'input-error' : ''}`} />
              </div>
              {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <div className="input-wrapper">
                <input type={showPassword ? 'text' : 'password'} name="password"
                  value={formData.password} onChange={handleChange}
                  placeholder="Min. 8 characters"
                  className={`form-input ${fieldErrors.password ? 'input-error' : ''}`} />
                <button type="button" className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
              {formData.password && (
                <div className="password-strength">
                  <div className={`strength-bar ${strengthCls}`} />
                  <span className="strength-label">{strengthLabel}</span>
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <div className="input-wrapper">
                <input type={showConfirm ? 'text' : 'password'} name="confirmPassword"
                  value={formData.confirmPassword} onChange={handleChange}
                  placeholder="Re-enter password"
                  className={`form-input ${fieldErrors.confirmPassword ? 'input-error' : ''}`} />
                <button type="button" className="password-toggle-icon" onClick={() => setShowConfirm(!showConfirm)}>
                  {showConfirm ? '🙈' : '👁️'}
                </button>
              </div>
              {fieldErrors.confirmPassword && <span className="field-error">{fieldErrors.confirmPassword}</span>}
              {formData.confirmPassword && formData.password && (
                <span className="field-error" style={{ color: formData.password === formData.confirmPassword ? '#22c55e' : '#ff6666' }}>
                  {formData.password === formData.confirmPassword ? '✅ Passwords match' : '❌ Passwords do not match'}
                </span>
              )}
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input type="checkbox" name="agreeToTerms" checked={formData.agreeToTerms} onChange={handleChange} />
                <span>I agree to the <Link to="/terms" className="forgot-link">Terms</Link> & <Link to="/privacy" className="forgot-link">Privacy Policy</Link></span>
              </label>
              {fieldErrors.agreeToTerms && <span className="field-error">{fieldErrors.agreeToTerms}</span>}
            </div>

            <button type="submit" className="submit-button" disabled={isLoading}>
              {isLoading ? '🔐 Creating account...' : 'Create Account & Start Monitoring →'}
            </button>
          </form>

          <div className="auth-footer">
            <p className="footer-text">
              Already have an account? <Link to="/login" className="footer-link">Login</Link>
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

export default SignupPage;