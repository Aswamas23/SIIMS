import { createContext, useContext, useState, useEffect, useCallback, ReactNode, createElement } from 'react';
import { setAccessToken } from '../services/api';
import authService from '../services/auth.service';
import api from '../services/api';
import type { User } from '../types';

// ---- Context shape ----
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: async () => {},
});

// ---- Provider ----
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: try to restore session by refreshing the access token.
  useEffect(() => {
    const restoreSession = async () => {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        setIsLoading(false);
        return;
      }
      try {
        const refreshRes = await api.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
        setAccessToken(refreshRes.data.access_token);
        const me = await authService.getMe();
        setUser(me);
      } catch {
        localStorage.removeItem('refresh_token');
        setAccessToken(null);
      } finally {
        setIsLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await authService.login(email, password);
    const me = await authService.getMe();
    setUser(me);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    window.location.href = '/login';
  }, []);

  return createElement(
    AuthContext.Provider,
    { value: { user, isAuthenticated: !!user, isLoading, login, logout } },
    children,
  );
}

// ---- Hook ----
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

export default useAuth;
