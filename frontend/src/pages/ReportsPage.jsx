/**
 * src/pages/ReportsPage.jsx
 * Route: /reports
 *
 * Placeholder charts area — connects to reports-api.
 */

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts';

export default function ReportsPage() {
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const [utilizationData, setUtilizationData] = useState([]);
  const [maintenanceData, setMaintenanceData] = useState([]);
  const [allocationData, setAllocationData] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [maintRetirementData, setMaintRetirementData] = useState(null);

  // Maintenance/Retirement table sort
  const [sortConfig, setSortConfig] = useState({ key: null, dir: 'asc' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const query = `?from_date=${fromDate}&to_date=${toDate}`;
        
        const [utilRes, maintRes, allocRes, heatRes, maintRetRes] = await Promise.all([
          fetch(`/api/reports/asset-utilization${query}`),
          fetch(`/api/reports/maintenance-frequency${query}`),
          fetch(`/api/reports/allocation-summary${query}`),
          fetch(`/api/reports/booking-heatmap${query}`),
          fetch(`/api/reports/maintenance-and-retirement-due`),
        ]);
        
        if (utilRes.ok) setUtilizationData(await utilRes.json());
        if (maintRes.ok) setMaintenanceData(await maintRes.json());
        if (allocRes.ok) setAllocationData(await allocRes.json());
        if (heatRes.ok) setHeatmapData(await heatRes.json());
        if (maintRetRes.ok) setMaintRetirementData(await maintRetRes.json());
        
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    };
    fetchData();
  }, [fromDate, toDate]);

  const handleExport = (type) => {
    window.open(`/api/reports/export?report_type=${type}`, '_blank');
  };

  const EmptyState = () => (
    <div className="empty-state" style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
      <p>No data available for this period</p>
    </div>
  );

  const COLORS = ['#6366f1', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#38bdf8'];

  // ── Sorting helper for maintenance/retirement tables ──
  const sortedRows = (rows, key) => {
    if (!rows) return [];
    if (!sortConfig.key || sortConfig.key !== key) return rows;
    return [...rows].sort((a, b) => {
      const av = a[sortConfig.key] ?? '';
      const bv = b[sortConfig.key] ?? '';
      return sortConfig.dir === 'asc' ? (av < bv ? -1 : 1) : (av > bv ? -1 : 1);
    });
  };
  const handleSort = (key) => {
    setSortConfig(prev =>
      prev.key === key ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }
    );
  };
  const SortTh = ({ col, label }) => (
    <th onClick={() => handleSort(col)} style={{ cursor: 'pointer', userSelect: 'none' }}>
      {label} {sortConfig.key === col ? (sortConfig.dir === 'asc' ? '↑' : '↓') : ''}
    </th>
  );

  // ── Maintenance/Retirement row renderer ──
  const MaintRetRow = ({ row, dateKey, daysKey }) => {
    const days = row[daysKey];
    const overdue = days !== null && days < 0;
    return (
      <tr style={{ background: overdue ? 'rgba(248,113,113,0.08)' : undefined }}>
        <td style={{ fontFamily: 'monospace', color: '#94a3b8' }}>{row.asset_tag}</td>
        <td>{row.name}</td>
        <td>{row[dateKey] || '—'}</td>
        <td>
          {days === null ? '—' : (
            <span style={{
              fontWeight: 600,
              color: overdue ? '#f87171' : days <= 7 ? '#f59e0b' : '#34d399',
            }}>
              {overdue ? `${Math.abs(days)}d overdue` : `${days}d remaining`}
            </span>
          )}
        </td>
        <td>
          <span style={{
            padding: '2px 8px', borderRadius: '12px', fontSize: '0.78rem', fontWeight: 600,
            background: row.status === 'Available' ? '#10b98120' : '#f59e0b20',
            color: row.status === 'Available' ? '#10b981' : '#f59e0b',
          }}>
            {row.status}
          </span>
        </td>
      </tr>
    );
  };

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0 }}>Reports & Analytics</h1>
          <p style={{ color: '#94a3b8', margin: '0.25rem 0 0', fontSize: '0.9rem' }}>Asset intelligence and operational insights</p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
            <label>From</label>
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </div>
          <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
            <label>To</label>
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </div>
        </div>
      </div>

      {/* ── Maintenance & Retirement Due ─────────────────────────────────── */}
      <div className="report-card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid #f59e0b' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ margin: 0 }}>⚙ Maintenance & Retirement Due</h3>
            <p style={{ color: '#94a3b8', margin: '0.25rem 0 0', fontSize: '0.85rem' }}>
              Due within 30 days for maintenance · Nearing retirement within 90 days
            </p>
          </div>
          <button className="btn btn-secondary" onClick={() => handleExport('maintenance-retirement')}>⬇ CSV</button>
        </div>

        {!maintRetirementData ? (
          <EmptyState />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Due for Maintenance */}
            <div>
              <h4 style={{ color: '#f59e0b', margin: '0 0 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                🔧 Due for Maintenance
                <span style={{ background: '#f59e0b20', color: '#f59e0b', borderRadius: '12px', padding: '1px 8px', fontSize: '0.78rem', fontWeight: 700 }}>
                  {maintRetirementData.due_for_maintenance?.length || 0}
                </span>
              </h4>
              {maintRetirementData.due_for_maintenance?.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>✓ No assets due for maintenance</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="table" style={{ fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        <SortTh col="asset_tag" label="Tag" />
                        <SortTh col="name" label="Name" />
                        <SortTh col="next_maintenance_due_date" label="Due Date" />
                        <SortTh col="days_until_maintenance" label="Days" />
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedRows(maintRetirementData.due_for_maintenance, 'days_until_maintenance').map((row, i) => (
                        <MaintRetRow key={i} row={row} dateKey="next_maintenance_due_date" daysKey="days_until_maintenance" />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Nearing Retirement */}
            <div>
              <h4 style={{ color: '#f87171', margin: '0 0 0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                🕐 Nearing Retirement
                <span style={{ background: '#f8717120', color: '#f87171', borderRadius: '12px', padding: '1px 8px', fontSize: '0.78rem', fontWeight: 700 }}>
                  {maintRetirementData.nearing_retirement?.length || 0}
                </span>
              </h4>
              {maintRetirementData.nearing_retirement?.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>✓ No assets nearing retirement</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="table" style={{ fontSize: '0.85rem' }}>
                    <thead>
                      <tr>
                        <SortTh col="asset_tag" label="Tag" />
                        <SortTh col="name" label="Name" />
                        <SortTh col="expected_retirement_date" label="Retire Date" />
                        <SortTh col="days_until_retirement" label="Days" />
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedRows(maintRetirementData.nearing_retirement, 'days_until_retirement').map((row, i) => (
                        <MaintRetRow key={i} row={row} dateKey="expected_retirement_date" daysKey="days_until_retirement" />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="report-grid">
        {/* Utilization Report */}
        <div className="report-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3>Asset Utilization</h3>
              <p>Utilization trends based on allocations vs idle.</p>
            </div>
            <button className="btn btn-secondary" onClick={() => handleExport('utilization')}>⬇ CSV</button>
          </div>
          {utilizationData.length === 0 ? <EmptyState /> : (
            <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
              <ResponsiveContainer>
                <BarChart data={utilizationData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1d27', borderColor: '#2a2d3a' }} />
                  <Bar dataKey="allocations" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Maintenance Frequency */}
        <div className="report-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3>Maintenance Frequency</h3>
              <p>Frequency of maintenance by category.</p>
            </div>
            <button className="btn btn-secondary" onClick={() => handleExport('maintenance')}>⬇ CSV</button>
          </div>
          {maintenanceData.length === 0 ? <EmptyState /> : (
            <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={maintenanceData} dataKey="frequency" nameKey="category" cx="50%" cy="50%" outerRadius={100} label>
                    {maintenanceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1a1d27', borderColor: '#2a2d3a' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Allocation Summary */}
        <div className="report-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3>Allocation Summary</h3>
              <p>Department-wise distribution of allocated assets.</p>
            </div>
            <button className="btn btn-secondary" onClick={() => handleExport('allocation')}>⬇ CSV</button>
          </div>
          {allocationData.length === 0 ? <EmptyState /> : (
            <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={allocationData} dataKey="active_allocations" nameKey="department" cx="50%" cy="50%" innerRadius={60} outerRadius={100} label>
                    {allocationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1a1d27', borderColor: '#2a2d3a' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Booking Heatmap */}
        <div className="report-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3>Booking Heatmap</h3>
              <p>Peak booking usage by day and hour.</p>
            </div>
            <button className="btn btn-secondary" onClick={() => handleExport('heatmap')}>⬇ CSV</button>
          </div>
          {heatmapData.length === 0 ? <EmptyState /> : (
            <div style={{ width: '100%', height: 300, marginTop: '1rem' }}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis type="number" dataKey="hour" name="Hour" unit="h" domain={[0, 24]} stroke="#64748b" />
                  <YAxis type="number" dataKey="day_of_week" name="Day" domain={[1, 7]} stroke="#64748b" />
                  <ZAxis type="number" dataKey="count" range={[50, 400]} name="Bookings" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1a1d27', borderColor: '#2a2d3a' }} />
                  <Scatter name="Bookings" data={heatmapData} fill="#fbbf24" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
