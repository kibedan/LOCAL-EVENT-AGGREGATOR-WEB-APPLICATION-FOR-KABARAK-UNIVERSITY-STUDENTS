import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';

function timeAgo(iso) {
  if (!iso) return '';
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Notifications({ onChange }) {
  const { token } = useAuth();
  const [notes, setNotes] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  function load() {
    api.notifications(token)
      .then((d) => { setNotes(d.notifications); onChange && onChange(d.notifications); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [token]);

  async function handleRead(id) {
    try {
      await api.markRead(id, token);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <Header title="Notifications" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && notes.length === 0 && (
          <p className="empty-state">No notifications yet. Enable alerts on an event to get notified here.</p>
        )}
        {notes.map((n) => (
          <Link
            to={`/events/${n.event_id}`}
            key={n.id}
            className="card"
            style={{ display: 'block', opacity: n.is_read ? 0.6 : 1 }}
            onClick={() => !n.is_read && handleRead(n.id)}
          >
            <p style={{ margin: 0, fontSize: 14 }}>{n.message}</p>
            <p className="meta" style={{ margin: '4px 0 0' }}>{timeAgo(n.created_at)}{!n.is_read ? ' · new' : ''}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
