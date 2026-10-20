import React, { useState, useEffect } from 'react';
import { LogOut, Bell, User as UserIcon, Check, Server } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ServerSettingsModal } from './ServerSettingsModal';
import { getApiBaseUrl } from '../config';
import { NotificationItem } from '../types';

export const Header: React.FC = () => {
  const { user, logout, token } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isServerModalOpen, setIsServerModalOpen] = useState(false);
  const [tapStatus, setTapStatus] = useState<{ online: boolean; records: number; latency: number }>({
    online: true,
    records: 65000,
    latency: 24.5
  });
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const clockTimer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clockTimer);
  }, []);

  useEffect(() => {
    fetchTapStatus();
    const tapTimer = setInterval(fetchTapStatus, 5000);
    return () => clearInterval(tapTimer);
  }, []);

  const fetchTapStatus = async () => {
    try {
      const res = await fetch('/api/tap/status');
      if (res.ok) {
        const data = await res.json();
        setTapStatus({
          online: data.tap_server_online,
          records: data.total_sql_readings || 0,
          latency: data.metrics?.last_write_latency_ms || 25.0
        });
      }
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, [token]);

  const fetchNotifications = async () => {
    try {
      const res = await fetch('/api/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const markAsRead = async (id: number) => {
    try {
      const res = await fetch(`/api/notifications/${id}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchNotifications();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="h-20 border-b border-[#1F2942]/60 bg-[#0A0D1A]/90 backdrop-blur-md flex items-center justify-between px-8 relative z-10">
      <div>
        <h2 className="text-base font-extrabold uppercase tracking-widest text-slate-100 bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400">
          Industrial Energy Intelligence Platform
        </h2>
        <div className="flex items-center gap-3 mt-0.5">
          <p className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">Gary Steel Works • Blast Furnace-1 Section</p>
          <span className="text-slate-600 text-[10px]">•</span>
          <span className="text-[10px] text-slate-400 font-mono tracking-wider">
            {currentTime.toLocaleTimeString()} UTC
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* BACKEND SERVER SETTINGS PILL */}
        <button
          onClick={() => setIsServerModalOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#10162B] hover:bg-[#161F3D] border border-[#1F2B50] hover:border-cyan-500/50 shadow-inner transition-all group"
          title="Click to configure backend API connection or test latency"
        >
          <Server className="h-4 w-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          <div className="text-left leading-none">
            <p className="text-[9px] text-slate-400 uppercase font-bold tracking-wider">Backend Link</p>
            <p className="text-[11px] font-bold text-cyan-400 font-mono">
              {getApiBaseUrl() ? getApiBaseUrl().replace(/^https?:\/\//, '') : 'Local:8000'}
            </p>
          </div>
        </button>

        {/* TAP INGESTION SERVER LIVE PILL */}
        <div className="hidden lg:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-[#10162B] border border-[#1F2B50] shadow-inner">
          <span className={`h-2.5 w-2.5 rounded-full ${tapStatus.online ? 'bg-emerald-400 animate-pulse shadow-lg shadow-emerald-500/50' : 'bg-amber-400'}`} />
          <div className="text-left leading-none">
            <p className="text-[9px] text-slate-400 uppercase font-bold tracking-wider">TAP Ingest Server (:8001)</p>
            <p className="text-[11px] font-bold text-emerald-400 font-mono">
              {tapStatus.online ? `${tapStatus.records.toLocaleString()} rows • ${tapStatus.latency}ms` : 'Direct Fallback'}
            </p>
          </div>
        </div>

        {/* NOTIFICATIONS PANEL */}
        <div className="relative">
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="p-2.5 rounded-xl bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942]/50 text-slate-300 relative transition-all"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-600 rounded-full text-[10px] font-bold text-white flex items-center justify-center animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>

          {isOpen && (
            <div className="absolute right-0 mt-3 w-80 bg-[#101529] border border-[#1F2942] rounded-2xl shadow-2xl overflow-hidden z-30">
              <div className="p-4 border-b border-[#1F2942]/80 bg-[#151C36] flex justify-between items-center">
                <span className="font-bold text-xs text-white uppercase tracking-wider">Alerts & System Notices</span>
                <span className="text-[9px] bg-red-600 text-white font-bold px-2 py-0.5 rounded-full">{unreadCount} New</span>
              </div>
              <div className="max-h-60 overflow-y-auto divide-y divide-[#1F2942]/40 text-xs">
                {notifications.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">No recent alerts recorded.</p>
                ) : (
                  notifications.map(n => (
                    <div key={n.id} className={`p-3.5 hover:bg-[#151C36]/50 flex justify-between items-start gap-2.5 ${!n.read ? 'bg-[#151C36]/20' : ''}`}>
                      <div className="flex-1">
                        <p className={`font-semibold ${n.type === 'ALARM' ? 'text-red-400' : 'text-slate-300'}`}>{n.message}</p>
                        <p className="text-[9px] text-slate-500 mt-1 font-mono">{new Date(n.created_at).toLocaleTimeString()}</p>
                      </div>
                      {!n.read && (
                        <button 
                          onClick={() => markAsRead(n.id)}
                          className="p-1 rounded bg-[#20294A] hover:bg-[#2F3D6C] text-emerald-400"
                          title="Mark as read"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* USER PROFILE INFO */}
        <div className="flex items-center gap-4 border-l border-[#1F2942]/50 pl-6">
          <div className="text-right">
            <p className="text-xs font-bold text-slate-200">{user?.username}</p>
            <span className="text-[9px] bg-cyan-600/10 border border-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
              {user?.role}
            </span>
          </div>

          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-bold">
            <UserIcon className="h-5 w-5" />
          </div>

          <button 
            onClick={logout}
            className="p-2.5 rounded-xl bg-[#131930] hover:bg-red-950/20 hover:border-red-900/30 hover:text-red-400 border border-[#1F2942]/50 text-slate-400 transition-all duration-200"
            title="Sign Out"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>

      <ServerSettingsModal 
        isOpen={isServerModalOpen} 
        onClose={() => setIsServerModalOpen(false)} 
      />
    </header>
  );
};
