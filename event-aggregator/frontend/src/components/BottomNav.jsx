import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function BottomNav({ unreadCount = 0 }) {
  const { user } = useAuth();

  const items = [
    { to: '/', label: 'Home', icon: '⌂' },
    { to: '/search', label: 'Search', icon: '⌕' },
  ];

  if (user?.role === 'organiser' || user?.role === 'admin') {
    items.push({ to: '/submit', label: 'Submit', icon: '+' });
    items.push({ to: '/mine', label: 'My events', icon: '☰' });
  }
  if (user?.role === 'admin') {
    items.push({ to: '/admin', label: 'Admin', icon: '⚙' });
  }
  if (user) {
    items.push({ to: '/notifications', label: 'Alerts', icon: '🔔', badge: unreadCount });
  }
  items.push({ to: user ? '/profile' : '/login', label: user ? 'Profile' : 'Log in', icon: '☺' });

  return (
    <nav className="bottom-nav">
      <div className="nav-brand">
        <strong>KABU Events</strong>
        <span>Kabarak University</span>
      </div>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
        >
          <span className="dot">
            {item.icon}
            {item.badge ? <span className="badge">{item.badge}</span> : null}
          </span>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
