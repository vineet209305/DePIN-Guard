import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authenticatedFetch } from '../utils/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const [stats, setStats] = useState({
    activeDevices: 24,
    totalData: 1543,
    alerts: 3,
    uptime: 99.9
  });

  const [recentData, setRecentData] = useState([
    { id: 1, device: 'Sensor-01', value: 23.5, unit: '°C', status: 'normal', time: '2 min ago' },
    { id: 2, device: 'Sensor-02', value: 65.2, unit: '%', status: 'normal', time: '3 min ago' },
    { id: 3, device: 'Sensor-03', value: 98.7, unit: 'kPa', status: 'warning', time: '5 min ago' },
    { id: 4, device: 'Sensor-04', value: 45.1, unit: '°C', status: 'critical', time: '7 min ago' },
  ]);

  const [timePeriod, setTimePeriod] = useState('24h');
  const [chartData, setChartData] = useState([]);

  const generateChartData = (period) => {
    let points = [];
    let numPoints = period === '24h' ? 12 : period === '7d' ? 7 : 15;
    for (let i = 0; i < numPoints; i++) {
      points.push({
        y: Math.floor(Math.random() * 70 + 20),
        label: period === '24h' ? `${i * 2}h` : period === '7d' ? `Day ${i + 1}` : `D-${i + 1}`
      });
    }
    return points;
  };

  useEffect(() => {
    setChartData(generateChartData(timePeriod));
  }, [timePeriod]);

  useEffect(() => {
    const statsInterval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        activeDevices: prev.activeDevices + (Math.random() > 0.5 ? 1 : -1),
        totalData: prev.totalData + Math.floor(Math.random() * 5),
        uptime: Math.min(100, Math.max(98, prev.uptime + (Math.random() * 0.02 - 0.01)))
      }));
    }, 5000);
    return () => clearInterval(statsInterval);
  }, []);

  // ✅ WEEK 6: Backend se live data fetch karna (token ke saath)
  const fetchLiveData = async () => {
    try {
      const response = await authenticatedFetch('http://localhost:8000/api/live-data');
      if (response) {
        const data = await response.json();
        if (data && data.length > 0) {
          setRecentData(data);
        }
      }
    } catch (err) {
      // Backend nahi chala to hardcoded data rahega — no crash
      console.log('Backend not available, using demo data.');
    }
  };

  const handleRefresh = () => {
    setChartData(generateChartData(timePeriod));
    setStats(prev => ({ ...prev, totalData: prev.totalData + 1 }));
    fetchLiveData(); // ✅ Refresh pe backend se bhi data aayega
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'normal': return '#22c55e';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const SVG_WIDTH = 600;
  const SVG_HEIGHT = 250;
  const MARGIN = { top: 20, right: 30, bottom: 40, left: 50 };
  const CHART_WIDTH = SVG_WIDTH - MARGIN.left - MARGIN.right;
  const CHART_HEIGHT = SVG_HEIGHT - MARGIN.top - MARGIN.bottom;

  return (
    <Layout>
      <div className="dashboard-container">
        {/* 1. Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">IoT Dashboard</h1>
            <p className="page-subtitle">System Health & Live Monitoring</p>
          </div>
          <button className="refresh-button" onClick={handleRefresh}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="18" height="18">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {/* 2. Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)' }}>
               <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20"><path strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.activeDevices}</div>
              <div className="stat-label">Active Devices</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' }}>
               <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20"><path strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.totalData.toLocaleString()}</div>
              <div className="stat-label">Total Records</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
               <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20"><path strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.alerts}</div>
              <div className="stat-label">Alerts</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}>
               <svg viewBox="0 0 24 24" fill="none" stroke="white" width="20"><path strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.uptime.toFixed(1)}%</div>
              <div className="stat-label">Uptime</div>
            </div>
          </div>
        </div>

        {/* 3. Live Sensor Feeds */}
        <div className="data-section">
          <div className="section-header">
            <h2 className="section-title">Live Sensor Feeds</h2>
            <button className="view-all-button">View All</button>
          </div>
          <div className="data-grid">
            {recentData.map((data) => (
              <div key={data.id} className="data-card">
                <div className="data-header">
                  <span className="device-name">{data.device}</span>
                  <span className="status-badge" style={{ backgroundColor: getStatusColor(data.status) + '20', color: getStatusColor(data.status) }}>
                    {data.status}
                  </span>
                </div>
                <div className="data-body">
                  <span className="data-value">{data.value}</span>
                  <span className="data-unit">{data.unit}</span>
                </div>
                <div className="data-footer">{data.time}</div>
              </div>
            ))}
          </div>
        </div>

        {/* 4. Bar Chart */}
        <div className="chart-section">
          <div className="section-header">
            <h2 className="section-title">Device Activity Analytics</h2>
            <select className="time-select" value={timePeriod} onChange={(e) => setTimePeriod(e.target.value)}>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
          <div className="chart-wrapper">
            <svg viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`} className="bar-chart-svg">
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#0ea5e9" />
                </linearGradient>
              </defs>
              {[0, 25, 50, 75, 100].map((tick) => (
                <g key={tick}>
                  <line x1={MARGIN.left} y1={MARGIN.top + CHART_HEIGHT - (tick/100)*CHART_HEIGHT} x2={SVG_WIDTH - MARGIN.right} y2={MARGIN.top + CHART_HEIGHT - (tick/100)*CHART_HEIGHT} stroke="#f1f5f9" />
                  <text x={MARGIN.left - 10} y={MARGIN.top + CHART_HEIGHT - (tick/100)*CHART_HEIGHT + 4} fontSize="11" textAnchor="end" fill="#94a3b8">{tick}</text>
                </g>
              ))}
              <line x1={MARGIN.left} y1={MARGIN.top + CHART_HEIGHT} x2={SVG_WIDTH - MARGIN.right} y2={MARGIN.top + CHART_HEIGHT} stroke="#cbd5e1" strokeWidth="2" />
              {chartData.map((data, i) => {
                const spacing = CHART_WIDTH / chartData.length;
                const barWidth = spacing * 0.7;
                const barHeight = (data.y / 100) * CHART_HEIGHT;
                const x = MARGIN.left + (i * spacing) + (spacing - barWidth) / 2;
                const y = MARGIN.top + CHART_HEIGHT - barHeight;
                return (
                  <g key={i} className="bar-group">
                    <rect x={x} y={y} width={barWidth} height={barHeight} fill="url(#barGradient)" rx="4" />
                    <text x={x + barWidth/2} y={SVG_HEIGHT - 10} fontSize="10" textAnchor="middle" fill="#64748b">{data.label}</text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;