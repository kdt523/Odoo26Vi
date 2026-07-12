/**
 * src/pages/MaintenancePage.jsx
 * Route: /maintenance
 *
 * Maintenance request list with workflow status display.
 */

import { useState, useEffect } from 'react';

// Mock current user role for testing purposes until Auth is built.
// Change this to 'Employee' to test read-only views.
const currentUserRole = 'AssetManager';

export default function MaintenancePage() {
  const STATUSES = ['Pending', 'Approved', 'Rejected', 'TechnicianAssigned', 'InProgress', 'Resolved'];
  
  const [activeFilter, setActiveFilter] = useState('');
  const [requests, setRequests] = useState([]);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newRequest, setNewRequest] = useState({ asset_id: '', issue_description: '', priority: 'Medium' });

  // Simulate fetching data
  useEffect(() => {
    // In a real app, this would be: fetch(`/api/v1/maintenance?status=${activeFilter}`)
    setRequests([
      { id: '111-222', asset_id: 'asset-1', issue_description: 'AC blowing hot air', priority: 'High', status: 'Pending' },
      { id: '333-444', asset_id: 'asset-2', issue_description: 'Projector bulb burnt', priority: 'Medium', status: 'Approved' },
      { id: '555-666', asset_id: 'asset-3', issue_description: 'Squeaky chair', priority: 'Low', status: 'InProgress', technician: 'Bob Fixit' }
    ]);
  }, [activeFilter]);

  const handleAction = async (id, actionStr, payload = {}) => {
    // Stub for calling backend APIs like /approve, /start, etc.
    console.log(`Calling POST /maintenance/${id}/${actionStr}`, payload);
    // Optimistically update the UI for demonstration purposes
    setRequests(requests.map(r => {
      if (r.id === id) {
        if (actionStr === 'approve') return { ...r, status: 'Approved' };
        if (actionStr === 'reject') return { ...r, status: 'Rejected' };
        if (actionStr === 'assign-technician') return { ...r, status: 'TechnicianAssigned', technician: payload.technician };
        if (actionStr === 'start') return { ...r, status: 'InProgress' };
        if (actionStr === 'resolve') return { ...r, status: 'Resolved' };
      }
      return r;
    }));
  };

  const handleRaiseSubmit = (e) => {
    e.preventDefault();
    console.log("Raising new request:", newRequest);
    setRequests([...requests, { id: Date.now().toString(), ...newRequest, status: 'Pending' }]);
    setIsModalOpen(false);
    setNewRequest({ asset_id: '', issue_description: '', priority: 'Medium' });
  };

  // Helper to render role-gated buttons
  const renderActionButtons = (req) => {
    const isManager = currentUserRole === 'AssetManager' || currentUserRole === 'Admin';
    
    if (req.status === 'Pending' && isManager) {
      return (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={() => handleAction(req.id, 'approve')}>Approve</button>
          <button className="btn btn-secondary" onClick={() => handleAction(req.id, 'reject')}>Reject</button>
        </div>
      );
    }
    if (req.status === 'Approved' && isManager) {
      return (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={() => handleAction(req.id, 'assign-technician', { technician: 'Auto-Assigned Tech' })}>
            Assign Technician
          </button>
        </div>
      );
    }
    if (req.status === 'TechnicianAssigned' && isManager) {
      return (
        <div style={{ marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={() => handleAction(req.id, 'start')}>Start Work</button>
        </div>
      );
    }
    if (req.status === 'InProgress' && isManager) {
      return (
        <div style={{ marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={() => handleAction(req.id, 'resolve')}>Resolve</button>
        </div>
      );
    }
    return null;
  };

  const filteredRequests = activeFilter ? requests.filter(r => r.status === activeFilter) : requests;

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>Maintenance Workflow</h1>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>+ Raise Request</button>
      </div>

      <div className="chip-group" style={{ marginBottom: '2rem' }}>
        <button className={`chip ${activeFilter === '' ? 'active' : ''}`} onClick={() => setActiveFilter('')}>All</button>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={`chip ${activeFilter === s ? 'active' : ''}`}
            onClick={() => setActiveFilter(s)}
            style={{ 
              backgroundColor: activeFilter === s ? '#6366f1' : 'transparent',
              borderColor: activeFilter === s ? '#6366f1' : '#334155'
            }}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="report-grid">
        {filteredRequests.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>No requests found for this status.</div>
        ) : (
          filteredRequests.map(req => (
            <div key={req.id} className="report-card" style={{ display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <span style={{ fontWeight: 'bold' }}>Asset: {req.asset_id}</span>
                <span className={`chip`} style={{ fontSize: '0.8rem', padding: '2px 8px', borderColor: '#334155' }}>
                  {req.status}
                </span>
              </div>
              <p style={{ flexGrow: 1, color: '#e2e8f0' }}>{req.issue_description}</p>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#94a3b8', marginTop: '1rem' }}>
                <span>Priority: <span style={{ color: req.priority === 'High' ? '#f87171' : '#fbbf24' }}>{req.priority}</span></span>
                {req.technician && <span>Tech: {req.technician}</span>}
              </div>

              {renderActionButtons(req)}
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
          backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}>
          <div className="report-card" style={{ width: '100%', maxWidth: '500px' }}>
            <h2>Raise Maintenance Request</h2>
            <form onSubmit={handleRaiseSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
              <div className="form-group">
                <label>Asset ID / Name</label>
                <input required type="text" value={newRequest.asset_id} onChange={e => setNewRequest({...newRequest, asset_id: e.target.value})} placeholder="Select asset..." style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
              </div>
              
              <div className="form-group">
                <label>Issue Description</label>
                <textarea required rows="4" value={newRequest.issue_description} onChange={e => setNewRequest({...newRequest, issue_description: e.target.value})} placeholder="Describe the problem..." style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
              </div>
              
              <div className="form-group">
                <label>Priority</label>
                <select value={newRequest.priority} onChange={e => setNewRequest({...newRequest, priority: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label>Photo Evidence (Optional)</label>
                <input type="file" accept="image/*" style={{ color: '#94a3b8' }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Submit Request</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
