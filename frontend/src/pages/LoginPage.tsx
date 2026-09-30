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
    <main className="grid min-h-dvh bg-slate-100 lg:grid-cols-[minmax(20rem,0.85fr)_minmax(32rem,1.15fr)]">
      <section className="hidden flex-col justify-between border-r border-white/10 bg-primary-950 p-10 text-white lg:flex xl:p-14">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-primary-400/40 bg-white/5 font-mono text-xs font-bold text-primary-200">
            R76
          </div>
          <div>
            <p className="text-sm font-semibold">NAWI Laboratory</p>
            <p className="text-xs text-slate-400">Type evaluation console</p>
          </div>
        </div>

        <div className="max-w-md">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-primary-300">Controlled workspace</p>
          <h1 className="mt-4 text-balance text-4xl font-semibold leading-tight tracking-tight xl:text-5xl">
            Precision records for regulated measurement.
          </h1>
          <p className="mt-5 max-w-sm text-sm leading-6 text-slate-300">
            Prepare, review, and issue OIML R 76 type-evaluation reports with traceable test data and controlled approvals.
          </p>
        </div>

        <p className="font-mono text-[11px] uppercase tracking-wider text-slate-500">SIH26035 · Department of Consumer Affairs</p>
      </section>

      <section className="flex items-center justify-center p-5 sm:p-8 lg:p-12">
        <div className="w-full max-w-md">
          <div className="mb-7 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-950 font-mono text-xs font-bold text-primary-100">R76</div>
            <p className="mt-4 text-xs font-semibold uppercase tracking-[0.16em] text-primary-700">NAWI Laboratory</p>
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-950">Sign in to the console</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">Use your assigned laboratory account to continue.</p>
          </div>

        <form
          onSubmit={onSubmit}
          className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-panel sm:p-8"
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
            <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
              {error}
            </div>
          )}

          <Button type="submit" loading={busy} className="w-full">
            {busy ? 'Signing in…' : 'Sign in'}
          </Button>

          <div className="rounded-md border border-slate-200 bg-slate-50 px-3.5 py-3 text-xs leading-5 text-slate-600">
            <p className="mb-1 font-semibold text-slate-700">Seeded demonstration accounts</p>
            <p className="font-mono text-[11px]">admin/Admin@123 · engineer/Engineer@123</p>
            <p className="font-mono text-[11px]">reviewer/Reviewer@123 · viewer/Viewer@123</p>
            <p className="mt-1 text-slate-500">
              Demo mode: any username &amp; password works — new usernames are created
              automatically.
            </p>
          </div>
        </form>

        {busy && (
          <p className="mt-4 flex items-center justify-center gap-2 text-sm font-medium text-primary-700">
            <Spinner className="h-4 w-4" /> Authenticating…
          </p>
        )}
      </div>
      </section>
    </main>
  );
}
