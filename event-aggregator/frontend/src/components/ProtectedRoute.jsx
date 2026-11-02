import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, roles }) {
  const { user, token, ready } = useAuth();

  if (!ready) return null;
  if (!token || !user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) {
    return (
      <div className="content">
        <div className="error-banner">You don't have access to this page.</div>
      </div>
    );
  }
  return children;
}
