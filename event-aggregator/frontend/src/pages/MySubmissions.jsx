import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function MySubmissions() {
  const { token } = useAuth();
  const [events, setEvents] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api.mySubmissions(token)
      .then((d) => setEvents(d.events))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [token]);

  async function handleWithdraw(id) {
    if (!confirm('Withdraw this submission?')) return;
    try {
      await api.withdrawEvent(id, token);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <Header title="My Submissions" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        <Link to="/submit" className="btn btn-primary" style={{ display: 'block', marginBottom: 16 }}>
          + Submit a new event
        </Link>

        {loading && <p className="empty-state">Loading…</p>}
        {!loading && events.length === 0 && (
          <p className="empty-state">You haven't submitted any events yet.</p>
        )}

        {events.map((ev) => (
          <div className="card" key={ev.id}>
            <div className="row-between">
              <p className="title" style={{ margin: 0, fontWeight: 700 }}>{ev.title}</p>
              <span className={`status-pill status-${ev.status}`}>{ev.status}</span>
            </div>
            <p className="meta">📅 {formatDate(ev.date)}{ev.time ? ` · ${ev.time}` : ''}</p>
            {ev.location ? <p className="meta">📍 {ev.location}</p> : null}
            {ev.status === 'rejected' && ev.rejection_reason ? (
              <p className="meta" style={{ color: 'var(--red)' }}>Reason: {ev.rejection_reason}</p>
            ) : null}
            {ev.status === 'pending' ? (
              <button className="btn btn-danger btn-block" onClick={() => handleWithdraw(ev.id)}>
                Withdraw submission
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </>
  );
}
