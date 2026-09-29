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
    <aside className="hidden w-60 shrink-0 flex-col bg-primary-950 md:flex">
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 font-bold text-white">
          ⚖
        </div>
        <div>
          <p className="text-sm font-semibold text-white">NAWI Portal</p>
          <p className="text-xs text-primary-300">OIML R 76 · Legal Metrology</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.filter((item) => !item.roles || (user && item.roles.includes(user.role))).map(
          (item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-primary-700 text-white'
                    : 'text-primary-200 hover:bg-primary-900 hover:text-white'
                }`
              }
            >
              {item.icon}
              <span className="flex-1">{item.label}</span>
              {item.tag && (
                <span className="rounded bg-primary-800 px-1.5 py-0.5 text-[10px] font-semibold text-primary-200">
                  {item.tag}
                </span>
              )}
            </NavLink>
          ),
        )}
      </nav>

      <p className="px-5 py-4 text-[11px] text-primary-400">
        SIH26035 · Dept. of Consumer Affairs
      </p>
    </aside>
  );
}