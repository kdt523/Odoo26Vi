import { useState, useEffect } from 'react';
import { coreApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const TABS = ['Departments', 'Asset Categories', 'Employee Directory'];

export default function OrgSetupPage() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('Departments');
  
  // Data states
  const [departments, setDepartments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Guard
  useEffect(() => {
    if (currentUser && currentUser.role !== 'Admin') {
      navigate('/dashboard', { replace: true });
    }
  }, [currentUser, navigate]);

  // Fetch data based on active tab
  useEffect(() => {
    if (activeTab === 'Departments') fetchDepartments();
    else if (activeTab === 'Asset Categories') fetchCategories();
    else if (activeTab === 'Employee Directory') fetchEmployees();
  }, [activeTab]);

  const fetchDepartments = async () => {
    try {
      const { data } = await coreApi.get('/org/departments');
      setDepartments(data);
    } catch (err) { console.error(err); }
  };

  const fetchCategories = async () => {
    try {
      const { data } = await coreApi.get('/org/categories');
      setCategories(data);
    } catch (err) { console.error(err); }
  };

  const fetchEmployees = async () => {
    try {
      const { data } = await coreApi.get('/org/employees');
      setEmployees(data);
    } catch (err) { console.error(err); }
  };

  // Promotion handler
  const handlePromote = async (employeeId, newRole) => {
    try {
      await coreApi.post(`/org/employees/${employeeId}/promote`, { role: newRole });
      fetchEmployees(); // refresh list
    } catch (err) {
      alert("Failed to promote employee: " + (err.response?.data?.detail || err.message));
    }
  };

  if (!currentUser || currentUser.role !== 'Admin') return null;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Org Setup</h1>
        <p className="page-subtitle">Manage departments, categories, and employees</p>
      </div>

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="tab-panel" role="tabpanel" style={{ marginTop: '2rem' }}>
        {activeTab === 'Departments' && (
          <div>
            <div className="panel-actions" style={{ marginBottom: '1rem' }}>
              <button className="btn btn-primary">+ New Department</button>
            </div>
            {departments.length === 0 ? (
              <div className="empty-state">No departments yet.</div>
            ) : (
              <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2d3a', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>Name</th>
                    <th style={{ padding: '0.5rem' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {departments.map(d => (
                    <tr key={d.id} style={{ borderBottom: '1px solid #2a2d3a' }}>
                      <td style={{ padding: '0.5rem' }}>{d.name}</td>
                      <td style={{ padding: '0.5rem' }}>{d.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'Asset Categories' && (
          <div>
            <div className="panel-actions" style={{ marginBottom: '1rem' }}>
              <button className="btn btn-primary">+ New Category</button>
            </div>
            {categories.length === 0 ? (
              <div className="empty-state">No categories yet.</div>
            ) : (
              <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2d3a', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>Name</th>
                    <th style={{ padding: '0.5rem' }}>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {categories.map(c => (
                    <tr key={c.id} style={{ borderBottom: '1px solid #2a2d3a' }}>
                      <td style={{ padding: '0.5rem' }}>{c.name}</td>
                      <td style={{ padding: '0.5rem' }}>{c.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'Employee Directory' && (
          <div>
            <div className="panel-actions" style={{ marginBottom: '1rem' }}>
              <button className="btn btn-primary">+ Add Employee</button>
            </div>
            {employees.length === 0 ? (
              <div className="empty-state">No employees yet.</div>
            ) : (
              <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2a2d3a', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>Name</th>
                    <th style={{ padding: '0.5rem' }}>Email</th>
                    <th style={{ padding: '0.5rem' }}>Role</th>
                    <th style={{ padding: '0.5rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map(e => (
                    <tr key={e.id} style={{ borderBottom: '1px solid #2a2d3a' }}>
                      <td style={{ padding: '0.5rem' }}>{e.name}</td>
                      <td style={{ padding: '0.5rem' }}>{e.email}</td>
                      <td style={{ padding: '0.5rem' }}><span className="badge">{e.role}</span></td>
                      <td style={{ padding: '0.5rem' }}>
                        <select 
                          value={e.role} 
                          onChange={(ev) => handlePromote(e.id, ev.target.value)}
                          style={{ padding: '0.2rem', borderRadius: '4px', background: '#1a1d27', color: 'white', border: '1px solid #2a2d3a' }}
                        >
                          <option value="Employee">Employee</option>
                          <option value="DepartmentHead">Department Head</option>
                          <option value="AssetManager">Asset Manager</option>
                          <option value="Admin">Admin</option>
                        </select>
                      </td>
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
