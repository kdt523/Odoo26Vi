/**
 * src/pages/AllocationsPage.jsx
 * Route: /allocations
 *
 * Allocation list + Return Approvals queue + Transfer Requests.
 * Role-aware: Employee sees only their own allocations + request-return flow.
 * AssetManager/Admin sees Return Approvals queue with Approve/Reject actions.
 */

import { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

const TABS = ['My Allocations', 'Return Approvals', 'Transfer Requests'];
const EMPLOYEE_TABS = ['My Allocations', 'Transfer Requests'];

export default function AllocationsPage() {
  const { user } = useContext(AuthContext) || {};
  const currentUserRole = user?.role || 'Employee';
  const currentUserId = user?.id || null;
  const isManager = ['AssetManager', 'Admin', 'DepartmentHead'].includes(currentUserRole);

  const visibleTabs = isManager ? TABS : EMPLOYEE_TABS;

  const [activeTab, setActiveTab] = useState('My Allocations');
  const [allocations, setAllocations] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null); // { type: 'success'|'error', msg }

  // Modals
  const [isAllocModalOpen, setIsAllocModalOpen] = useState(false);
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);

  // Form State
  const [allocForm, setAllocForm] = useState({ asset_id: '', employee_id: '', expected_return_date: '' });
  const [allocConflict, setAllocConflict] = useState(null);
  const [returnForm, setReturnForm] = useState({ allocation_id: '', condition_check_in_notes: '' });
  const [rejectForm, setRejectForm] = useState({ allocation_id: '', reason: '' });
  const [submitting, setSubmitting] = useState(false);

  const showToast = (type, msg) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Fetch ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('access_token');
        const headers = { Authorization: `Bearer ${token}` };

        const [allocRes, transferRes] = await Promise.all([
          fetch('/api/allocations/', { headers }),
          fetch('/api/allocations/transfers', { headers }),
        ]);

        if (!allocRes.ok) throw new Error('Failed to load allocations');
        if (!transferRes.ok) throw new Error('Failed to load transfers');

        const [allocData, transferData] = await Promise.all([
          allocRes.json(),
          transferRes.json(),
        ]);

        setAllocations(allocData);
        setTransfers(transferData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // ── Allocation helpers ────────────────────────────────────────────────────
  // Filter my allocations: Employee sees only their own; managers see all
  const myAllocations = isManager
    ? allocations.filter(a => ['Active', 'ReturnRequested'].includes(a.status))
    : allocations.filter(a =>
        ['Active', 'ReturnRequested'].includes(a.status) &&
        (currentUserId ? a.employee_id === currentUserId : true)
      );

  const pendingReturns = allocations.filter(a => a.status === 'ReturnRequested');

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleAllocateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      if (allocConflict) {
        // Create transfer request
        const res = await fetch('/api/allocations/transfers', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({ allocation_id: allocConflict.current_allocation_id, reason: 'Requested via conflict flow' }),
        });
        if (!res.ok) throw new Error('Failed to create transfer request');
        const newTransfer = await res.json();
        setTransfers(prev => [...prev, newTransfer]);
        showToast('success', 'Transfer request submitted.');
      } else {
        const res = await fetch('/api/allocations/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            asset_id: allocForm.asset_id,
            employee_id: allocForm.employee_id || null,
            allocated_date: new Date().toISOString().slice(0, 10),
            expected_return_date: allocForm.expected_return_date || null,
          }),
        });
        if (res.status === 409) {
          const data = await res.json();
          setAllocConflict({ message: data.detail?.message || 'Asset unavailable', current_allocation_id: data.detail?.current_allocation_id });
          return;
        }
        if (!res.ok) throw new Error('Allocation failed');
        const newAlloc = await res.json();
        setAllocations(prev => [...prev, newAlloc]);
        showToast('success', 'Asset allocated successfully.');
      }
      setIsAllocModalOpen(false);
      setAllocConflict(null);
      setAllocForm({ asset_id: '', employee_id: '', expected_return_date: '' });
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReturnSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/allocations/${returnForm.allocation_id}/return-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ condition_check_in_notes: returnForm.condition_check_in_notes }),
      });
      if (!res.ok) throw new Error('Failed to submit return request');
      const updated = await res.json();
      setAllocations(prev => prev.map(a => a.id === updated.id ? updated : a));
      showToast('success', 'Return request submitted. Awaiting manager approval.');
      setIsReturnModalOpen(false);
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReturnApprove = async (allocationId) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/allocations/${allocationId}/return-approve`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to approve return');
      const updated = await res.json();
      setAllocations(prev => prev.map(a => a.id === updated.id ? updated : a));
      showToast('success', 'Return approved. Asset marked Available.');
    } catch (err) {
      showToast('error', err.message);
    }
  };

  const handleReturnRejectSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/allocations/${rejectForm.allocation_id}/return-reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reason: rejectForm.reason }),
      });
      if (!res.ok) throw new Error('Failed to reject return');
      const updated = await res.json();
      setAllocations(prev => prev.map(a => a.id === updated.id ? updated : a));
      showToast('success', 'Return request rejected. Allocation restored to Active.');
      setIsRejectModalOpen(false);
    } catch (err) {
      showToast('error', err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransferAction = async (id, action) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`/api/allocations/transfers/${id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ action }),
      });
      if (!res.ok) throw new Error(`Failed to ${action} transfer`);
      const updated = await res.json();
      setTransfers(prev => prev.map(t => t.id === updated.id ? updated : t));
      if (action === 'approve') {
        showToast('success', 'Transfer approved.');
      } else {
        showToast('success', 'Transfer rejected.');
      }
    } catch (err) {
      showToast('error', err.message);
    }
  };

  // ── Styles ────────────────────────────────────────────────────────────────
  const inputStyle = {
    padding: '0.75rem', borderRadius: '8px',
    border: '1px solid #334155', background: '#0f172a', color: 'white',
    width: '100%', boxSizing: 'border-box',
  };
  const overlayStyle = {
    position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.75)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  };
  const modalStyle = {
    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    border: '1px solid #334155', borderRadius: '16px', padding: '2rem',
    width: '100%', maxWidth: '500px', boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
  };

  // ── Status badge helpers ──────────────────────────────────────────────────
  const statusBadge = (status) => {
    const map = {
      Active: { bg: '#10b98120', color: '#10b981', label: 'Active' },
      ReturnRequested: { bg: '#f59e0b20', color: '#f59e0b', label: 'Return Pending' },
      Returned: { bg: '#64748b20', color: '#64748b', label: 'Returned' },
      Transferred: { bg: '#6366f120', color: '#6366f1', label: 'Transferred' },
    };
    const s = map[status] || { bg: '#334155', color: '#94a3b8', label: status };
    return (
      <span style={{ background: s.bg, color: s.color, padding: '0.25rem 0.65rem', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600 }}>
        {s.label}
      </span>
    );
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="page">
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: '1.5rem', right: '1.5rem', zIndex: 9999,
          background: toast.type === 'success' ? '#10b981' : '#f87171',
          color: 'white', padding: '0.75rem 1.25rem', borderRadius: '10px',
          fontWeight: 600, boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
          transition: 'all 0.3s ease',
        }}>
          {toast.type === 'success' ? '✓ ' : '✗ '}{toast.msg}
        </div>
      )}

      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ margin: 0 }}>Allocations & Transfers</h1>
          <p style={{ color: '#94a3b8', margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
            Manage asset allocations, returns, and transfers
          </p>
        </div>
        {isManager && activeTab === 'My Allocations' && (
          <button className="btn btn-primary" onClick={() => { setAllocConflict(null); setIsAllocModalOpen(true); }}>
            + Allocate Asset
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs" role="tablist">
        {visibleTabs.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
            {tab === 'Return Approvals' && pendingReturns.length > 0 && (
              <span style={{ background: '#f59e0b', color: '#0f172a', borderRadius: '50%', width: '20px', height: '20px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700, marginLeft: '0.5rem' }}>
                {pendingReturns.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading && <p style={{ color: '#94a3b8', marginTop: '2rem' }}>Loading allocations…</p>}
      {error && <p style={{ color: '#f87171', marginTop: '2rem' }}>Error: {error}</p>}

      {!loading && !error && (
        <div className="tab-panel" role="tabpanel" style={{ marginTop: '2rem' }}>

          {/* ── My Allocations ──────────────────────────────────────────── */}
          {activeTab === 'My Allocations' && (
            <div>
              {myAllocations.length === 0 && (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '4rem 0' }}>
                  <p style={{ fontSize: '3rem' }}>📦</p>
                  <p>No active allocations found.</p>
                </div>
              )}
              <div className="report-grid">
                {myAllocations.map(a => (
                  <div key={a.id} className="report-card" style={{
                    borderLeft: a.is_overdue ? '4px solid #f87171' : a.status === 'ReturnRequested' ? '4px solid #f59e0b' : '4px solid #34d399'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h3 style={{ margin: 0, fontSize: '1rem' }}>{a.asset_id || 'Asset'}</h3>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {a.is_overdue && <span style={{ color: '#f87171', fontSize: '0.78rem', fontWeight: 700 }}>OVERDUE</span>}
                        {statusBadge(a.status)}
                      </div>
                    </div>
                    <p style={{ color: '#94a3b8', margin: '0.5rem 0', fontSize: '0.85rem' }}>
                      Holder: {a.employee_id || a.department_id || 'N/A'}
                    </p>
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: 0 }}>
                      Return by: {a.expected_return_date || 'No date set'}
                    </p>

                    {/* Holder action: request return */}
                    {a.status === 'Active' && (
                      <div style={{ marginTop: '1rem' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: '0.85rem', padding: '0.4rem 0.9rem' }}
                          onClick={() => { setReturnForm({ allocation_id: a.id, condition_check_in_notes: '' }); setIsReturnModalOpen(true); }}
                        >
                          Request Return
                        </button>
                      </div>
                    )}

                    {/* ReturnRequested state — show notes, holder sees status, manager sees nothing here (handled in Return Approvals tab) */}
                    {a.status === 'ReturnRequested' && (
                      <div style={{ marginTop: '1rem', background: 'rgba(245,158,11,0.08)', border: '1px solid #f59e0b', borderRadius: '8px', padding: '0.75rem' }}>
                        <p style={{ color: '#f59e0b', margin: '0 0 0.35rem', fontWeight: 600, fontSize: '0.85rem' }}>⏳ Return Pending Approval</p>
                        {a.return_condition_notes && (
                          <p style={{ fontSize: '0.82rem', color: '#cbd5e1', margin: 0 }}>
                            Notes: {a.return_condition_notes}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Return Approvals (managers only) ───────────────────────── */}
          {activeTab === 'Return Approvals' && isManager && (
            <div>
              {pendingReturns.length === 0 && (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '4rem 0' }}>
                  <p style={{ fontSize: '3rem' }}>✅</p>
                  <p>No pending return approvals.</p>
                </div>
              )}
              <div className="report-grid">
                {pendingReturns.map(a => (
                  <div key={a.id} className="report-card" style={{ borderLeft: '4px solid #f59e0b' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h3 style={{ margin: 0, fontSize: '1rem' }}>{a.asset_id || 'Asset'}</h3>
                      {statusBadge(a.status)}
                    </div>
                    <p style={{ color: '#94a3b8', margin: '0.5rem 0 0.25rem', fontSize: '0.85rem' }}>
                      Holder: {a.employee_id || a.department_id || 'N/A'}
                    </p>
                    {a.return_condition_notes && (
                      <div style={{ background: '#0f172a', borderRadius: '6px', padding: '0.6rem', margin: '0.75rem 0', border: '1px solid #1e293b' }}>
                        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.8rem', fontWeight: 600 }}>Condition Notes:</p>
                        <p style={{ color: '#e2e8f0', margin: '0.25rem 0 0', fontSize: '0.85rem' }}>{a.return_condition_notes}</p>
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                      <button
                        className="btn btn-primary"
                        style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                        onClick={() => handleReturnApprove(a.id)}
                      >
                        ✓ Approve
                      </button>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem', borderColor: '#f87171', color: '#f87171' }}
                        onClick={() => { setRejectForm({ allocation_id: a.id, reason: '' }); setIsRejectModalOpen(true); }}
                      >
                        ✗ Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Transfer Requests ───────────────────────────────────────── */}
          {activeTab === 'Transfer Requests' && (
            <div>
              {transfers.filter(t => t.status === 'Requested').length === 0 && (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '4rem 0' }}>
                  <p style={{ fontSize: '3rem' }}>🔄</p>
                  <p>No pending transfer requests.</p>
                </div>
              )}
              <div className="report-grid">
                {transfers.filter(t => t.status === 'Requested').map(t => (
                  <div key={t.id} className="report-card">
                    <h3 style={{ margin: '0 0 0.5rem' }}>Transfer Request</h3>
                    <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '0.25rem 0' }}>Allocation ID: {t.allocation_id}</p>
                    <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: '0.25rem 0' }}>Requested by: {t.requested_by || 'N/A'}</p>
                    {t.reason && (
                      <p style={{ fontStyle: 'italic', color: '#94a3b8', fontSize: '0.85rem', margin: '0.5rem 0' }}>"{t.reason}"</p>
                    )}
                    {isManager && (
                      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                        <button className="btn btn-primary" style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem' }} onClick={() => handleTransferAction(t.id, 'approve')}>Approve</button>
                        <button className="btn btn-secondary" style={{ padding: '0.4rem 0.9rem', fontSize: '0.85rem' }} onClick={() => handleTransferAction(t.id, 'reject')}>Reject</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Allocate Modal ──────────────────────────────────────────────── */}
      {isAllocModalOpen && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h2 style={{ margin: '0 0 1.5rem' }}>{allocConflict ? '⚠ Asset Unavailable' : '+ Allocate Asset'}</h2>
            {allocConflict && (
              <div style={{ background: 'rgba(248,113,113,0.1)', border: '1px solid #f87171', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                <p style={{ color: '#f87171', margin: 0, fontWeight: 700 }}>Conflict Detected</p>
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.9rem' }}>{allocConflict.message}</p>
              </div>
            )}
            <form onSubmit={handleAllocateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Asset ID</label>
                <input required disabled={!!allocConflict} type="text" value={allocForm.asset_id} onChange={e => setAllocForm({ ...allocForm, asset_id: e.target.value })} style={inputStyle} placeholder="Enter asset UUID" />
              </div>
              {!allocConflict && (
                <>
                  <div>
                    <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Employee ID</label>
                    <input type="text" value={allocForm.employee_id} onChange={e => setAllocForm({ ...allocForm, employee_id: e.target.value })} style={inputStyle} placeholder="Employee UUID (optional)" />
                  </div>
                  <div>
                    <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Expected Return Date</label>
                    <input type="date" value={allocForm.expected_return_date} onChange={e => setAllocForm({ ...allocForm, expected_return_date: e.target.value })} style={inputStyle} />
                  </div>
                </>
              )}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '0.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => { setIsAllocModalOpen(false); setAllocConflict(null); }}>Cancel</button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ background: allocConflict ? 'linear-gradient(135deg, #f59e0b, #d97706)' : undefined }}>
                  {submitting ? 'Saving…' : allocConflict ? 'Request Transfer Instead' : 'Allocate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Request Return Modal ────────────────────────────────────────── */}
      {isReturnModalOpen && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <h2 style={{ margin: '0 0 0.5rem' }}>Request Return</h2>
            <p style={{ color: '#94a3b8', margin: '0 0 1.5rem', fontSize: '0.9rem' }}>Describe the asset's current condition. A manager will review and approve the return.</p>
            <form onSubmit={handleReturnSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Condition / Check-in Notes</label>
                <textarea
                  rows="4"
                  value={returnForm.condition_check_in_notes}
                  onChange={e => setReturnForm({ ...returnForm, condition_check_in_notes: e.target.value })}
                  style={{ ...inputStyle, resize: 'vertical' }}
                  placeholder="e.g. Minor scratches on lid, fully functional…"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsReturnModalOpen(false)}>Cancel</button>
                <button type="submit" disabled={submitting} className="btn btn-primary">{submitting ? 'Submitting…' : 'Submit Return Request'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Reject Return Modal ─────────────────────────────────────────── */}
      {isRejectModalOpen && (
        <div style={overlayStyle}>
          <div style={{ ...modalStyle, maxWidth: '440px' }}>
            <h2 style={{ margin: '0 0 0.5rem', color: '#f87171' }}>Reject Return</h2>
            <p style={{ color: '#94a3b8', margin: '0 0 1.5rem', fontSize: '0.9rem' }}>Provide a reason so the holder can address the issue and resubmit.</p>
            <form onSubmit={handleReturnRejectSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.4rem', fontSize: '0.85rem' }}>Reason for Rejection *</label>
                <textarea
                  required
                  rows="3"
                  value={rejectForm.reason}
                  onChange={e => setRejectForm({ ...rejectForm, reason: e.target.value })}
                  style={{ ...inputStyle, resize: 'vertical' }}
                  placeholder="e.g. Condition notes are insufficient, please photograph the damage…"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsRejectModalOpen(false)}>Cancel</button>
                <button type="submit" disabled={submitting} className="btn btn-primary" style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)' }}>
                  {submitting ? 'Rejecting…' : 'Reject Return'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
