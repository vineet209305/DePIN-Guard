import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import BlockchainPage from './pages/BlockchainPage';
import AIAnalysisPage from './pages/AIAnalysisPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import LandingPage from './pages/LandingPage';
import FraudReport from './pages/FraudReport';

// ✅ Casing fix — file ka naam Securitypage.jsx hai
import SecurityPage from './pages/Securitypage';

const isTokenUsable = (token) => {
  if (!token || token === 'null') {
    return false;
  }

  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }

    const payloadJson = atob(parts[1]);
    const payload = JSON.parse(payloadJson);

    if (!payload.exp) {
      return true;
    }

    const now = Math.floor(Date.now() / 1000);
    return payload.exp > now;
  } catch {
    return false;
  }
};

// Protected Route — login nahi hai to /login pe bhejo
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!isTokenUsable(token)) {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('token');
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Public Route — already logged in hai to /dashboard pe bhejo
const PublicRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (isTokenUsable(token)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    // ✅ React Router v7 future flags — warnings band ho jaayenge
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>

        {/* Landing Page — Home */}
        <Route path="/" element={<LandingPage />} />

        {/* Public Routes */}
        <Route path="/login" element={
          <PublicRoute><LoginPage /></PublicRoute>
        } />
        <Route path="/signup" element={
          <PublicRoute><SignupPage /></PublicRoute>
        } />

        {/* Protected Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/blockchain" element={
          <ProtectedRoute><BlockchainPage /></ProtectedRoute>
        } />
        <Route path="/ai-analysis" element={
          <ProtectedRoute><AIAnalysisPage /></ProtectedRoute>
        } />
        <Route path="/history" element={
          <ProtectedRoute><HistoryPage /></ProtectedRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute><SettingsPage /></ProtectedRoute>
        } />
        <Route path="/fraud-alerts" element={
          <ProtectedRoute><FraudReport /></ProtectedRoute>
        } />
        <Route path="/security" element={
          <ProtectedRoute><SecurityPage /></ProtectedRoute>
        } />

        {/* 404 — Landing pe bhejo */}
        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>
    </Router>
  );
}

export default App;