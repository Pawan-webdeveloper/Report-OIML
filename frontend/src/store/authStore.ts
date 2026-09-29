import { create } from 'zustand';
import * as authApi from '../api/auth';
import { setAuthHeader } from '../api/client';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  initialized: boolean; // true once the bootstrap attempt has settled
  setAuth: (user: User, token: string) => void;
  setToken: (token: string) => void;
  clear: () => void;
  bootstrap: () => Promise<void>;
  login: (username: string, password: string) => Promise<{ mustChangePassword: boolean }>;
  logout: () => Promise<void>;
}

/** Module-level guard: concurrent bootstrap calls share one in-flight promise. */
let bootstrapping: Promise<void> | null = null;

/**
 * The access token lives ONLY in memory. Sessions survive reloads because the
 * backend keeps the refresh token in an httpOnly cookie; bootstrap() exchanges
 * it for a fresh access token. Simpler and safer than localStorage.
 */
export const useAuthStore = create<AuthState>()((set, get) => ({
  user: null,
  accessToken: null,
  initialized: false,

  setAuth: (user, token) => {
    setAuthHeader(token);
    set({ user, accessToken: token, initialized: true });
  },
  setToken: (token) => {
    setAuthHeader(token);
    set({ accessToken: token });
  },
  clear: () => {
    setAuthHeader(null);
    set({ user: null, accessToken: null, initialized: true });
  },

  bootstrap: () => {
    if (get().initialized) return Promise.resolve();
    bootstrapping ??= (async () => {
      try {
        const { access_token } = await authApi.refresh();
        setAuthHeader(access_token);
        set({ accessToken: access_token });
        const user = await authApi.me(access_token);
        set({ user, initialized: true });
      } catch {
        setAuthHeader(null);
        set({ user: null, accessToken: null, initialized: true });
      } finally {
        bootstrapping = null;
      }
    })();
    return bootstrapping;
  },

  login: async (username, password) => {
    const data = await authApi.login(username, password);
    setAuthHeader(data.access_token);
    set({ user: data.user, accessToken: data.access_token, initialized: true });
    return { mustChangePassword: data.must_change_password };
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      /* best-effort — cookie may already be gone */
    }
    setAuthHeader(null);
    set({ user: null, accessToken: null, initialized: true });
  },
}));

// The axios interceptor fires this when a refresh ultimately fails.
window.addEventListener('auth:expired', () => {
  setAuthHeader(null);
  useAuthStore.setState({ user: null, accessToken: null, initialized: true });
});