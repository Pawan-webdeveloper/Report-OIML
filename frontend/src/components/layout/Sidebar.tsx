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
}

const NAV: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <IconDashboard />, end: true },
  { to: '/evaluations', label: 'Evaluations', icon: <IconClipboard /> },
  { to: '/tests', label: 'Samples', icon: <IconFlask /> },
  { to: '/instruments', label: 'Instruments', icon: <IconScale /> },
  { to: '/reports', label: 'Reports', icon: <IconReport /> },
  { to: '/calibration', label: 'Calibration', icon: <IconFlask /> },
  { to: '/admin/users', label: 'Users', icon: <IconUsers />, roles: ['ADMIN'] },
  { to: '/settings', label: 'Settings', icon: <IconKey /> },
  { to: '/audit', label: 'Audit Trail', icon: <IconKey />, roles: ['ADMIN', 'REVIEWER'] },
];

export default function Sidebar() {
  const user = useAuthStore((s) => s.user);

  return (
    <aside className="hidden w-60 shrink-0 flex-col bg-teal-800 md:flex">
      <div className="flex min-h-16 items-center gap-3 px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8 text-white">
            <path d="M9 3L7 9H17L15 3H9Z" fill="currentColor" opacity="0.9"/>
            <path d="M7 9L5 15H19L17 9H7Z" fill="currentColor"/>
            <circle cx="12" cy="18" r="2" fill="currentColor"/>
            <path d="M10 21H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-lg font-bold tracking-tight text-white">LabTest</p>
          <p className="text-[10px] font-medium uppercase tracking-wider text-teal-200">Laboratory System</p>
        </div>
      </div>

      <nav aria-label="Primary navigation" className="flex-1 space-y-1 px-3 py-4">
        {NAV.filter((item) => !item.roles || (user && item.roles.includes(user.role))).map(
          (item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-teal-700 text-white shadow-sm'
                    : 'text-teal-100 hover:bg-teal-700/50 hover:text-white'
                }`
              }
            >
              <span className="flex h-5 w-5 items-center justify-center">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
            </NavLink>
          ),
        )}
      </nav>

      <div className="border-t border-teal-700 px-4 py-4">
        <button className="flex w-full items-center gap-2 text-xs font-medium text-teal-200 hover:text-white">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          Collapse
        </button>
      </div>
    </aside>
  );
}
