/**
 * src/pages/DashboardPage.jsx
 * Route: /dashboard
 *
 * KPI cards + overdue returns section.
 * All data is placeholder — wire to core-api + reports-api in a later pass.
 */

import { useAuth } from '../context/AuthContext';

const KPI_CARDS = [
  { id: 'kpi-assets-available',   label: 'Assets Available',   value: '—', icon: '✅' },
  { id: 'kpi-assets-allocated',   label: 'Assets Allocated',   value: '—', icon: '🔗' },
  { id: 'kpi-maintenance-today',  label: 'Maintenance Today',  value: '—', icon: '🔧' },
  { id: 'kpi-active-bookings',    label: 'Active Bookings',    value: '—', icon: '📅' },
  { id: 'kpi-pending-transfers',  label: 'Pending Transfers',  value: '—', icon: '🔄' },
  { id: 'kpi-upcoming-returns',   label: 'Upcoming Returns',   value: '—', icon: '📦' },
];

export default function DashboardPage() {
  const { currentUser, role } = useAuth();

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">
          Welcome back{currentUser?.name ? `, ${currentUser.name}` : ''}
          {role ? ` · ${role}` : ''}
        </p>
      </div>

      {/* ── KPI Cards ── */}
      <section aria-label="Key performance indicators">
        <div className="kpi-grid">
          {KPI_CARDS.map((card) => (
            <div key={card.id} id={card.id} className="kpi-card">
              <div className="kpi-icon">{card.icon}</div>
              <div className="kpi-body">
                <div className="kpi-value">{card.value}</div>
                <div className="kpi-label">{card.label}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Overdue Returns ── */}
      <section aria-label="Overdue returns" style={{ marginTop: '2rem' }}>
        <h2>Overdue Returns</h2>
        <div className="empty-state" id="overdue-returns-table">
          <p>⚠️ No data yet — connect to <code>GET /api/allocations?status=Overdue</code></p>
          {/* TODO: fetch allocations where expected_return_date < today AND actual_return_date IS NULL */}
        </div>
      </section>

      <p className="scaffold-note">
        🚧 Scaffold pass — KPI values and overdue data are placeholders.
      </p>
    </div>
  );
}
