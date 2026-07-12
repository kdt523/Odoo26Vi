/**
 * src/pages/BookingsPage.jsx
 * Route: /bookings
 *
 * Calendar-view shell + booking list.
 */

export default function BookingsPage() {
  return (
    <div className="page">
      <div className="page-header">
        <h1>Bookings</h1>
        <button id="btn-create-booking" className="btn btn-primary">
          + New Booking
        </button>
      </div>

      {/* ── Calendar placeholder ── */}
      <div className="calendar-shell" id="booking-calendar">
        <p>📅 Calendar view coming soon.</p>
        <p className="scaffold-note">
          TODO: fetch GET /api/bookings/calendar?from_date=&amp;to_date= and render
          a weekly/monthly calendar grid.
          Integrate a calendar library (e.g. react-big-calendar or FullCalendar).
        </p>
      </div>

      {/* ── Upcoming bookings list ── */}
      <div style={{ marginTop: '2rem' }}>
        <h2>My Bookings</h2>
        <div className="empty-state" id="bookings-list">
          <p>No bookings found.</p>
          <p className="scaffold-note">
            TODO: fetch GET /api/bookings and render list with Cancel / Reschedule actions.
          </p>
        </div>
      </div>
    </div>
  );
}
