// frontend/src/components/LiveChart.jsx
// Week 8: Live WebSocket data table with anomaly highlighting

import { useEffect, useRef, useState } from 'react';

const MAX_POINTS = 20;

export default function LiveChart() {
  const [data, setData] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/live');

    ws.onopen = () => {
      setConnected(true);
      console.log('✅ WebSocket connected to backend');
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('❌ WebSocket disconnected');
    };

    ws.onerror = (err) => {
      console.log('⚠️ WebSocket error:', err);
      setConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData((prev) => [...prev.slice(-(MAX_POINTS - 1)), parsed]);
      } catch (e) {
        console.log('Could not parse WebSocket message');
      }
    };

    wsRef.current = ws;

    return () => ws.close();
  }, []);

  return (
    <div className="live-chart-container" style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '12px',
      padding: '20px',
      marginTop: '24px'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: '16px', fontWeight: '600' }}>
          📡 Live Sensor Stream
        </h3>
        <span style={{
          color: connected ? '#22c55e' : '#ef4444',
          fontWeight: 'bold',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <span style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: connected ? '#22c55e' : '#ef4444',
            display: 'inline-block',
            animation: connected ? 'pulse 2s infinite' : 'none'
          }}></span>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Data Table */}
      {data.length === 0 ? (
        <p style={{ opacity: 0.5, textAlign: 'center', padding: '40px 0', margin: 0, color: '#94a3b8' }}>
          {connected ? '⏳ Waiting for data from simulator...' : '🔌 Backend WebSocket not available. Run the backend to see live data.'}
        </p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                {['Device', 'Temp °C', 'Vibration', 'Power W', 'Status'].map((h) => (
                  <th key={h} style={{
                    padding: '8px 12px', textAlign: 'left',
                    color: '#94a3b8', fontWeight: '600', fontSize: '11px',
                    textTransform: 'uppercase', letterSpacing: '0.5px'
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...data].reverse().map((row, i) => (
                <tr
                  key={i}
                  style={{
                    background: row.is_anomaly ? 'rgba(239,68,68,0.1)' : 'transparent',
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    transition: 'background 0.2s'
                  }}
                >
                  <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{row.device_id || 'N/A'}</td>
                  <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{row.temperature ?? 'N/A'}</td>
                  <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{row.vibration ?? 'N/A'}</td>
                  <td style={{ padding: '10px 12px', color: '#e2e8f0' }}>{row.power_usage ?? 'N/A'}</td>
                  <td style={{
                    padding: '10px 12px',
                    color: row.is_anomaly ? '#ef4444' : '#22c55e',
                    fontWeight: 'bold'
                  }}>
                    {row.is_anomaly ? '🔴 ANOMALY' : '🟢 Normal'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}