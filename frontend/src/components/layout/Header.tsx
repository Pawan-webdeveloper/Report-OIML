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
    <header className="flex min-h-16 items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6 lg:px-8">
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-primary-700">OIML R 76</p>
        <h1 className="truncate text-base font-semibold tracking-tight text-slate-900">{pageTitle(pathname)}</h1>
      </div>

      {user && (
        <div className="ml-4 flex items-center gap-2 sm:gap-3">
          <div className="hidden text-right sm:block">
            <p className="max-w-40 truncate text-sm font-medium text-slate-800">{user.full_name}</p>
            <p className="font-mono text-[11px] text-slate-500">@{user.username}</p>
          </div>
          <Badge label={titleCase(user.role)} className={`${ROLE_STYLES[user.role]} hidden sm:inline-flex`} />
          <Button variant="ghost" onClick={onLogout} title="Log out" aria-label="Log out" className="!px-2.5">
            <IconLogout />
          </Button>
        </div>
      )}
    </header>
  );
}
