/**
 * src/pages/OrgSetupPage.jsx
 * Route: /org-setup  (Admin only — guarded in router)
 *
 * Three tabs: Departments | Asset Categories | Employee Directory
 */

import { useState } from 'react';

const TABS = ['Departments', 'Asset Categories', 'Employee Directory'];

export default function OrgSetupPage() {
  const [activeTab, setActiveTab] = useState('Departments');

  return (
    <div className="page">
      <div className="page-header">
        <h1>Org Setup</h1>
        <p className="page-subtitle">Manage departments, categories, and employees</p>
      </div>

      {/* ── Tabs ── */}
      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            id={`tab-${tab.toLowerCase().replace(/\s+/g, '-')}`}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ── Tab Panels ── */}
      <div className="tab-panel" role="tabpanel">
        {activeTab === 'Departments' && (
          <div id="panel-departments">
            <div className="panel-actions">
              <button id="btn-create-department" className="btn btn-primary">
                + New Department
              </button>
            </div>
            <div className="empty-state">
              <p>🏢 No departments yet.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/org/departments and render a table.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'Asset Categories' && (
          <div id="panel-asset-categories">
            <div className="panel-actions">
              <button id="btn-create-category" className="btn btn-primary">
                + New Category
              </button>
            </div>
            <div className="empty-state">
              <p>🗂️ No categories yet.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/org/categories and render a table.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'Employee Directory' && (
          <div id="panel-employee-directory">
            <div className="panel-actions">
              <button id="btn-create-employee" className="btn btn-primary">
                + Add Employee
              </button>
            </div>
            <div className="empty-state">
              <p>👥 No employees yet.</p>
              <p className="scaffold-note">
                TODO: fetch GET /api/org/employees and render a table with a Promote Role action.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
