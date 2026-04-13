import React from 'react';
import './AnalyticsTable.css';

/**
 * AnalyticsTable Component
 * Displays data analytics in easy-to-understand table format
 * Shows device activity with clear metrics
 */
export const AnalyticsTable = ({ chartData = [], timePeriod = '24h' }) => {
  // Calculate summary statistics
  const totalEvents = chartData.reduce((sum, d) => sum + (d.raw || 0), 0);
  const maxEvents = Math.max(...chartData.map(d => d.raw || 0), 1);
  const avgEvents = totalEvents > 0 ? (totalEvents / chartData.length).toFixed(1) : 0;

  const getActivityLevel = (value, max) => {
    const percent = (value / max) * 100;
    if (percent === 0) return 'Idle';
    if (percent < 30) return 'Low';
    if (percent < 60) return 'Moderate';
    if (percent < 80) return 'High';
    return 'Peak';
  };

  const getActivityColor = (level) => {
    switch (level) {
      case 'Idle': return '#64748b';
      case 'Low': return '#22c55e';
      case 'Moderate': return '#3b82f6';
      case 'High': return '#f59e0b';
      case 'Peak': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="analytics-table-wrapper">
      <div className="analytics-header">
        <div>
          <h3 className="analytics-title">Device Activity Analytics</h3>
          <p className="analytics-subtitle">Time period: Last {timePeriod === '24h' ? '24 Hours' : timePeriod === '7d' ? '7 Days' : '30 Days'}</p>
        </div>
        <div className="analytics-summary">
          <div className="summary-box">
            <div className="summary-label">Total Events</div>
            <div className="summary-value">{totalEvents.toLocaleString()}</div>
          </div>
          <div className="summary-box">
            <div className="summary-label">Average/Period</div>
            <div className="summary-value">{avgEvents}</div>
          </div>
          <div className="summary-box">
            <div className="summary-label">Peak Activity</div>
            <div className="summary-value">{maxEvents.toLocaleString()}</div>
          </div>
        </div>
      </div>

      <div className="analytics-content">
        {chartData.length === 0 ? (
          <div className="analytics-empty">
            <p>No activity data available for this period</p>
          </div>
        ) : (
          <div className="analytics-table-container">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Events</th>
                  <th>Activity Level</th>
                  <th>Visual</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((item, idx) => {
                  const activityLevel = getActivityLevel(item.raw, maxEvents);
                  const activityPercent = maxEvents > 0 ? (item.raw / maxEvents) * 100 : 0;
                  
                  return (
                    <tr key={idx}>
                      <td className="period-column">
                        <span className="period-label">{item.label}</span>
                      </td>
                      <td className="events-column">
                        <span className="event-count">{item.raw.toLocaleString()}</span>
                      </td>
                      <td className="activity-column">
                        <span 
                          className="activity-badge"
                          style={{ backgroundColor: getActivityColor(activityLevel) + '20', color: getActivityColor(activityLevel) }}
                        >
                          {activityLevel}
                        </span>
                      </td>
                      <td className="visual-column">
                        <div className="micro-bar-container">
                          <div 
                            className="micro-bar" 
                            style={{
                              width: `${Math.max(activityPercent, 5)}%`,
                              backgroundColor: getActivityColor(activityLevel),
                            }}
                          />
                          <span className="bar-label">{Math.round(activityPercent)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="analytics-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#64748b' }}></div>
          <span>Idle (0 events)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#22c55e' }}></div>
          <span>Low (&lt;30%)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
          <span>Moderate (30-60%)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
          <span>High (60-80%)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
          <span>Peak (&gt;80%)</span>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsTable;
