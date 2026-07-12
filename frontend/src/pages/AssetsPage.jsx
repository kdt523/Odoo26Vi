import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coreApi } from '../api/client';

export default function AssetsPage() {
  const { role } = useAuth();
  
  // Default scope based on role
  const defaultScope = role === 'Employee' ? 'mine' : (role === 'DepartmentHead' ? 'department' : 'all');
  
  const [scope, setScope] = useState(defaultScope);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  const ASSET_STATUSES = [
    'Available', 'Allocated', 'Reserved', 'UnderMaintenance',
    'Lost', 'Retired', 'Disposed',
  ];

  useEffect(() => {
    const fetchAssets = async () => {
      setLoading(true);
      try {
        const endpoint = scope === 'mine' ? '/assets/mine' : (scope === 'department' ? '/assets/department' : '/assets');
        const params = {};
        if (search) params.tag = search; // Assuming 'tag' is used for search based on backend route definition
        if (statusFilter) params.status = statusFilter;

        const { data } = await coreApi.get(endpoint, { params });
        // The backend schema returns AssetListResponse which typically has an 'items' array. If not, fallback to 'data' if it's an array
        setAssets(data.items || data || []);
      } catch (err) {
        console.error('Failed to fetch assets', err);
        setAssets([]);
      } finally {
        setLoading(false);
      }
    };
    
    // Slight debounce for search could be added here, but direct is fine for now
    fetchAssets();
  }, [scope, search, statusFilter]);

  return (
    <div className="page">
      <div className="page-header">
        <h1>{role === 'Employee' ? 'My Assets' : 'Assets'}</h1>
        {role !== 'Employee' && (
          <button id="btn-register-asset" className="btn btn-primary">
            + Register Asset
          </button>
        )}
      </div>

      {/* ── Scope Toggle for Department Head ── */}
      {role === 'DepartmentHead' && (
        <div className="tabs" style={{ marginBottom: '1.5rem' }}>
          <button 
            className={`tab ${scope === 'department' ? 'tab--active' : ''}`}
            onClick={() => setScope('department')}
          >
            Department
          </button>
          <button 
            className={`tab ${scope === 'all' ? 'tab--active' : ''}`}
            onClick={() => setScope('all')}
          >
            Org-wide
          </button>
        </div>
      )}

      {/* ── Search & Filters ── */}
      <div className="filter-bar">
        <input
          id="asset-search"
          type="text"
          placeholder="Search by tag…"
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
        {/* We can remove the manual 'Apply Filters' button since useEffect handles it reactively, or keep it visual only */}
      </div>

      {/* ── Asset List ── */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        {loading ? (
          <p>Loading assets...</p>
        ) : assets.length === 0 ? (
          <div className="empty-state" id="asset-list">
            <p>🗂️ No assets found.</p>
            {/* The endpoints currently return 501, so this will be hit often during initial integration */}
            <p className="scaffold-note" style={{ fontSize: '0.85rem' }}>
              (Note: Endpoints might return 501 Not Implemented until backend is wired up)
            </p>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Tag</th>
                <th>Name</th>
                <th>Status</th>
                <th>Category</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td>{asset.asset_tag}</td>
                  <td>{asset.name}</td>
                  <td>
                    <span className={`status-badge status-${asset.status?.toLowerCase()}`}>
                      {asset.status}
                    </span>
                  </td>
                  <td>{asset.category_id}</td>
                  <td>
                    <Link to={`/assets/${asset.id}`} className="btn-link">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
