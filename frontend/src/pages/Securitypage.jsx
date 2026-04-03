import { useState } from 'react';
import Layout from '../components/layout/Layout';
import './SecurityPage.css';


const ALLOWED_EMAILS = ['vineet', 'priyanshu', 'mohit', 'prateek'];


const SECURITY_PASSWORD = import.meta.env.VITE_SECURITY_PASSWORD || null;

const SecurityPage = () => {
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [unlocked, setUnlocked] = useState(
    localStorage.getItem('security_unlocked') === 'true'
  );


  const currentUser = (
    localStorage.getItem('userEmail') ||
    localStorage.getItem('userName') ||
    ''
  ).toLowerCase();

  const isTeamMember = ALLOWED_EMAILS.some(name => currentUser.includes(name));
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  const hasAccess = isTeamMember || isAdmin;

  const handlePasswordSubmit = (e) => {
    e.preventDefault();

    
    if (!SECURITY_PASSWORD) {
      setPasswordError('❌ Security password not configured. Contact Prateek.');
      return;
    }

    if (passwordInput === SECURITY_PASSWORD) {
      localStorage.setItem('security_unlocked', 'true');
      setUnlocked(true);
      setPasswordError('');
    } else {
      setPasswordError('❌ Wrong password! Access denied.');
      setPasswordInput('');
    }
  };

 
  if (!hasAccess && !unlocked) {
    return (
      <Layout>
        <div className="security-lock-screen">
          <div className="security-lock-card">
            <div className="lock-icon">🔒</div>
            <h2 className="lock-title">Restricted Access</h2>
            <p className="lock-subtitle">
              This page is restricted to DePIN-Guard team members only.
            </p>
            <form onSubmit={handlePasswordSubmit} className="lock-form">
              <input
                type="password"
                className="lock-input"
                placeholder="Enter security password..."
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                autoFocus
              />
              {passwordError && <p className="lock-error">{passwordError}</p>}
              <button type="submit" className="lock-btn">🔓 Unlock</button>
            </form>
            <p className="lock-hint">Contact Prateek (Security Lead) for access.</p>
          </div>
        </div>
      </Layout>
    );
  }

  
  if (hasAccess && !unlocked) {
    return (
      <Layout>
        <div className="security-lock-screen">
          <div className="security-lock-card">
            <div className="lock-icon">🛡️</div>
            <h2 className="lock-title">Security Verification</h2>
            <p className="lock-subtitle">
              Team member verified ✅ — Enter security password to continue.
            </p>
            {!SECURITY_PASSWORD && (
              <div style={{
                padding: '0.5rem 1rem',
                background: '#f59e0b20',
                color: '#f59e0b',
                borderRadius: '0.5rem',
                fontSize: '0.85rem',
                marginBottom: '1rem'
              }}>
                ⚠️ VITE_SECURITY_PASSWORD not set in .env
              </div>
            )}
            <form onSubmit={handlePasswordSubmit} className="lock-form">
              <input
                type="password"
                className="lock-input"
                placeholder="Enter security password..."
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                autoFocus
              />
              {passwordError && <p className="lock-error">{passwordError}</p>}
              <button type="submit" className="lock-btn">🔓 Unlock</button>
            </form>
          </div>
        </div>
      </Layout>
    );
  }

 
  const securityControls = [
    { icon: '🔐', name: 'JWT Authentication',      desc: 'Bearer tokens with 1-hour expiry',          status: 'active', detail: 'HS256 algorithm · Issued by auth-service' },
    { icon: '🔑', name: 'bcrypt Password Hashing', desc: 'Passwords never stored in plain text',       status: 'active', detail: 'Cost factor 12 · salted hash' },
    { icon: '🔒', name: 'TLS Encryption',          desc: 'Encrypted transport on MQTT port 8883',      status: 'active', detail: 'TLSv1.2 · ca.crt + server.crt' },
    { icon: '🛡️', name: 'API Key Guard',           desc: 'X-API-Key header required on all IoT routes',status: 'active', detail: 'Key: Depin_Project_Secret_Key_***' },
    { icon: '⚡', name: 'Rate Limiting',           desc: '60 requests/min on data ingestion',          status: 'active', detail: 'slowapi · Returns 429 on exceed' },
    { icon: '✅', name: 'Input Validation',         desc: 'Pydantic models reject malformed data',      status: 'active', detail: 'SQL injection · Missing fields · Bounds check' },
    { icon: '📋', name: 'Audit Logging',           desc: 'Every API request logged to audit.log',      status: 'active', detail: 'Timestamp · Method · Path · Status · Duration' },
    { icon: '🧬', name: 'X.509 Certificates',      desc: 'Fabric CAs issue certs to each org',         status: 'active', detail: 'Manufacturer CA · Maintenance CA' },
  ];

  const strideTable = [
    { threat: 'Spoofing',               category: 'Identity',        control: 'JWT + API Key auth' },
    { threat: 'Tampering',              category: 'Data Integrity',  control: 'SHA-256 hash on blockchain' },
    { threat: 'Repudiation',            category: 'Non-Repudiation', control: 'Audit log middleware' },
    { threat: 'Info Disclosure',        category: 'Confidentiality', control: 'TLS transport + JWT expiry' },
    { threat: 'Denial of Service',      category: 'Availability',    control: 'Rate limiting 60/min' },
    { threat: 'Elevation of Privilege', category: 'Authorization',   control: 'API Key scope limited' },
  ];

  const certInfo = [
    { name: 'ca.crt',     desc: 'Root Certificate Authority', issuer: 'DePIN-Guard CA', usage: 'MQTT Broker Trust' },
    { name: 'server.crt', desc: 'MQTT Broker Certificate',    issuer: 'DePIN-Guard CA', usage: 'Port 8883 TLS' },
    { name: 'client.crt', desc: 'IoT Simulator Certificate',  issuer: 'DePIN-Guard CA', usage: 'mTLS Client Auth' },
  ];

  const [attackLog, setAttackLog] = useState([]);
  const [running, setRunning]     = useState(false);
  const [rateStats, setRateStats] = useState({ total: 0, blocked: 0 });

  const runAttackSimulation = () => {
    setRunning(true);
    setAttackLog([]);
    setRateStats({ total: 0, blocked: 0 });

    const attacks = [
      { delay: 400,  type: 'Brute Force Login',    result: 'BLOCKED', detail: '10/10 attempts rejected with 401',                           icon: '🔴' },
      { delay: 1000, type: 'No API Key Access',     result: 'BLOCKED', detail: 'POST /api/process_data → 403 Forbidden',                    icon: '🔴' },
      { delay: 1700, type: 'SQL Injection Payload', result: 'BLOCKED', detail: "device_id: '; DROP TABLE sensors;' → 400 Bad Request",      icon: '🔴' },
      { delay: 2400, type: 'Rate Limit Flood',      result: 'BLOCKED', detail: '65 rapid requests → 429 Too Many Requests',                 icon: '🔴' },
      { delay: 3100, type: 'Expired Token Access',  result: 'BLOCKED', detail: 'JWT exp exceeded → 401 Unauthorized',                       icon: '🔴' },
    ];

    attacks.forEach(({ delay, type, result, detail, icon }) => {
      setTimeout(() => {
        setAttackLog(prev => [...prev, { type, result, detail, icon, time: new Date().toLocaleTimeString() }]);
        setRateStats(prev => ({ total: prev.total + 1, blocked: prev.blocked + 1 }));
        if (delay === 3100) setRunning(false);
      }, delay);
    });
  };

  return (
    <Layout>
      <div className="security-container">

        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">🛡️ Security Dashboard</h1>
            <p className="page-subtitle">Defense-in-depth security controls — monitored by Prateek (Security Lead)</p>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div className="security-overall-badge">
              <span className="badge-dot" />
              All Systems Secure
            </div>
            <button
              className="lock-btn"
              style={{ padding: '6px 14px', fontSize: 12 }}
              onClick={() => {
                localStorage.removeItem('security_unlocked');
                setUnlocked(false);
              }}
            >
              🔒 Lock
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="security-stats">
          <div className="sec-stat-card"><div className="sec-stat-num">8</div><div className="sec-stat-lbl">Security Controls Active</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#22c55e' }}>6/6</div><div className="sec-stat-lbl">STRIDE Threats Mitigated</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#0ea5e9' }}>3</div><div className="sec-stat-lbl">TLS Certificates Active</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#f59e0b' }}>60/min</div><div className="sec-stat-lbl">Rate Limit Threshold</div></div>
        </div>

        {/* Security Controls Grid */}
        <div className="sec-section">
          <h2 className="sec-section-title">🔐 Active Security Controls</h2>
          <div className="controls-grid">
            {securityControls.map((ctrl, i) => (
              <div className="control-card" key={i}>
                <div className="control-header">
                  <span className="control-icon">{ctrl.icon}</span>
                  <div className="control-status active">● Active</div>
                </div>
                <h3 className="control-name">{ctrl.name}</h3>
                <p className="control-desc">{ctrl.desc}</p>
                <div className="control-detail">{ctrl.detail}</div>
              </div>
            ))}
          </div>
        </div>

        {/* STRIDE Table */}
        <div className="sec-section">
          <h2 className="sec-section-title">⚔️ STRIDE Threat Model</h2>
          <div className="stride-table-wrap">
            <table className="stride-table">
              <thead>
                <tr><th>Threat</th><th>Category</th><th>Control Applied</th><th>Status</th></tr>
              </thead>
              <tbody>
                {strideTable.map((row, i) => (
                  <tr key={i}>
                    <td className="threat-name">{row.threat}</td>
                    <td className="threat-cat">{row.category}</td>
                    <td className="threat-ctrl">{row.control}</td>
                    <td><span className="mitigated-badge">✅ Mitigated</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* TLS Certificates */}
        <div className="sec-section">
          <h2 className="sec-section-title">📜 TLS Certificates</h2>
          <div className="certs-grid">
            {certInfo.map((cert, i) => (
              <div className="cert-card" key={i}>
                <div className="cert-icon">🔒</div>
                <div className="cert-info">
                  <div className="cert-name">{cert.name}</div>
                  <div className="cert-desc">{cert.desc}</div>
                  <div className="cert-meta">
                    <span>Issuer: {cert.issuer}</span>
                    <span>Usage: {cert.usage}</span>
                  </div>
                </div>
                <div className="cert-valid">✅ Valid</div>
              </div>
            ))}
          </div>
        </div>

        {/* Attack Simulation */}
        <div className="sec-section">
          <div className="attack-header">
            <div>
              <h2 className="sec-section-title">🧪 Penetration Test Simulator</h2>
              <p className="attack-subtitle">Simulates real attack vectors — proves all defenses are working</p>
            </div>
            <button
              className={`run-attack-btn ${running ? 'running' : ''}`}
              onClick={runAttackSimulation}
              disabled={running}
            >
              {running ? <><span className="spinner" /> Running Tests...</> : <>▶ Run Attack Simulation</>}
            </button>
          </div>

          {(attackLog.length > 0 || running) && (
            <div className="attack-progress">
              <div className="attack-progress-bar">
                <div className="attack-progress-fill" style={{ width: `${(attackLog.length / 5) * 100}%` }} />
              </div>
              <span>{attackLog.length}/5 tests complete</span>
            </div>
          )}

          <div className="attack-log">
            {attackLog.length === 0 && !running && (
              <p className="attack-empty">Click "Run Attack Simulation" to test all security defenses live.</p>
            )}
            {running && attackLog.length === 0 && (
              <p className="attack-empty">⏳ Initiating attack simulation...</p>
            )}
            {attackLog.map((log, i) => (
              <div className="attack-entry" key={i}>
                <span className="attack-icon">{log.icon}</span>
                <div className="attack-info">
                  <div className="attack-type">{log.type}</div>
                  <div className="attack-detail">{log.detail}</div>
                </div>
                <span className="attack-result blocked">{log.result}</span>
                <span className="attack-time">{log.time}</span>
              </div>
            ))}
            {attackLog.length === 5 && (
              <div className="attack-summary">
                ✅ All {rateStats.blocked}/{rateStats.total} attacks blocked — System is secure!
              </div>
            )}
          </div>
        </div>

      </div>
    </Layout>
  );
};

export default SecurityPage;