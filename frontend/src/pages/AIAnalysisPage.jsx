import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './AIAnalysisPage.css';

const AIAnalysisPage = () => {
  const [analysisResults, setAnalysisResults] = useState([]);
  const [aiStats, setAiStats]                 = useState({
    totalAnalyses: 0, anomaliesDetected: 0, accuracy: 0, modelsActive: 3,
  });
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [selectedModel, setSelectedModel]       = useState('All Models');
  const [loading, setLoading]                   = useState(true);

  const aiModels = ['LSTM Autoencoder', 'Isolation Forest', 'Graph Neural Network'];

  // ✅ Backend se real AI analysis fetch karo
  const fetchAIData = async () => {
    try {
      const res = await authenticatedFetch('/api/ai-analysis');
      if (!res) return;
      const data = await res.json();

      if (data) {
        // Stats update karo
        setAiStats({
          totalAnalyses:    data.total_analyses   ?? 0,
          anomaliesDetected:data.anomalies_found  ?? 0,
          accuracy:         94.2,
          modelsActive:     3,
        });

        // Recent results update karo — purane bhi rakho
        if (data.recent_results && data.recent_results.length > 0) {
          setAnalysisResults(prev => {
            const existingIds = new Set(prev.map(r => r.timestamp + r.device));
            const newResults = data.recent_results
              .filter(r => !existingIds.has(r.timestamp + r.device))
              .map((rec, i) => ({
                id:             Date.now() + i,
                device:         rec.device       ?? 'Unknown',
                type:           'Anomaly Detection',
                severity:       rec.severity     ?? 'high',
                confidence:     rec.confidence   ?? 95,
                detected:       rec.timestamp    ?? new Date().toLocaleTimeString(),
                description:    `Anomaly detected on ${rec.device}`,
                recommendation: rec.recommendation ?? 'Inspect device immediately.',
                aiModel:        'LSTM Autoencoder',
              }));
            return [...newResults, ...prev].slice(0, 50); // max 50 store karo
          });
        }
      }
    } catch (err) {
      console.log('AI Analysis API not available:', err);
    } finally {
      setLoading(false);
    }
  };

  // Page load pe fetch + har 5 second mein refresh
  useEffect(() => {
    fetchAIData();
    const interval = setInterval(fetchAIData, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredResults = selectedModel === 'All Models'
    ? analysisResults
    : analysisResults.filter(a => a.aiModel === selectedModel);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':   return { bg: '#ef444420', text: '#ef4444' };
      case 'medium': return { bg: '#f59e0b20', text: '#f59e0b' };
      case 'low':    return { bg: '#22c55e20', text: '#22c55e' };
      default:       return { bg: '#6b728020', text: '#6b7280' };
    }
  };

  return (
    <Layout>
      <div className="ai-analysis-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">AI Analysis</h1>
            <p className="page-subtitle">Real-time anomaly detection and predictive analytics</p>
          </div>
          <button className="analyze-button" onClick={fetchAIData}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Refresh Analysis
          </button>
        </div>

        {/* Stats */}
        <div className="ai-stats-grid">
          {[
            { bg: 'linear-gradient(135deg,#0ea5e9,#0284c7)', value: loading ? '...' : aiStats.totalAnalyses.toLocaleString(), label: 'Total Analyses',     icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
            { bg: 'linear-gradient(135deg,#ef4444,#dc2626)', value: loading ? '...' : aiStats.anomaliesDetected, label: 'Anomalies Found',    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
            { bg: 'linear-gradient(135deg,#22c55e,#16a34a)', value: loading ? '...' : `${aiStats.accuracy.toFixed(1)}%`, label: 'Model Accuracy',  icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
            { bg: 'linear-gradient(135deg,#8b5cf6,#7c3aed)', value: aiStats.modelsActive, label: 'Active Models',    icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
          ].map((stat, i) => (
            <div key={i} className="ai-stat-card">
              <div className="ai-stat-icon" style={{ background: stat.bg }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={stat.icon} />
                </svg>
              </div>
              <div className="ai-stat-content">
                <div className="ai-stat-value">{stat.value}</div>
                <div className="ai-stat-label">{stat.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Results */}
        <div className="analysis-section">
          <div className="section-header">
            <h2 className="section-title">Recent Analysis Results</h2>
            <select
              className="model-filter"
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
            >
              <option>All Models</option>
              {aiModels.map(m => <option key={m}>{m}</option>)}
            </select>
          </div>

          {loading ? (
            <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
              Loading AI analysis...
            </p>
          ) : filteredResults.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>
              No anomalies detected yet — start the simulator!
            </p>
          ) : (
            <div className="analysis-list">
              {filteredResults.map((analysis) => (
                <div key={analysis.id} className="analysis-card">
                  <div className="analysis-header">
                    <div className="analysis-device">
                      <div className="device-icon-ai">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                        </svg>
                      </div>
                      <div>
                        <div className="device-name-ai">{analysis.device}</div>
                        <div className="analysis-type">{analysis.type}</div>
                      </div>
                    </div>
                    <div
                      className="severity-badge"
                      style={{
                        background: getSeverityColor(analysis.severity).bg,
                        color:      getSeverityColor(analysis.severity).text,
                      }}
                    >
                      {analysis.severity.toUpperCase()}
                    </div>
                  </div>

                  <div className="confidence-bar-container">
                    <div className="confidence-label">
                      <span>Confidence</span>
                      <span className="confidence-value">{analysis.confidence}%</span>
                    </div>
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{
                          width: `${analysis.confidence}%`,
                          background: analysis.confidence > 80 ? '#22c55e'
                            : analysis.confidence > 60 ? '#f59e0b' : '#ef4444',
                        }}
                      />
                    </div>
                  </div>

                  <div className="analysis-description">{analysis.description}</div>

                  <div className="analysis-meta">
                    <div className="meta-item">
                      <svg viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                      </svg>
                      {analysis.detected}
                    </div>
                    <div className="meta-item">
                      <svg viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                        <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                      </svg>
                      {analysis.aiModel}
                    </div>
                  </div>

                  <button
                    className="view-recommendation-button"
                    onClick={() => setSelectedAnalysis(analysis)}
                  >
                    View Recommendation
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal */}
        {selectedAnalysis && (
          <div className="modal-overlay" onClick={() => setSelectedAnalysis(null)}>
            <div className="modal-content-ai" onClick={e => e.stopPropagation()}>
              <div className="modal-header-ai">
                <h2>Analysis Details</h2>
                <button className="modal-close-ai" onClick={() => setSelectedAnalysis(null)}>
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              <div className="modal-body-ai">
                <div className="detail-section">
                  <h3>Device Information</h3>
                  <p><strong>Device:</strong> {selectedAnalysis.device}</p>
                  <p><strong>Type:</strong> {selectedAnalysis.type}</p>
                  <p><strong>Severity:</strong>{' '}
                    <span style={{ color: getSeverityColor(selectedAnalysis.severity).text }}>
                      {selectedAnalysis.severity.toUpperCase()}
                    </span>
                  </p>
                </div>
                <div className="detail-section">
                  <h3>Analysis Details</h3>
                  <p><strong>Description:</strong> {selectedAnalysis.description}</p>
                  <p><strong>Confidence:</strong> {selectedAnalysis.confidence}%</p>
                  <p><strong>AI Model:</strong> {selectedAnalysis.aiModel}</p>
                  <p><strong>Detected:</strong> {selectedAnalysis.detected}</p>
                </div>
                <div className="detail-section recommendation-section">
                  <h3>🎯 Recommendation</h3>
                  <div className="recommendation-box">{selectedAnalysis.recommendation}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AIAnalysisPage;