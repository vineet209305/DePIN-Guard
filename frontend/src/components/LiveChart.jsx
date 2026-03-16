// frontend/src/components/LiveChart.jsx
// Week 8: Live WebSocket data table with anomaly highlighting

import { useEffect, useRef, useState } from 'react';
import './LiveChart.css';

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

    ws.onerror = () => setConnected(false);

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
    <div className="live-chart-container">

      {/* Header */}
      <div className="live-chart-header">
        <h3 className="live-chart-title">📡 Live Sensor Stream</h3>
        <span className={`connection-badge ${connected ? 'connected' : 'disconnected'}`}>
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`}></span>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Empty State */}
      {data.length === 0 ? (
        <p className="live-chart-empty">
          {connected
            ? '⏳ Waiting for data from simulator...'
            : '🔌 Backend WebSocket not available. Run the backend to see live data.'}
        </p>
      ) : (
        <div className="live-chart-table-wrapper">
          <table className="live-chart-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Temp °C</th>
                <th>Vibration</th>
                <th>Power W</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {[...data].reverse().map((row, i) => (
                <tr
                  key={i}
                  className={row.is_anomaly ? 'anomaly-row' : 'normal-row'}
                >
                  <td className="device-name">{row.device_id ?? 'N/A'}</td>
                  <td className="temp-value">{row.temperature ?? 'N/A'}</td>
                  <td className="vib-value">{row.vibration ?? 'N/A'}</td>
                  <td className="pwr-value">{row.power_usage ?? 'N/A'}</td>
                  <td>
                    <span className={`status-cell ${row.is_anomaly ? 'anomaly' : 'normal'}`}>
                      {row.is_anomaly ? '🔴 ANOMALY' : '🟢 Normal'}
                    </span>
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