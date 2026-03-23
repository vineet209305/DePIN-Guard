import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [count, setCount] = useState({ devices: 0, threats: 0, uptime: 0 });
  const [menuOpen, setMenuOpen] = useState(false);
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [contactSent, setContactSent] = useState(false);

  useEffect(() => {
    const duration = 2000;
    const steps = 60;
    const interval = duration / steps;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      const p = step / steps;
      setCount({
        devices: Math.floor(p * 5000),
        threats: Math.floor(p * 342),
        uptime: Math.floor(p * 999) / 10,
      });
      if (step >= steps) clearInterval(timer);
    }, interval);
    return () => clearInterval(timer);
  }, []);

  const handleNavClick = (id) => {
    setMenuOpen(false);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleContactChange = (e) => {
    setContactForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleContactSubmit = (e) => {
    e.preventDefault();
    setContactSent(true);
    setTimeout(() => setContactSent(false), 3000);
    setContactForm({ name: '', email: '', message: '' });
  };

  const features = [
    { icon: '📡', title: 'Real-Time IoT Monitoring', desc: 'Live sensor data — temperature, vibration, pressure, power — streamed instantly to your dashboard.' },
    { icon: '🔗', title: 'Blockchain Trust Layer', desc: 'Every data event is cryptographically hashed on Hyperledger Fabric. Tamper-proof audit trail guaranteed.' },
    { icon: '🤖', title: 'AI Anomaly Detection', desc: 'LSTM neural network detects real-time anomalies. GNN catches systemic fraud across the network.' },
    { icon: '🛡️', title: 'Enterprise Security', desc: 'JWT + bcrypt + TLS encryption + STRIDE threat modeling — defense in depth at every layer.' },
  ];

  const useCases = [
    { icon: '🏭', label: 'Smart Manufacturing' },
    { icon: '⚡', label: 'Energy Management' },
    { icon: '🚚', label: 'Supply Chain' },
    { icon: '💊', label: 'Pharma Cold Chain' },
    { icon: '🛢️', label: 'Oil & Gas' },
    { icon: '🏗️', label: 'Structural Monitoring' },
  ];

  return (
    <div className="lp-root" id="home">
      {/* BG */}
      <div className="lp-bg">
        <div className="lp-grid" />
        <div className="lp-orb lp-orb1" />
        <div className="lp-orb lp-orb2" />
      </div>

      {/* NAV */}
      <nav className="lp-nav">
        <div className="lp-nav-inner">
          <div className="lp-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="lp-brand-icon">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
            <span>DePIN-Guard</span>
          </div>

          {/* Desktop Links */}
          <div className="lp-nav-links">
            <button className="lp-nav-link" onClick={() => handleNavClick('home')}>Home</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('features')}>Features</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('how')}>How It Works</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('contact')}>Contact</button>
          </div>

          <div className="lp-nav-actions">
            <button className="lp-btn-ghost" onClick={() => navigate('/login')}>Login</button>
            <button className="lp-btn-primary" onClick={() => navigate('/signup')}>Sign Up</button>
          </div>

          {/* Hamburger */}
          <button className="lp-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            <span /><span /><span />
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="lp-mobile-menu">
            <button className="lp-mobile-link" onClick={() => handleNavClick('home')}>Home</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('features')}>Features</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('how')}>How It Works</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('contact')}>Contact</button>
            <div className="lp-mobile-actions">
              <button className="lp-btn-ghost" onClick={() => navigate('/login')}>Login</button>
              <button className="lp-btn-primary" onClick={() => navigate('/signup')}>Sign Up</button>
            </div>
          </div>
        )}
      </nav>

      {/* HERO */}
      <section className="lp-hero">
        <div className="lp-hero-inner">
          <div className="lp-hero-tag">🔐 IoT + Blockchain + AI</div>
          <h1 className="lp-hero-title">
            Secure Your Industrial<br />
            <span className="lp-accent">IoT Network</span>
          </h1>
          <p className="lp-hero-desc">
            DePIN-Guard combines real-time AI anomaly detection with blockchain-verified audit trails —
            giving you complete trust in your industrial data.
          </p>
          <div className="lp-hero-btns">
            <button className="lp-btn-cta" onClick={() => navigate('/signup')}>
              Start Monitoring Free
              <svg viewBox="0 0 20 20" fill="currentColor" width="18" height="18">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            <button className="lp-btn-outline" onClick={() => navigate('/login')}>
              Already have an account? Login
            </button>
          </div>

          {/* Stats */}
          <div className="lp-stats">
            <div className="lp-stat">
              <div className="lp-stat-num">{count.devices.toLocaleString()}+</div>
              <div className="lp-stat-lbl">Devices Monitored</div>
            </div>
            <div className="lp-stat-div" />
            <div className="lp-stat">
              <div className="lp-stat-num">{count.threats}+</div>
              <div className="lp-stat-lbl">Threats Detected</div>
            </div>
            <div className="lp-stat-div" />
            <div className="lp-stat">
              <div className="lp-stat-num">{count.uptime}%</div>
              <div className="lp-stat-lbl">System Uptime</div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="lp-section lp-section-alt" id="features">
        <div className="lp-section-inner">
          <div className="lp-section-tag">Why DePIN-Guard?</div>
          <h2 className="lp-section-title">Everything You Need to Secure Industrial IoT</h2>
          <div className="lp-features-grid">
            {features.map((f, i) => (
              <div className="lp-feature-card" key={i}>
                <span className="lp-feature-icon">{f.icon}</span>
                <h3 className="lp-feature-title">{f.title}</h3>
                <p className="lp-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="lp-section" id="how">
        <div className="lp-section-inner">
          <div className="lp-section-tag">How It Works</div>
          <h2 className="lp-section-title">From Sensor to Blockchain in Seconds</h2>
          <div className="lp-steps">
            {[
              { num: '01', title: 'Sensor Publishes', desc: 'IoT device sends JSON payload over MQTT broker' },
              { num: '02', title: 'AI Analyzes', desc: 'LSTM model checks for anomalies in real-time' },
              { num: '03', title: 'Blockchain Records', desc: 'SHA-256 hash stored on Hyperledger Fabric' },
              { num: '04', title: 'Dashboard Alerts', desc: 'React dashboard shows live data and anomaly alerts' },
            ].map((s, i) => (
              <div className="lp-step" key={i}>
                <div className="lp-step-num">{s.num}</div>
                <h4 className="lp-step-title">{s.title}</h4>
                <p className="lp-step-desc">{s.desc}</p>
                {i < 3 && <div className="lp-step-arrow">→</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* USE CASES */}
      <section className="lp-section lp-section-alt">
        <div className="lp-section-inner">
          <div className="lp-section-tag">Industries</div>
          <h2 className="lp-section-title">Built for Critical Infrastructure</h2>
          <div className="lp-usecases">
            {useCases.map((u, i) => (
              <div className="lp-usecase" key={i}>
                <span className="lp-usecase-icon">{u.icon}</span>
                <span className="lp-usecase-lbl">{u.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CONTACT — Only shows when scrolled to */}
      <section className="lp-section" id="contact">
        <div className="lp-section-inner lp-contact-inner">
          <div className="lp-section-tag">Contact Us</div>
          <h2 className="lp-section-title">Get In Touch</h2>
          <div className="lp-contact-grid">

            {/* Left: Info */}
            <div className="lp-contact-info">
              <div className="lp-contact-item">
                <span className="lp-contact-icon">📧</span>
                <div>
                  <h4>Email Us</h4>
                  <p>Have questions? Reach out to our team directly.</p>
                  <a href="mailto:depin.guard@example.com" className="lp-contact-link">depin.guard@example.com</a>
                </div>
              </div>
              <div className="lp-contact-item">
                <span className="lp-contact-icon">💻</span>
                <div>
                  <h4>GitHub Repository</h4>
                  <p>Explore the source code and contribute.</p>
                  <a href="https://github.com/MohitSingh-2335/DePIN-Guard" target="_blank" rel="noreferrer" className="lp-contact-link">
                    MohitSingh-2335/DePIN-Guard
                  </a>
                </div>
              </div>
              <div className="lp-contact-item">
                <span className="lp-contact-icon">🚀</span>
                <div>
                  <h4>Get Started</h4>
                  <p>Ready to secure your IoT network?</p>
                  <button className="lp-contact-link" style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }} onClick={() => navigate('/signup')}>
                    Create a free account →
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Contact Form */}
            <div className="lp-contact-form">
              {contactSent ? (
                <div className="lp-contact-success">
                  <span>✅</span>
                  <p>Message sent! We'll get back to you soon.</p>
                </div>
              ) : (
                <form onSubmit={handleContactSubmit}>
                  <div className="lp-form-group">
                    <label>Your Name</label>
                    <input type="text" name="name" value={contactForm.name} onChange={handleContactChange} placeholder="Enter your name" className="lp-form-input" required />
                  </div>
                  <div className="lp-form-group">
                    <label>Email Address</label>
                    <input type="email" name="email" value={contactForm.email} onChange={handleContactChange} placeholder="your@email.com" className="lp-form-input" required />
                  </div>
                  <div className="lp-form-group">
                    <label>Message</label>
                    <textarea name="message" value={contactForm.message} onChange={handleContactChange} placeholder="Write your message..." className="lp-form-input lp-textarea" rows="4" required />
                  </div>
                  <button type="submit" className="lp-btn-cta" style={{ width: '100%', justifyContent: 'center' }}>
                    Send Message
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="lp-cta-section">
        <div className="lp-cta-box">
          <h2 className="lp-cta-title">Ready to Secure Your IoT Network?</h2>
          <p className="lp-cta-desc">Join DePIN-Guard and get real-time anomaly detection with blockchain-verified audit trails.</p>
          <div className="lp-cta-btns">
            <button className="lp-btn-cta" onClick={() => navigate('/signup')}>Create Free Account</button>
            <button className="lp-btn-outline" onClick={() => navigate('/login')}>Login to Dashboard</button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-footer-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
            DePIN-Guard
          </div>
          <div className="lp-footer-links">
            <button className="lp-footer-link" onClick={() => handleNavClick('home')}>Home</button>
            <button className="lp-footer-link" onClick={() => handleNavClick('features')}>Features</button>
            <button className="lp-footer-link" onClick={() => handleNavClick('contact')}>Contact</button>
            <button className="lp-footer-link" onClick={() => navigate('/login')}>Login</button>
            <button className="lp-footer-link" onClick={() => navigate('/signup')}>Sign Up</button>
          </div>
          <p className="lp-footer-copy">© 2025 DePIN-Guard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;