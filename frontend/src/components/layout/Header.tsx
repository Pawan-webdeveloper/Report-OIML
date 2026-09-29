import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Badge } from '../ui/Badge';
import { ROLE_STYLES, titleCase } from '../../lib/status';
import { Button } from '../ui/Button';
import { IconLogout } from '../icons';

const TITLES: [RegExp, string][] = [
  [/^\/$/, 'Dashboard'],
  [/^\/change-password/, 'Change Password'],
  [/^\/evaluations/, 'Evaluations'],
  [/^\/instruments/, 'Instruments'],
  [/^\/tests/, 'Test Entry'],
  [/^\/reports/, 'Reports'],
  [/^\/admin\/users/, 'User Management'],
    [/^\/rulesets/, 'Rule Sets (OIML R 76)'],
  [/^\/audit/, 'Audit Log'],
];

function pageTitle(pathname: string): string {
  for (const [re, title] of TITLES) if (re.test(pathname)) return title;
  return 'NAWI Portal';
}

export default function Header() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const { pathname } = useLocation();

  async function onLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm md:px-6">
      <h1 className="text-base font-semibold text-slate-800">{pageTitle(pathname)}</h1>

      {user && (
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-slate-800">{user.full_name}</p>
            <p className="text-xs text-slate-500">@{user.username}</p>
          </div>
          <Badge label={titleCase(user.role)} className={ROLE_STYLES[user.role]} />
          <Button variant="ghost" onClick={onLogout} title="Log out" className="!px-2">
            <IconLogout />
          </Button>
        </div>
      )}
    </header>
  );
}