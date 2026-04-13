import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { authFetch } from '../utils/authApi';
import { clearAuthStorage, storeUserProfile } from '../utils/sessionAuth';
import './SettingsPage.css';

const NAV_ITEMS = [
  { id: 'profile',       label: 'Profile',       icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { id: 'security',      label: 'Security',      icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
  { id: 'notifications', label: 'Notifications', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' },
  { id: 'appearance',    label: 'Appearance',    icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01' },
  { id: 'devices',       label: 'Devices',       icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z' },
];

const Toggle = ({ checked, onChange }) => (
  <label className="sp-toggle">
    <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
    <span className="sp-toggle-track"><span className="sp-toggle-thumb" /></span>
  </label>
);

const Field = ({ label, children }) => (
  <div className="sp-field">
    <label className="sp-field-label">{label}</label>
    {children}
  </div>
);

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [settings, setSettings] = useState({
    fullName: '', email: '', phone: '', bio: '',
    emailNotifications: true, smsNotifications: false, alertNotifications: true,
    weeklyDigest: true, securityAlerts: true,
    autoRefresh: true, refreshInterval: '30', dataRetention: '90',
    theme: 'dark', language: 'en', density: 'comfortable',
  });
  const [original, setOriginal]     = useState(null);
  const [isSaving, setIsSaving]     = useState(false);
  const [toast, setToast]           = useState(null);
  const [passwordData, setPassword] = useState({ current: '', newPass: '', confirm: '' });
  const [pwMsg, setPwMsg]           = useState(null);

  useEffect(() => {
    (async () => {
      const email = localStorage.getItem('userEmail') || '';
      const name  = localStorage.getItem('userName')  || '';
      try {
        const res = await authFetch('/profile');
        if (res.ok) {
          const { profile = {} } = await res.json();
          const init = { ...settings, fullName: profile.full_name || name, email: profile.email || email, phone: profile.phone || '', bio: profile.bio || '' };
          setSettings(init); setOriginal(init);
          storeUserProfile(profile); return;
        }
      } catch {}
      const init = { ...settings, fullName: name, email };
      setSettings(init); setOriginal(init);
    })();
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', settings.theme === 'auto' ? '' : settings.theme);
    root.style.colorScheme = settings.theme === 'auto' ? 'auto' : settings.theme;
  }, [settings.theme]);

  const hasChanges = original && JSON.stringify(settings) !== JSON.stringify(original);

  const flash = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const set = (k, v) => setSettings(p => ({ ...p, [k]: v }));

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const res = await authFetch('/profile', {
        method: 'POST',
        body: JSON.stringify({ full_name: settings.fullName, email: settings.email, phone: settings.phone }),
      });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Save failed'); }
      const data = await res.json();
      storeUserProfile(data.profile || settings);
      localStorage.setItem('iot-settings', JSON.stringify(settings));
      setOriginal({ ...settings });
      flash('Changes saved successfully');
    } catch (err) { flash(err.message, 'error'); }
    finally { setIsSaving(false); }
  };

  const handlePasswordChange = () => {
    setPwMsg(null);
    if (!passwordData.current || !passwordData.newPass || !passwordData.confirm)
      return setPwMsg({ text: 'All fields are required.', type: 'error' });
    if (passwordData.newPass.length < 8)
      return setPwMsg({ text: 'Password must be at least 8 characters.', type: 'error' });
    if (passwordData.newPass !== passwordData.confirm)
      return setPwMsg({ text: 'Passwords do not match.', type: 'error' });
    setPwMsg({ text: 'Password update is not yet enabled. Contact your admin.', type: 'warning' });
  };

  const handleReset = () => {
    if (!window.confirm('Reset all settings to defaults?')) return;
    const def = {
      fullName: localStorage.getItem('userName') || '', email: localStorage.getItem('userEmail') || '',
      phone: '', bio: '', emailNotifications: true, smsNotifications: false, alertNotifications: true,
      weeklyDigest: true, securityAlerts: true, autoRefresh: true,
      refreshInterval: '30', dataRetention: '90', theme: 'dark', language: 'en', density: 'comfortable',
    };
    setSettings(def); setOriginal(def);
    localStorage.setItem('iot-settings', JSON.stringify(def));
    flash('Settings reset to defaults');
  };

  const handleDeleteAccount = () => {
    if (!window.confirm('This will permanently delete your account. This cannot be undone.')) return;
    if (window.prompt('Type DELETE to confirm:') === 'DELETE') {
      clearAuthStorage();
      localStorage.removeItem('iot-settings');
      window.location.href = '/login';
    }
  };

  const initials = settings.fullName
    ? settings.fullName.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
    : 'U';

  if (!original) return null;

  return (
    <Layout>
      <div className="sp-root">

        {/* ── Sidebar ── */}
        <aside className="sp-sidebar">
          <div className="sp-sidebar-header">
            <div className="sp-avatar-lg">{initials}</div>
            <div className="sp-sidebar-name">{settings.fullName || 'User'}</div>
            <div className="sp-sidebar-email">{settings.email}</div>
          </div>

          <nav className="sp-nav">
            <p className="sp-nav-label">Account</p>
            {NAV_ITEMS.slice(0, 3).map(({ id, label, icon }) => (
              <button key={id} className={`sp-nav-item${activeTab === id ? ' active' : ''}`} onClick={() => setActiveTab(id)}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={icon} />
                </svg>
                {label}
              </button>
            ))}
            <p className="sp-nav-label">Preferences</p>
            {NAV_ITEMS.slice(3).map(({ id, label, icon }) => (
              <button key={id} className={`sp-nav-item${activeTab === id ? ' active' : ''}`} onClick={() => setActiveTab(id)}>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={icon} />
                </svg>
                {label}
              </button>
            ))}
            <p className="sp-nav-label">Danger</p>
            <button className="sp-nav-item sp-nav-danger" onClick={handleDeleteAccount}>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Account
            </button>
          </nav>
        </aside>

        {/* ── Main ── */}
        <main className="sp-main">

          {/* Top bar */}
          <div className="sp-topbar">
            <div>
              <h1 className="sp-page-title">
                {NAV_ITEMS.find(n => n.id === activeTab)?.label ?? 'Settings'}
              </h1>
              <p className="sp-page-sub">Manage your account and preferences</p>
            </div>
            <div className="sp-topbar-actions">
              <button className="sp-btn-ghost" onClick={handleReset}>Reset defaults</button>
              <button
                className={`sp-btn-primary${!hasChanges || isSaving ? ' disabled' : ''}`}
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
              >
                {isSaving
                  ? <><span className="sp-spinner" />Saving…</>
                  : hasChanges ? 'Save changes' : 'Saved'}
              </button>
            </div>
          </div>

          {/* ── Profile ── */}
          {activeTab === 'profile' && (
            <div className="sp-pane">
              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Personal information</h2>
                  <p>Your name and contact details</p>
                </div>
                <div className="sp-avatar-row">
                  <div className="sp-avatar-xl">{initials}</div>
                  <div>
                    <p className="sp-avatar-name">{settings.fullName || 'User'}</p>
                    <p className="sp-avatar-hint">PNG, JPG up to 2MB</p>
                    <button className="sp-btn-ghost sp-btn-sm">Change photo</button>
                  </div>
                </div>
                <div className="sp-fields-grid">
                  <Field label="Full name">
                    <input className="sp-input" value={settings.fullName} onChange={e => set('fullName', e.target.value)} placeholder="Your full name" />
                  </Field>
                  <Field label="Email address">
                    <input className="sp-input" type="email" value={settings.email} onChange={e => set('email', e.target.value)} placeholder="you@example.com" />
                  </Field>
                  <Field label="Phone number">
                    <input className="sp-input" type="tel" value={settings.phone} onChange={e => set('phone', e.target.value)} placeholder="+91 XXXXX XXXXX" />
                  </Field>
                  <Field label="Language">
                    <select className="sp-select" value={settings.language} onChange={e => set('language', e.target.value)}>
                      <option value="en">English</option>
                      <option value="hi">हिन्दी</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                    </select>
                  </Field>
                  <Field label="Bio">
                    <textarea className="sp-textarea" rows={3} value={settings.bio} onChange={e => set('bio', e.target.value)} placeholder="Short bio…" />
                  </Field>
                </div>
              </div>
            </div>
          )}

          {/* ── Security ── */}
          {activeTab === 'security' && (
            <div className="sp-pane">
              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Change password</h2>
                  <p>Use a strong, unique password</p>
                </div>
                <div className="sp-fields-grid sp-fields-single">
                  {[
                    { label: 'Current password',    key: 'current', placeholder: 'Enter current password' },
                    { label: 'New password',         key: 'newPass', placeholder: 'Minimum 8 characters'   },
                    { label: 'Confirm new password', key: 'confirm', placeholder: 'Re-enter new password'  },
                  ].map(({ label, key, placeholder }) => (
                    <Field key={key} label={label}>
                      <input
                        className="sp-input"
                        type="password"
                        value={passwordData[key]}
                        onChange={e => setPassword(p => ({ ...p, [key]: e.target.value }))}
                        placeholder={placeholder}
                      />
                    </Field>
                  ))}
                  {pwMsg && <div className={`sp-inline-msg sp-inline-msg--${pwMsg.type}`}>{pwMsg.text}</div>}
                  <button className="sp-btn-primary sp-btn-full" onClick={handlePasswordChange}>Update password</button>
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Active sessions</h2>
                  <p>Devices currently signed in</p>
                </div>
                {[
                  { device: 'Chrome on Windows', location: 'Mumbai, IN', time: 'Active now', active: true },
                  { device: 'Safari on iPhone',  location: 'Delhi, IN',  time: '2 days ago', active: false },
                ].map((s, i) => (
                  <div key={i} className="sp-session-row">
                    <span className={`sp-session-dot${s.active ? '' : ' inactive'}`} />
                    <div className="sp-session-info">
                      <p>{s.device}</p>
                      <span>{s.location} · {s.time}</span>
                    </div>
                    {!s.active && <button className="sp-btn-ghost sp-btn-sm sp-btn-danger-ghost">Revoke</button>}
                    {s.active && <span className="sp-badge-active">This device</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Notifications ── */}
          {activeTab === 'notifications' && (
            <div className="sp-pane">
              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Notification preferences</h2>
                  <p>Choose how you want to be notified</p>
                </div>
                {[
                  { label: 'Email notifications', desc: 'Updates and summaries via email',   field: 'emailNotifications' },
                  { label: 'SMS notifications',   desc: 'Text message alerts to your phone', field: 'smsNotifications'   },
                  { label: 'Alert notifications', desc: 'Critical device and system alerts', field: 'alertNotifications' },
                  { label: 'Weekly digest',        desc: 'Summary of activity every Monday',  field: 'weeklyDigest'       },
                  { label: 'Security alerts',      desc: 'Login and access notifications',    field: 'securityAlerts'     },
                ].map(({ label, desc, field }) => (
                  <div key={field} className="sp-toggle-row">
                    <div>
                      <p className="sp-toggle-label">{label}</p>
                      <p className="sp-toggle-desc">{desc}</p>
                    </div>
                    <Toggle checked={settings[field]} onChange={v => set(field, v)} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Appearance ── */}
          {activeTab === 'appearance' && (
            <div className="sp-pane">
              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Theme</h2>
                  <p>Choose your preferred look</p>
                </div>
                <div className="sp-theme-grid">
                  {[
                    { value: 'dark',  label: 'Dark',   desc: 'Easy on the eyes' },
                    { value: 'light', label: 'Light',  desc: 'Clean and bright'  },
                    { value: 'auto',  label: 'System', desc: 'Follows your OS'   },
                  ].map(t => (
                    <button
                      key={t.value}
                      className={`sp-theme-option${settings.theme === t.value ? ' active' : ''}`}
                      onClick={() => set('theme', t.value)}
                    >
                      <div className={`sp-theme-preview sp-theme-preview--${t.value}`} />
                      <p>{t.label}</p>
                      <span>{t.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Interface density</h2>
                  <p>Adjust how compact the UI appears</p>
                </div>
                <div className="sp-fields-grid sp-fields-single">
                  <Field label="Density">
                    <select className="sp-select" value={settings.density} onChange={e => set('density', e.target.value)}>
                      <option value="comfortable">Comfortable</option>
                      <option value="compact">Compact</option>
                      <option value="spacious">Spacious</option>
                    </select>
                  </Field>
                </div>
              </div>
            </div>
          )}

          {/* ── Devices ── */}
          {activeTab === 'devices' && (
            <div className="sp-pane">
              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Data refresh</h2>
                  <p>Control how often device data updates</p>
                </div>
                <div className="sp-toggle-row">
                  <div>
                    <p className="sp-toggle-label">Auto refresh</p>
                    <p className="sp-toggle-desc">Automatically pull latest device data</p>
                  </div>
                  <Toggle checked={settings.autoRefresh} onChange={v => set('autoRefresh', v)} />
                </div>
                <div className="sp-fields-grid sp-fields-single" style={{ marginTop: '1.25rem' }}>
                  <Field label={`Refresh interval${!settings.autoRefresh ? ' (disabled)' : ''}`}>
                    <select className="sp-select" value={settings.refreshInterval} onChange={e => set('refreshInterval', e.target.value)} disabled={!settings.autoRefresh}>
                      <option value="10">10 seconds</option>
                      <option value="30">30 seconds</option>
                      <option value="60">1 minute</option>
                      <option value="300">5 minutes</option>
                    </select>
                  </Field>
                  <Field label="Data retention">
                    <select className="sp-select" value={settings.dataRetention} onChange={e => set('dataRetention', e.target.value)}>
                      <option value="30">30 days</option>
                      <option value="60">60 days</option>
                      <option value="90">90 days</option>
                      <option value="180">180 days</option>
                      <option value="365">1 year</option>
                    </select>
                  </Field>
                </div>
              </div>

              <div className="sp-card">
                <div className="sp-card-head">
                  <h2>Data export / import</h2>
                  <p>Backup or restore your settings</p>
                </div>
                <div className="sp-export-row">
                  <button className="sp-btn-ghost" onClick={() => {
                    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
                    const url  = URL.createObjectURL(blob);
                    const a    = Object.assign(document.createElement('a'), { href: url, download: `settings-${new Date().toISOString().split('T')[0]}.json` });
                    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
                    flash('Settings exported!');
                  }}>Export settings</button>
                  <button className="sp-btn-ghost" onClick={() => {
                    const input = Object.assign(document.createElement('input'), { type: 'file', accept: '.json' });
                    input.onchange = e => {
                      const file = e.target.files[0]; if (!file) return;
                      const reader = new FileReader();
                      reader.onload = ev => { try { setSettings(JSON.parse(ev.target.result)); flash('Imported! Click Save to apply.', 'warning'); } catch { alert('Invalid file.'); } };
                      reader.readAsText(file);
                    };
                    input.click();
                  }}>Import settings</button>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>

      {/* Toast */}
      {toast && <div className={`sp-toast sp-toast--${toast.type}`}>{toast.msg}</div>}
    </Layout>
  );
}