import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FilePlus2, ListChecks, LogOut, Users,
  ShieldAlert, ActivityIcon, Settings2, PanelLeftClose, PanelLeftOpen
} from 'lucide-react';

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/solicitudes', label: 'Solicitudes', icon: ListChecks },
  { to: '/nueva-simulacion', label: 'Nueva simulación', icon: FilePlus2 },
  { to: '/clintes', label: 'Clientes', icon: Users },
  { to: '/riesgo', label: 'Riesgo', icon: ShieldAlert },
  { to: '/estados', label: 'Estados', icon: ActivityIcon },
  { to: '/ajustes', label: 'Ajustes', icon: Settings2 }
];

export default function Sidebar({ onLogout }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      <aside className={`
        hidden md:flex flex-col border-r border-white/10 bg-[rgba(0,0,51,1)]
        h-screen sticky top-0
        transition-all duration-300 ease-in-out
        ${collapsed? 'w-0 -translate-x-full opacity-0 overflow-hidden' : 'w-64 translate-x-0 opacity-100'}
      `}>
        {/* HEADER - FIJO */}
        <div className="flex items-center h-20 border-b border-white/10 px-4 gap-2 min-w-[16rem] shrink-0">
          <img
            src="/pacifico-blancos.png"
            alt="Inversiones Pacífico"
            className="h-20 w-auto object-contain flex-1"
          />
          <button
            onClick={() => setCollapsed(true)}
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20 transition"
            title="Ocultar menú"
          >
            <PanelLeftClose size={18} />
          </button>
        </div>

        {/* NAV - CON SCROLL */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1 min-w-[16rem] scrollbar-thin">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                  ? 'bg-[rgba(2,106,255,1)] text-white shadow-sm'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* LOGOUT - FIJO ABAJO, SIEMPRE VISIBLE */}
        <div className="shrink-0 p-3 border-t border-white/10 min-w-[16rem]">
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-white/70 hover:bg-white/10 hover:text-white transition"
          >
            <LogOut size={18} /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* BOTÓN FLOTANTE CUANDO ESTÁ OCULTO */}
      <button
        onClick={() => setCollapsed(false)}
        className={`
          hidden md:flex fixed top-4 left-4 z-50 p-2.5 rounded-xl
          bg-[rgba(0,0,51,1)] border border-white/20 text-white shadow-lg
          transition-all duration-300 ease-in-out
          ${collapsed? 'opacity-100 translate-x-0 scale-100' : 'opacity-0 -translate-x-10 scale-90 pointer-events-none'}
        `}
        title="Mostrar menú"
      >
        <PanelLeftOpen size={20} />
      </button>
    </>
  );
}