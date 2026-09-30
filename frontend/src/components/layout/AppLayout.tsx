import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

export default function AppLayout() {
  return (
    <div className="flex h-dvh min-h-[36rem] overflow-hidden bg-slate-100">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main id="main-content" className="flex-1 overflow-y-auto px-4 py-5 md:px-6 md:py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
