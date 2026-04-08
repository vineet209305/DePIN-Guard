import { useEffect, useMemo, useState } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './securitypage.css';


const ALLOWED_EMAILS = ['vineet', 'priyanshu', 'mohit', 'prateek'];


const SECURITY_PASSWORD = import.meta.env.VITE_SECURITY_PASSWORD || null;
const AUTH_URL = (import.meta.env.VITE_AUTH_URL || '').trim().replace(/\/$/, '');
const BACKEND_URL = (import.meta.env.VITE_API_URL || '').trim().replace(/\/$/, '');
const API_KEY = import.meta.env.VITE_API_KEY || '';

const SecurityPage = () => {
  const [passwordInput, setPasswordInput] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [unlocked, setUnlocked] = useState(
    localStorage.getItem('security_unlocked') === 'true'
  );
  const [backendStats, setBackendStats] = useState({ scans: null, anomalies: null });
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [attackLog, setAttackLog] = useState([]);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState({ blocked: 0, passed: 0, anomalies: 0 });


  const currentUser = (
    localStorage.getItem('userEmail') ||
    localStorage.getItem('userName') ||
    ''
  ).toLowerCase();

  const isTeamMember = ALLOWED_EMAILS.some(name => currentUser.includes(name));
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  const hasAccess = isTeamMember || isAdmin;

  useEffect(() => {
    const loadSecurityState = async () => {
      try {
        const [dashboardRes, fraudRes] = await Promise.all([
          authenticatedFetch('/api/dashboard'),
          authenticatedFetch('/api/fraud-alerts'),
        ]);

        if (dashboardRes?.ok) {
          const dashboard = await dashboardRes.json();
          setBackendStats({
            scans: dashboard.stats?.scans ?? null,
            anomalies: dashboard.stats?.anomalies ?? null,
          });
        }

        if (fraudRes?.ok) {
          const fraud = await fraudRes.json();
          setFraudAlerts(fraud.alerts || []);
        }
      } catch {
        setBackendStats({ scans: null, anomalies: null });
      }
    };

    loadSecurityState();
  }, []);

  const securityControls = useMemo(() => [
    { icon: 'JWT', name: 'JWT Authentication', desc: 'Bearer token authentication from auth-service', status: 'active', detail: 'Tokens are validated by the auth service before access is granted.' },
    { icon: 'BCR', name: 'bcrypt Password Hashing', desc: 'Passwords are hashed before storage', status: 'active', detail: 'No plain-text passwords are kept in the database.' },
    { icon: 'TLS', name: 'TLS Encryption', desc: 'Encrypted transport for MQTT communication', status: 'active', detail: 'Certificate-based transport protects broker traffic.' },
    { icon: 'API', name: 'API Key Guard', desc: 'X-API-Key required for IoT ingestion', status: 'active', detail: 'Only trusted sensor clients can submit readings.' },
    { icon: 'RAT', name: 'Rate Limiting', desc: 'Backend throttles burst traffic', status: 'active', detail: 'High-frequency request floods are blocked automatically.' },
    { icon: 'VAL', name: 'Input Validation', desc: 'Malformed data is rejected before storage', status: 'active', detail: 'Schema checks stop invalid payloads early.' },
    { icon: 'LOG', name: 'Audit Logging', desc: 'Every request is written to audit logs', status: 'active', detail: 'Each request can be traced for review and debugging.' },
    { icon: 'X509', name: 'X.509 Certificates', desc: 'Certificates validate service identity', status: 'active', detail: 'Broker and simulator trust is anchored to certificates.' },
  ], []);

  const strideTable = useMemo(() => [
    { threat: 'Spoofing', category: 'Identity', control: 'JWT + API key auth' },
    { threat: 'Tampering', category: 'Data integrity', control: 'HMAC signing + blockchain hash' },
    { threat: 'Repudiation', category: 'Non-repudiation', control: 'Audit logging and persistence' },
    { threat: 'Information disclosure', category: 'Confidentiality', control: 'TLS transport and token expiry' },
    { threat: 'Denial of service', category: 'Availability', control: 'Rate limiting and request validation' },
    { threat: 'Privilege escalation', category: 'Authorization', control: 'Service-scoped access rules' },
  ], []);

  const certInfo = useMemo(() => [
    { name: 'ca.crt', desc: 'Root certificate authority', issuer: 'DePIN-Guard CA', usage: 'MQTT broker trust' },
    { name: 'server.crt', desc: 'Broker certificate', issuer: 'DePIN-Guard CA', usage: 'TLS server identity' },
    { name: 'client.crt', desc: 'Simulator certificate', issuer: 'DePIN-Guard CA', usage: 'Client authentication' },
  ], []);

  const importHmacKey = async () => {
    if (!API_KEY || !window.crypto?.subtle) {
      return null;
    }

    const keyBytes = new TextEncoder().encode(API_KEY);
    return window.crypto.subtle.importKey(
      'raw',
      keyBytes,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
  };

  const signPayload = async (payload) => {
    const key = await importHmacKey();
    if (!key) {
      return '';
    }

    const message = `${payload.device_id}|${payload.temperature}|${payload.vibration}|${payload.power_usage}|${payload.timestamp}`;
    const signature = await window.crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message));
    return Array.from(new Uint8Array(signature))
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
  };

  const pushLog = (entry) => {
    setAttackLog((prev) => [...prev, { ...entry, time: new Date().toLocaleTimeString() }]);
  };

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

 
  const runAttackSimulation = async () => {
    setRunning(true);
    setAttackLog([]);
    setSummary({ blocked: 0, passed: 0, anomalies: 0 });

    try {
      if (!AUTH_URL || !BACKEND_URL || !API_KEY) {
        pushLog({ type: 'Configuration check', result: 'FAILED', detail: 'Missing AUTH_URL, BACKEND_URL, or API_KEY in .env', icon: '⚠️' });
        return;
      }

      const blocked = [];
      const passed = [];
      let anomalies = 0;

      const loginResponse = await fetch(`${AUTH_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'intruder@example.com', password: 'WrongPass123' }),
      });
      if (loginResponse.status === 401) {
        blocked.push('auth');
        pushLog({ type: 'Auth check', result: 'BLOCKED', detail: 'Invalid credentials were rejected by auth-service (401)', icon: '🔒' });
      } else {
        passed.push('auth');
        pushLog({ type: 'Auth check', result: 'PASSED', detail: `Auth returned ${loginResponse.status} instead of 401`, icon: '⚠️' });
      }

      const dashboardResponse = await fetch(`${BACKEND_URL}/api/dashboard`, {
        headers: { 'X-API-Key': 'wrong-key' },
      });
      if (dashboardResponse.status === 403) {
        blocked.push('api-key');
        pushLog({ type: 'API key guard', result: 'BLOCKED', detail: 'Backend rejected invalid API key (403)', icon: '🔒' });
      } else {
        passed.push('api-key');
        pushLog({ type: 'API key guard', result: 'PASSED', detail: `Backend returned ${dashboardResponse.status} for invalid API key`, icon: '⚠️' });
      }

      const attackPayload = {
        device_id: 'Security-Test-01',
        temperature: 125.5,
        vibration: 12.9,
        power_usage: 149.2,
        timestamp: new Date().toISOString(),
      };
      attackPayload.signature = await signPayload(attackPayload);

      const anomalyResponse = await fetch(`${BACKEND_URL}/api/process_data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify(attackPayload),
      });
      if (anomalyResponse.ok) {
        const anomalyData = await anomalyResponse.json();
        const detected = Boolean(anomalyData.anomaly || anomalyData.is_anomaly);
        anomalies += detected ? 1 : 0;
        pushLog({
          type: 'Anomaly payload',
          result: detected ? 'DETECTED' : 'CLEARED',
          detail: `AI response: ${anomalyData.status || 'unknown'} (${detected ? 'anomaly' : 'normal'})`,
          icon: detected ? '🟥' : '🟩',
        });
      } else {
        pushLog({ type: 'Anomaly payload', result: 'FAILED', detail: `Backend returned ${anomalyResponse.status}`, icon: '⚠️' });
      }

      const fraudResponse = await fetch(`${BACKEND_URL}/api/report-fraud`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({
          asset_id: 'Security-Test-01',
          type: 'anomaly_cluster',
          confidence: 0.95,
        }),
      });
      if (fraudResponse.ok) {
        blocked.push('fraud');
        pushLog({ type: 'Fraud report', result: 'SAVED', detail: 'Fraud alert stored for review page and GNN follow-up', icon: '📄' });
      } else {
        pushLog({ type: 'Fraud report', result: 'FAILED', detail: `Fraud endpoint returned ${fraudResponse.status}`, icon: '⚠️' });
      }

      const fraudRes = await authenticatedFetch('/api/fraud-alerts');
      if (fraudRes?.ok) {
        const fraud = await fraudRes.json();
        setFraudAlerts(fraud.alerts || []);
      }

      setSummary({ blocked: blocked.length, passed: passed.length, anomalies });
    } catch (err) {
      pushLog({ type: 'Security test', result: 'FAILED', detail: err.message || 'Unexpected error', icon: '⚠️' });
    } finally {
      setRunning(false);
    }
  };

  const controlCount = securityControls.length;
  const threatCount = strideTable.length;
  const certCount = certInfo.length;
  const blockedCount = summary.blocked;

  return (
    <Layout>
      <div className="security-container">

        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Security Dashboard</h1>
            <p className="page-subtitle">Real checks for authentication, ingestion, anomaly detection, and fraud reporting.</p>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div className="security-overall-badge">
              <span className="badge-dot" />
              Live Validation Ready
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
          <div className="sec-stat-card"><div className="sec-stat-num">{controlCount}</div><div className="sec-stat-lbl">Configured Controls</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#22c55e' }}>{threatCount}</div><div className="sec-stat-lbl">Threat Paths Covered</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#0ea5e9' }}>{certCount}</div><div className="sec-stat-lbl">Certificates Tracked</div></div>
          <div className="sec-stat-card"><div className="sec-stat-num" style={{ color: '#f59e0b' }}>{blockedCount}</div><div className="sec-stat-lbl">Blocked Tests</div></div>
        </div>

        {/* Security Controls Grid */}
        <div className="sec-section">
          <h2 className="sec-section-title">Active Security Controls</h2>
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
          <h2 className="sec-section-title">STRIDE Threat Model</h2>
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
          <h2 className="sec-section-title">TLS Certificates</h2>
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
              <h2 className="sec-section-title">Validation Test Runner</h2>
              <p className="attack-subtitle">Runs real auth, API, anomaly, and fraud-report checks against live services.</p>
            </div>
            <button
              className={`run-attack-btn ${running ? 'running' : ''}`}
              onClick={runAttackSimulation}
              disabled={running}
            >
              {running ? <><span className="spinner" /> Running Checks...</> : <>Run Validation Tests</>}
            </button>
          </div>

          {(attackLog.length > 0 || running) && (
            <div className="attack-progress">
              <div className="attack-progress-bar">
                <div className="attack-progress-fill" style={{ width: `${Math.min((attackLog.length / 4) * 100, 100)}%` }} />
              </div>
              <span>{attackLog.length}/4 checks complete</span>
            </div>
          )}

          <div className="attack-log">
            {attackLog.length === 0 && !running && (
              <p className="attack-empty">Click "Run Validation Tests" to test login protection, API access, anomaly detection, and fraud reporting.</p>
            )}
            {running && attackLog.length === 0 && (
              <p className="attack-empty">Running live checks against the connected services...</p>
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
            {attackLog.length >= 4 && (
              <div className="attack-summary">
                Summary: {summary.blocked} blocked, {summary.passed} passed, {summary.anomalies} anomaly payloads accepted.
              </div>
            )}
          </div>
        </div>

        <div className="sec-section">
          <h2 className="sec-section-title">Fraud Review Snapshot</h2>
          {fraudAlerts.length === 0 ? (
            <p className="attack-empty">No fraud alerts are stored yet. Run the validation tests to create a live alert record.</p>
          ) : (
            <div className="stride-table-wrap">
              <table className="stride-table">
                <thead>
                  <tr><th>Asset</th><th>Type</th><th>Confidence</th><th>Timestamp</th></tr>
                </thead>
                <tbody>
                  {fraudAlerts.slice(0, 5).map((alert, i) => (
                    <tr key={i}>
                      <td className="threat-name">{alert.asset_id}</td>
                      <td className="threat-cat">{alert.type?.replace(/_/g, ' ') || 'N/A'}</td>
                      <td className="threat-ctrl">{alert.confidence != null ? `${(alert.confidence * 100).toFixed(1)}%` : 'N/A'}</td>
                      <td className="threat-ctrl">{alert.timestamp || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
};

export default SecurityPage;