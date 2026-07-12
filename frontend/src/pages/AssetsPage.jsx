/**
 * src/pages/AssetsPage.jsx
 * Route: /assets
 *
 * Asset list + search/filter shell.
 * Detail page is at /assets/:id (AssetDetailPage).
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function AssetsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const ASSET_STATUSES = [
    'Available', 'Allocated', 'Reserved', 'UnderMaintenance',
    'Lost', 'Retired', 'Disposed',
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Assets</h1>
        <button id="btn-register-asset" className="btn btn-primary">
          + Register Asset
        </button>
      </div>

      {/* ── Search & Filters ── */}
      <div className="filter-bar">
        <input
          id="asset-search"
          type="text"
          placeholder="Search by tag, serial, name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="filter-input"
        />
        <select
          id="asset-status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">All statuses</option>
          {ASSET_STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button id="btn-apply-filters" className="btn btn-secondary">
          Apply Filters
        </button>
        {/* TODO: also add category_id, department_id, location filters */}
      </div>

      {/* ── Asset List ── */}
      <div className="empty-state" id="asset-list">
        <p>🗂️ No assets found.</p>
        <p className="scaffold-note">
          TODO: fetch GET /api/assets with search/filter params and render a sortable table.
        </p>
      </div>
    </div>
  );
}
