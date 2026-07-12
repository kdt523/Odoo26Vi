/**
 * src/pages/AuditsPage.jsx
 * Route: /audits
 *
 * Audit cycle list + create cycle shell.
 */

export default function AuditsPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1>Audit Cycles</h1>
        <button id="btn-create-audit-cycle" className="btn btn-primary">
          + New Audit Cycle
        </button>
      </div>

      {/* ── Cycle list ── */}
      <div className="empty-state" id="audit-cycles-list">
        <p>📋 No audit cycles yet.</p>
        <p className="scaffold-note">
          TODO: fetch GET /api/audits and render a table with columns:
          Scope (dept/location), Start Date, End Date, Status, # Items, # Auditors.
          Link each row to cycle detail → assign auditors + mark items.
        </p>
      </div>
    </div>
  );
}
