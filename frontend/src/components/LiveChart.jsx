import { useEffect, useRef, useState } from 'react';
import './LiveChart.css';

const MAX_POINTS = 20;

// ✅ Localtunnel ya custom env variable se WebSocket URL lo
// .env mein set karo: VITE_WS_URL=wss://depin-backend.loca.lt
// Agar env nahi hai toh same host pe backend assume karo (Vite proxy)
const getWsUrl = () => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  // Vite proxy use ho raha hai — same host but ws protocol
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${protocol}://${window.location.hostname}:8000/ws/live`;
};

const WS_URL = getWsUrl();

export default function LiveChart({ onConnect }) {
  const [data, setData]           = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let ws;
    let retryTimeout;

    const connect = () => {
      console.log('🔌 Connecting to WebSocket:', WS_URL);
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnected(true);
        onConnect?.();
      };

      ws.onclose = () => {
        console.log('❌ WebSocket disconnected — retrying in 3s...');
        setConnected(false);
        retryTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setData((prev) => [...prev.slice(-(MAX_POINTS - 1)), parsed]);
        } catch {
          // ignore malformed messages
        }
      };

      wsRef.current = ws;
    };

    connect();
    return () => {
      clearTimeout(retryTimeout);
      ws?.close();
    };
  }, []);

  return (
    <div className="live-chart-container">
      <div className="live-chart-header">
        <h3 className="live-chart-title">📡 Live Sensor Stream</h3>
        <span className={`connection-badge ${connected ? 'connected' : 'disconnected'}`}>
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {data.length === 0 ? (
        <p className="live-chart-empty">
          {connected ? '⏳ Waiting for data from simulator...' : '🔌 Connecting to backend WebSocket...'}
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
                <tr key={i} className={row.is_anomaly ? 'anomaly-row' : 'normal-row'}>
                  <td>{row.device_id   ?? 'N/A'}</td>
                  <td>{row.temperature ?? 'N/A'}</td>
                  <td>{row.vibration   ?? 'N/A'}</td>
                  <td>{row.power_usage ?? 'N/A'}</td>
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