import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { coreApi } from '../api/client';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchUnreadCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const { data } = await coreApi.get('/notifications');
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to fetch unread notifications count:', err);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchUnreadCount();
    
    // Optional: Poll every 60 seconds
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  const decrementUnreadCount = useCallback(() => {
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);
  
  const resetUnreadCount = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const value = {
    unreadCount,
    fetchUnreadCount,
    decrementUnreadCount,
    resetUnreadCount,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotification must be used within <NotificationProvider>');
  return ctx;
}
