import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { apiErrorDetail } from '../api/client';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Spinner } from '../components/ui/Spinner';

export default function LoginPage() {
  const login = useAuthStore((s) => s.login);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? '/';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from} replace />;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { mustChangePassword } = await login(username.trim(), password);
      navigate(mustChangePassword ? '/change-password' : from, { replace: true });
    } catch (err) {
      setError(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-primary-950 p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary-600 text-2xl text-white shadow-lg">
            ⚖
          </div>
          <h1 className="mt-4 text-2xl font-bold text-white">NAWI Portal</h1>
          <p className="mt-1 text-sm text-primary-300">
            OIML R 76 Type-Evaluation Reporting System
          </p>
        </div>

        <form
          onSubmit={onSubmit}
          className="space-y-4 rounded-2xl bg-white p-8 shadow-xl"
        >
          <Input
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          {error && (
            <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-inset ring-red-200">
              {error}
            </div>
          )}

          <Button type="submit" loading={busy} className="w-full">
            {busy ? 'Signing in…' : 'Sign in'}
          </Button>

          <div className="rounded-lg bg-slate-50 px-3 py-3 text-xs text-slate-500 ring-1 ring-inset ring-slate-200">
            <p className="mb-1 font-semibold text-slate-600">Demo accounts (seeded):</p>
            <p>admin/Admin@123 · engineer/Engineer@123</p>
            <p>reviewer/Reviewer@123 · viewer/Viewer@123</p>
            <p className="mt-1 text-slate-400">
              Demo mode: any username &amp; password works — new usernames are created
              automatically.
            </p>
          </div>
        </form>

        {busy && (
          <p className="mt-4 flex items-center justify-center gap-2 text-sm text-primary-200">
            <Spinner className="h-4 w-4" /> Authenticating…
          </p>
        )}
      </div>
    </div>
  );
}