/**
 * src/context/AuthContext.jsx — JWT storage and current user context.
 *
 * Provides:
 *   - currentUser: { id, name, email, role, department_id } | null
 *   - login(email, password): calls core-api, stores tokens
 *   - logout(): clears tokens + user
 *   - isAuthenticated: bool
 *   - role: string | null  (convenience accessor)
 */

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { coreApi } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true); // checking stored token on mount

  // ── Restore session from localStorage on app load ──────────────────────
  useEffect(() => {
    const checkToken = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const { data } = await coreApi.get('/auth/me', {
            headers: { Authorization: `Bearer ${token}` }
          });
          setCurrentUser(data);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setCurrentUser(null);
        }
      }
      setLoading(false);
    };
    checkToken();
  }, []);

  // ── Login ──────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { data } = await coreApi.post('/auth/login', { email, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // Fetch fresh user data after login
    const { data: userData } = await coreApi.get('/auth/me', {
      headers: { Authorization: `Bearer ${data.access_token}` }
    });
    setCurrentUser(userData);
  }, []);

  // ── Logout ─────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await coreApi.post('/auth/logout');
    } catch { /* ignore */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setCurrentUser(null);
  }, []);

  const value = {
    currentUser,
    loading,
    isAuthenticated: !!currentUser,
    role: currentUser?.role ?? null,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook: must be used inside <AuthProvider> */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}

export default AuthContext;
