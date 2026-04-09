import { useEffect, useState, useCallback } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './FraudReport.css';

export default function FraudReport() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Memoized fetch function taaki unnecessary re-renders na ho
  const fetchAlerts = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const res = await authenticatedFetch('/api/fraud-alerts');
      if (!res) throw new Error('No response from server');
      
      const data = await res.json();
      
      // FIX: Data format check (kabhi kabhi data direct array hota hai, kabhi object mein)
      const alertsData = Array.isArray(data) ? data : (data.alerts || []);
      setAlerts(alertsData);
      setError(null);
    } catch (err) {
      console.error("Fraud Fetch Error:", err);
      setError('Could not load fraud alerts. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Pehli baar load karein
    fetchAlerts(true);

    // FIX: Live monitoring ke liye interval set karein (har 5 seconds)
    const interval = setInterval(() => fetchAlerts(false), 5000);
    
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const getConfidenceColor = (confidence) => {
    const conf = parseFloat(confidence);
    if (conf > 0.8) return '#ef4444'; // Red
    if (conf > 0.6) return '#f59e0b'; // Amber
    return '#22c55e'; // Green
  };

  const getTypeIcon = (type) => {
    const t = type?.toLowerCase() || '';
    if (t.includes('cluster')) return '🔴';
    if (t.includes('frequency')) return '⚡';
    if (t.includes('injection')) return '💉';
    return '⚠️';
  };

  return (
    <Layout>
      <div className="fraud-container">
        <div className="fraud-header">
          <div>
            <h1 className="fraud-title">🚨 Fraud Alerts</h1>
            <p className="fraud-subtitle">Real-time AI-detected systemic fraud patterns</p>
          </div>
          <button 
            className={`fraud-refresh-btn ${loading ? 'spinning' : ''}`} 
            onClick={() => fetchAlerts(true)}
          >
            Refresh Data
          </button>
        </div>

        {/* Stats Grid - Ab ye alerts state ke saath auto-update hoga */}
        <div className="fraud-stats">
          <div className="fraud-stat-card">
            <div className="fraud-stat-num">{alerts.length}</div>
            <div className="fraud-stat-lbl">Total Alerts</div>
          </div>
          <div className="fraud-stat-card">
            <div className="fraud-stat-num" style={{ color: '#ef4444' }}>
              {alerts.filter(a => parseFloat(a.confidence) > 0.8).length}
            </div>
            <div className="fraud-stat-lbl">Critical Risk</div>
          </div>
        </div>

        {loading && alerts.length === 0 ? (
          <div className="fraud-loading">
            <div className="fraud-spinner" />
            <p>Scanning network for fraud...</p>
          </div>
        ) : error ? (
          <div className="fraud-error">
            <p>⚠️ {error}</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="fraud-empty">
            <div className="check-icon">✅</div>
            <h3>System Secure</h3>
            <p>No suspicious patterns detected in recent blocks.</p>
          </div>
        ) : (
          <div className="fraud-table-container">
            <table className="fraud-table">
              <thead>
                <tr>
                  <th>Detection Type</th>
                  <th>Target Asset</th>
                  <th>Confidence</th>
                  <th>Time Detected</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, i) => {
                  const confValue = parseFloat(alert.confidence || 0);
                  return (
                    <tr key={alert.id || i} className={confValue > 0.8 ? 'row-high' : ''}>
                      <td>
                        <span className="type-badge">
                          {getTypeIcon(alert.type)} {alert.type?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="asset-id"><code>{alert.asset_id}</code></td>
                      <td>
                        <div className="confidence-cell">
                          <div className="conf-bar-bg">
                            <div
                              className="conf-bar-fill"
                              style={{
                                width: `${(confValue * 100)}%`,
                                background: getConfidenceColor(confValue)
                              }}
                            />
                          </div>
                          <span style={{ color: getConfidenceColor(confValue) }}>
                            {(confValue * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td className="timestamp">{alert.timestamp}</td>
                      <td>
                        <span 
                          className="risk-badge"
                          style={{ borderLeft: `4px solid ${getConfidenceColor(confValue)}` }}
                        >
                          {confValue > 0.8 ? 'CRITICAL' : confValue > 0.6 ? 'WARNING' : 'STABLE'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}