import React from 'react';
import './IoTAlertCard.css';

/**
 * IoTAlertCard - Displays IoT device status with professional, non-technical format
 * 
 * Props:
 *   device_id (string): Device identifier
 *   machine_name (string): Human-readable machine name (e.g., "Compressor")
 *   alert_level (string): "normal" | "warning" | "critical"
 *   status_short (string): Brief status description
 *   temperature (number): Temperature in Celsius
 *   vibration (number): Vibration in mm/s
 *   power_usage (number): Power in kW
 *   recommendations (array): List of actionable recommendations
 *   timestamp (string): ISO timestamp
 */
const IoTAlertCard = ({
  device_id = 'Device-000',
  machine_name = 'Unknown Machine',
  alert_level = 'normal',
  status_short = 'Running normally',
  temperature = 0,
  vibration = 0,
  power_usage = 0,
  recommendations = [],
  timestamp = null,
}) => {
  // Map alert levels to display properties
  const alertConfig = {
    normal: {
      icon: '✅',
      bgColor: '#ecfdf5',
      borderColor: '#10b981',
      textColor: '#065f46',
      badgeText: 'NORMAL',
      instruction: 'Continue normal operation. No action needed.',
    },
    warning: {
      icon: '⚠️',
      bgColor: '#fffbeb',
      borderColor: '#f59e0b',
      textColor: '#78350f',
      badgeText: 'WARNING',
      instruction: 'Monitor closely! Take corrective action if status worsens.',
    },
    critical: {
      icon: '🚨',
      bgColor: '#fef2f2',
      borderColor: '#ef4444',
      textColor: '#7f1d1d',
      badgeText: 'CRITICAL',
      instruction: 'IMMEDIATE ACTION REQUIRED. Stop machine and alert maintenance.',
    },
  };

  const config = alertConfig[alert_level] || alertConfig.normal;

  // Format timestamp
  const formatTime = (ts) => {
    if (!ts) return 'N/A';
    try {
      return new Date(ts).toLocaleTimeString();
    } catch {
      return 'N/A';
    }
  };

  // Categorize readings
  const categorizeReading = (label, value, unit, normalRange) => {
    const { min, max } = normalRange;
    let category = 'normal';
    let indicator = '✓';

    if (value < min || value > max) {
      category = 'concerning';
      indicator = '⚠';
    }

    return { category, indicator, label, value, unit };
  };

  // Get normal ranges based on metric
  const getStatusForMetric = (metric, value) => {
    const ranges = {
      temperature: { min: 20, max: 85 },
      vibration: { min: 0, max: 10 },
      power_usage: { min: 10, max: 150 },
    };
    return categorizeReading(metric, value, metric === 'temperature' ? '°C' : metric === 'vibration' ? 'mm/s' : 'kW', ranges[metric] || { min: 0, max: 100 });
  };

  const readings = [
    getStatusForMetric('temperature', temperature),
    getStatusForMetric('vibration', vibration),
    getStatusForMetric('power_usage', power_usage),
  ];

  return (
    <div className="iot-alert-card" style={{ borderColor: config.borderColor, backgroundColor: config.bgColor }}>
      {/* Header */}
      <div className="iot-header">
        <div className="iot-title-section">
          <span className="iot-icon">{config.icon}</span>
          <div className="iot-machine-info">
            <h3 className="iot-machine-name">{machine_name}</h3>
            <p className="iot-device-id">{device_id}</p>
          </div>
        </div>
        <span className="iot-badge" style={{ backgroundColor: config.borderColor, color: 'white' }}>
          {config.badgeText}
        </span>
      </div>

      {/* Status Short Description */}
      <div className="iot-status-section">
        <p className="iot-status-text" style={{ color: config.textColor }}>
          {status_short}
        </p>
        <p className="iot-instruction" style={{ color: config.textColor }}>
          {config.instruction}
        </p>
      </div>

      {/* Readings Grid */}
      <div className="iot-readings-grid">
        {readings.map((reading) => (
          <div key={reading.label} className="iot-reading-card">
            <div className="iot-reading-indicator">{reading.indicator}</div>
            <p className="iot-reading-label">{reading.label}</p>
            <p className="iot-reading-value">
              {reading.value}
              <span className="iot-reading-unit">{reading.unit}</span>
            </p>
            <p className="iot-reading-status">{reading.category}</p>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div className="iot-recommendations">
          <h4 className="iot-recommendations-title">✓ Recommended Actions:</h4>
          <ol className="iot-recommendations-list">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="iot-recommendation-item">
                {rec}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Footer with Timestamp */}
      <div className="iot-footer">
        <p className="iot-timestamp">Updated: {formatTime(timestamp)}</p>
      </div>
    </div>
  );
};

export default IoTAlertCard;
