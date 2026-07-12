import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';

const locales = {
  'en-US': enUS,
};
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

export default function BookingsPage() {
  const [assets, setAssets] = useState([]);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [myBookings, setMyBookings] = useState([]);
  
  // Modals state
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState({
    id: null,
    asset_id: '',
    start_time: '',
    end_time: '',
  });
  const [formError, setFormError] = useState('');
  
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Time range for calendar fetching
  const [currentDate, setCurrentDate] = useState(new Date());

  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;
  const isManager = user && ['Admin', 'AssetManager', 'DepartmentHead'].includes(user.role);

  useEffect(() => {
    fetchAssets();
    fetchMyBookings();
  }, []);

  useEffect(() => {
    fetchCalendarEvents(currentDate);
  }, [selectedAssetId, currentDate]);

  const authHeaders = { headers: { Authorization: `Bearer ${token}` } };

  const fetchAssets = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/assets', authHeaders);
      const bookable = res.data.filter(a => a.is_bookable !== false);
      setAssets(bookable);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMyBookings = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/bookings', authHeaders);
      setMyBookings(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCalendarEvents = async (date) => {
    // Fetch +/- 1 month around the current date
    const from = new Date(date.getFullYear(), date.getMonth() - 1, 1).toISOString();
    const to = new Date(date.getFullYear(), date.getMonth() + 2, 0).toISOString();
    
    let url = `http://localhost:8000/api/v1/bookings/calendar?from_date=${from}&to_date=${to}`;
    if (selectedAssetId) url += `&asset_id=${selectedAssetId}`;

    try {
      const res = await axios.get(url, authHeaders);
      const events = res.data.map(b => ({
        ...b,
        title: `Booking (${b.status})`,
        start: new Date(b.start_time),
        end: new Date(b.end_time),
      }));
      setCalendarEvents(events);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectSlot = ({ start, end }) => {
    setFormError('');
    setFormData({
      id: null,
      asset_id: selectedAssetId || (assets.length > 0 ? assets[0].id : ''),
      start_time: format(start, "yyyy-MM-dd'T'HH:mm"),
      end_time: format(end, "yyyy-MM-dd'T'HH:mm"),
    });
    setIsFormOpen(true);
  };

  const handleSelectEvent = (event) => {
    setSelectedEvent(event);
    setIsDetailsOpen(true);
  };

  const closeForm = () => setIsFormOpen(false);
  const closeDetails = () => setIsDetailsOpen(false);

  const getEventPropGetter = (event) => {
    let backgroundColor = '#6366f1'; // Upcoming - Blue
    if (event.status === 'Ongoing') backgroundColor = '#34d399'; // Green
    if (event.status === 'Completed') backgroundColor = '#64748b'; // Gray
    if (event.status === 'Cancelled') backgroundColor = '#f87171'; // Red
    
    return { style: { backgroundColor, color: 'white' } };
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    const payload = {
      asset_id: formData.asset_id,
      start_time: new Date(formData.start_time).toISOString(),
      end_time: new Date(formData.end_time).toISOString(),
    };

    try {
      if (formData.id) {
        await axios.put(`http://localhost:8000/api/v1/bookings/${formData.id}/reschedule`, payload, authHeaders);
      } else {
        await axios.post('http://localhost:8000/api/v1/bookings', payload, authHeaders);
      }
      closeForm();
      fetchCalendarEvents(currentDate);
      fetchMyBookings();
    } catch (err) {
      if (err.response && err.response.status === 409 && err.response.data.detail?.error === 'BookingOverlap') {
        const detail = err.response.data.detail;
        const sTime = new Date(detail.conflicting_start).toLocaleString();
        const eTime = new Date(detail.conflicting_end).toLocaleString();
        setFormError(`Overlap rejected: Conflicting booking exists from ${sTime} to ${eTime}`);
      } else {
        setFormError(err.response?.data?.detail || 'An error occurred.');
      }
    }
  };

  const handleCancelBooking = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;
    try {
      await axios.post(`http://localhost:8000/api/v1/bookings/${id}/cancel`, {}, authHeaders);
      closeDetails();
      fetchCalendarEvents(currentDate);
      fetchMyBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel');
    }
  };

  const handleOpenReschedule = (booking) => {
    closeDetails();
    setFormError('');
    setFormData({
      id: booking.id,
      asset_id: booking.asset_id,
      start_time: format(new Date(booking.start_time || booking.start), "yyyy-MM-dd'T'HH:mm"),
      end_time: format(new Date(booking.end_time || booking.end), "yyyy-MM-dd'T'HH:mm"),
    });
    setIsFormOpen(true);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Bookings</h1>
        <button className="btn btn-primary" onClick={() => handleSelectSlot({ start: new Date(), end: new Date(Date.now() + 3600000) })}>
          + New Booking
        </button>
      </div>

      <div className="filter-bar">
        <select 
          className="filter-select" 
          value={selectedAssetId} 
          onChange={e => setSelectedAssetId(e.target.value)}
        >
          <option value="">All Bookable Assets</option>
          {assets.map(a => (
            <option key={a.id} value={a.id}>{a.name} ({a.asset_tag})</option>
          ))}
        </select>
      </div>

      <div className="calendar-shell" style={{ height: '600px', background: 'var(--color-bg)', border: 'none' }}>
        <Calendar
          localizer={localizer}
          events={calendarEvents}
          startAccessor="start"
          endAccessor="end"
          style={{ height: '100%', width: '100%' }}
          selectable
          onSelectSlot={handleSelectSlot}
          onSelectEvent={handleSelectEvent}
          onNavigate={(date) => setCurrentDate(date)}
          eventPropGetter={getEventPropGetter}
          views={['month', 'week', 'day', 'agenda']}
          defaultView="week"
        />
      </div>

      {/* ── Upcoming bookings list ── */}
      <div style={{ marginTop: '2rem' }}>
        <h2>My Bookings</h2>
        {myBookings.length === 0 ? (
          <div className="empty-state">
            <p>No bookings found.</p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Asset ID</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {myBookings.map(b => (
                <tr key={b.id}>
                  <td>
                    {new Date(b.start_time).toLocaleString()} - {new Date(b.end_time).toLocaleTimeString()}
                  </td>
                  <td>{b.asset_id}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: b.status === 'Upcoming' ? '#6366f1' : (b.status === 'Cancelled' ? '#f87171' : '#64748b'), color: 'white' }}>
                      {b.status}
                    </span>
                  </td>
                  <td>
                    {b.status === 'Upcoming' && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => handleOpenReschedule(b)}>Reschedule</button>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: '#f87171', color: '#f87171' }} onClick={() => handleCancelBooking(b.id)}>Cancel</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Form Modal ── */}
      {isFormOpen && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ marginBottom: '1rem' }}>{formData.id ? 'Reschedule Booking' : 'New Booking'}</h2>
            <form className="auth-form" onSubmit={handleFormSubmit}>
              <div className="form-group">
                <label>Asset</label>
                <select 
                  className="filter-select"
                  value={formData.asset_id}
                  onChange={e => setFormData({ ...formData, asset_id: e.target.value })}
                  required
                  disabled={!!formData.id}
                >
                  <option value="">Select an asset...</option>
                  {assets.map(a => (
                    <option key={a.id} value={a.id}>{a.name} ({a.asset_tag})</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Start Time</label>
                <input 
                  type="datetime-local" 
                  value={formData.start_time}
                  onChange={e => setFormData({ ...formData, start_time: e.target.value })}
                  required 
                />
              </div>
              <div className="form-group">
                <label>End Time</label>
                <input 
                  type="datetime-local" 
                  value={formData.end_time}
                  onChange={e => setFormData({ ...formData, end_time: e.target.value })}
                  required 
                />
              </div>
              
              {formError && <div className="form-error">{formError}</div>}
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Save Booking</button>
                <button type="button" className="btn btn-secondary" onClick={closeForm}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Details Modal ── */}
      {isDetailsOpen && selectedEvent && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <h2 style={{ marginBottom: '1rem' }}>Booking Details</h2>
            <div style={{ margin: '1rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <p><strong>Asset:</strong> {assets.find(a => a.id === selectedEvent.asset_id)?.name || selectedEvent.asset_id}</p>
              <p><strong>Status:</strong> {selectedEvent.status}</p>
              <p><strong>Start:</strong> {selectedEvent.start.toLocaleString()}</p>
              <p><strong>End:</strong> {selectedEvent.end.toLocaleString()}</p>
            </div>
            
            <div style={{ display: 'flex', gap: '1rem' }}>
              {selectedEvent.status === 'Upcoming' && (user?.id === selectedEvent.employee_id || isManager) && (
                <>
                  <button className="btn btn-primary" onClick={() => handleOpenReschedule(selectedEvent)}>Reschedule</button>
                  <button className="btn btn-secondary" style={{ borderColor: '#f87171', color: '#f87171' }} onClick={() => handleCancelBooking(selectedEvent.id)}>Cancel</button>
                </>
              )}
              <button className="btn btn-secondary" onClick={closeDetails}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const modalOverlayStyle = {
  position: 'fixed',
  top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(0,0,0,0.6)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalContentStyle = {
  backgroundColor: 'var(--color-surface)',
  border: '1px solid var(--color-border)',
  borderRadius: '8px',
  padding: '2rem',
  width: '100%',
  maxWidth: '500px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
};
