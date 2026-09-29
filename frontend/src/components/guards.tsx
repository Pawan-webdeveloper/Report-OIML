import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { FullPageSpinner } from './ui/Spinner';
import { useAuthStore } from '../store/authStore';
import type { Role } from '../types';

/** Blocks everything until the session bootstrap attempt has settled. */
export function RequireAuth() {
  const { user, initialized } = useAuthStore();
  const location = useLocation();

  if (!initialized) return <FullPageSpinner label="Restoring session…" />;
  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  // Forced first-login password change (backend sets must_change_password).
  if (user.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }
  return <Outlet />;
}

export function RequireRole({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return null; // RequireAuth already redirected
  if (!roles.includes(user.role)) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-4xl">🔒</p>
        <h1 className="mt-3 text-lg font-semibold text-slate-800">403 — Access denied</h1>
        <p className="mt-1 text-sm text-slate-500">
          Your role (<b>{user.role}</b>) does not have access to this area.
          Required: {roles.join(' / ')}.
        </p>
      </div>
    );
  }
  return <>{children}</>;
}