/**
 * src/components/RouteGuard.jsx — Role-based route guard.
 *
 * Usage:
 *   <RouteGuard>                         — any authenticated user
 *   <RouteGuard roles={["Admin"]}>       — Admin only
 *   <RouteGuard roles={["Admin","AssetManager"]}>
 *
 * Redirects:
 *   - Not authenticated → /login
 *   - Wrong role → /dashboard (with an alert TODO)
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RouteGuard({ children, roles = [] }) {
  const { isAuthenticated, role, loading } = useAuth();
  const location = useLocation();

  // Wait for auth state to restore from localStorage
  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Checking authentication…
      </div>
    );
  }

  // Not logged in → redirect to login, preserve intended path
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role check — empty roles array means "any authenticated user"
  if (roles.length > 0 && !roles.includes(role)) {
    // TODO: show a toast/alert "Insufficient permissions"
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
