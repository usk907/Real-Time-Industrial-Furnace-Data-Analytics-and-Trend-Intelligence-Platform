import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Activity, 
  TrendingUp, 
  FileText, 
  Sliders, 
  Settings, 
  FileSpreadsheet,
  AlertTriangle,
  Users,
  Shield,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Zap
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (c: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const { user, connectionStatus } = useAuth();
  const location = useLocation();

  const isRole = (roles: string[]) => {
    return user && roles.includes(user.role);
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: Activity, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Live Monitoring', path: '/live', icon: Sliders, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Trend Analysis', path: '/trends', icon: TrendingUp, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Consumption Ledger', path: '/consumption', icon: Zap, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'AI Database Copilot', path: '/ai-query', icon: Sparkles, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Advanced Analytics', path: '/analytics', icon: FileText, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Alarms Console', path: '/alarms', icon: AlertTriangle, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator', 'Viewer'] },
    { name: 'Reports', path: '/reports', icon: FileSpreadsheet, roles: ['Admin', 'Plant Manager', 'Engineer', 'Operator'] },
    { name: 'Management', path: '/management', icon: Users, roles: ['Admin', 'Plant Manager'] },
    { name: 'Settings', path: '/settings', icon: Settings, roles: ['Admin', 'Plant Manager'] }
  ];

  return (
    <aside className={`bg-[#0F1424] border-r border-[#1F2942]/60 flex flex-col justify-between transition-all duration-300 ${collapsed ? 'w-20' : 'w-64'} h-screen z-20`}>
      <div>
        {/* LOGO */}
        <div className="flex items-center justify-between p-5 border-b border-[#1F2942]/50">
          <div className="flex items-center gap-3 overflow-hidden">
            <Shield className="h-6 w-6 text-cyan-400 animate-pulse flex-shrink-0" />
            {!collapsed && (
              <div>
                <h1 className="font-extrabold text-sm tracking-wider text-white bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-400">IEIP MONITOR</h1>
                <p className="text-[9px] text-[#556994] font-bold uppercase tracking-widest">Enterprise IoT</p>
              </div>
            )}
          </div>
          <button 
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded bg-[#1A233D] hover:bg-[#253258] text-slate-400 transition hidden md:block"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* NAVIGATION LINKS */}
        <nav className="p-4 space-y-1.5 mt-4">
          {navItems.map((item) => {
            if (!isRole(item.roles)) return null;
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.name}
                to={item.path}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive 
                    ? 'bg-gradient-to-r from-blue-600/20 to-cyan-600/10 border-l-4 border-cyan-400 text-cyan-300 font-semibold' 
                    : 'text-slate-400 hover:bg-[#1A233D] hover:text-slate-200'
                }`}
                title={collapsed ? item.name : ''}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                {!collapsed && <span className="text-xs tracking-wide">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* FOOTER AND CONNECTION STATUS */}
      <div className="p-4 border-t border-[#1F2942]/50 text-xs">
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'} p-2 rounded-lg bg-[#0A0D18]/60`}>
          <span className={`h-2.5 w-2.5 rounded-full ${connectionStatus === 'Connected' ? 'bg-emerald-500 animate-ping' : 'bg-red-500'}`} />
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Telemetry Link</p>
              <p className={`text-xs font-semibold ${connectionStatus === 'Connected' ? 'text-emerald-400' : 'text-red-400'}`}>{connectionStatus}</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
