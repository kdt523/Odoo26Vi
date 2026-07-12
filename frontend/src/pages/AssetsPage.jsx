/**
 * src/pages/AssetsPage.jsx
 * Route: /assets
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coreApi } from '../api/client';

export default function AssetsPage() {
  const { currentUser, role } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const defaultScope = role === 'DepartmentHead' ? 'department' : 'all';
  const [scope, setScope] = useState(defaultScope);

  // URL bound filters
  const search = searchParams.get('tag') || searchParams.get('serial_number') || searchParams.get('name') || '';
  const statusFilter = searchParams.get('status') || '';
  const categoryFilter = searchParams.get('category_id') || '';
  const departmentFilter = searchParams.get('department_id') || '';
  const locationFilter = searchParams.get('location') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  // Local state
  const [assets, setAssets] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scope, setScope] = useState(role === 'DepartmentHead' ? 'department' : 'org');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    category_id: '',
    serial_number: '',
    acquisition_date: '',
    acquisition_cost: '',
    condition: 'New',
    location: '',
    is_bookable: false,
    photo_ref: '',
  });

  const ASSET_STATUSES = [
    'Available', 'Allocated', 'Reserved', 'UnderMaintenance',
    'Lost', 'Retired', 'Disposed',
  ];

  const CONDITIONS = ['New', 'Good', 'Fair', 'Poor', 'Damaged'];
  const canRegisterAsset = role === 'Admin' || role === 'AssetManager';

  useEffect(() => {
    setScope(defaultScope);
  }, [defaultScope]);

  useEffect(() => {
    // Fetch categories and departments for dropdowns
    coreApi.get('/org/categories').then(res => setCategories(res.data)).catch(console.error);
    coreApi.get('/org/departments').then(res => setDepartments(res.data)).catch(console.error);
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [searchParams, scope, currentUser?.department_id]);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      // Build query
      const params = new URLSearchParams();
      if (search) params.append('tag', search); // using tag to search globally for demo
      if (statusFilter) params.append('status', statusFilter);
      if (categoryFilter) params.append('category_id', categoryFilter);
      if (locationFilter) params.append('location', locationFilter);

      if (scope === 'department' && currentUser?.department_id) {
        params.append('department_id', currentUser.department_id);
      } else if (departmentFilter) {
        params.append('department_id', departmentFilter);
      }

      params.append('page', page);
      params.append('page_size', 20);

      let endpointToCall = forcedEndpoint;
      if (!endpointToCall) {
        endpointToCall = scope === 'department' ? '/assets/department' : '/assets';
      }

      const res = await coreApi.get(`${endpointToCall}?${params.toString()}`);
      setAssets(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const updateFilters = (key, value) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    // reset page to 1 on filter change
    if (key !== 'page') newParams.set('page', '1');
    setSearchParams(newParams);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      // convert empty strings to undefined/null for optional fields
      const payload = { ...formData };
      if (!payload.serial_number) delete payload.serial_number;
      if (!payload.acquisition_date) delete payload.acquisition_date;
      if (!payload.acquisition_cost) delete payload.acquisition_cost;
      if (!payload.location) delete payload.location;
      if (!payload.photo_ref) delete payload.photo_ref;

      await coreApi.post('/assets/', payload);
      setIsRegistering(false);
      // reset form
      setFormData({
        name: '', category_id: '', serial_number: '', acquisition_date: '',
        acquisition_cost: '', condition: 'New', location: '', is_bookable: false, photo_ref: ''
      });
      fetchAssets();
    } catch (err) {
      alert('Failed to register asset: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>{role === 'Employee' ? 'My Assets' : 'Assets'}</h1>
        {canRegisterAsset && (
          <button id="btn-register-asset" className="btn btn-primary" onClick={() => setIsRegistering(!isRegistering)}>
            {isRegistering ? 'Cancel' : '+ Register Asset'}
          </button>
        )}
      </div>

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

      {isRegistering && (
        <div className="card" style={{ marginBottom: '20px', padding: '20px' }}>
          <h3>Register New Asset</h3>
          <form onSubmit={handleRegister} style={{ display: 'grid', gap: '10px', gridTemplateColumns: '1fr 1fr' }}>
            <div>
              <label>Name *</label>
              <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="filter-input" />
            </div>
            <div>
              <label>Category *</label>
              <select required value={formData.category_id} onChange={e => setFormData({...formData, category_id: e.target.value})} className="filter-select">
                <option value="">Select Category</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label>Serial Number</label>
              <input type="text" value={formData.serial_number} onChange={e => setFormData({...formData, serial_number: e.target.value})} className="filter-input" />
            </div>
            <div>
              <label>Acquisition Date</label>
              <input type="date" value={formData.acquisition_date} onChange={e => setFormData({...formData, acquisition_date: e.target.value})} className="filter-input" />
            </div>
            <div>
              <label>Acquisition Cost</label>
              <input type="number" step="0.01" value={formData.acquisition_cost} onChange={e => setFormData({...formData, acquisition_cost: e.target.value})} className="filter-input" />
            </div>
            <div>
              <label>Condition</label>
              <select value={formData.condition} onChange={e => setFormData({...formData, condition: e.target.value})} className="filter-select">
                {CONDITIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label>Location</label>
              <input type="text" value={formData.location} onChange={e => setFormData({...formData, location: e.target.value})} className="filter-input" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <input type="checkbox" id="bookable" checked={formData.is_bookable} onChange={e => setFormData({...formData, is_bookable: e.target.checked})} />
              <label htmlFor="bookable" style={{ marginLeft: '8px' }}>Is Bookable?</label>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label>Photo URL / Ref</label>
              <input type="text" placeholder="Upload placeholder" value={formData.photo_ref} onChange={e => setFormData({...formData, photo_ref: e.target.value})} className="filter-input" style={{ width: '100%' }} />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" className="btn btn-primary">Save Asset</button>
            </div>
          </form>
        </div>
      )}

      {/* ── Search & Filters ── */}
      <div className="filter-bar" style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        <input
          id="asset-search"
          type="text"
          placeholder="Search tag/serial…"
          value={search}
          onChange={(e) => updateFilters('tag', e.target.value)}
          className="filter-input"
        />
        <select value={statusFilter} onChange={(e) => updateFilters('status', e.target.value)} className="filter-select">
          <option value="">All Statuses</option>
          {ASSET_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={categoryFilter} onChange={(e) => updateFilters('category_id', e.target.value)} className="filter-select">
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        {scope !== 'department' && (
          <select value={departmentFilter} onChange={(e) => updateFilters('department_id', e.target.value)} className="filter-select">
            <option value="">All Departments</option>
            {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        )}
        <input
          type="text"
          placeholder="Location…"
          value={locationFilter}
          onChange={(e) => updateFilters('location', e.target.value)}
          className="filter-input"
        />
      </div>

      {/* ── Asset List ── */}
      {loading ? (
        <p>Loading...</p>
      ) : assets.length === 0 ? (
        <div className="empty-state" id="asset-list">
          <p>🗂️ No assets found.</p>
        </div>
      ) : (
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ccc', textAlign: 'left' }}>
              <th>Tag</th>
              <th>Name</th>
              <th>Serial</th>
              <th>Status</th>
              <th>Condition</th>
              <th>Location</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {assets.map(asset => (
              <tr key={asset.id} style={{ borderBottom: '1px solid #eee' }}>
                <td><Link to={`/assets/${asset.id}`}>{asset.asset_tag}</Link></td>
                <td>{asset.name}</td>
                <td>{asset.serial_number || '-'}</td>
                <td><span className={`badge badge-${asset.status.toLowerCase()}`}>{asset.status}</span></td>
                <td>{asset.condition}</td>
                <td>{asset.location || '-'}</td>
                <td>
                  <Link to={`/assets/${asset.id}`} className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 8px' }}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between' }}>
        <span>Total: {total}</span>
        <div>
          <button disabled={page <= 1} onClick={() => updateFilters('page', (page - 1).toString())}>Prev</button>
          <span style={{ margin: '0 10px' }}>Page {page}</span>
          <button disabled={assets.length < 20} onClick={() => updateFilters('page', (page + 1).toString())}>Next</button>
        </div>
      </div>
    </div>
  );
}
