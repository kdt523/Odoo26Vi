/**
 * src/pages/AssetDetailPage.jsx
 * Route: /assets/:id
 *
 * Asset detail with two tabs: Allocation History | Maintenance History
 */

import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const DETAIL_TABS = ['Allocation History', 'Maintenance History'];

export default function AssetDetailPage() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('Allocation History');

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/assets" className="back-link">← Back to Assets</Link>
        <h1>Asset Detail</h1>
        <p className="page-subtitle">Asset ID: {id}</p>
      </div>

      {/* ── Asset metadata card ── */}
      <div className="detail-card" id="asset-detail-card">
        <p className="scaffold-note">
          TODO: fetch GET /api/assets/{'{id}'} and render: name, tag, category,
          serial_number, condition, location, status, acquisition info.
        </p>
      </div>

      {/* ── History tabs ── */}
      <div className="tabs" role="tablist" style={{ marginTop: '2rem' }}>
        {DETAIL_TABS.map((tab) => (
          <button
            key={tab}
            id={`detail-tab-${tab.toLowerCase().replace(/\s+/g, '-')}`}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="tab-panel" role="tabpanel">
        {activeTab === 'Allocation History' && (
          <div id="panel-allocation-history">
            <div className="empty-state">
              <p>🔗 No allocation history.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/assets/{'{id}'}/history and render allocation records.
              </p>
            </div>
          </div>
        )}
        {activeTab === 'Maintenance History' && (
          <div id="panel-maintenance-history">
            <div className="empty-state">
              <p>🔧 No maintenance history.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/maintenance?asset_id={'{id}'} and render records.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
