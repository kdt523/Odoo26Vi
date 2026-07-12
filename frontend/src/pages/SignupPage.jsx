/**
 * src/pages/SignupPage.jsx
 * Route: /signup
 *
 * Creates an Employee-only account.
 * Role field is NOT shown — assigned server-side.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { coreApi } from '../api/client';

export default function SignupPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // TODO: wire when signup endpoint is implemented
      await coreApi.post('/auth/signup', form);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <span className="logo-icon">⚡</span>
          <h1>AssetFlow</h1>
          <p>Create your account</p>
        </div>

        <form id="signup-form" onSubmit={handleSubmit} className="auth-form">
          {error && <div className="form-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="signup-name">Full name</label>
            <input
              id="signup-name"
              name="name"
              type="text"
              value={form.name}
              onChange={handleChange}
              placeholder="Jane Smith"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="signup-email">Email address</label>
            <input
              id="signup-email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Min 8 characters"
              minLength={8}
              required
            />
          </div>

          {/* Role is NOT offered — always Employee */}

          <button id="signup-submit" type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
