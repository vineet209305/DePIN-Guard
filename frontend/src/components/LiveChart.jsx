import { useEffect, useRef, useState } from 'react';
import './LiveChart.css';

const MAX_POINTS = 20;

const getWsUrl = () => {
  const apiUrl = import.meta.env.VITE_API_URL;

  // No external URL set — use Vite WS proxy (relative, same origin)
  if (!apiUrl) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/ws/live`;
  }

  // External URL (tunnel/production) — convert http→ws, https→wss
  return apiUrl.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws/live';
};

export default function LiveChart({ onConnect }) {
  const [data, setData]           = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef                     = useRef(null);

  useEffect(() => {
    let ws;
    let retryTimeout;

    const connect = () => {
      const WS_URL = getWsUrl();
      console.log('[LiveChart] Connecting to:', WS_URL);

      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('[LiveChart] Connected');
        setConnected(true);
        onConnect?.();
      };

      ws.onclose = () => {
        console.log('[LiveChart] Disconnected — retrying in 3s');
        setConnected(false);
        retryTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('[LiveChart] WebSocket error:', err);
        setConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (!parsed || typeof parsed !== 'object') {
            console.warn('[LiveChart] Invalid message format:', parsed);
            return;
          }
          setData((prev) => [...prev.slice(-(MAX_POINTS - 1)), parsed]);
        } catch (error) {
          console.warn('[LiveChart] Failed to parse message:', error.message);
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
        <h3 className="live-chart-title">Live Sensor Updates</h3>
        <span className={`connection-badge ${connected ? 'connected' : 'disconnected'}`}>
          <span className={`status-dot ${connected ? 'connected' : 'disconnected'}`} />
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {data.length === 0 ? (
        <p className="live-chart-empty">
          {connected
            ? 'Waiting for sensor data...'
            : 'Connecting to live data stream...'}
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
                      {row.is_anomaly ? 'Anomaly' : 'Normal'}
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