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
import { ROLE_STYLES, titleCase } from '../lib/status';

const ROLES: Role[] = ['ADMIN', 'ENGINEER', 'REVIEWER', 'VIEWER'];

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
    <div className="space-y-6">
      <Card
        title="User management (RBAC)"
        actions={<Button onClick={() => { setCreating(!creating); setEditing(null); }}>
          {creating ? 'Close' : '+ New user'}
        </Button>}
      >
        {notice && (
          <div className="mb-4 rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800 ring-1 ring-inset ring-emerald-200">
            {notice}
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-inset ring-red-200">
            {error}
          </div>
        )}

        {creating && (
          <form onSubmit={submitCreate} className="mb-6 grid grid-cols-1 gap-3 rounded-lg bg-slate-50 p-4 md:grid-cols-3">
            <Input label="Username *" value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            <Input label="Full name *" value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
            <Input label="Email *" type="email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            <Input label="Initial password *" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              hint="Min 8 chars, letter + digit — user must change it at first login" required />
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Role *</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
                className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300">
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="flex items-end">
              <Button type="submit" loading={busy === 'create'} disabled={users.loading}>
                Create user
              </Button>
            </div>
          </form>
        )}

        {users.loading && <p className="text-sm text-slate-500">Loading…</p>}
        {users.data && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                  <th className="py-2 pr-4">Username</th>
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">State</th>
                  <th className="py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.data.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="py-2 pr-4 font-medium">
                      @{u.username}{me?.id === u.id && <span className="ml-1 text-xs text-primary-600">(you)</span>}
                    </td>
                    <td className="py-2 pr-4">{u.full_name}</td>
                    <td className="py-2 pr-4 text-slate-600">{u.email}</td>
                    <td className="py-2 pr-4">
                      <Badge label={titleCase(u.role)} className={ROLE_STYLES[u.role]} />
                    </td>
                    <td className="py-2 pr-4 space-x-1">
                      <Badge label={u.is_active ? 'Active' : 'Disabled'}
                        className={u.is_active
                          ? 'bg-emerald-100 text-emerald-800 ring-emerald-300'
                          : 'bg-red-100 text-red-800 ring-red-300'} />
                      {u.must_change_password && (
                        <Badge label="Password change due"
                          className="bg-amber-100 text-amber-800 ring-amber-300" />
                      )}
                    </td>
                    <td className="py-2 text-right">
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
        <Card title={`Edit — @${editing.username}`}>
          <form onSubmit={submitEdit} className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Input label="Full name" value={edit.full_name ?? ''}
              onChange={(e) => setEdit({ ...edit, full_name: e.target.value })} />
            <Input label="Email" type="email" value={edit.email ?? ''}
              onChange={(e) => setEdit({ ...edit, email: e.target.value })} />
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Role</label>
              <select value={edit.role ?? editing.role}
                onChange={(e) => setEdit({ ...edit, role: e.target.value as Role })}
                className="block w-full rounded-lg border-0 px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300">
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <Input label="Reset password (optional)" value={edit.new_password ?? ''}
              onChange={(e) => setEdit({ ...edit, new_password: e.target.value })}
              hint="Leave blank to keep the current password" />
            <label className="flex items-end gap-2 pb-2 text-sm">
              <input type="checkbox" className="h-4 w-4"
                checked={edit.is_active ?? editing.is_active}
                disabled={editing.id === me?.id}
                onChange={(e) => setEdit({ ...edit, is_active: e.target.checked })} />
              Active {editing.id === me?.id && '(cannot disable yourself)'}
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