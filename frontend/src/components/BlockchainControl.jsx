import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * BlockchainControl Component
 * Allows users to start/stop blockchain via API calls
 * Place this in: frontend/src/components/BlockchainControl.jsx
 */

export const BlockchainControl = ({ apiUrl, apiKey }) => {
  const [status, setStatus] = useState('unknown');
  const [loading, setLoading] = useState(false);
  const [containers, setContainers] = useState([]);
  const [message, setMessage] = useState('');

  // Check blockchain status
  const checkStatus = async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/blockchain/status`, {
        headers: { 'X-API-Key': apiKey }
      });
      if (response.data) {
        setStatus(response.data.status || 'unknown');
        setContainers(response.data.containers || []);
        setMessage(response.data.message || '');
      }
    } catch (error) {
      console.error('[BlockchainControl] Status check failed:', error.message);
      setStatus('error');
      setMessage(error.response?.data?.detail || error.message || 'Connection failed');
    }
  };

  // Start blockchain
  const handleStart = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${apiUrl}/api/blockchain/start`, {}, {
        headers: { 'X-API-Key': apiKey }
      });
      if (response.data) {
        setStatus(response.data.status || 'unknown');
        setContainers(response.data.containers || []);
        setMessage(response.data.message || 'Blockchain started');
      }
    } catch (error) {
      console.error('[BlockchainControl] Start failed:', error.message);
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Failed to start blockchain');
    } finally {
      setLoading(false);
    }
  };

  // Stop blockchain
  const handleStop = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${apiUrl}/api/blockchain/stop`, {}, {
        headers: { 'X-API-Key': apiKey }
      });
      if (response.data) {
        setStatus(response.data.status || 'unknown');
        setContainers(response.data.containers || []);
        setMessage(response.data.message || 'Blockchain stopped');
      }
    } catch (error) {
      console.error('[BlockchainControl] Stop failed:', error.message);
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Failed to stop blockchain');
    } finally {
      setLoading(false);
    }
  };

  // Check status on mount
  useEffect(() => {
    checkStatus();
    // Polling every 5 seconds
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Status colors
  const statusColors = {
    running: '#10b981',    // green
    stopped: '#ef4444',    // red
    partial: '#f59e0b',    // amber
    error: '#dc2626',      // dark red
    unknown: '#6b7280'     // gray
  };

  return (
    <div style={{
      padding: '20px',
      border: `2px solid ${statusColors[status] || '#ccc'}`,
      borderRadius: '8px',
      backgroundColor: '#f9fafb',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <h2 style={{ margin: '0 0 15px 0', color: '#111827' }}>🔗 Blockchain Control</h2>

      {/* Status Badge */}
      <div style={{
        display: 'inline-block',
        padding: '6px 12px',
        backgroundColor: statusColors[status] || '#ccc',
        color: 'white',
        borderRadius: '4px',
        fontSize: '14px',
        fontWeight: 'bold',
        marginBottom: '15px'
      }}>
        {status.toUpperCase()}
      </div>

      {/* Message */}
      {message && (
        <p style={{
          margin: '10px 0 15px 0',
          color: '#374151',
          fontSize: '14px',
          fontStyle: 'italic'
        }}>
          {message}
        </p>
      )}

      {/* Control Buttons */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <button
          onClick={handleStart}
          disabled={loading || status === 'running'}
          style={{
            padding: '8px 16px',
            backgroundColor: status === 'running' ? '#d1d5db' : '#10b981',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: status === 'running' ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '14px'
          }}
        >
          {loading ? '⏳ Starting...' : '▶️ Start'}
        </button>

        <button
          onClick={handleStop}
          disabled={loading || status === 'stopped'}
          style={{
            padding: '8px 16px',
            backgroundColor: status === 'stopped' ? '#d1d5db' : '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: status === 'stopped' ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '14px'
          }}
        >
          {loading ? '⏳ Stopping...' : '⏹️ Stop'}
        </button>

        <button
          onClick={checkStatus}
          disabled={loading}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px'
          }}
        >
          {loading ? '🔄 Updating...' : '🔄 Refresh'}
        </button>
      </div>

      {/* Containers List */}
      {containers.length > 0 && (
        <div>
          <h4 style={{ margin: '15px 0 10px 0', color: '#374151', fontSize: '14px' }}>
            Running Containers:
          </h4>
          <ul style={{ margin: '0', paddingLeft: '20px', fontSize: '13px', color: '#555' }}>
            {containers.map(container => (
              <li key={container}>{container}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default BlockchainControl;
