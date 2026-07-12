import { useState, useEffect, useCallback } from 'react';
import { coreApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

export default function NotificationsPage() {
  const { role } = useAuth();
  const { decrementUnreadCount, fetchUnreadCount, resetUnreadCount } = useNotification();
  const [activeTab, setActiveTab] = useState('notifications');

  const isAdminOrManager = role === 'Admin' || role === 'AssetManager';

  // ── Notifications State ──
  const [notifications, setNotifications] = useState([]);
  const [loadingNotifs, setLoadingNotifs] = useState(false);
  const [notifTypeFilter, setNotifTypeFilter] = useState('All');

  // ── Activity Log State ──
  const [activityLogs, setActivityLogs] = useState([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [loadingLogs, setLoadingLogs] = useState(false);
  
  // Activity Log Filters
  const [logUserId, setLogUserId] = useState('');
  const [logFromDate, setLogFromDate] = useState('');
  const [logToDate, setLogToDate] = useState('');
  const [logEntityType, setLogEntityType] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({
    userId: '',
    fromDate: '',
    toDate: '',
    entityType: ''
  });
  const [page, setPage] = useState(1);
  const pageSize = 50;

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

  // ── Fetching Notifications ──
  const loadNotifications = useCallback(async () => {
    setLoadingNotifs(true);
    try {
      const { data } = await coreApi.get('/notifications');
      setNotifications(data.items || []);
    } catch (err) {
      console.error('Failed to load notifications', err);
    } finally {
      setLoadingNotifs(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'notifications') {
      loadNotifications();
      fetchUnreadCount();
    }
  }, [activeTab, loadNotifications, fetchUnreadCount]);

  const handleMarkAsRead = async (notifId, isRead) => {
    if (isRead) return;
    try {
      await coreApi.post(`/notifications/${notifId}/read`);
      setNotifications(prev =>
        prev.map(n => n.id === notifId ? { ...n, is_read: true } : n)
      );
      decrementUnreadCount();
    } catch (err) {
      console.error('Failed to mark as read', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await coreApi.post('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      resetUnreadCount();
    } catch (err) {
      console.error('Failed to mark all as read', err);
    }
  };

  // ── Fetching Activity Log ──
  const loadActivityLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      const params = { page, page_size: pageSize };
      if (appliedFilters.userId) params.user_id = appliedFilters.userId;
      if (appliedFilters.fromDate) params.from_date = new Date(appliedFilters.fromDate).toISOString();
      if (appliedFilters.toDate) params.to_date = new Date(appliedFilters.toDate).toISOString();
      if (appliedFilters.entityType) params.entity_type = appliedFilters.entityType;

      const { data } = await coreApi.get('/activity-log', { params });
      setActivityLogs(data.items || []);
      setTotalLogs(data.total || 0);
    } catch (err) {
      console.error('Failed to load activity logs', err);
    } finally {
      setLoadingLogs(false);
    }
  }, [page, appliedFilters]);

  useEffect(() => {
    if (activeTab === 'activity_log' && isAdminOrManager) {
      loadActivityLogs();
    }
  }, [activeTab, loadActivityLogs, isAdminOrManager]);

  // ── Renders ──

  const filteredNotifications = notifications.filter(
    n => notifTypeFilter === 'All' || n.type === notifTypeFilter
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Notifications & Activity</h1>
        {activeTab === 'notifications' && (
          <button id="btn-mark-all-read" className="btn btn-secondary" onClick={handleMarkAllRead}>
            Mark all as read
          </button>
        )}
      </div>

      {isAdminOrManager && (
        <div className="tabs" style={{ marginBottom: '1.5rem' }}>
          <button
            className={`tab ${activeTab === 'notifications' ? 'tab--active' : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            Notifications
          </button>
          <button
            className={`tab ${activeTab === 'activity_log' ? 'tab--active' : ''}`}
            onClick={() => setActiveTab('activity_log')}
          >
            Activity Log
          </button>
        </div>
      )}

      {/* ── Notifications Tab ── */}
      {activeTab === 'notifications' && (
        <>
          <div className="chip-group">
            <button
              id="chip-notif-all"
              className={`chip ${notifTypeFilter === 'All' ? 'chip--active' : ''}`}
              onClick={() => setNotifTypeFilter('All')}
            >
              All
            </button>
            {NOTIFICATION_TYPES.map((t) => (
              <button
                key={t}
                id={`chip-notif-${t.toLowerCase()}`}
                className={`chip ${notifTypeFilter === t ? 'chip--active' : ''}`}
                onClick={() => setNotifTypeFilter(t)}
              >
                {t}
              </button>
            ))}
          </div>

          <div id="notifications-feed" style={{ marginTop: '1.5rem' }}>
            {loadingNotifs ? (
              <p>Loading...</p>
            ) : filteredNotifications.length === 0 ? (
              <div className="empty-state">
                <p>🔔 No notifications.</p>
              </div>
            ) : (
              <ul className="notification-list">
                {filteredNotifications.map(n => (
                  <li
                    key={n.id}
                    className={`notification-item ${!n.is_read ? 'notification-item--unread' : ''}`}
                    onClick={() => handleMarkAsRead(n.id, n.is_read)}
                  >
                    <div className="notification-content">
                      <strong>{n.type}</strong>
                      <p>{n.message}</p>
                      <span className="notification-time">{new Date(n.created_at).toLocaleString()}</span>
                    </div>
                    {!n.is_read && <span className="unread-dot"></span>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}

      {/* ── Activity Log Tab ── */}
      {activeTab === 'activity_log' && isAdminOrManager && (
        <div id="activity-log-view">
          <div className="filters-card" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <div className="form-group">
              <label>User ID</label>
              <input
                type="text"
                placeholder="UUID"
                value={logUserId}
                onChange={e => setLogUserId(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>From Date</label>
              <input
                type="date"
                value={logFromDate}
                onChange={e => setLogFromDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>To Date</label>
              <input
                type="date"
                value={logToDate}
                onChange={e => setLogToDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Entity Type</label>
              <input
                type="text"
                placeholder="e.g. Allocation"
                value={logEntityType}
                onChange={e => setLogEntityType(e.target.value)}
              />
            </div>
            <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => {
                setAppliedFilters({
                  userId: logUserId,
                  fromDate: logFromDate,
                  toDate: logToDate,
                  entityType: logEntityType
                });
                setPage(1);
              }}>Apply Filters</button>
            </div>
          </div>

          <div className="card">
            {loadingLogs ? (
              <p>Loading activity log...</p>
            ) : (
              <>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>User</th>
                      <th>Action</th>
                      <th>Entity Type</th>
                      <th>Entity ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activityLogs.length === 0 ? (
                      <tr><td colSpan="5" className="text-center">No activity found.</td></tr>
                    ) : (
                      activityLogs.map(log => (
                        <tr key={log.id}>
                          <td>{new Date(log.timestamp).toLocaleString()}</td>
                          <td>{log.user_id || 'System'}</td>
                          <td>{log.action}</td>
                          <td>{log.entity_type}</td>
                          <td>{log.entity_id}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
                <div className="pagination" style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, totalLogs)} of {totalLogs} entries</span>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      className="btn btn-secondary"
                      disabled={page === 1}
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                    >
                      Previous
                    </button>
                    <button
                      className="btn btn-secondary"
                      disabled={page * pageSize >= totalLogs}
                      onClick={() => setPage(p => p + 1)}
                    >
                      Next
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
