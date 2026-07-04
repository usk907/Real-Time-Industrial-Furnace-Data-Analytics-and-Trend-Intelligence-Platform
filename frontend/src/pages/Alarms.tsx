import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Filter } from 'lucide-react';

interface AlarmItem {
  id: number;
  time: string;
  end_time?: string;
  sensor_id: number;
  alarm_type: string;
  severity: string;
  trigger_value: number;
  status: string;
  acknowledged_by?: string;
  comments?: string;
}

export const Alarms: React.FC = () => {
  const { token, user } = useAuth();
  const [alarms, setAlarms] = useState<AlarmItem[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [ackComment, setAckComment] = useState<string>('');
  const [selectedAlarmId, setSelectedAlarmId] = useState<number | null>(null);

  useEffect(() => {
    fetchAlarms();
    const interval = setInterval(fetchAlarms, 3000);
    return () => clearInterval(interval);
  }, [token, filterSeverity, filterStatus]);

  const fetchAlarms = async () => {
    try {
      let query = '';
      if (filterSeverity !== 'ALL') query += `severity=${filterSeverity}&`;
      if (filterStatus !== 'ALL') query += `status=${filterStatus}&`;
      
      const res = await fetch(`/api/alarms?${query}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlarms(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAcknowledge = async (id: number) => {
    if (!ackComment) return;
    try {
      const res = await fetch(`/api/alarms/${id}/acknowledge`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          acknowledged_by: user?.username || 'engineer_default',
          comments: ackComment
        })
      });
      if (res.ok) {
        setAckComment('');
        setSelectedAlarmId(null);
        fetchAlarms();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-xs font-semibold">
      
      {/* Filters Toolbar */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2 text-slate-400">
          <Filter className="h-4.5 w-4.5" />
          <span>Filters:</span>
        </div>
        
        <div>
          <label className="block text-slate-500 mb-1.5 uppercase text-[9px] tracking-wider">Severity</label>
          <select 
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-[#0D1227] border border-[#1F2942]/60 rounded-lg p-2 text-slate-300 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical Alerts</option>
            <option value="WARNING">Warnings</option>
            <option value="INFO">Info Logs</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-500 mb-1.5 uppercase text-[9px] tracking-wider">Operational Status</label>
          <select 
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-[#0D1227] border border-[#1F2942]/60 rounded-lg p-2 text-slate-300 focus:outline-none"
          >
            <option value="ALL">All States</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="CLEARED">CLEARED</option>
          </select>
        </div>
      </div>

      {/* Main Alarms Grid */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur">
        <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36]/50">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Alarms logs database</h4>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0A0E1A] text-[#556994] font-bold uppercase tracking-wider border-b border-[#1F2942]/50 text-[10px]">
                <th className="p-4 pl-6">ID</th>
                <th className="p-4">Time Triggered</th>
                <th className="p-4">Anomaly Event</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Trigger Value</th>
                <th className="p-4">Operational Status</th>
                <th className="p-4">Assigned Inspector</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2942]/40 font-medium">
              {alarms.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-slate-500">
                    No matching alarms recorded in current log window.
                  </td>
                </tr>
              ) : (
                alarms.map(a => (
                  <tr key={a.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{a.id}</td>
                    <td className="p-4 text-slate-400 font-mono">
                      {new Date(a.time).toLocaleString()}
                    </td>
                    <td className="p-4 font-bold text-slate-200">{a.alarm_type}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        a.severity === 'CRITICAL' 
                          ? 'bg-red-950/30 text-red-400 border border-red-900/40' 
                          : 'bg-amber-950/30 text-amber-400 border border-amber-900/40'
                      }`}>
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-bold text-cyan-400">
                      {a.trigger_value ? Math.round(a.trigger_value).toLocaleString() : '-'}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        a.status === 'ACTIVE' 
                          ? 'bg-red-950/20 text-red-400 animate-pulse' 
                          : (a.status === 'ACKNOWLEDGED' ? 'bg-blue-950/20 text-blue-400' : 'bg-emerald-950/20 text-emerald-400')
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-4 text-slate-400">
                      {a.acknowledged_by || (a.status === 'ACTIVE' ? 'Shift Engineer Contact' : '-')}
                    </td>
                    <td className="p-4 pr-6 text-right">
                      {a.status === 'ACTIVE' ? (
                        <div>
                          {selectedAlarmId === a.id ? (
                            <div className="flex items-center gap-1.5 justify-end">
                              <input 
                                type="text"
                                placeholder="Log check remarks"
                                value={ackComment}
                                onChange={(e) => setAckComment(e.target.value)}
                                className="bg-[#0D1227] border border-[#1F2942] rounded px-2.5 py-1 text-slate-200 focus:outline-none"
                              />
                              <button 
                                onClick={() => handleAcknowledge(a.id)}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 rounded"
                              >
                                Submit
                              </button>
                            </div>
                          ) : (
                            <button 
                              onClick={() => setSelectedAlarmId(a.id)}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg font-bold"
                            >
                              ACK
                            </button>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-500 font-bold italic">{a.comments || 'Checked'}</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
