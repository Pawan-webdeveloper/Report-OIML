import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as authApi from '../api/auth';
import { apiErrorDetail } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';

const POLICY = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

export default function ChangePasswordPage() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (next !== confirm) return setError('New passwords do not match');
    if (!POLICY.test(next)) {
      return setError('Password must be at least 8 characters with a letter and a digit');
    }
    setBusy(true);
    try {
      await authApi.changePassword(current, next);
      if (user) {
        useAuthStore.setState({ user: { ...user, must_change_password: false } });
      }
      setDone(true);
    } catch (err) {
      setError(apiErrorDetail(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg py-4">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary-700">Account security</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">Choose a password used only for this laboratory console.</p>
      </div>
      <Card title={user?.must_change_password ? 'Set a new password (required)' : 'Change password'}>
        {done ? (
          <div className="space-y-4 py-3 text-center">
            <p className="mx-auto w-fit rounded bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-inset ring-emerald-300">Password updated</p>
            <p className="mx-auto max-w-sm text-sm leading-6 text-slate-600">
              Password updated successfully. You can continue to the dashboard.
            </p>
            <Button onClick={() => navigate('/', { replace: true })}>Go to Dashboard</Button>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <Input
              label="Current password"
              type="password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoComplete="current-password"
              required
            />
            <Input
              label="New password"
              type="password"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              hint="Min 8 characters, at least one letter and one digit"
              autoComplete="new-password"
              required
            />
            <Input
              label="Confirm new password"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
            />
            {error && (
              <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
                {error}
              </div>
            )}
            <Button type="submit" loading={busy} className="w-full">
              Update password
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
