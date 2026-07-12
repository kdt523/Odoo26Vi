/**
 * src/pages/DashboardPage.jsx
 * Route: /dashboard
 *
 * KPI cards + overdue returns section.
 * All data is placeholder — wire to core-api + reports-api in a later pass.
 */
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

// Placeholder data matching the mockup
const KPI_CARDS = [
  { id: 'kpi-assets-available',   label: 'Available',          value: '128' },
  { id: 'kpi-assets-allocated',   label: 'Allocated',          value: '76' },
  { id: 'kpi-maintenance-today',  label: 'Maintenance',        value: '4' },
  { id: 'kpi-active-bookings',    label: 'Active Bookings',    value: '9' },
  { id: 'kpi-pending-transfers',  label: 'Pending Transfers',  value: '3' },
  { id: 'kpi-upcoming-returns',   label: 'Upcoming returns',   value: '12' },
];

const RECENT_ACTIVITY = [
  { id: 1, icon: '🔄', title: 'Laptop AF-0114', desc: 'allocated to Priya shah - IT dept' },
  { id: 2, icon: '📅', title: 'Room B2', desc: 'booking confirmed - 2:00 to 3:00 PM' },
  { id: 3, icon: '🔧', title: 'Projector AF-0062', desc: 'maintenance resolved' },
];

export default function DashboardPage() {
  const { currentUser, role } = useAuth();
  
  const defaultScope = role === 'DepartmentHead' ? 'department' : 'all';
  const [scope, setScope] = useState(defaultScope);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">
          Welcome back{currentUser?.name ? `, ${currentUser.name}` : ''}
          {role ? ` · ${role}` : ''}
        </p>
      </div>

      {/* ── Scope Toggle for Department Head ── */}
      {role === 'DepartmentHead' && (
        <div className="tabs" style={{ marginBottom: '1.5rem' }}>
          <button 
            className={`tab ${scope === 'department' ? 'tab--active' : ''}`}
            onClick={() => setScope('department')}
          >
            Department
          </button>
          <button 
            className={`tab ${scope === 'all' ? 'tab--active' : ''}`}
            onClick={() => setScope('all')}
          >
            Org-wide
          </button>
        </div>
      )}

      {/* ── KPI Cards ── */}
      <section aria-label="Key performance indicators">
        <h2 className="dashboard-section-title">Today's Overview</h2>
        <div className="kpi-grid">
          {KPI_CARDS.map((card) => (
            <div key={card.id} id={card.id} className="kpi-card">
              <div className="kpi-label">{card.label}</div>
              <div className="kpi-value">{card.value}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Overdue Returns ── */}
      <section aria-label="Overdue returns" style={{ marginTop: '1.5rem' }}>
        <div className="overdue-banner">
          <div className="overdue-banner-icon">⚠️</div>
          <div>3 assets overdue for return - flagged for follow-up</div>
        </div>
      </section>

      {/* ── Quick Actions ── */}
      <section aria-label="Quick actions">
        <div className="quick-actions-bar">
          <Link to="/assets" className="btn-quick-action primary">
            + register asset
          </Link>
          <Link to="/bookings" className="btn-quick-action">
            Book resource
          </Link>
          <Link to="/maintenance" className="btn-quick-action">
            Raise requests
          </Link>
        </div>
      </section>

      {/* ── Recent Activity ── */}
      <section aria-label="Recent activity">
        <h2 className="dashboard-section-title">Recent Activity</h2>
        <div className="recent-activity-list">
          {RECENT_ACTIVITY.map(act => (
            <div key={act.id} className="activity-item">
              <div className="activity-icon">{act.icon}</div>
              <div className="activity-content">
                <div className="activity-title">{act.title}</div>
                <div className="activity-meta">{act.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <p className="scaffold-note" style={{ marginTop: '2rem' }}>
        🚧 Scaffold pass — KPI values and overdue data are placeholders.
      </p>
    </div>
  );
}
