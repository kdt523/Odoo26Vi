/**
 * src/pages/AllocationsPage.jsx
 * Route: /allocations
 *
 * Allocation list + transfer request shell.
 */

import { useState } from 'react';

const TABS = ['Allocations', 'Transfer Requests'];

export default function AllocationsPage() {
  const [activeTab, setActiveTab] = useState('Allocations');

  return (
    <div className="page">
      <div className="page-header">
        <h1>Allocations</h1>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            id={`alloc-tab-${tab.toLowerCase().replace(/\s+/g, '-')}`}
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
        {activeTab === 'Allocations' && (
          <div id="panel-allocations">
            <div className="panel-actions">
              <button id="btn-allocate-asset" className="btn btn-primary">
                + Allocate Asset
              </button>
            </div>
            <div className="empty-state">
              <p>🔗 No active allocations.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/allocations and render table with Return / Transfer actions.
              </p>
            </div>
          </div>
        )}
        {activeTab === 'Transfer Requests' && (
          <div id="panel-transfers">
            <div className="empty-state">
              <p>🔄 No transfer requests.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/allocations/transfers and render with Approve/Reject actions.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
