import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Header({ title, subtitle, back }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div>
        {back ? (
          <button className="icon-btn" onClick={() => navigate(-1)} style={{ marginBottom: 6 }}>
            ← Back
          </button>
        ) : null}
        <h1>{title}</h1>
        {subtitle ? <div className="subtitle">{subtitle}</div> : null}
      </div>
      {!back && (
        user ? (
          <button className="icon-btn" onClick={() => { logout(); navigate('/'); }}>
            {user.full_name.split(' ')[0]} · Log out
          </button>
        ) : (
          <button className="icon-btn" onClick={() => navigate('/login')}>Log in</button>
        )
      )}
    </header>
  );
}
