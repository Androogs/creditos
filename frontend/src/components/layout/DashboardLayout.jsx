import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function DashboardLayout() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex bg-slate-50">
      <Sidebar onLogout={() => { localStorage.removeItem('uw_auth'); navigate('/login'); }} />
      <div className="flex-1 flex flex-col min-w-0">
        <Outlet />
      </div>
    </div>
  );
}
