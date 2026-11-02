import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import BottomNav from './components/BottomNav';

import Home from './pages/Home';
import Search from './pages/Search';
import EventDetail from './pages/EventDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import SubmitEvent from './pages/SubmitEvent';
import MySubmissions from './pages/MySubmissions';
import AdminDashboard from './pages/AdminDashboard';
import Notifications from './pages/Notifications';
import Profile from './pages/Profile';
import ProtectedRoute from './components/ProtectedRoute';

function Shell() {
  const { ready } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();

  const handleNotificationsChange = useCallback((notes) => {
    setUnreadCount(notes.filter((n) => !n.is_read).length);
  }, []);

  if (!ready) {
    return <div className="content"><p className="empty-state">Loading…</p></div>;
  }

  // Auth pages render without the bottom nav for a focused, full-screen feel.
  const hideNav = ['/login', '/register'].includes(location.pathname);

  return (
    <div className={`shell${hideNav ? ' no-nav' : ''}`}>
      <main className="main-col">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/notifications" element={
          <ProtectedRoute><Notifications onChange={handleNotificationsChange} /></ProtectedRoute>
        } />
        <Route path="/submit" element={
          <ProtectedRoute roles={['organiser', 'admin']}><SubmitEvent /></ProtectedRoute>
        } />
        <Route path="/mine" element={
          <ProtectedRoute roles={['organiser', 'admin']}><MySubmissions /></ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute roles={['admin']}><AdminDashboard /></ProtectedRoute>
        } />
        <Route path="*" element={<Home />} />
      </Routes>
      </main>
      {!hideNav && <BottomNav unreadCount={unreadCount} />}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </BrowserRouter>
  );
}
