import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import './SettingsPage.css';

const SettingsPage = () => {
  const [settings, setSettings] = useState({
    fullName: '',
    email: '',
    phone: '',
    emailNotifications: true,
    smsNotifications: false,
    alertNotifications: true,
    autoRefresh: true,
    refreshInterval: '30',
    dataRetention: '90',
    theme: 'dark',
    language: 'en'
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [originalSettings, setOriginalSettings] = useState(null);
  const [passwordData, setPasswordData] = useState({ current: '', newPass: '', confirm: '' });
  const [passwordMsg, setPasswordMsg] = useState('');

  // ✅ Load settings — signup data + saved settings
  useEffect(() => {
    // Signup se aaya hua data
    const userEmail = localStorage.getItem('userEmail') || '';
    const userName = localStorage.getItem('userName') || '';

    // Registered users list se phone bhi nikalo agar ho
    const registeredUsersRaw = localStorage.getItem('registeredUsers');
    const registeredUsers = registeredUsersRaw ? JSON.parse(registeredUsersRaw) : [];
    const matchedUser = registeredUsers.find(u => u.email?.toLowerCase() === userEmail.toLowerCase());

    const baseProfile = {
      fullName: matchedUser?.fullName || userName || 'User',
      email: matchedUser?.email || userEmail || '',
      phone: matchedUser?.phone || '',
    };

    // Pehle saved settings dekho
    const savedRaw = localStorage.getItem('iot-settings');
    if (savedRaw) {
      const saved = JSON.parse(savedRaw);
      // Profile ko signup se override karo (agar manually change nahi kiya)
      const merged = {
        ...saved,
        fullName: saved.fullName || baseProfile.fullName,
        email: saved.email || baseProfile.email,
        phone: saved.phone || baseProfile.phone,
      };
      setSettings(merged);
      setOriginalSettings(merged);
    } else {
      const initial = {
        ...settings,
        ...baseProfile,
      };
      setSettings(initial);
      setOriginalSettings(initial);
    }
  }, []);

  // ✅ Theme apply — dark/light/auto
  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === 'dark') {
      root.setAttribute('data-theme', 'dark');
      root.style.colorScheme = 'dark';
    } else if (settings.theme === 'light') {
      root.setAttribute('data-theme', 'light');
      root.style.colorScheme = 'light';
    } else {
      // auto — system preference follow karo
      root.removeAttribute('data-theme');
      root.style.colorScheme = 'auto';
    }
  }, [settings.theme]);

  // ✅ Track changes
  useEffect(() => {
    if (!originalSettings) return;
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [settings, originalSettings]);

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
    setSaveMessage('');
  };

  // ✅ Save — localStorage + userName/userEmail bhi update karo
  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage('');
    await new Promise(resolve => setTimeout(resolve, 1000));

    localStorage.setItem('iot-settings', JSON.stringify(settings));
    localStorage.setItem('userName', settings.fullName);
    localStorage.setItem('userEmail', settings.email);

    // registeredUsers mein bhi update karo
    const registeredUsersRaw = localStorage.getItem('registeredUsers');
    if (registeredUsersRaw) {
      const users = JSON.parse(registeredUsersRaw);
      const idx = users.findIndex(u => u.email?.toLowerCase() === originalSettings.email?.toLowerCase());
      if (idx !== -1) {
        users[idx] = { ...users[idx], fullName: settings.fullName, email: settings.email, phone: settings.phone };
        localStorage.setItem('registeredUsers', JSON.stringify(users));
      }
    }

    setOriginalSettings(settings);
    setIsSaving(false);
    setSaveMessage('✅ Settings saved successfully!');
    setHasChanges(false);
    setTimeout(() => setSaveMessage(''), 3000);
  };

  // ✅ Password change
  const handlePasswordChange = () => {
    setPasswordMsg('');
    if (!passwordData.current || !passwordData.newPass || !passwordData.confirm) {
      setPasswordMsg('❌ Please fill all password fields.');
      return;
    }
    if (passwordData.newPass.length < 8) {
      setPasswordMsg('❌ New password must be at least 8 characters.');
      return;
    }
    if (passwordData.newPass !== passwordData.confirm) {
      setPasswordMsg('❌ New passwords do not match.');
      return;
    }

    // Verify current password
    const registeredUsersRaw = localStorage.getItem('registeredUsers');
    const users = registeredUsersRaw ? JSON.parse(registeredUsersRaw) : [];
    const idx = users.findIndex(u => u.email?.toLowerCase() === settings.email?.toLowerCase());

    if (idx === -1 || users[idx].password !== passwordData.current) {
      setPasswordMsg('❌ Current password is incorrect.');
      return;
    }

    users[idx].password = passwordData.newPass;
    localStorage.setItem('registeredUsers', JSON.stringify(users));
    setPasswordData({ current: '', newPass: '', confirm: '' });
    setPasswordMsg('✅ Password changed successfully!');
    setTimeout(() => setPasswordMsg(''), 3000);
  };

  const handleReset = () => {
    if (window.confirm('Reset all settings to default?')) {
      const userEmail = localStorage.getItem('userEmail') || '';
      const userName = localStorage.getItem('userName') || '';
      const def = {
        fullName: userName,
        email: userEmail,
        phone: '',
        emailNotifications: true,
        smsNotifications: false,
        alertNotifications: true,
        autoRefresh: true,
        refreshInterval: '30',
        dataRetention: '90',
        theme: 'dark',
        language: 'en'
      };
      setSettings(def);
      setOriginalSettings(def);
      localStorage.setItem('iot-settings', JSON.stringify(def));
      setSaveMessage('✅ Reset to defaults!');
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  const handleDeleteAccount = () => {
    if (window.confirm('⚠️ This will permanently delete your account. Cannot be undone!')) {
      const confirmation = window.prompt('Type DELETE to confirm:');
      if (confirmation === 'DELETE') {
        // Remove this user from registeredUsers
        const registeredUsersRaw = localStorage.getItem('registeredUsers');
        if (registeredUsersRaw) {
          const users = JSON.parse(registeredUsersRaw);
          const filtered = users.filter(u => u.email?.toLowerCase() !== settings.email?.toLowerCase());
          localStorage.setItem('registeredUsers', JSON.stringify(filtered));
        }
        localStorage.removeItem('token');
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userName');
        localStorage.removeItem('iot-settings');
        alert('Account deleted. Redirecting to login...');
        window.location.href = '/login';
      } else {
        alert('Account deletion cancelled.');
      }
    }
  };

  const handleExportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `depin-settings-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setSaveMessage('✅ Settings exported!');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const handleImportSettings = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const imported = JSON.parse(event.target.result);
            setSettings(imported);
            setSaveMessage('⚠️ Settings imported! Click Save to apply.');
          } catch {
            alert('Invalid file format.');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  if (!originalSettings) return null;

  return (
    <Layout>
      <div className="settings-container">

        {/* Page Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">Settings</h1>
            <p className="page-subtitle">Manage your account and preferences</p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {saveMessage && (
              <div style={{
                padding: '0.5rem 1rem',
                background: saveMessage.includes('⚠️') ? '#f59e0b20' : '#22c55e20',
                color: saveMessage.includes('⚠️') ? '#f59e0b' : '#22c55e',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '600'
              }}>
                {saveMessage}
              </div>
            )}
            <button
              className={`save-button ${isSaving ? 'saving' : ''}`}
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
              style={{ opacity: hasChanges ? 1 : 0.5, cursor: hasChanges ? 'pointer' : 'not-allowed' }}
            >
              {isSaving ? (
                <>
                  <svg className="spinner" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" opacity="0.25"/>
                    <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" opacity="0.75"/>
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  {hasChanges ? 'Save Changes' : 'No Changes'}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          {[
            { label: 'Export Settings', fn: handleExportSettings, color: '#0ea5e9' },
            { label: 'Import Settings', fn: handleImportSettings, color: '#8b5cf6' },
            { label: 'Reset to Defaults', fn: handleReset, color: '#f59e0b' },
          ].map(({ label, fn, color }) => (
            <button key={label} onClick={fn} style={{
              padding: '0.5rem 1rem',
              background: color + '20',
              color,
              border: `1px solid ${color}40`,
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '600',
            }}>
              {label}
            </button>
          ))}
        </div>

        <div className="settings-grid">

          {/* ── Profile ── */}
          <div className="settings-card">
            <div className="card-header">
              <div className="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h2 className="card-title">Profile Information</h2>
                <p className="card-subtitle">Update your personal details</p>
              </div>
            </div>
            {[
              { label: 'Full Name', field: 'fullName', type: 'text', placeholder: 'Enter your full name' },
              { label: 'Email Address', field: 'email', type: 'email', placeholder: 'your@email.com' },
              { label: 'Phone Number', field: 'phone', type: 'tel', placeholder: '+91 XXXXX XXXXX' },
            ].map(({ label, field, type, placeholder }) => (
              <div className="form-group" key={field}>
                <label className="form-label">{label}</label>
                <input
                  type={type}
                  value={settings[field]}
                  onChange={(e) => handleChange(field, e.target.value)}
                  className="form-input"
                  placeholder={placeholder}
                />
              </div>
            ))}
          </div>

          {/* ── Change Password ── */}
          <div className="settings-card">
            <div className="card-header">
              <div className="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h2 className="card-title">Change Password</h2>
                <p className="card-subtitle">Update your login password</p>
              </div>
            </div>
            {[
              { label: 'Current Password', key: 'current', placeholder: 'Enter current password' },
              { label: 'New Password', key: 'newPass', placeholder: 'Min. 8 characters' },
              { label: 'Confirm New Password', key: 'confirm', placeholder: 'Re-enter new password' },
            ].map(({ label, key, placeholder }) => (
              <div className="form-group" key={key}>
                <label className="form-label">{label}</label>
                <input
                  type="password"
                  value={passwordData[key]}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, [key]: e.target.value }))}
                  className="form-input"
                  placeholder={placeholder}
                />
              </div>
            ))}
            {passwordMsg && (
              <div style={{
                padding: '0.5rem 0.75rem',
                background: passwordMsg.includes('✅') ? '#22c55e20' : '#ff444420',
                color: passwordMsg.includes('✅') ? '#22c55e' : '#ff8080',
                borderRadius: '0.5rem',
                fontSize: '0.85rem',
                marginBottom: '0.5rem'
              }}>{passwordMsg}</div>
            )}
            <button
              onClick={handlePasswordChange}
              style={{
                width: '100%', padding: '0.75rem',
                background: 'linear-gradient(135deg, #00d4ff, #0066ff)',
                border: 'none', borderRadius: '8px',
                color: '#fff', fontWeight: '700', cursor: 'pointer',
                fontSize: '0.9rem', marginTop: '0.25rem'
              }}
            >
              Update Password
            </button>
          </div>

          {/* ── Notifications ── */}
          <div className="settings-card">
            <div className="card-header">
              <div className="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <div>
                <h2 className="card-title">Notifications</h2>
                <p className="card-subtitle">Manage how you receive alerts</p>
              </div>
            </div>
            <div className="toggle-group">
              {[
                { label: 'Email Notifications', desc: 'Receive updates via email', field: 'emailNotifications' },
                { label: 'SMS Notifications', desc: 'Get text message alerts', field: 'smsNotifications' },
                { label: 'Alert Notifications', desc: 'Critical device alerts', field: 'alertNotifications' },
              ].map(({ label, desc, field }) => (
                <div className="toggle-item" key={field}>
                  <div className="toggle-info">
                    <div className="toggle-label">{label}</div>
                    <div className="toggle-description">{desc}</div>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={settings[field]}
                      onChange={(e) => handleChange(field, e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* ── Device Settings ── */}
          <div className="settings-card">
            <div className="card-header">
              <div className="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <h2 className="card-title">Device Settings</h2>
                <p className="card-subtitle">Configure device behavior</p>
              </div>
            </div>
            <div className="toggle-group">
              <div className="toggle-item">
                <div className="toggle-info">
                  <div className="toggle-label">Auto Refresh</div>
                  <div className="toggle-description">Automatically update data</div>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={settings.autoRefresh}
                    onChange={(e) => handleChange('autoRefresh', e.target.checked)}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">
                Refresh Interval (seconds)
                {!settings.autoRefresh && <span style={{ color: '#6b7280', marginLeft: '0.5rem' }}>(Disabled)</span>}
              </label>
              <select
                value={settings.refreshInterval}
                onChange={(e) => handleChange('refreshInterval', e.target.value)}
                className="form-select"
                disabled={!settings.autoRefresh}
                style={{ opacity: settings.autoRefresh ? 1 : 0.5 }}
              >
                <option value="10">10 seconds</option>
                <option value="30">30 seconds</option>
                <option value="60">1 minute</option>
                <option value="300">5 minutes</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Data Retention (days)</label>
              <select
                value={settings.dataRetention}
                onChange={(e) => handleChange('dataRetention', e.target.value)}
                className="form-select"
              >
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
              </select>
            </div>
          </div>

          {/* ── Appearance ── */}
          <div className="settings-card">
            <div className="card-header">
              <div className="card-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
              <div>
                <h2 className="card-title">Appearance</h2>
                <p className="card-subtitle">Customize your interface</p>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Theme</label>
              <select value={settings.theme} onChange={(e) => handleChange('theme', e.target.value)} className="form-select">
                <option value="dark">🌙 Dark</option>
                <option value="light">☀️ Light</option>
                <option value="auto">🔄 Auto (System)</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Language</label>
              <select value={settings.language} onChange={(e) => handleChange('language', e.target.value)} className="form-select">
                <option value="en">🇬🇧 English</option>
                <option value="hi">🇮🇳 हिन्दी</option>
                <option value="es">🇪🇸 Español</option>
                <option value="fr">🇫🇷 Français</option>
              </select>
            </div>
          </div>

        </div>

        {/* Danger Zone */}
        <div className="danger-zone">
          <div className="danger-header">
            <h2 className="danger-title">⚠️ Danger Zone</h2>
            <p className="danger-subtitle">Irreversible actions — proceed with caution</p>
          </div>
          <div className="danger-actions">
            <button className="danger-button" onClick={handleDeleteAccount}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Account & All Data
            </button>
          </div>
        </div>

      </div>
    </Layout>
  );
};

export default SettingsPage;