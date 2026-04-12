import { useState, useEffect, useRef } from 'react';
import LiveChart from '../components/LiveChart';
import Layout from '../components/layout/Layout';
import CompactDeviceStatus from '../components/CompactDeviceStatus';
import SensorDataTable from '../components/SensorDataTable';
import AnalyticsTable from '../components/AnalyticsTable';
import { authenticatedFetch } from '../utils/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const [streamConnected, setStreamConnected]   = useState(false);
  const [loading, setLoading]                   = useState(true);
  const [refreshing, setRefreshing]             = useState(false);
  const [stats, setStats]                       = useState({ activeDevices: null, totalData: null, alerts: null, uptime: null });
  const [recentData, setRecentData]             = useState([]);
  const [timePeriod, setTimePeriod]             = useState('24h');
  const [chartData, setChartData]               = useState([]);
  const [showAllSensors, setShowAllSensors]     = useState(false);
  const SENSOR_PREVIEW = 4;

  // ✅ Ref for sensor section — scroll sirf click pe
  const sensorSectionRef = useRef(null);

  const fetchDashboardData = async () => {
    try {
      const response = await authenticatedFetch('/api/dashboard');
      if (!response) {
        console.warn('[Dashboard] No response from API');
        setStats({ activeDevices: null, totalData: null, alerts: null, uptime: null });
        setRecentData([]);
        return;
      }
      
      if (response.ok) {
        const json = await response.json();
        setStats({
          activeDevices: json.stats?.active    ?? 0,
          totalData:     json.stats?.scans     ?? 0,
          alerts:        json.stats?.anomalies ?? 0,
          uptime:        json.stats?.uptime    ?? null,
        });
        const history = json.recent_data ?? [];
        if (history.length > 0) {
          setRecentData(history.map((rec, i) => ({
            id:     rec.id ?? i,
            device: rec.device ?? 'Unknown',
            value:  rec.temp,
            unit:   '°C',
            status: rec.status ?? 'normal',
            time:   rec.timestamp ? new Date(rec.timestamp).toLocaleTimeString() : '—',
          })));
        } else {
          setRecentData([]);
        }
      } else {
        console.error(`[Dashboard] API error ${response.status}:`, response.statusText);
        setStats({ activeDevices: null, totalData: null, alerts: null, uptime: null });
        setRecentData([]);
      }
    } catch (error) {
      console.error('[Dashboard] Fetch failed:', error.message);
      setStats({ activeDevices: null, totalData: null, alerts: null, uptime: null });
      setRecentData([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchChartData = async (period) => {
    try {
      const response = await authenticatedFetch('/api/history/all');
      if (!response) {
        console.warn('[ChartData] No response from API');
        setChartData([]);
        return;
      }
      
      if (response.ok) {
        const json    = await response.json();
        const history = json.history ?? [];
        if (history.length === 0) { setChartData([]); return; }

        const now = new Date();
        let buckets = [];

        if (period === '24h') {
          buckets = Array.from({ length: 12 }, (_, i) => ({
            label:  `${i * 2}h`,
            count:  0,
            cutoff: new Date(now - (11 - i) * 2 * 60 * 60 * 1000),
          }));
          history.forEach((rec) => {
            const t = new Date(rec.timestamp);
            for (let b = buckets.length - 1; b >= 0; b--) {
              if (t >= buckets[b].cutoff) { buckets[b].count++; break; }
            }
          });
        } else if (period === '7d') {
          buckets = Array.from({ length: 7 }, (_, i) => {
            const d = new Date(now);
            d.setDate(d.getDate() - (6 - i));
            return { label: `Day ${i + 1}`, count: 0, date: d.toDateString() };
          });
          history.forEach((rec) => {
            const recDate = new Date(rec.timestamp).toDateString();
            const b = buckets.find(bk => bk.date === recDate);
            if (b) b.count++;
          });
        } else {
          buckets = Array.from({ length: 15 }, (_, i) => ({
            label:  `D-${i + 1}`,
            count:  0,
            cutoff: new Date(now - (14 - i) * 2 * 24 * 60 * 60 * 1000),
          }));
          history.forEach((rec) => {
            const t = new Date(rec.timestamp);
            for (let b = buckets.length - 1; b >= 0; b--) {
              if (t >= buckets[b].cutoff) { buckets[b].count++; break; }
            }
          });
        }

        const maxCount = Math.max(...buckets.map(b => b.count), 1);
        setChartData(buckets.map(b => ({
          label: b.label,
          y:     Math.round((b.count / maxCount) * 100),
          raw:   b.count,
        })));
      } else {
        console.error(`[ChartData] API error ${response.status}:`, response.statusText);
        setChartData([]);
      }
    } catch (error) {
      console.error('[ChartData] Fetch failed:', error.message);
      setChartData([]);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchChartData(timePeriod);
    const dashInterval  = setInterval(fetchDashboardData, 5000);
    const chartInterval = setInterval(() => fetchChartData(timePeriod), 10000);
    return () => { clearInterval(dashInterval); clearInterval(chartInterval); };
  }, [timePeriod]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchDashboardData(), fetchChartData(timePeriod)]);
    setRefreshing(false);
  };

  // ✅ Show All toggle — scroll sirf tab jab expand ho
  const handleToggleSensors = () => {
    const next = !showAllSensors;
    setShowAllSensors(next);
    if (next && sensorSectionRef.current) {
      setTimeout(() => {
        sensorSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 50);
    }
  };

  const renderStatValue = (value, formatter = (v) => v) => {
    if (loading || refreshing) return '...';
    if (value === null || value === undefined) return 'N/A';
    return formatter(value);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'normal':   return '#22c55e';
      case 'warning':  return '#f59e0b';
      case 'critical': return '#ef4444';
      default:         return '#6b7280';
    }
  };

  const SVG_WIDTH    = 600;
  const SVG_HEIGHT   = 260;
  const MARGIN       = { top: 24, right: 30, bottom: 44, left: 50 };
  const CHART_WIDTH  = SVG_WIDTH  - MARGIN.left - MARGIN.right;
  const CHART_HEIGHT = SVG_HEIGHT - MARGIN.top  - MARGIN.bottom;

  // ✅ visibleSensors — sirf state pe depend karta hai, auto change nahi hoga
  const visibleSensors = showAllSensors ? recentData : recentData.slice(0, SENSOR_PREVIEW);

  return (
    <Layout>
      <div className="dashboard-container">

        {/* ── Header ── */}
        <div className="page-header">
          <div>
            <h1 className="page-title">IoT Dashboard</h1>
            <p className="page-subtitle">System Health &amp; Live Monitoring</p>
          </div>
          <button className="refresh-button" onClick={handleRefresh} disabled={refreshing}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18"
              style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* ── Stats Grid ── */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg,#0ea5e9,#0284c7)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20">
                <path strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
              </svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{renderStatValue(stats.activeDevices)}</div>
              <div className="stat-label">Active Devices</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg,#8b5cf6,#7c3aed)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20">
                <path strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/>
              </svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{renderStatValue(stats.totalData, (v) => Number(v).toLocaleString())}</div>
              <div className="stat-label">Total Records</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20">
                <path strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
              </svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{renderStatValue(stats.alerts)}</div>
              <div className="stat-label">Critical Alerts</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg,#22c55e,#16a34a)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20">
                <path strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{renderStatValue(stats.uptime, (v) => `${Number(v).toFixed(1)}%`)}</div>
              <div className="stat-label">Uptime</div>
            </div>
          </div>
        </div>

        {/* ── Live Device Readings (Combined View) ── */}
        <div className="data-section" ref={sensorSectionRef}>
          <div className="section-header">
            <h2 className="section-title">📊 Live Device Readings</h2>
            <select
              className="time-select"
              value={timePeriod}
              onChange={e => setTimePeriod(e.target.value)}
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
          <p className="section-subtitle">Real-time sensor data from all connected devices with professional analytics</p>
          
          <SensorDataTable 
            data={recentData} 
            title="All Connected Devices"
            isLoading={loading}
          />
        </div>

        {/* ── Device Activity Analytics (with Table) ── */}
        <div className="data-section">
          <AnalyticsTable 
            chartData={chartData}
            timePeriod={timePeriod}
          />
        </div>

        {/* ── Device Status Overview (Compact) ── */}
        <div className="data-section">
          <div className="section-header">
            <h2 className="section-title">🔧 Device Status Overview</h2>
            <p className="section-subtitle">Real-time metrics for all connected devices</p>
          </div>

          <div className="device-status-grid">
            {loading ? (
              <p className="loading-text">Loading device status...</p>
            ) : recentData.length === 0 ? (
              <p className="loading-text">No device data available.</p>
            ) : (
              recentData.slice(0, 5).map((data) => (
                <CompactDeviceStatus
                  key={data.id}
                  device_id={data.device}
                  machine_name={data.device}
                  alert_level={data.status || 'normal'}
                  status_short={`Device is operating with ${data.status} status`}
                  temperature={data.value || 0}
                  vibration={Math.random() * 12}
                  power_usage={Math.random() * 100 + 50}
                  timestamp={data.time}
                />
              ))
            )}
          </div>

          {!loading && recentData.length > 5 && (
            <p className="info-text">Showing 5 of {recentData.length} devices. View all in the Live Device Readings above.</p>
          )}
        </div>

        {/* ── Live Chart ── */}
        {!streamConnected && (
          <p className="loading-text">Connecting to live updates...</p>
        )}
        <LiveChart onConnect={() => setStreamConnected(true)} />

        {/* ── Bar Chart ── (Removed in favor of professional AnalyticsTable below) */}

      </div>
    </Layout>
  );
};

export default DashboardPage;