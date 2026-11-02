import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSchools, audienceLabel } from '../useSchools';
import { api } from '../api/client';
import Header from '../components/Header';

const CATEGORY_COLOURS = {
  academic: 'var(--blue)', social: '#7c3aed', career: 'var(--green-dark)',
  religious: 'var(--amber)', sports: 'var(--red)',
};

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
}

export default function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const { user, token, loginSuccess } = useAuth();
  const navigate = useNavigate();
  const schools = useSchools();

  useEffect(() => {
    api.getEvent(id).then((d) => setEvent(d.event)).catch((e) => setError(e.message));
  }, [id]);

  return (
    <>
      <Header title="Event Detail" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        {!event && !error && <p className="empty-state">Loading…</p>}
        {event && (
          <>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ background: CATEGORY_COLOURS[event.category] || 'var(--blue)', color: 'white', padding: '10px 14px', fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>
                {event.category}
              </div>
              <div style={{ padding: 16 }}>
                <h2 style={{ margin: '0 0 10px', fontSize: 19 }}>{event.title}</h2>
                <p className="meta">📅 {formatDate(event.date)}{event.time ? ` · ${event.time}` : ''}</p>
                {event.location ? <p className="meta">📍 {event.location}</p> : null}
                {event.organiser ? <p className="meta">👤 Organised by {event.organiser}</p> : null}
                <p className="meta">🎓 Open to: {audienceLabel(schools, event.audience)}</p>
              </div>
            </div>

            {event.description ? (
              <div className="card">
                <p className="section-title" style={{ marginTop: 0 }}>Description</p>
                <p style={{ fontSize: 14, lineHeight: 1.5, margin: 0 }}>{event.description}</p>
              </div>
            ) : null}

            {(!user || user.role === 'student') && (() => {
              const subscribed = user?.interests?.includes(event.category);
              async function subscribe() {
                if (!user) { navigate('/login'); return; }
                try {
                  const next = [...(user.interests || []), event.category];
                  const { user: updated } = await api.updateInterests(next, token);
                  loginSuccess({ token, user: updated });
                } catch (e) {
                  setStatus(e.message);
                }
              }
              return (
                <>
                  <button className="btn btn-primary" onClick={subscribe} disabled={subscribed}>
                    {subscribed
                      ? `✓ You get alerts for new ${event.category} events`
                      : `🔔 Alert me about new ${event.category} events`}
                  </button>
                  {status && <p className="meta" style={{ marginTop: 8 }}>{status}</p>}
                </>
              );
            })()}
          </>
        )}
      </div>
    </>
  );
}
