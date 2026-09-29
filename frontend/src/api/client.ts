import axios from 'axios';
import type { AxiosError, InternalAxiosRequestConfig } from 'axios';

/** Same-origin /api by default (Vite dev proxy); override for a live deploy. */
export const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

/** Unauthenticated instance — used for login/refresh only. */
export const raw = axios.create({ baseURL: API_BASE, withCredentials: true });

/** Main instance: Authorization header + silent 401 → refresh → retry. */
export const client = axios.create({ baseURL: API_BASE, withCredentials: true });

let authToken: string | null = null;
let refreshing: Promise<string | null> | null = null;

/** Store pushes the in-memory access token here (avoids an import cycle). */
export function setAuthHeader(token: string | null): void {
  authToken = token;
  if (token) client.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete client.defaults.headers.common.Authorization;
}

export function getAuthHeader(): string | null {
  return authToken;
}

/** Single-flight refresh via the httpOnly cookie; returns the new token. */
async function refreshAccessToken(): Promise<string | null> {
  try {
    const { data } = await raw.post<{ access_token?: string }>('/auth/refresh');
    if (!data.access_token) return null;
    setAuthHeader(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

client.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;
    const url = config?.url ?? '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/refresh') ||
      url.includes('/auth/logout');
    if (error.response?.status === 401 && config && !config._retry && !isAuthCall) {
      config._retry = true;
      refreshing ??= refreshAccessToken().finally(() => {
        refreshing = null;
      });
      const token = await refreshing;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        return client(config);
      }
      setAuthHeader(null);
      window.dispatchEvent(new Event('auth:expired'));
    }
    return Promise.reject(error);
  },
);

/**
 * Project error shape: FastAPI detail may be a string, an object
 * `{code, message, field_errors}`, or a 422 list — flatten for display.
 */
export function apiErrorDetail(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const body = (err.response?.data ?? null) as
      | { detail?: unknown; message?: unknown }
      | string
      | null;
    const detail = typeof body === 'object' && body !== null ? body.detail : body;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
        .filter(Boolean);
      if (msgs.length) return msgs.join('; ');
    }
    if (detail && typeof detail === 'object') {
      const obj = detail as { message?: unknown; code?: unknown };
      if (typeof obj.message === 'string') {
        return typeof obj.code === 'string' && obj.code !== 'ERROR'
          ? `${obj.message}`
          : obj.message;
      }
      return JSON.stringify(detail);
    }
    if (err.code === 'ERR_NETWORK' || !err.response) {
      return 'Cannot reach the API server. Is the backend running?';
    }
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return String(err);
}

/** Parsed `{detail.errors: [...]}` payload from Table-3 validation (400). */
export function apiErrorFieldErrors(err: unknown): { code: string; message: string }[] {
  if (!axios.isAxiosError(err)) return [];
  const data = err.response?.data as { detail?: { errors?: { code?: string; message?: string }[] } } | undefined;
  const errors = data?.detail?.errors;
  return Array.isArray(errors)
    ? errors.map((e) => ({ code: e.code ?? '', message: e.message ?? '' }))
    : [];
}
