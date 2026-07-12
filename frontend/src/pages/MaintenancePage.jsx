/**
 * src/pages/MaintenancePage.jsx
 * Route: /maintenance
 *
 * Maintenance request list with workflow status display.
 */

export default function MaintenancePage() {
  const STATUSES = ['Pending', 'Approved', 'Rejected', 'TechnicianAssigned', 'InProgress', 'Resolved'];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Maintenance</h1>
        <button id="btn-raise-maintenance" className="btn btn-primary">
          + Raise Request
        </button>
      </div>

      {/* ── Status filter chips ── */}
      <div className="chip-group">
        {STATUSES.map((s) => (
          <button
            key={s}
            id={`chip-maint-${s.toLowerCase()}`}
            className="chip"
          >
            {s}
          </button>
        ))}
      </div>

      {/* ── Request list ── */}
      <div className="empty-state" id="maintenance-list" style={{ marginTop: '1.5rem' }}>
        <p>🔧 No maintenance requests.</p>
        <p className="scaffold-note">
          TODO: fetch GET /api/maintenance (filtered by status chip selection)
          and render cards with Approve / Assign Technician / Update Status actions.
        </p>
      </div>
    </div>
  );
}
