import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Header from '../components/Header';
import { useSchools } from '../useSchools';

export default function Profile() {
  const { user, token, logout, loginSuccess } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [selected, setSelected] = useState(user?.interests || []);
  const [status, setStatus] = useState('');
  const [school, setSchool] = useState(user?.school || '');
  const schools = useSchools();

  useEffect(() => {
    api.listCategories().then((d) => setCategories(d.categories)).catch(() => {});
  }, []);

  if (!user) return null;

  function toggle(name) {
    setStatus('');
    setSelected((cur) => (cur.includes(name) ? cur.filter((n) => n !== name) : [...cur, name]));
  }

  async function save() {
    try {
      await api.updateSchool(school, token);
      const { user: updated } = await api.updateInterests(selected, token);
      loginSuccess({ token, user: updated });
      setStatus('Preferences saved.');
    } catch (e) {
      setStatus(e.message);
    }
  }

  return (
    <>
      <Header title="Profile" back />
      <div className="content">
        <div className="card">
          <p style={{ margin: '0 0 4px', fontWeight: 700, fontSize: 16 }}>{user.full_name}</p>
          <p className="meta">{user.email}</p>
          <p className="meta" style={{ textTransform: 'capitalize' }}>Role: {user.role}</p>
          {user.organisation ? <p className="meta">Organisation: {user.organisation}</p> : null}
        </div>

        {user.role === 'student' && (
          <div className="card">
            <div className="form-group">
              <label>My school</label>
              <select value={school} onChange={(e) => { setSchool(e.target.value); setStatus(''); }}>
                <option value="">Not set</option>
                {schools.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
              </select>
            </div>
            <p style={{ margin: '0 0 4px', fontWeight: 700 }}>Alert me about</p>
            <p className="meta" style={{ marginBottom: 10 }}>
              You are only notified when a newly published event is in one of these categories and is open to you.
            </p>
            <div className="chip-row" style={{ flexWrap: 'wrap' }}>
              {categories.map((c) => (
                <button
                  key={c.id}
                  className={`chip${selected.includes(c.name) ? ' active' : ''}`}
                  onClick={() => toggle(c.name)}
                >
                  {c.name[0].toUpperCase() + c.name.slice(1)}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={save}>Save preferences</button>
            {status && <p className="meta" style={{ marginTop: 8 }}>{status}</p>}
          </div>
        )}

        <button
          className="btn btn-danger btn-block"
          onClick={() => { logout(); navigate('/'); }}
        >
          Log out
        </button>
      </div>
    </>
  );
}
