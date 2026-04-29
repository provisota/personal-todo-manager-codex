import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { api } from '../api/client';
import type { User } from '../types/domain';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
  testLogin: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const currentUser = await api.me();
      setUser(currentUser);
    } catch (err) {
      setUser(null);
      const message = err instanceof Error ? err.message : 'Unable to load session';
      setError(message === 'Authentication required' || message === 'Session expired' ? null : message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await api.logout().catch(() => undefined);
    setUser(null);
  }, []);

  const testLogin = useCallback(async () => {
    const currentUser = await api.testLogin();
    setUser(currentUser);
  }, []);

  useEffect(() => {
    void refreshUser();
    const onExpired = () => setUser(null);
    window.addEventListener('auth:expired', onExpired);
    return () => window.removeEventListener('auth:expired', onExpired);
  }, [refreshUser]);

  const value = useMemo(
    () => ({ user, loading, error, refreshUser, logout, testLogin }),
    [user, loading, error, refreshUser, logout, testLogin]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
