import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  LayoutDashboard, 
  Laptop, 
  AlertTriangle, 
  FileWarning, 
  Database, 
  Search, 
  Cpu, 
  History, 
  Settings, 
  LogOut,
  FileText
} from 'lucide-react';

export default function Sidebar() {
  const { logout, user, role } = useAuth();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Endpoints', path: '/endpoints', icon: Laptop },
    { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
    { name: 'Incidents', path: '/incidents', icon: FileWarning },
    { name: 'IOC Registry', path: '/iocs', icon: Database },
    { name: 'MITRE ATT&CK', path: '/mitre', icon: Search },
    { name: 'File Analysis', path: '/file-analysis', icon: Cpu },
    { name: 'Incident Reports', path: '/reports', icon: FileText },
    { name: 'Audit Logs', path: '/audit-logs', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-bgCard border-r border-borderDark flex flex-col h-screen select-none">
      {/* Top Header */}
      <div className="p-5 border-b border-borderDark flex items-center gap-3">
        <div className="p-2 bg-blue-500/10 border border-blue-500/30 rounded-lg text-accentBlue">
          <Shield size={20} />
        </div>
        <div>
          <h1 className="font-bold text-textPrimary text-sm tracking-wider">SENTINELX</h1>
          <p className="text-[10px] text-textSecondary uppercase tracking-wider font-semibold">EDR PLATFORM</p>
        </div>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition duration-150 ${
                  isActive 
                    ? 'bg-blue-500/15 border-l-2 border-accentBlue text-textPrimary' 
                    : 'text-textSecondary hover:bg-bgInput hover:text-textPrimary'
                }`
              }
            >
              <Icon size={16} />
              {item.name}
            </NavLink>
          );
        })}
      </div>

      {/* Current Analyst Profile */}
      <div className="p-4 border-t border-borderDark flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-500/10 border border-blue-500/30 flex items-center justify-center font-bold text-accentBlue text-xs">
            {user?.substring(0, 2).toUpperCase() || 'AN'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-textPrimary truncate">{user || 'Analyst'}</p>
            <p className="text-[10px] text-textSecondary truncate font-semibold uppercase">{role || 'analyst'}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center justify-center gap-2 w-full py-2 bg-bgInput hover:bg-accentRed/10 hover:text-accentRed border border-borderDark hover:border-accentRed/30 rounded-lg text-xs font-semibold text-textSecondary transition duration-150 cursor-pointer"
        >
          <LogOut size={14} />
          Log Out
        </button>
      </div>
    </div>
  );
}
