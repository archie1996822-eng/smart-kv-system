import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import SpecManagement from './pages/SpecManagement';
import MaterialLibrary from './pages/MaterialLibrary';
import Workbench from './pages/Workbench';
import PreviewExport from './pages/PreviewExport';
import History from './pages/History';
import Login from './pages/Login';
import Home from './pages/Home';
import BrandKit from './pages/BrandKit';
import Dashboard from './pages/Dashboard';
import ShareView from './pages/ShareView';
import { getCurrentUser, logout, isAdmin, UserContext } from './data/auth';

const PUBLIC_PATHS = ['/login', '/'];

export default function App() {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Load user on mount
  useEffect(() => {
    const u = getCurrentUser();
    setUser(u);
    setReady(true);
    if (!u && !PUBLIC_PATHS.includes(location.pathname)) {
      navigate('/', { replace: true });
    }
  }, []);

  const handleLogin = (u) => {
    setUser(u);
    navigate('/app', { replace: true });
  };

  const handleLogout = () => {
    logout();
    setUser(null);
    navigate('/', { replace: true });
  };

  // Expose logout
  useEffect(() => { window.__kvLogout = handleLogout; return () => { delete window.__kvLogout; }; }, []);

  if (!ready) return null;

  const admin = isAdmin();

  return (
    <UserContext.Provider value={user}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={user ? <Navigate to="/app" replace /> : <Login onLogin={handleLogin} />} />
        <Route path="/app" element={user ? <Dashboard /> : <Navigate to="/login" replace />} />
        <Route path="/workbench" element={user ? <Workbench /> : <Navigate to="/login" replace />} />
        <Route path="/material-lib" element={user ? <MaterialLibrary /> : <Navigate to="/login" replace />} />
        <Route path="/brand-kit" element={user ? <BrandKit /> : <Navigate to="/login" replace />} />
        <Route path="/history" element={user ? <History /> : <Navigate to="/login" replace />} />
        <Route path="/spec-settings" element={admin ? <SpecManagement /> : <Navigate to="/app" replace />} />
        <Route path="/export-center" element={user ? <PreviewExport /> : <Navigate to="/login" replace />} />
        <Route path="/share/:shareKey" element={<ShareView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </UserContext.Provider>
  );
}
