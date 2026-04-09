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
import { getStoredToken, clearAuthStorage } from './utils/sessionAuth';

// ✅ Correct import (file: SecurityPage.jsx)
import SecurityPage from './pages/SecurityPage';

const isTokenUsable = (token) => {
  if (!token || token === 'null') return false;

  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;

    const payload = JSON.parse(atob(parts[1]));
    if (!payload.exp) return true;

    return payload.exp > Math.floor(Date.now() / 1000);
  } catch {
    return false;
  }
};

const ProtectedRoute = ({ children }) => {
  const token = getStoredToken();
  if (!isTokenUsable(token)) {
    clearAuthStorage();
    return <Navigate to="/login" replace />;
  }
  return children;
};

const PublicRoute = ({ children }) => {
  const token = getStoredToken();
  if (isTokenUsable(token)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>

        <Route path="/" element={<LandingPage />} />

        <Route path="/login" element={
          <PublicRoute><LoginPage /></PublicRoute>
        } />
        <Route path="/signup" element={
          <PublicRoute><SignupPage /></PublicRoute>
        } />

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

        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>
    </Router>
  );
}

export default App;