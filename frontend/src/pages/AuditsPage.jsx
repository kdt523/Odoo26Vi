import React, { useState, useEffect } from 'react';
import { coreApi } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function AuditsPage() {
  const { currentUser, role } = useAuth();
  
  // Data states
  const [cycles, setCycles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  
  // Active selection states
  const [selectedCycleDetails, setSelectedCycleDetails] = useState(null);
  const [discrepancyReport, setDiscrepancyReport] = useState([]);
  
  // Create form state
  const [formData, setFormData] = useState({
    scopeType: 'department', // 'department' or 'location'
    scope_department_id: '',
    location: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    auditor_ids: [],
  });
  const [formError, setFormError] = useState('');

  // Resolution modal state
  const [isResolveOpen, setIsResolveOpen] = useState(false);
  const [resolveTarget, setResolveTarget] = useState(null); // { asset_id, asset_name }
  const [resolveForm, setResolveForm] = useState({ action: '', notes: '' });
  const [resolveError, setResolveError] = useState('');

  // ── Initialization ──
  useEffect(() => {
    fetchCycles();
    fetchDepartments();
    fetchEmployees();
  }, []);

  const fetchCycles = async () => {
    try {
      const { data } = await coreApi.get('/audits/');
      setCycles(data);
    } catch (err) { console.error(err); }
  };

  const fetchDepartments = async () => {
    try {
      const { data } = await coreApi.get('/org/departments');
      setDepartments(data);
    } catch (err) { console.error(err); }
  };

  const fetchEmployees = async () => {
    try {
      const { data } = await coreApi.get('/org/employees');
      setEmployees(data);
    } catch (err) { console.error(err); }
  };

  const fetchCycleDetail = async (cycleId) => {
    try {
      const { data } = await coreApi.get(`/audits/${cycleId}`);
      setSelectedCycleDetails(data);
      setIsDetailOpen(true);
    } catch (err) {
      alert("Failed to load cycle details.");
    }
  };

  // ── Actions ──
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    try {
      const payload = {
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        auditor_ids: formData.auditor_ids.length > 0 ? formData.auditor_ids : undefined,
      };
      
      if (formData.scopeType === 'department') {
        if (!formData.scope_department_id) return setFormError("Select a department.");
        payload.scope_department_id = formData.scope_department_id;
      } else {
        if (!formData.location) return setFormError("Enter a location.");
        payload.location = formData.location;
      }

      await coreApi.post('/audits/', payload);
      setIsCreateOpen(false);
      fetchCycles();
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message);
    }
  };

  const handleMarkItem = async (assetId, result) => {
    try {
      await coreApi.post(`/audits/${selectedCycleDetails.cycle.id}/items/${assetId}`, {
        result,
        notes: ''
      });
      // Refresh details
      fetchCycleDetail(selectedCycleDetails.cycle.id);
    } catch (err) {
      alert("Failed to record result: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleCloseCycle = async () => {
    if (!window.confirm("Are you sure you want to close this cycle? Missing assets will be marked as Lost.")) return;
    try {
      const { data } = await coreApi.post(`/audits/${selectedCycleDetails.cycle.id}/close`);
      setIsDetailOpen(false);
      setDiscrepancyReport(data.discrepancy_report);
      setIsReportOpen(true);
      fetchCycles();
    } catch (err) {
      alert("Failed to close cycle: " + (err.response?.data?.detail || err.message));
    }
  };

  const openResolveModal = (assetId, assetName) => {
    setResolveTarget({ asset_id: assetId, asset_name: assetName });
    setResolveForm({ action: '', notes: '' });
    setResolveError('');
    setIsResolveOpen(true);
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    setResolveError('');
    if (!resolveForm.action) return setResolveError('Select an action.');
    if (resolveForm.action === 'override_verified' && !resolveForm.notes) {
      return setResolveError('A reason is required for Override Verified.');
    }
    try {
      const cycleId = selectedCycleDetails.cycle.id;
      await coreApi.post(
        `/audits/${cycleId}/items/${resolveTarget.asset_id}/resolve`,
        { action: resolveForm.action, notes: resolveForm.notes || null }
      );
      setIsResolveOpen(false);
      // Refresh the detail view so the resolved badge appears immediately
      await fetchCycleDetail(cycleId);
    } catch (err) {
      setResolveError(err.response?.data?.detail || err.message);
    }
  };

  // ── Render Helpers ──
  const isManager = ['Admin', 'AssetManager'].includes(role);
  
  const getProgress = (details) => {
    if (!details || !details.assets || details.assets.length === 0) return 0;
    const checked = details.assets.filter(a => a.audit_item !== null).length;
    return Math.round((checked / details.assets.length) * 100);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Audit Cycles</h1>
        {isManager && (
          <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
            + New Audit Cycle
          </button>
        )}
      </div>

      {/* ── Cycle list ── */}
      {cycles.length === 0 ? (
        <div className="empty-state">
          <p>📋 No audit cycles yet.</p>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Scope</th>
              <th>Start Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {cycles.map(c => (
              <tr key={c.id}>
                <td>
                  {c.scope_department_id 
                    ? `Dept: ${departments.find(d => d.id === c.scope_department_id)?.name || c.scope_department_id}` 
                    : `Loc: ${c.location}`}
                </td>
                <td>{c.start_date}</td>
                <td>
                  <span className="badge" style={{ 
                    backgroundColor: c.status === 'Active' ? '#34d399' : (c.status === 'Closed' ? '#64748b' : '#6366f1'),
                    color: 'white'
                  }}>
                    {c.status}
                  </span>
                </td>
                <td>
                  <button className="btn btn-secondary" onClick={() => fetchCycleDetail(c.id)}>
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* ── Create Modal ── */}
      {isCreateOpen && (
        <div style={modalOverlayStyle}>
          <div style={modalContentStyle}>
            <h2>Create Audit Cycle</h2>
            <form onSubmit={handleCreateSubmit} className="auth-form" style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label>Scope Type</label>
                <select 
                  className="filter-select" 
                  value={formData.scopeType}
                  onChange={e => setFormData({...formData, scopeType: e.target.value})}
                >
                  <option value="department">By Department</option>
                  <option value="location">By Location</option>
                </select>
              </div>

              {formData.scopeType === 'department' ? (
                <div className="form-group">
                  <label>Department</label>
                  <select 
                    className="filter-select"
                    value={formData.scope_department_id}
                    onChange={e => setFormData({...formData, scope_department_id: e.target.value})}
                  >
                    <option value="">Select Dept...</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="form-group">
                  <label>Location</label>
                  <input 
                    type="text" 
                    value={formData.location}
                    onChange={e => setFormData({...formData, location: e.target.value})}
                    placeholder="e.g. Building A, Floor 2"
                  />
                </div>
              )}

              <div className="form-group">
                <label>Start Date</label>
                <input 
                  type="date" 
                  value={formData.start_date}
                  onChange={e => setFormData({...formData, start_date: e.target.value})}
                  required 
                />
              </div>

              <div className="form-group">
                <label>Assign Auditors</label>
                <select 
                  multiple 
                  className="filter-select" 
                  style={{ height: '100px' }}
                  value={formData.auditor_ids}
                  onChange={e => {
                    const options = [...e.target.options];
                    const values = options.filter(o => o.selected).map(o => o.value);
                    setFormData({...formData, auditor_ids: values});
                  }}
                >
                  {employees.map(e => (
                    <option key={e.id} value={e.id}>{e.name} ({e.role})</option>
                  ))}
                </select>
                <small style={{ color: '#888' }}>Hold Ctrl/Cmd to select multiple</small>
              </div>

              {formError && <div className="form-error">{formError}</div>}
              
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary">Create Cycle</button>
                <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Detail / Verification Modal ── */}
      {isDetailOpen && selectedCycleDetails && (
        <div style={{...modalOverlayStyle, zIndex: 100}}>
          <div style={{...modalContentStyle, maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto'}}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <h2>Cycle Details</h2>
              <button className="btn btn-secondary" onClick={() => setIsDetailOpen(false)}>Close</button>
            </div>
            
            <div style={{ margin: '1rem 0', background: '#1a1d27', padding: '1rem', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <p><strong>Status:</strong> {selectedCycleDetails.cycle.status}</p>
                <p><strong>Date:</strong> {selectedCycleDetails.cycle.start_date}</p>
              </div>
              
              <div style={{ marginTop: '1rem' }}>
                <strong>Progress:</strong> {getProgress(selectedCycleDetails)}%
                <div style={{ background: '#2a2d3a', height: '8px', borderRadius: '4px', marginTop: '4px', overflow: 'hidden' }}>
                  <div style={{ background: '#34d399', height: '100%', width: `${getProgress(selectedCycleDetails)}%` }}></div>
                </div>
              </div>
            </div>

            <h3>Assets in Scope</h3>
            {selectedCycleDetails.assets.length === 0 ? (
              <p className="empty-state">No assets found in this scope.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Result</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedCycleDetails.assets.map(({ asset, audit_item }) => {
                    const isAssignedAuditor = selectedCycleDetails.auditor_ids.includes(currentUser?.id);
                    const canEdit = isAssignedAuditor && selectedCycleDetails.cycle.status === 'Active';
                    const isFlagged = audit_item && ['Missing', 'Damaged'].includes(audit_item.result);
                    const isResolved = audit_item?.resolved;
                    
                    return (
                      <tr key={asset.id}>
                        <td>{asset.name} ({asset.asset_tag})</td>
                        <td>
                          {audit_item ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span className="badge" style={{
                                backgroundColor: audit_item.result === 'Verified' ? '#34d399' : (audit_item.result === 'Missing' ? '#f87171' : '#f59e0b'),
                                color: 'white'
                              }}>
                                {audit_item.result}
                              </span>
                              {isResolved && (
                                <span style={{ background: '#10b98120', color: '#10b981', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
                                  ✓ Resolved
                                </span>
                              )}
                            </div>
                          ) : (
                            <span style={{ color: '#888' }}>Pending</span>
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                            {canEdit && (
                              <>
                                <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: '#34d399', color: '#34d399' }} onClick={() => handleMarkItem(asset.id, 'Verified')}>Verify</button>
                                <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: '#f87171', color: '#f87171' }} onClick={() => handleMarkItem(asset.id, 'Missing')}>Missing</button>
                                <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', borderColor: '#f59e0b', color: '#f59e0b' }} onClick={() => handleMarkItem(asset.id, 'Damaged')}>Damaged</button>
                              </>
                            )}
                            {/* Asset Manager resolution buttons — only for flagged, unresolved items */}
                            {isManager && isFlagged && !isResolved && selectedCycleDetails.cycle.status === 'Active' && (
                              <button
                                className="btn btn-secondary"
                                style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: '#6366f1', color: '#6366f1' }}
                                onClick={() => openResolveModal(asset.id, asset.name)}
                              >
                                ⚡ Resolve
                              </button>
                            )}
                            {!canEdit && !isManager && selectedCycleDetails.cycle.status !== 'Closed' && (
                              <span style={{ fontSize: '0.85rem', color: '#888' }}>Read-only</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}

            {isManager && selectedCycleDetails.cycle.status === 'Active' && (
              <div style={{ marginTop: '2rem', borderTop: '1px solid #2a2d3a', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button className="btn btn-primary" style={{ background: '#f87171' }} onClick={handleCloseCycle}>
                  Close Cycle
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Resolve Item Modal ── */}
      {isResolveOpen && resolveTarget && (
        <div style={{...modalOverlayStyle, zIndex: 300}}>
          <div style={{...modalContentStyle, maxWidth: '460px'}}>
            <h2 style={{ margin: '0 0 0.5rem' }}>⚡ Resolve Discrepancy</h2>
            <p style={{ color: '#94a3b8', margin: '0 0 1.5rem', fontSize: '0.9rem' }}>
              Asset: <strong>{resolveTarget.asset_name}</strong>
            </p>
            <form onSubmit={handleResolveSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label>Resolution Action</label>
                <select
                  required
                  className="filter-select"
                  value={resolveForm.action}
                  onChange={e => setResolveForm({ ...resolveForm, action: e.target.value })}
                >
                  <option value="">Select action…</option>
                  <option value="confirm_lost">Confirm Lost — mark asset as Lost immediately</option>
                  <option value="confirm_damaged_to_maintenance">Send to Maintenance — create a maintenance request</option>
                  <option value="override_verified">Override as Verified — dispute the finding (requires reason)</option>
                </select>
              </div>
              <div className="form-group">
                <label>
                  Notes / Reason
                  {resolveForm.action === 'override_verified' && <span style={{ color: '#f87171' }}> *</span>}
                </label>
                <textarea
                  rows="3"
                  value={resolveForm.notes}
                  onChange={e => setResolveForm({ ...resolveForm, notes: e.target.value })}
                  placeholder={resolveForm.action === 'override_verified' ? 'Required: explain why the finding is incorrect…' : 'Optional: additional context…'}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '6px', color: 'inherit', resize: 'vertical' }}
                />
              </div>
              {resolveError && <div className="form-error">{resolveError}</div>}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <button type="submit" className="btn btn-primary" style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)' }}>Apply Resolution</button>
                <button type="button" className="btn btn-secondary" onClick={() => setIsResolveOpen(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Discrepancy Report Modal ── */}
      {isReportOpen && (
        <div style={{...modalOverlayStyle, zIndex: 200}}>
          <div style={{...modalContentStyle, maxWidth: '600px'}}>
            <h2 style={{ color: '#f87171', marginBottom: '1rem' }}>Discrepancy Report</h2>
            <p style={{ marginBottom: '1rem' }}>The cycle has been closed. Missing assets have been marked as Lost.</p>
            
            {discrepancyReport.length === 0 ? (
              <div className="empty-state" style={{ color: '#34d399' }}>✅ All assets verified successfully!</div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Asset</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {discrepancyReport.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.asset_name} ({item.asset_tag})</td>
                      <td style={{ color: item.result === 'Missing' ? '#f87171' : '#f59e0b' }}>
                        {item.result}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            
            <div style={{ marginTop: '1rem', textAlign: 'right' }}>
              <button className="btn btn-primary" onClick={() => setIsReportOpen(false)}>Done</button>
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
  width: '90%',
  maxWidth: '500px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
};

