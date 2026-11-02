import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import { useSchools } from '../useSchools';

export default function SubmitEvent() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    title: '', description: '', date: '', time: '', location: '', category_id: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const schools = useSchools();
  const [audienceMode, setAudienceMode] = useState('all');
  const [audience, setAudience] = useState([]);

  function toggleSchool(code) {
    setAudience((cur) => (cur.includes(code) ? cur.filter((c) => c !== code) : [...cur, code]));
  }

  useEffect(() => {
    api.listCategories().then((d) => {
      setCategories(d.categories);
      if (d.categories.length) {
        setForm((f) => ({ ...f, category_id: d.categories[0].id }));
      }
    }).catch(() => {});
  }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (audienceMode === 'some' && audience.length === 0) {
      setError('Choose at least one school, or select "All students".');
      return;
    }
    setLoading(true);
    try {
      await api.submitEvent({
        ...form,
        category_id: Number(form.category_id),
        audience: audienceMode === 'all' ? 'all' : audience,
      }, token);
      setSuccess(true);
      setForm({ title: '', description: '', date: '', time: '', location: '', category_id: categories[0]?.id || '' });
      setTimeout(() => navigate('/mine'), 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header title="Submit an Event" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="success-banner">Submitted! Redirecting to your submissions…</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Event Title *</label>
            <input required value={form.title} onChange={(e) => update('title', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Category *</label>
            <select required value={form.category_id} onChange={(e) => update('category_id', e.target.value)}>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name[0].toUpperCase() + c.name.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Who is this event for? *</label>
            <div className="radio-row">
              <label><input type="radio" checked={audienceMode === 'all'} onChange={() => setAudienceMode('all')} /> All students</label>
              <label><input type="radio" checked={audienceMode === 'some'} onChange={() => setAudienceMode('some')} /> Specific schools</label>
            </div>
            {audienceMode === 'some' && (
              <div className="check-list">
                {schools.map((s) => (
                  <label key={s.code}>
                    <input type="checkbox" checked={audience.includes(s.code)} onChange={() => toggleSchool(s.code)} />
                    {s.name.replace(/^School of /, '')}
                  </label>
                ))}
              </div>
            )}
            <div className="form-hint">Events for specific schools still appear under "All events".</div>
          </div>
          <div className="form-group">
            <label>Date *</label>
            <input type="date" required min={new Date().toLocaleDateString('en-CA')} value={form.date} onChange={(e) => update('date', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Time</label>
            <input type="time" value={form.time} onChange={(e) => update('time', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Location</label>
            <input value={form.location} onChange={(e) => update('location', e.target.value)} placeholder="e.g. CS Lab 3, Block B" />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={form.description} onChange={(e) => update('description', e.target.value)}
              placeholder="What should attendees know?" />
          </div>
          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Submitting…' : 'Submit for Review'}
          </button>
          <p className="form-hint" style={{ textAlign: 'center', marginTop: 10 }}>
            * Required fields. Your event will be reviewed by an administrator before it appears publicly.
          </p>
        </form>
      </div>
    </>
  );
}
