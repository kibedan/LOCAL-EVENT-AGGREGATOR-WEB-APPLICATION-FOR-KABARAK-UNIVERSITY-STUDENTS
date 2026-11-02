import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import { useSchools } from '../useSchools';

export default function Register() {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'student', organisation: '', school: '' });
  const schools = useSchools();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginSuccess } = useAuth();
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.register(form);
      loginSuccess(data);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Header title="Create Account" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full name</label>
            <input required value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" required value={form.email} onChange={(e) => update('email', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" required minLength={8} value={form.password} onChange={(e) => update('password', e.target.value)} />
            <div className="form-hint">At least 8 characters.</div>
          </div>
          <div className="form-group">
            <label>I am a…</label>
            <select value={form.role} onChange={(e) => update('role', e.target.value)}>
              <option value="student">Student</option>
              <option value="organiser">Event Organiser</option>
            </select>
          </div>
          {form.role === 'student' && (
            <div className="form-group">
              <label>School</label>
              <select required value={form.school} onChange={(e) => update('school', e.target.value)}>
                <option value="">Select your school…</option>
                {schools.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
              </select>
            </div>
          )}
          {form.role === 'organiser' && (
            <div className="form-group">
              <label>Organisation</label>
              <input value={form.organisation} onChange={(e) => update('organisation', e.target.value)}
                placeholder="e.g. CS Student Association" />
            </div>
          )}
          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating account…' : 'Create Account'}
          </button>
        </form>
        <p style={{ fontSize: 13, marginTop: 14, textAlign: 'center', color: 'var(--text-muted)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--blue)', fontWeight: 600 }}>Log in</Link>
        </p>
      </div>
    </>
  );
}
