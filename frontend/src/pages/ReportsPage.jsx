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

  useEffect(() => {
    // This is where you would fetch data from the backend.
    // For now, we simulate fetching empty or placeholder data
    // to prove the empty state UI works as required by the acceptance criteria.
    const fetchData = async () => {
      try {
        const query = `?from_date=${fromDate}&to_date=${toDate}`;
        
        const [utilRes, maintRes, allocRes, heatRes] = await Promise.all([
          fetch(`/api/v1/reports/asset-utilization${query}`),
          fetch(`/api/v1/reports/maintenance-frequency${query}`),
          fetch(`/api/v1/reports/allocation-summary${query}`),
          fetch(`/api/v1/reports/booking-heatmap${query}`)
        ]);
        
        setUtilizationData(await utilRes.json());
        setMaintenanceData(await maintRes.json());
        setAllocationData(await allocRes.json());
        setHeatmapData(await heatRes.json());
        
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      }
    };
    fetchData();
  }, [fromDate, toDate]);

  const handleExport = (type) => {
    const url = `/api/v1/reports/export?report_type=${type}&from_date=${fromDate}&to_date=${toDate}`;
    window.open(url, '_blank');
  };

  const EmptyState = () => (
    <div className="empty-state" style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '1rem' }}>
      <p>No data available for this period</p>
    </div>
  );

  const COLORS = ['#6366f1', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#38bdf8'];

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <h1>Reports & Analytics</h1>
        
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
