/**
 * src/components/Layout.jsx — Shared app shell with role-aware navigation.
 *
 * Navigation links are filtered based on the current user's role.
 * Active link is highlighted via NavLink.
 */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

const NAV_ITEMS = [
  { path: '/dashboard',    label: '📊 Dashboard',    roles: [] },          // all roles
  { path: '/assets',       label: '🗂️ Assets',        roles: ['Admin', 'AssetManager', 'DepartmentHead'] },
  { path: '/my-assets',    label: '🗂️ My Assets',     roles: ['Employee'] },
  { path: '/allocations',  label: '🔗 Allocations',   roles: ['Admin', 'AssetManager', 'DepartmentHead'] },
  { path: '/bookings',     label: '📅 Bookings',      roles: [] },
  { path: '/maintenance',  label: '🔧 Maintenance',   roles: [] },
  { path: '/audits',       label: '📋 Audits',        roles: ['Admin', 'AssetManager'] },
  { path: '/reports',      label: '📈 Reports',       roles: ['Admin', 'AssetManager'] },
  { path: '/org-setup',    label: '🏢 Org Setup',     roles: ['Admin'] },
  { path: '/notifications',label: '🔔 Notifications', roles: [] },
];

export default function Layout() {
  const { currentUser, role, logout } = useAuth();
  const { unreadCount } = useNotification();
  const navigate = useNavigate();

  const visibleNav = NAV_ITEMS.filter(
    (item) => item.roles.length === 0 || item.roles.includes(role)
  );

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">AssetFlow</span>
        </div>

        <nav className="sidebar-nav">
          {visibleNav.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link--active' : ''}`
              }
            >
              <span className="nav-label">
                {item.path === '/assets' && role === 'Employee' ? '🗂️ My Assets' : item.label}
              </span>
              {item.path === '/notifications' && unreadCount > 0 && (
                <span className="badge badge--unread">{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <span className="user-name">{currentUser?.name ?? currentUser?.id ?? 'User'}</span>
            <span className="user-role">{role}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
