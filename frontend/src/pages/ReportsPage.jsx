/**
 * src/pages/ReportsPage.jsx
 * Route: /reports
 *
 * Placeholder charts area — connects to reports-api.
 */

export default function ReportsPage() {
  const REPORT_CARDS = [
    {
      id: 'report-asset-utilization',
      title: 'Asset Utilization',
      description: 'Utilization trends over time by category / department.',
      endpoint: 'GET /api/reports/asset-utilization',
    },
    {
      id: 'report-maintenance-frequency',
      title: 'Maintenance Frequency',
      description: 'How often assets require maintenance, average resolution time.',
      endpoint: 'GET /api/reports/maintenance-frequency',
    },
    {
      id: 'report-allocation-summary',
      title: 'Allocation Summary',
      description: 'Department-wise breakdown of allocated vs available assets.',
      endpoint: 'GET /api/reports/allocation-summary',
    },
    {
      id: 'report-booking-heatmap',
      title: 'Booking Heatmap',
      description: 'Booking density by hour-of-day and day-of-week.',
      endpoint: 'GET /api/reports/booking-heatmap',
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Reports & Analytics</h1>
        <button id="btn-export-report" className="btn btn-secondary">
          ⬇ Export
        </button>
      </div>

      <div className="report-grid">
        {REPORT_CARDS.map((card) => (
          <div key={card.id} id={card.id} className="report-card">
            <h3>{card.title}</h3>
            <p>{card.description}</p>
            <div className="chart-placeholder">
              📊 Chart placeholder
            </div>
            <p className="scaffold-note">
              TODO: call <code>{card.endpoint}</code> and render chart (e.g. Recharts).
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
