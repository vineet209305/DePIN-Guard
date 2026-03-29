import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const [count, setCount] = useState({ devices: 0, threats: 0, uptime: 0 });
  const [menuOpen, setMenuOpen] = useState(false);
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [contactSent, setContactSent] = useState(false);

  useEffect(() => {
    const duration = 2200;
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
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleContactChange = (e) =>
    setContactForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleContactSubmit = (e) => {
    e.preventDefault();
    setContactSent(true);
    setTimeout(() => setContactSent(false), 3000);
    setContactForm({ name: '', email: '', message: '' });
  };

  const features = [
    { icon: '📡', title: 'Real-Time IoT Monitoring', desc: 'Live sensor data — temperature, vibration, pressure, power — streamed instantly to your dashboard.' },
    { icon: '🔗', title: 'Blockchain Trust Layer', desc: 'Every data event is cryptographically hashed on Hyperledger Fabric. Tamper-proof audit trail guaranteed.' },
    { icon: '🤖', title: 'Dual AI Engine', desc: 'LSTM detects real-time anomalies. Graph Neural Network catches systemic fraud across the entire ledger.' },
    { icon: '🛡️', title: 'Enterprise Security', desc: 'JWT + bcrypt + TLS + STRIDE threat modeling — defense in depth at every layer of the stack.' },
  ];

  const useCases = [
    { icon: '🏭', label: 'Smart Manufacturing' },
    { icon: '⚡', label: 'Energy Management' },
    { icon: '🚚', label: 'Supply Chain' },
    { icon: '💊', label: 'Pharma Cold Chain' },
    { icon: '🛢️', label: 'Oil & Gas' },
    { icon: '🏗️', label: 'Structural Monitoring' },
  ];

  const steps = [
    { num: '01', title: 'Sensor Publishes', desc: 'IoT device sends JSON payload over MQTT broker to the ingestion service.' },
    { num: '02', title: 'AI Analyzes', desc: 'LSTM Autoencoder checks reconstruction error — anomaly flagged in milliseconds.' },
    { num: '03', title: 'Blockchain Records', desc: 'SHA-256 hash written to Hyperledger Fabric — immutable, tamper-proof.' },
    { num: '04', title: 'Dashboard Alerts', desc: 'WebSocket pushes live data to React dashboard. Red alert on anomaly detection.' },
  ];

  return (
    <div className="lp-root" id="home">

      {/* ── BACKGROUND ── */}
      <div className="lp-bg">
        <div className="lp-grid" />
        <div className="lp-orb lp-orb1" />
        <div className="lp-orb lp-orb2" />
        <div className="lp-orb lp-orb3" />
      </div>

      {/* ── NAV ── */}
      <nav className="lp-nav">
        <div className="lp-nav-inner">
          <button className="lp-brand" onClick={() => handleNavClick('home')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="lp-brand-icon">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
            DePIN<span className="lp-brand-accent">Guard</span>
          </button>

          <div className="lp-nav-links">
            <button className="lp-nav-link" onClick={() => handleNavClick('features')}>Features</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('how')}>How It Works</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('industries')}>Industries</button>
            <button className="lp-nav-link" onClick={() => handleNavClick('contact')}>Contact</button>
          </div>

          <div className="lp-nav-actions">
            <button className="lp-btn-ghost" onClick={() => navigate('/login')}>Login</button>
            <button className="lp-btn-primary" onClick={() => navigate('/signup')}>Get Started →</button>
          </div>

          <button className="lp-hamburger" onClick={() => setMenuOpen(!menuOpen)}>
            <span className={menuOpen ? 'open' : ''}/><span className={menuOpen ? 'open' : ''}/><span className={menuOpen ? 'open' : ''}/>
          </button>
        </div>

        {menuOpen && (
          <div className="lp-mobile-menu">
            <button className="lp-mobile-link" onClick={() => handleNavClick('features')}>Features</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('how')}>How It Works</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('industries')}>Industries</button>
            <button className="lp-mobile-link" onClick={() => handleNavClick('contact')}>Contact</button>
            <div className="lp-mobile-actions">
              <button className="lp-btn-ghost" onClick={() => navigate('/login')}>Login</button>
              <button className="lp-btn-primary" onClick={() => navigate('/signup')}>Get Started</button>
            </div>
          </div>
        )}
      </nav>

      {/* ── HERO ── */}
      <section className="lp-hero" id="hero">
        <div className="lp-hero-inner">
          <div className="lp-hero-badge">
            <span className="lp-badge-dot" />
            Decentralized IoT Security Platform
          </div>

          <h1 className="lp-hero-title">
            Industrial IoT Security<br />
            <span className="lp-hero-gradient">Powered by AI &amp; Blockchain</span>
          </h1>

          <p className="lp-hero-desc">
            DePIN-Guard combines real-time LSTM anomaly detection with Hyperledger Fabric's
            immutable audit trail — giving industrial operators complete trust in their sensor data.
          </p>

          <div className="lp-hero-btns">
            <button className="lp-btn-cta" onClick={() => navigate('/signup')}>
              Start Monitoring Free
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            <button className="lp-btn-ghost-hero" onClick={() => navigate('/login')}>
              Sign in to Dashboard
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

      {/* ── FEATURES ── */}
      <section className="lp-section lp-section-dark" id="features">
        <div className="lp-section-inner">
          <div className="lp-section-eyebrow">Core Capabilities</div>
          <h2 className="lp-section-title">Everything You Need to Secure Industrial IoT</h2>
          <p className="lp-section-sub">Built on three pillars: real-time intelligence, cryptographic trust, and enterprise-grade security.</p>
          <div className="lp-features-grid">
            {features.map((f, i) => (
              <div className="lp-feature-card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
                <div className="lp-feature-icon-wrap">{f.icon}</div>
                <h3 className="lp-feature-title">{f.title}</h3>
                <p className="lp-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="lp-section" id="how">
        <div className="lp-section-inner">
          <div className="lp-section-eyebrow">The Pipeline</div>
          <h2 className="lp-section-title">From Sensor to Blockchain in Seconds</h2>
          <p className="lp-section-sub">A fully automated, end-to-end data pipeline — no manual intervention required.</p>
          <div className="lp-steps">
            {steps.map((s, i) => (
              <div className="lp-step" key={i}>
                <div className="lp-step-number">{s.num}</div>
                <div className="lp-step-content">
                  <h4 className="lp-step-title">{s.title}</h4>
                  <p className="lp-step-desc">{s.desc}</p>
                </div>
                {i < steps.length - 1 && <div className="lp-step-connector" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── INDUSTRIES ── */}
      <section className="lp-section lp-section-dark" id="industries">
        <div className="lp-section-inner">
          <div className="lp-section-eyebrow">Industries</div>
          <h2 className="lp-section-title">Built for Critical Infrastructure</h2>
          <p className="lp-section-sub">Deployable anywhere industrial sensors generate high-frequency operational data.</p>
          <div className="lp-industries-grid">
            {useCases.map((u, i) => (
              <div className="lp-industry-card" key={i}>
                <span className="lp-industry-icon">{u.icon}</span>
                <span className="lp-industry-label">{u.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CONTACT ── */}
      <section className="lp-section" id="contact">
        <div className="lp-section-inner lp-contact-inner">
          <div className="lp-section-eyebrow">Get In Touch</div>
          <h2 className="lp-section-title">We'd Love to Hear From You</h2>
          <p className="lp-section-sub">Have a question, a feature request, or want to collaborate? Send us a message.</p>

          <div className="lp-contact-card">
            {contactSent ? (
              <div className="lp-contact-success">
                <div className="lp-success-icon">✅</div>
                <h3>Message Sent!</h3>
                <p>We'll get back to you as soon as possible.</p>
              </div>
            ) : (
              <form onSubmit={handleContactSubmit} className="lp-contact-form">
                <div className="lp-form-row">
                  <div className="lp-form-group">
                    <label className="lp-form-label">Your Name</label>
                    <input type="text" name="name" value={contactForm.name} onChange={handleContactChange} placeholder="Enter your name" className="lp-form-input" required />
                  </div>
                  <div className="lp-form-group">
                    <label className="lp-form-label">Email Address</label>
                    <input type="email" name="email" value={contactForm.email} onChange={handleContactChange} placeholder="xyz@company.com" className="lp-form-input" required />
                  </div>
                </div>
                <div className="lp-form-group">
                  <label className="lp-form-label">Message</label>
                  <textarea name="message" value={contactForm.message} onChange={handleContactChange} placeholder="Tell us about your project or question..." className="lp-form-input lp-textarea" rows="5" required />
                </div>
                <button type="submit" className="lp-btn-cta lp-form-submit">
                  Send Message
                  <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                  </svg>
                </button>
              </form>
            )}
          </div>

          {/* Quick Links below form */}
          <div className="lp-contact-links">
            <a href="https://github.com/MohitSingh-2335/DePIN-Guard" target="_blank" rel="noreferrer" className="lp-contact-pill">
              <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/></svg>
              GitHub Repository
            </a>
            <button className="lp-contact-pill" onClick={() => navigate('/signup')}>
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16"><path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" /></svg>
              Create Free Account
            </button>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="lp-cta-section">
        <div className="lp-cta-inner">
          <div className="lp-cta-badge">Ready to get started?</div>
          <h2 className="lp-cta-title">Secure Your IoT Infrastructure Today</h2>
          <p className="lp-cta-desc">Join DePIN-Guard and gain complete visibility, AI-powered anomaly detection, and blockchain-verified trust over your industrial network.</p>
          <div className="lp-cta-btns">
            <button className="lp-btn-cta" onClick={() => navigate('/signup')}>Create Free Account →</button>
            <button className="lp-btn-ghost-hero" onClick={() => navigate('/login')}>Login to Dashboard</button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="lp-footer">
        <div className="lp-footer-inner">
          <div className="lp-footer-top">
            <button className="lp-brand lp-footer-brand" onClick={() => handleNavClick('home')}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="22" height="22">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
              </svg>
              DePIN<span className="lp-brand-accent">Guard</span>
            </button>
            <div className="lp-footer-nav">
              <button className="lp-footer-link" onClick={() => handleNavClick('features')}>Features</button>
              <button className="lp-footer-link" onClick={() => handleNavClick('how')}>How It Works</button>
              <button className="lp-footer-link" onClick={() => handleNavClick('industries')}>Industries</button>
              <button className="lp-footer-link" onClick={() => handleNavClick('contact')}>Contact</button>
              <button className="lp-footer-link" onClick={() => navigate('/login')}>Login</button>
              <button className="lp-footer-link" onClick={() => navigate('/signup')}>Sign Up</button>
            </div>
          </div>
          <div className="lp-footer-bottom">
            <p className="lp-footer-copy">© 2025 DePIN-Guard. All rights reserved.</p>
            <p className="lp-footer-copy">IoT · Blockchain · AI</p>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default LandingPage;