import React, { useState, useEffect } from 'react';
import { LogOut, Bell, User as UserIcon, Check, Server } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ServerSettingsModal } from './ServerSettingsModal';
import { getApiBase } from '../config';

export const Header: React.FC = () => {
  const { user, logout, token, connectionStatus, tagList } = useAuth();
  const [alarms, setAlarms] = useState<any[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isServerModalOpen, setIsServerModalOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const clockTimer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clockTimer);
  }, []);

  useEffect(() => {
    if (!token) return;
    fetchAlarms();
    const interval = setInterval(fetchAlarms, 8000);
    return () => clearInterval(interval);
  }, [token]);

  const fetchAlarms = async () => {
    try {
      const res = await fetch('/api/alarms?active=true&limit=10', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlarms(data);
      }
    } catch {
      // Fallback
    }
  };

  const acknowledgeAlarm = async (id: number) => {
    try {
      const res = await fetch(`/api/alarms/${id}/ack`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAlarms();
      }
    } catch {
      // Fallback
    }
  };

  const unacknowledgedCount = alarms.filter(a => !a.acknowledged).length;

  return (
    <header className="h-20 border-b border-[#1F2942]/60 bg-[#0A0D1A]/90 backdrop-blur-md flex items-center justify-between px-8 relative z-10">
      <div>
        <h2 className="text-base font-extrabold uppercase tracking-widest text-slate-100 bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400">
          Industrial Energy Intelligence Platform
        </h2>
        <div className="flex items-center gap-3 mt-0.5">
          <p className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest">
            Gary Steel Works • Blast Furnace Section
          </p>
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
              {getApiBase() ? getApiBase().replace(/^https?:\/\//, '') : '127.0.0.1:8000'}
            </p>
          </div>
        </button>

        {/* WEBSOCKET LIVE STATUS PILL */}
        <div className="hidden lg:flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-[#10162B] border border-[#1F2B50] shadow-inner">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              connectionStatus === 'Connected'
                ? 'bg-emerald-400 animate-pulse shadow-lg shadow-emerald-500/50'
                : connectionStatus === 'Connecting'
                ? 'bg-amber-400 animate-pulse shadow-lg shadow-amber-500/50'
                : 'bg-rose-500 shadow-lg shadow-rose-500/50'
            }`}
          />
          <div className="text-left leading-none">
            <p className="text-[9px] text-slate-400 uppercase font-bold tracking-wider">Live Stream (WS)</p>
            <p
              className={`text-[11px] font-bold font-mono ${
                connectionStatus === 'Connected'
                  ? 'text-emerald-400'
                  : connectionStatus === 'Connecting'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {connectionStatus === 'Connected'
                ? `${tagList.length || 60} Tags Active`
                : connectionStatus === 'Connecting'
                ? 'Reconnecting...'
                : 'Offline'}
            </p>
          </div>
        </div>

        {/* ALARMS NOTIFICATION BELL */}
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-2.5 rounded-xl bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942]/50 text-slate-300 relative transition-all"
            title="Active Alarms"
          >
            <Bell className="h-5 w-5" />
            {unacknowledgedCount > 0 && (
              <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-600 rounded-full text-[10px] font-bold text-white flex items-center justify-center animate-bounce">
                {unacknowledgedCount}
              </span>
            )}
          </button>

          {isOpen && (
            <div className="absolute right-0 mt-3 w-80 bg-[#101529] border border-[#1F2942] rounded-2xl shadow-2xl overflow-hidden z-30">
              <div className="p-4 border-b border-[#1F2942]/80 bg-[#151C36] flex justify-between items-center">
                <span className="font-bold text-xs text-white uppercase tracking-wider">Active Alarms</span>
                <span className="text-[9px] bg-red-600 text-white font-bold px-2 py-0.5 rounded-full">
                  {unacknowledgedCount} Unacked
                </span>
              </div>
              <div className="max-h-60 overflow-y-auto divide-y divide-[#1F2942]/40 text-xs">
                {alarms.length === 0 ? (
                  <p className="text-slate-500 text-center py-8">No active alarms recorded.</p>
                ) : (
                  alarms.map(a => (
                    <div
                      key={a.id}
                      className={`p-3.5 hover:bg-[#151C36]/50 flex justify-between items-start gap-2.5 ${
                        !a.acknowledged ? 'bg-[#151C36]/30' : ''
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                              a.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                            }`}
                          >
                            {a.severity}
                          </span>
                          <span className="font-semibold text-slate-200">{a.tag}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 font-mono">
                          Value: {a.value} • Limit: {a.threshold}
                        </p>
                        <p className="text-[9px] text-slate-500 mt-0.5 font-mono">
                          {new Date(a.ts).toLocaleTimeString()}
                        </p>
                      </div>
                      {!a.acknowledged && (
                        <button
                          onClick={() => acknowledgeAlarm(a.id)}
                          className="p-1 rounded bg-[#20294A] hover:bg-[#2F3D6C] text-emerald-400"
                          title="Acknowledge alarm"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* USER PROFILE & LOGOUT */}
        <div className="flex items-center gap-3 pl-2 border-l border-[#1F2942]/50">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-md">
              {user ? user.username.slice(0, 2).toUpperCase() : <UserIcon className="h-4 w-4" />}
            </div>
            <div className="hidden md:block text-left">
              <span className="block text-xs font-bold text-slate-200">{user?.username || 'Operator'}</span>
              <span className="block text-[10px] text-cyan-400 capitalize font-medium">{user?.role || 'Viewer'}</span>
            </div>
          </div>

          <button
            onClick={logout}
            className="p-2 rounded-xl bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942]/50 text-slate-400 hover:text-red-400 transition-all"
            title="Sign Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>

      <ServerSettingsModal isOpen={isServerModalOpen} onClose={() => setIsServerModalOpen(false)} />
    </header>
  );
};
