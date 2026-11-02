import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginSuccess } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api.login({ email, password });
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
      <Header title="Log In" back />
      <div className="content">
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button className="btn btn-primary" disabled={loading}>
            {loading ? 'Logging in…' : 'Log In'}
          </button>
        </form>
        <p style={{ fontSize: 13, marginTop: 14, textAlign: 'center', color: 'var(--text-muted)' }}>
          No account? <Link to="/register" style={{ color: 'var(--blue)', fontWeight: 600 }}>Register</Link>
        </p>
        <div className="card" style={{ marginTop: 20 }}>
          <p className="form-hint" style={{ margin: 0 }}>
            <strong>Demo accounts</strong> (password: Password123)<br />
            student@kabarak.ac.ke · organiser@kabarak.ac.ke · admin@kabarak.ac.ke
          </p>
        </div>
      </div>
    </>
  );
}
