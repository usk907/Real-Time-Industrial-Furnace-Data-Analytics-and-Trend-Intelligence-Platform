import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { CheckCircle2, RefreshCw, ShieldAlert } from 'lucide-react';
import { ServerAlarm, getAlarms, acknowledgeAlarm } from '../api/alarms';

export const Alarms: React.FC = () => {
  const { token, user } = useAuth();
  const [alarms, setAlarms] = useState<ServerAlarm[]>([]);
  const [filterActive, setFilterActive] = useState<string>('ACTIVE_ONLY');
  const [loading, setLoading] = useState<boolean>(false);
  const [ackLoading, setAckLoading] = useState<number | null>(null);

  const fetchAlarmData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const activeParam = filterActive === 'ACTIVE_ONLY' ? true : filterActive === 'RESOLVED_ONLY' ? false : undefined;
      const data = await getAlarms(activeParam, 100);
      setAlarms(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlarmData();
    const interval = setInterval(fetchAlarmData, 4000);
    return () => clearInterval(interval);
  }, [filterActive, token]);

  const handleAck = async (id: number) => {
    setAckLoading(id);
    try {
      await acknowledgeAlarm(id);
      await fetchAlarmData();
    } catch (e) {
      console.error(e);
    } finally {
      setAckLoading(null);
    }
  };

  const isAckPermitted = user && ['admin', 'manager', 'engineer', 'operator'].includes(user.role.toLowerCase());

  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      {/* Header and Filter */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 className="text-base font-extrabold uppercase tracking-wider text-white flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            <span>Industrial Alarm Management</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-Time Threshold Supervision & Incident Lifecycle Tracking
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-xl bg-[#10162B] border border-[#1F2B50] p-0.5">
            {[
              { id: 'ACTIVE_ONLY', label: 'Active Incidents' },
              { id: 'ALL', label: 'All Logs' },
              { id: 'RESOLVED_ONLY', label: 'Resolved' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setFilterActive(tab.id)}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
                  filterActive === tab.id
                    ? 'bg-cyan-500 text-slate-950 shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={fetchAlarmData}
            disabled={loading}
            className="p-2 rounded-xl bg-[#10162B] hover:bg-[#161F3D] border border-[#1F2B50] text-cyan-400"
            title="Refresh Alarms"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alarm Table */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#10162B] border-b border-[#1F2B50] text-slate-400 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Tag Channel</th>
                <th className="py-3 px-4">Trigger Value</th>
                <th className="py-3 px-4">Threshold</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Resolution</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2B50]/60 font-mono">
              {alarms.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500 font-sans">
                    No alarm incidents found for the selected view.
                  </td>
                </tr>
              ) : (
                alarms.map(alarm => {
                  const isResolved = Boolean(alarm.resolved_at);
                  const isCritical = alarm.severity === 'CRITICAL';

                  return (
                    <tr key={alarm.id} className="hover:bg-[#10162B]/50 transition-colors">
                      <td className="py-3 px-4 font-sans font-bold">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                            isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {alarm.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {new Date(alarm.ts).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-bold text-white font-sans">{alarm.tag}</td>
                      <td className="py-3 px-4 text-rose-400 font-bold">{alarm.value}</td>
                      <td className="py-3 px-4 text-slate-400">{alarm.threshold}</td>
                      <td className="py-3 px-4 font-sans">
                        {alarm.acknowledged ? (
                          <span className="text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            <span>Ack by {alarm.acknowledged_by || 'Staff'}</span>
                          </span>
                        ) : (
                          <span className="text-amber-400 font-bold animate-pulse">Unacknowledged</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">
                        {isResolved ? (
                          <span className="text-emerald-400">
                            Resolved ({new Date(alarm.resolved_at!).toLocaleTimeString()})
                          </span>
                        ) : (
                          <span className="text-red-400 font-bold">Active Breach</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        {!alarm.acknowledged && isAckPermitted ? (
                          <button
                            onClick={() => handleAck(alarm.id)}
                            disabled={ackLoading === alarm.id}
                            className="px-2.5 py-1 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 text-[11px] font-bold transition-all disabled:opacity-50"
                          >
                            {ackLoading === alarm.id ? 'Saving...' : 'Acknowledge'}
                          </button>
                        ) : alarm.acknowledged ? (
                          <span className="text-slate-500 text-[11px]">Acknowledged</span>
                        ) : (
                          <span className="text-slate-600 text-[11px]" title="Requires operator role">
                            Read Only
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
