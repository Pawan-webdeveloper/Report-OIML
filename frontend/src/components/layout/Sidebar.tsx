import { NavLink } from 'react-router-dom';
import type { Role } from '../../types';
import { useAuthStore } from '../../store/authStore';
import {
  IconClipboard, IconDashboard, IconFlask, IconKey, IconReport, IconScale, IconUsers,
} from '../icons';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  roles?: Role[];
  end?: boolean;
  tag?: string;
}

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <IconDashboard />, end: true },
  { to: '/evaluations', label: 'Evaluations', icon: <IconClipboard /> },
  { to: '/instruments', label: 'Instruments', icon: <IconScale /> },
  { to: '/parties', label: 'Manufacturers', icon: <IconUsers /> },
  { to: '/reports', label: 'Reports', icon: <IconReport /> },
  { to: '/rulesets', label: 'Rule Sets', icon: <IconFlask /> },
  { to: '/audit', label: 'Audit Log', icon: <IconKey />, roles: ['ADMIN', 'REVIEWER'] },
  { to: '/admin/users', label: 'Users', icon: <IconUsers />, roles: ['ADMIN'] },
];

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);

  return (
    <aside className="hidden w-56 shrink-0 flex-col border-r border-white/10 bg-primary-950 md:flex lg:w-60">
      <div className="flex min-h-16 items-center gap-3 border-b border-white/10 px-4 lg:px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-md border border-primary-400/40 bg-white/5 font-mono text-[11px] font-bold tracking-tight text-primary-200">
          R76
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight text-white">NAWI Laboratory</p>
          <p className="truncate text-[11px] text-slate-400">Type evaluation console</p>
        </div>
      </div>

      <div className="px-4 pb-2 pt-5 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        Workspace
      </div>
      <nav aria-label="Primary navigation" className="flex-1 space-y-1 px-2.5">
        {NAV.filter((item) => !item.roles || (user && item.roles.includes(user.role))).map(
          (item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex min-h-10 items-center gap-3 rounded-md border-l-2 px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-primary-400 bg-white/10 text-white'
                    : 'border-transparent text-slate-300 hover:bg-white/[0.06] hover:text-white'
                }`
              }
            >
              {item.icon}
              <span className="flex-1">{item.label}</span>
              {item.tag && (
                <span className="rounded-sm bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold text-slate-300">
                  {item.tag}
                </span>
              )}
            </NavLink>
          ),
        )}
      </nav>

      <div className="border-t border-white/10 px-4 py-4 lg:px-5">
        <p className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Laboratory record</p>
        <p className="mt-1 text-[11px] leading-4 text-slate-400">SIH26035 · Consumer Affairs</p>
      </div>
    </aside>
  );
}
