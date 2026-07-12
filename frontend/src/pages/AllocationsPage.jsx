/**
 * src/pages/AllocationsPage.jsx
 * Route: /allocations
 *
 * Allocation list + transfer request shell.
 */

import { useState, useEffect } from 'react';

const TABS = ['Allocations', 'Transfer Requests'];
const currentUserRole = 'AssetManager'; // Mock role for testing

export default function AllocationsPage() {
  const [activeTab, setActiveTab] = useState('Allocations');
  const [allocations, setAllocations] = useState([]);
  const [transfers, setTransfers] = useState([]);

  // Modals
  const [isAllocModalOpen, setIsAllocModalOpen] = useState(false);
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);

  // Alloc Form State
  const [allocForm, setAllocForm] = useState({ asset_id: '', employee_id: '', expected_return_date: '' });
  const [allocConflict, setAllocConflict] = useState(null); // { message, current_allocation_id }
  
  // Return Form State
  const [returnForm, setReturnForm] = useState({ allocation_id: '', condition_check_in_notes: '' });
  const [rejectForm, setRejectForm] = useState({ allocation_id: '', reason: '' });
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);

  // Dummy fetch
  useEffect(() => {
    setAllocations([
      { id: 'a1', asset_id: 'MacBook Pro 16"', employee_id: 'Alice', expected_return_date: '2026-06-01', is_overdue: true, status: 'Active' },
      { id: 'a2', asset_id: 'Projector', department_id: 'Marketing', expected_return_date: '2026-12-31', is_overdue: false, status: 'Active' },
      { id: 'a3', asset_id: 'Standing Desk', employee_id: 'Bob', expected_return_date: '2026-10-15', is_overdue: false, status: 'ReturnRequested', return_condition_notes: 'Some scratches' }
    ]);
    setTransfers([
      { id: 't1', allocation_id: 'a1', reason: 'Need a laptop for travel', status: 'Requested', requested_by: 'Bob' }
    ]);
  }, []);

  const handleAllocateSubmit = async (e) => {
    e.preventDefault();
    if (allocConflict) {
      // It's in "Request Transfer" mode
      console.log("Requesting transfer for allocation", allocConflict.current_allocation_id);
      setTransfers([...transfers, { id: Date.now().toString(), allocation_id: allocConflict.current_allocation_id, reason: 'Requested via conflict flow', status: 'Requested' }]);
      setIsAllocModalOpen(false);
      setAllocConflict(null);
      setAllocForm({ asset_id: '', employee_id: '', expected_return_date: '' });
      return;
    }

    // Try to allocate
    console.log("Attempting allocation...", allocForm);
    
    // Simulate hitting a 409 Conflict if asset_id is 'taken'
    if (allocForm.asset_id.toLowerCase() === 'taken') {
      console.log("409 Conflict hit!");
      setAllocConflict({
        message: "Currently held by John Doe",
        current_allocation_id: "a-taken-123"
      });
    } else {
      setAllocations([...allocations, { id: Date.now().toString(), status: 'Active', is_overdue: false, ...allocForm }]);
      setIsAllocModalOpen(false);
      setAllocForm({ asset_id: '', employee_id: '', expected_return_date: '' });
    }
  };

  const handleReturnSubmit = async (e) => {
    e.preventDefault();
    console.log("Requesting asset return...", returnForm);
    setAllocations(allocations.map(a => a.id === returnForm.allocation_id ? { ...a, status: 'ReturnRequested', return_condition_notes: returnForm.condition_check_in_notes } : a));
    setIsReturnModalOpen(false);
  };

  const handleReturnApprove = async (allocationId) => {
    console.log("Approving return...", allocationId);
    setAllocations(allocations.map(a => a.id === allocationId ? { ...a, status: 'Returned' } : a));
  };

  const handleReturnRejectSubmit = async (e) => {
    e.preventDefault();
    console.log("Rejecting return...", rejectForm);
    setAllocations(allocations.map(a => a.id === rejectForm.allocation_id ? { ...a, status: 'Active' } : a));
    setIsRejectModalOpen(false);
  };

  const handleTransferAction = (id, action) => {
    console.log(`Transfer ${id} -> ${action}`);
    setTransfers(transfers.map(t => t.id === id ? { ...t, status: action === 'approve' ? 'Approved' : 'Rejected' } : t));
    if (action === 'approve') {
      const tr = transfers.find(t => t.id === id);
      setAllocations(allocations.map(a => a.id === tr.allocation_id ? { ...a, status: 'Transferred' } : a));
    }
  };

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>Allocations & Transfers</h1>
        {activeTab === 'Allocations' && (
          <button className="btn btn-primary" onClick={() => { setAllocConflict(null); setIsAllocModalOpen(true); }}>
            + Allocate Asset
          </button>
        )}
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="tab-panel" role="tabpanel" style={{ marginTop: '2rem' }}>
        {activeTab === 'Allocations' && (
          <div className="report-grid">
            {allocations.filter(a => a.status === 'Active' || a.status === 'ReturnRequested').map(a => (
              <div key={a.id} className="report-card" style={{ borderLeft: a.is_overdue ? '4px solid #f87171' : '4px solid #34d399' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <h3>{a.asset_id}</h3>
                  {a.is_overdue && <span style={{ color: '#f87171', fontSize: '0.8rem', fontWeight: 'bold' }}>OVERDUE</span>}
                </div>
                <p>Holder: {a.employee_id || a.department_id}</p>
                <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Return by: {a.expected_return_date || 'N/A'}</p>
                
                {a.status === 'Active' && (
                  <div style={{ marginTop: '1rem' }}>
                    <button className="btn btn-secondary" onClick={() => {
                      setReturnForm({ allocation_id: a.id, condition_check_in_notes: '' });
                      setIsReturnModalOpen(true);
                    }}>Request Return</button>
                  </div>
                )}

                {a.status === 'ReturnRequested' && (
                  <div style={{ marginTop: '1rem', backgroundColor: 'rgba(251, 191, 36, 0.1)', padding: '0.75rem', borderRadius: '4px', border: '1px solid #f59e0b' }}>
                    <p style={{ color: '#f59e0b', margin: '0 0 0.5rem 0', fontWeight: 'bold', fontSize: '0.9rem' }}>Return Requested</p>
                    <p style={{ fontSize: '0.85rem', color: '#e2e8f0', margin: '0 0 0.75rem 0' }}>Notes: {a.return_condition_notes || 'None'}</p>
                    
                    {(currentUserRole === 'AssetManager' || currentUserRole === 'Admin') && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => handleReturnApprove(a.id)}>Approve</button>
                        <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => {
                          setRejectForm({ allocation_id: a.id, reason: '' });
                          setIsRejectModalOpen(true);
                        }}>Reject</button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'Transfer Requests' && (
          <div className="report-grid">
            {transfers.filter(t => t.status === 'Requested').map(t => (
              <div key={t.id} className="report-card">
                <h3>Transfer Request</h3>
                <p>Target Alloc: {t.allocation_id}</p>
                <p>Requested by: {t.requested_by}</p>
                <p style={{ fontStyle: 'italic', color: '#94a3b8' }}>"{t.reason}"</p>
                
                {(currentUserRole === 'AssetManager' || currentUserRole === 'DepartmentHead') && (
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                    <button className="btn btn-primary" onClick={() => handleTransferAction(t.id, 'approve')}>Approve</button>
                    <button className="btn btn-secondary" onClick={() => handleTransferAction(t.id, 'reject')}>Reject</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Allocate Modal */}
      {isAllocModalOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="report-card" style={{ width: '100%', maxWidth: '500px' }}>
            <h2>{allocConflict ? 'Asset Unavailable' : 'Allocate Asset'}</h2>
            
            {allocConflict && (
              <div style={{ backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid #f87171', padding: '1rem', borderRadius: '4px', marginTop: '1rem' }}>
                <p style={{ color: '#f87171', margin: 0, fontWeight: 'bold' }}>Conflict Detected</p>
                <p style={{ margin: '0.5rem 0 0 0' }}>{allocConflict.message}</p>
              </div>
            )}

            <form onSubmit={handleAllocateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
              <div className="form-group">
                <label>Asset ID (Type 'taken' to trigger 409)</label>
                <input required disabled={allocConflict !== null} type="text" value={allocForm.asset_id} onChange={e => setAllocForm({...allocForm, asset_id: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
              </div>
              
              {!allocConflict && (
                <>
                  <div className="form-group">
                    <label>Assign to Employee</label>
                    <input required type="text" value={allocForm.employee_id} onChange={e => setAllocForm({...allocForm, employee_id: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
                  </div>
                  <div className="form-group">
                    <label>Expected Return Date</label>
                    <input type="date" value={allocForm.expected_return_date} onChange={e => setAllocForm({...allocForm, expected_return_date: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
                  </div>
                </>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => { setIsAllocModalOpen(false); setAllocConflict(null); }}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ backgroundColor: allocConflict ? '#fbbf24' : '#6366f1' }}>
                  {allocConflict ? 'Request Transfer instead' : 'Allocate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Return Modal */}
      {isReturnModalOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="report-card" style={{ width: '100%', maxWidth: '400px' }}>
            <h2>Request Return</h2>
            <form onSubmit={handleReturnSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
              <div className="form-group">
                <label>Condition / Check-in Notes</label>
                <textarea rows="3" value={returnForm.condition_check_in_notes} onChange={e => setReturnForm({...returnForm, condition_check_in_notes: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsReturnModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Request Return</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Return Modal */}
      {isRejectModalOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="report-card" style={{ width: '100%', maxWidth: '400px' }}>
            <h2>Reject Return Request</h2>
            <form onSubmit={handleReturnRejectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
              <div className="form-group">
                <label>Reason for Rejection</label>
                <textarea required rows="3" value={rejectForm.reason} onChange={e => setRejectForm({...rejectForm, reason: e.target.value})} style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #334155', background: '#0f172a', color: 'white' }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsRejectModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" style={{ backgroundColor: '#f87171' }}>Reject Return</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
