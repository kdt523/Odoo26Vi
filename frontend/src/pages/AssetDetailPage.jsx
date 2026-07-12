/**
 * src/pages/AssetDetailPage.jsx
 * Route: /assets/:id
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { coreApi } from '../api/client';

const DETAIL_TABS = ['Allocation History', 'Maintenance History'];

export default function AssetDetailPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('Allocation History');
  
  const [asset, setAsset] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAssetDetail();
  }, [id]);

  const fetchAssetDetail = async () => {
    setLoading(true);
    try {
      const [assetRes, historyRes] = await Promise.all([
        coreApi.get(`/assets/${id}`),
        coreApi.get(`/assets/${id}/history`)
      ]);
      setAsset(assetRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="page"><p>Loading...</p></div>;
  if (!asset) return <div className="page"><p>Asset not found.</p></div>;

  const allocationHistory = history.filter(h => h.type === 'allocation');
  const maintenanceHistory = history.filter(h => h.type === 'maintenance');

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/assets" className="back-link">← Back to Assets</Link>
        <h1>Asset Detail: {asset.name}</h1>
        <p className="page-subtitle">Asset ID: {id}</p>
      </div>

      {/* ── Asset metadata card ── */}
      <div className="detail-card" id="asset-detail-card" style={{ padding: '20px', border: '1px solid #eee', borderRadius: '8px', marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div><strong>Tag:</strong> {asset.asset_tag}</div>
          <div><strong>Status:</strong> <span className={`badge badge-${asset.status.toLowerCase()}`}>{asset.status}</span></div>
          <div><strong>Serial Number:</strong> {asset.serial_number || '-'}</div>
          <div><strong>Condition:</strong> {asset.condition}</div>
          <div><strong>Location:</strong> {asset.location || '-'}</div>
          <div><strong>Bookable:</strong> {asset.is_bookable ? 'Yes' : 'No'}</div>
          <div><strong>Acquisition Date:</strong> {asset.acquisition_date || '-'}</div>
          <div><strong>Acquisition Cost:</strong> {asset.acquisition_cost ? `$${asset.acquisition_cost}` : '-'}</div>
        </div>
      </div>

      {/* ── History tabs ── */}
      <div className="tabs" role="tablist" style={{ marginTop: '2rem', display: 'flex', gap: '10px' }}>
        {DETAIL_TABS.map((tab) => (
          <button
            key={tab}
            id={`detail-tab-${tab.toLowerCase().replace(/\s+/g, '-')}`}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderBottom: activeTab === tab ? '3px solid #1D76DB' : '3px solid transparent',
              background: 'none',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 'bold' : 'normal'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="tab-panel" role="tabpanel" style={{ padding: '20px 0' }}>
        {activeTab === 'Allocation History' && (
          <div id="panel-allocation-history">
            {allocationHistory.length === 0 ? (
              <div className="empty-state"><p>🔗 No allocation history.</p></div>
            ) : (
              <table className="data-table" style={{ width: '100%', textAlign: 'left' }}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Employee ID</th>
                    <th>Department ID</th>
                    <th>Return Date</th>
                  </tr>
                </thead>
                <tbody>
                  {allocationHistory.map(h => (
                    <tr key={h.id}>
                      <td>{new Date(h.date).toLocaleString()}</td>
                      <td>{h.status}</td>
                      <td>{h.details.employee_id || '-'}</td>
                      <td>{h.details.department_id || '-'}</td>
                      <td>{h.details.actual_return_date || 'Not returned'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
        
        {activeTab === 'Maintenance History' && (
          <div id="panel-maintenance-history">
            {maintenanceHistory.length === 0 ? (
              <div className="empty-state"><p>🔧 No maintenance history.</p></div>
            ) : (
              <table className="data-table" style={{ width: '100%', textAlign: 'left' }}>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Issue Description</th>
                  </tr>
                </thead>
                <tbody>
                  {maintenanceHistory.map(h => (
                    <tr key={h.id}>
                      <td>{new Date(h.date).toLocaleString()}</td>
                      <td>{h.status}</td>
                      <td>{h.details.priority}</td>
                      <td>{h.details.issue_description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
