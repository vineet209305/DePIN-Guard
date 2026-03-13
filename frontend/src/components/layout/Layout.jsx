import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Footer from './Footer';
import './Layout.css';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  
  const location = useLocation();
  const navigate = useNavigate();
  const profileRef = useRef(null);
  const searchRef = useRef(null);

  // Apply theme logic
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Handle Search
  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      alert(`Searching for: ${searchQuery}`);
      setSearchOpen(false);
      setSearchQuery('');
    }
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      localStorage.removeItem('isAuthenticated');
      navigate('/login');
    }
  };

  const navItems = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard', description: 'Overview' },
    { path: '/blockchain', icon: '🔗', label: 'Blockchain', description: 'Explorer' },
    { path: '/ai-analysis', icon: '🤖', label: 'AI Analysis', description: 'Anomaly' },
    { path: '/history', icon: '📜', label: 'History', description: 'Records' },
    { path: '/settings', icon: '⚙️', label: 'Settings', description: 'Setup' },
  ];

  return (
    <div className={`layout ${theme}-theme`}>
      {/* Search Bar Overlay */}
      {searchOpen && (
        <div className="search-overlay" onClick={() => setSearchOpen(false)}>
          <div className="search-container" onClick={e => e.stopPropagation()}>
            <form onSubmit={handleSearch} className="search-form">
              <input 
                type="text" 
                placeholder="Search..." 
                autoFocus 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit">Search</button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <span className="logo-text">IoT Dashboard</span>
        </div>
        
        <div className="header-right">
          <div className={`status-indicator ${isOnline ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            <span>{isOnline ? 'Online' : 'Offline'}</span>
          </div>

          <button className="header-button" onClick={() => setSearchOpen(true)}>🔍</button>
          <button className="header-button" onClick={toggleTheme}>
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          <div className="dropdown-container" ref={profileRef}>
            <button className="user-button" onClick={() => setProfileOpen(!profileOpen)}>
              <div className="user-avatar-small">👤</div>
            </button>
            {profileOpen && (
              <div className="profile-dropdown">
                <button className="profile-menu-item" onClick={() => navigate('/settings')}>Profile</button>
                <button className="profile-menu-item logout-item" onClick={handleLogout}>Logout</button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Sidebar Overlay for Mobile */}
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link 
              key={item.path} 
              to={item.path} 
              className={`nav-item ${location.pathname === item.path ? 'nav-item-active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <div className="nav-text">
                <span className="nav-label">{item.label}</span>
              </div>
            </Link>
          ))}
        </nav>

        {/* Fixed Bottom Logout Section */}
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">👤</div>
            <div className="user-details">
              <div className="user-name">Admin User</div>
              <div className="user-email">admin@iot.com</div>
            </div>
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>🚪</button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {children}
        <Footer />
      </main>
    </div>
  );
};

export default Layout;