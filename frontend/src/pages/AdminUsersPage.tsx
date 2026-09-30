import { useState } from 'react';
import {
  createUser, listUsers, unlockUser, updateUser,
  type UserInput, type UserPatch,
} from '../api/admin';
import { apiErrorDetail } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { useAuthStore } from '../store/authStore';
import type { Role, User } from '../types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { titleCase } from '../lib/status';

const ROLES: Role[] = ['ADMIN', 'ENGINEER', 'REVIEWER', 'VIEWER'];

const ROLE_STYLES: Record<Role, string> = {
  ADMIN: 'bg-teal-50 text-teal-800 ring-teal-200',
  ENGINEER: 'bg-slate-100 text-slate-800 ring-slate-300',
  REVIEWER: 'bg-slate-100 text-slate-800 ring-slate-300',
  VIEWER: 'bg-slate-100 text-slate-700 ring-slate-300',
};

const EMPTY: UserInput = {
  username: '', full_name: '', email: '', password: '', role: 'VIEWER',
};

export default function AdminUsersPage() {
  const me = useAuthStore((s) => s.user);
  const users = useAsync(listUsers);

  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<UserInput>(EMPTY);
  const [editing, setEditing] = useState<User | null>(null);
  const [edit, setEdit] = useState<UserPatch>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function run(name: string, fn: () => Promise<unknown>, after?: () => void) {
    setBusy(name);
    setError(null);
    setNotice(null);
    try {
      await fn();
      users.reload();
      after?.();
    } catch (err) {
      setError(apiErrorDetail(err));
    } finally {
      setBusy(null);
    }
  }

  async function submitCreate(e: React.FormEvent) {
    e.preventDefault();
    await run('create', async () => {
      await createUser(form);
      setForm(EMPTY);
      setCreating(false);
      setNotice(`User "${form.username}" created — they must change the password at first login.`);
    });
  }

  async function submitEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    const patch: UserPatch = { ...edit };
    if (!patch.new_password) delete patch.new_password;
    await run('edit', async () => {
      await updateUser(editing.id, patch);
      setEditing(null);
      setEdit({});
      setNotice('User updated.');
    });
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-700">Access control</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">User administration</h1>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Manage role-based access, account state, and credential recovery.</p>
        </div>
        <Button onClick={() => { setCreating(!creating); setEditing(null); }} aria-expanded={creating} aria-controls="create-user-form">
          {creating ? 'Close form' : 'New user'}
        </Button>
      </header>

      <Card
        title="Authorised users"
        actions={<span className="text-xs tabular-nums text-slate-500">{users.data?.length ?? 0} accounts</span>}
      >
        {notice && (
          <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
            {notice}
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            {error}
          </div>
        )}

        {users.error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            <p className="font-semibold">User directory could not be loaded</p>
            <p className="mt-1 text-xs">{users.error}</p>
            <Button variant="secondary" className="mt-3" onClick={users.reload}>Retry</Button>
          </div>
        )}

        {creating && (
          <form id="create-user-form" onSubmit={submitCreate} className="mb-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="mb-4">
              <h2 className="text-sm font-semibold text-slate-900">Create an account</h2>
              <p className="mt-1 text-xs text-slate-500">The user must replace the initial password at first sign-in.</p>
            </div>
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
              <Input label="Username" value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })} required />
              <Input label="Full name" value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
              <Input label="Email address" type="email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              <Input label="Initial password" type="password" autoComplete="new-password" value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                hint="At least 8 characters with one letter and one digit" required />
              <div>
                <label htmlFor="create-role" className="mb-1 block text-sm font-medium text-slate-700">Role</label>
                <select id="create-role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
                  className="block w-full rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-600">
                  {ROLES.map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
                </select>
              </div>
              <div className="flex items-end gap-2">
                <Button type="submit" loading={busy === 'create'} disabled={users.loading}>Create user</Button>
                <Button variant="secondary" onClick={() => setCreating(false)}>Cancel</Button>
              </div>
            </div>
          </form>
        )}

        {users.loading && (
          <div className="space-y-2" aria-label="Loading user directory">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-12 animate-pulse rounded-md bg-slate-100 motion-reduce:animate-none" />
            ))}
          </div>
        )}
        {!users.loading && !users.error && users.data && users.data.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
            <p className="text-sm font-semibold text-slate-800">No user accounts found</p>
            <p className="mt-1 text-xs text-slate-500">Create an account to grant controlled access.</p>
          </div>
        )}
        {!users.loading && !users.error && users.data && users.data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <caption className="sr-only">Authorised user accounts and access roles</caption>
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-[0.08em] text-slate-500">
                  <th scope="col" className="px-3 py-2.5 font-semibold">Username</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Name</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Email</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Role</th>
                  <th scope="col" className="px-3 py-2.5 font-semibold">Account state</th>
                  <th scope="col" className="px-3 py-2.5 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.data.map((u) => (
                  <tr key={u.id} className="transition-colors hover:bg-slate-50">
                    <td className="px-3 py-3 font-semibold text-slate-900">
                      @{u.username}{me?.id === u.id && <span className="ml-1 text-xs font-medium text-teal-700">Current user</span>}
                    </td>
                    <td className="px-3 py-3 text-slate-700">{u.full_name}</td>
                    <td className="px-3 py-3 text-slate-600">{u.email}</td>
                    <td className="px-3 py-3">
                      <Badge label={titleCase(u.role)} className={ROLE_STYLES[u.role]} />
                    </td>
                    <td className="space-x-1 px-3 py-3">
                      <Badge label={u.is_active ? 'Active' : 'Disabled'}
                        className={u.is_active
                          ? 'bg-emerald-100 text-emerald-800 ring-emerald-300'
                          : 'bg-red-100 text-red-800 ring-red-300'} />
                      {u.must_change_password && (
                        <Badge label="Password change due"
                          className="bg-amber-100 text-amber-800 ring-amber-300" />
                      )}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary" className="!px-2 !py-1"
                          onClick={() => { setEditing(u); setEdit({
                            full_name: u.full_name, email: u.email,
                            role: u.role, is_active: u.is_active,
                          }); setCreating(false); }}>
                          Edit
                        </Button>
                        <Button variant="secondary" className="!px-2 !py-1"
                          loading={busy === `unlock-${u.id}`}
                          onClick={() => run(`unlock-${u.id}`, () => unlockUser(u.id))}>
                          Unlock
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {editing && (
        <Card title={`Edit account · @${editing.username}`}>
          <form onSubmit={submitEdit} className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <Input label="Full name" value={edit.full_name ?? ''}
              onChange={(e) => setEdit({ ...edit, full_name: e.target.value })} />
            <Input label="Email" type="email" value={edit.email ?? ''}
              onChange={(e) => setEdit({ ...edit, email: e.target.value })} />
            <div>
              <label htmlFor="edit-role" className="mb-1 block text-sm font-medium text-slate-700">Role</label>
              <select id="edit-role" value={edit.role ?? editing.role}
                onChange={(e) => setEdit({ ...edit, role: e.target.value as Role })}
                className="block w-full rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-600">
                {ROLES.map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
              </select>
            </div>
            <Input label="Reset password (optional)" type="password" autoComplete="new-password" value={edit.new_password ?? ''}
              onChange={(e) => setEdit({ ...edit, new_password: e.target.value })}
              hint="Leave blank to keep the current password" />
            <label className="flex items-center gap-2 self-end rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-teal-700 focus:ring-teal-600"
                checked={edit.is_active ?? editing.is_active}
                disabled={editing.id === me?.id}
                onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} />
              Account active {editing.id === me?.id && '(current user cannot be disabled)'}
            </label>
            <div className="flex items-end gap-3">
              <Button type="submit" loading={busy === 'edit'}>Save changes</Button>
              <Button variant="secondary" onClick={() => { setEditing(null); setEdit({}); }}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
