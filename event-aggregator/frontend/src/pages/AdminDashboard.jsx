import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function AdminDashboard() {
  const { token } = useAuth();
  const [pending, setPending] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [rejectingId, setRejectingId] = useState(null);
  const [reason, setReason] = useState('');
  const [dates, setDates] = useState({});
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState('');

  function load() {
    setLoading(true);
    Promise.all([api.pendingEvents(token), api.analytics(token)])
      .then(([p, a]) => { setPending(p.events); setStats(a); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [token]);

  async function handleImport() {
    setImporting(true);
    setImportMsg('');
    setError('');
    try {
      const s = await api.importFromWebsite(token);
      const latest = s.latest_posted ? formatDate(s.latest_posted) : 'none';
      setImportMsg(
        `Checked the university events page: ${s.listings_found} listings, latest posted ${latest}. ` +
        (s.added
          ? `Added ${s.added} to the queue${s.unconfirmed_dates ? ` (${s.unconfirmed_dates} need a date)` : ''}.`
          : 'No new upcoming events to add.')
      );
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setImporting(false);
    }
  }

  async function handleApprove(id) {
    try {
      await api.approveEvent(id, token, dates[id]);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function submitReject(id) {
    try {
      await api.rejectEvent(id, reason, token);
      setRejectingId(null);
      setReason('');
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <Header title="Admin Dashboard" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}

        {stats && (
          <>
            <p className="section-title">Usage Analytics</p>
            <div className="stat-grid">
              <div className="stat-box"><div className="num">{stats.total_events}</div><div className="label">Total events</div></div>
              <div className="stat-box"><div className="num">{stats.pending}</div><div className="label">Pending review</div></div>
              <div className="stat-box"><div className="num">{stats.approved}</div><div className="label">Approved</div></div>
              <div className="stat-box"><div className="num">{stats.total_users}</div><div className="label">Registered users</div></div>
            </div>
            {Object.keys(stats.events_by_category).length > 0 && (
              <div className="card">
                <p className="section-title" style={{ marginTop: 0 }}>Approved events by category</p>
                {Object.entries(stats.events_by_category).map(([name, count]) => (
                  <div className="row-between" key={name} style={{ fontSize: 13, marginBottom: 4 }}>
                    <span style={{ textTransform: 'capitalize' }}>{name}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        <div className="card">
          <p className="section-title" style={{ marginTop: 0 }}>University website</p>
          <p className="meta" style={{ marginBottom: 10 }}>
            Collect upcoming events from the public events page. Results join the queue below as pending.
          </p>
          <button className="btn btn-secondary" onClick={handleImport} disabled={importing}>
            {importing ? 'Checking the website…' : '⟳ Import from university website'}
          </button>
          {importMsg && <div className="success-banner" style={{ marginTop: 10, marginBottom: 0 }}>{importMsg}</div>}
        </div>

        <p className="section-title">Pending Submissions ({pending.length})</p>
        {loading && <p className="empty-state">Loading…</p>}
        {!loading && pending.length === 0 && (
          <p className="empty-state">Nothing waiting for review. 🎉</p>
        )}

        {pending.map((ev) => (
          <div className="card" key={ev.id}>
            <p className="title" style={{ margin: '0 0 4px', fontWeight: 700 }}>{ev.title}</p>
            <p className="meta">{ev.category} · 📅 {ev.date_confirmed ? formatDate(ev.date) : `posted ${formatDate(ev.date)}`}{ev.time ? ` · ${ev.time}` : ''}</p>
            {ev.location ? <p className="meta">📍 {ev.location}</p> : null}
            {ev.organiser ? <p className="meta">Submitted by {ev.organiser}</p> : null}
            {ev.description ? <p className="desc">{ev.description}</p> : null}
            <p className="meta" style={{ fontSize: 11, opacity: 0.7 }}>Source: {ev.source}</p>
            {!ev.date_confirmed && (
              <div className="form-group" style={{ marginTop: 10, marginBottom: 0 }}>
                <label htmlFor={`date-${ev.id}`}>Event date not found on the website. Set it before approving:</label>
                <input
                  id={`date-${ev.id}`}
                  type="date"
                  min={new Date().toLocaleDateString('en-CA')}
                  value={dates[ev.id] || ''}
                  onChange={(e) => setDates((d) => ({ ...d, [ev.id]: e.target.value }))}
                />
              </div>
            )}

            {rejectingId === ev.id ? (
              <div style={{ marginTop: 10 }}>
                <textarea
                  placeholder="Reason for rejection (optional)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid var(--border)', fontFamily: 'inherit' }}
                />
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => submitReject(ev.id)}>Confirm reject</button>
                  <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => { setRejectingId(null); setReason(''); }}>Cancel</button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => handleApprove(ev.id)} disabled={!ev.date_confirmed && !dates[ev.id]}>Approve</button>
                <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => setRejectingId(ev.id)}>Reject</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
