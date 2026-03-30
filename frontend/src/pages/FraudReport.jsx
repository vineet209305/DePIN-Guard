import { useEffect, useState } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './FraudReport.css';

export default function FraudReport() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await authenticatedFetch('/fraud-alerts');
      if (!res) return;
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      setError('Could not load fraud alerts. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return '#ef4444';
    if (confidence > 0.6) return '#f59e0b';
    return '#22c55e';
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'anomaly_cluster':    return '🔴';
      case 'high_frequency':     return '⚡';
      case 'injection_attempt':  return '💉';
      default:                   return '⚠️';
    }
  };

  return (
    <Layout>
      <div className="fraud-container">

        <div className="fraud-header">
          <div>
            <h1 className="fraud-title">🚨 Fraud Alerts</h1>
            <p className="fraud-subtitle">AI-detected systemic fraud patterns from blockchain transaction analysis</p>
          </div>
          <button className="fraud-refresh-btn" onClick={fetchAlerts}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="16" height="16">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        <div className="fraud-stats">
          <div className="fraud-stat-card">
            <div className="fraud-stat-num">{alerts.length}</div>
            <div className="fraud-stat-lbl">Total Alerts</div>
          </div>
          <div className="fraud-stat-card">
            <div className="fraud-stat-num" style={{ color: '#ef4444' }}>
              {alerts.filter(a => a.confidence > 0.8).length}
            </div>
            <div className="fraud-stat-lbl">High Risk</div>
          </div>
          <div className="fraud-stat-card">
            <div className="fraud-stat-num" style={{ color: '#f59e0b' }}>
              {alerts.filter(a => a.confidence > 0.6 && a.confidence <= 0.8).length}
            </div>
            <div className="fraud-stat-lbl">Medium Risk</div>
          </div>
          <div className="fraud-stat-card">
            <div className="fraud-stat-num" style={{ color: '#22c55e' }}>
              {alerts.filter(a => a.confidence <= 0.6).length}
            </div>
            <div className="fraud-stat-lbl">Low Risk</div>
          </div>
        </div>

        {loading ? (
          <div className="fraud-loading">
            <div className="fraud-spinner" />
            <p>Loading fraud alerts...</p>
          </div>
        ) : error ? (
          <div className="fraud-error">
            <span>⚠️</span>
            <p>{error}</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="fraud-empty">
            <span>✅</span>
            <h3>No Fraud Detected</h3>
            <p>No fraud alerts recorded yet. Check back after the GNN scheduler runs.</p>
          </div>
        ) : (
          <div className="fraud-table-container">
            <table className="fraud-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Asset ID</th>
                  <th>Confidence</th>
                  <th>Timestamp</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, i) => (
                  <tr
                    key={i}
                    className={alert.confidence > 0.8 ? 'row-high' : alert.confidence > 0.6 ? 'row-medium' : 'row-low'}
                  >
                    <td>
                      <span className="type-badge">
                        {getTypeIcon(alert.type)} {alert.type?.replace(/_/g, ' ') || 'N/A'}
                      </span>
                    </td>
                    <td className="asset-id">{alert.asset_id || 'N/A'}</td>
                    <td>
                      <div className="confidence-cell">
                        <div className="conf-bar-bg">
                          <div
                            className="conf-bar-fill"
                            style={{
                              width: `${((alert.confidence || 0) * 100).toFixed(0)}%`,
                              background: getConfidenceColor(alert.confidence)
                            }}
                          />
                        </div>
                        <span style={{ color: getConfidenceColor(alert.confidence), fontWeight: 700 }}>
                          {alert.confidence != null ? `${(alert.confidence * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="timestamp">{alert.timestamp || 'N/A'}</td>
                    <td>
                      <span
                        className="risk-badge"
                        style={{
                          background: `${getConfidenceColor(alert.confidence)}20`,
                          color: getConfidenceColor(alert.confidence)
                        }}
                      >
                        {alert.confidence > 0.8 ? '🔴 High' : alert.confidence > 0.6 ? '🟡 Medium' : '🟢 Low'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </Layout>
  );
}