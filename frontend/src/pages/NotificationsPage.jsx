/**
 * src/pages/NotificationsPage.jsx
 * Route: /notifications
 *
 * Activity feed / notification list shell — reads from reports-api.
 */

export default function NotificationsPage() {
  const NOTIFICATION_TYPES = [
    'AssetAssigned',
    'MaintenanceApproved',
    'MaintenanceRejected',
    'BookingCreated',
    'BookingCancelled',
    'TransferApproved',
    'OverdueReturnAlert',
    'AuditDiscrepancyFlagged',
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Notifications</h1>
        <button id="btn-mark-all-read" className="btn btn-secondary">
          Mark all as read
        </button>
      </div>

      {/* ── Type filter ── */}
      <div className="chip-group">
        <button id="chip-notif-all" className="chip chip--active">All</button>
        {NOTIFICATION_TYPES.map((t) => (
          <button key={t} id={`chip-notif-${t.toLowerCase()}`} className="chip">
            {t}
          </button>
        ))}
      </div>

      {/* ── Feed ── */}
      <div className="empty-state" id="notifications-feed" style={{ marginTop: '1.5rem' }}>
        <p>🔔 No notifications.</p>
        <p className="scaffold-note">
          TODO: fetch GET /api/notifications (reports-api) and render a feed.
          Unread items should be visually highlighted.
          POST /api/notifications/mark-read on click.
        </p>
      </div>
    </div>
  );
}
