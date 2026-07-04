import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Settings as SettingsIcon, BookOpen } from 'lucide-react';

interface AuditLogItem {
  id: number;
  time: string;
  user_id?: number;
  action: string;
  details?: string;
  ip_address?: string;
}

export const Settings: React.FC = () => {
  const { token } = useAuth();
  
  // Settings limits state
  const [breakerLimit, setBreakerLimit] = useState(45000);
  const [tgLimit, setTgLimit] = useState(30000);
  const [smsLimit, setSmsLimit] = useState(95000);
  const [samplingRate, setSamplingRate] = useState(1);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    fetchSettings();
    fetchAuditLogs();
  }, [token]);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        // Array of key values
        const breaker = data.find((s: any) => s.key === 'alarm_threshold_breaker_max')?.value;
        const tg = data.find((s: any) => s.key === 'alarm_threshold_tg_max')?.value;
        const sms = data.find((s: any) => s.key === 'alarm_threshold_sms_max')?.value;
        const rate = data.find((s: any) => s.key === 'sampling_interval_seconds')?.value;

        if (breaker) setBreakerLimit(parseFloat(breaker));
        if (tg) setTgLimit(parseFloat(tg));
        if (sms) setSmsLimit(parseFloat(sms));
        if (rate) setSamplingRate(parseInt(rate));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch('/api/audit-logs', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setAuditLogs(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(false);
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          alarm_threshold_breaker_max: breakerLimit,
          alarm_threshold_tg_max: tgLimit,
          alarm_threshold_sms_max: smsLimit,
          sampling_interval_seconds: samplingRate
        })
      });
      if (res.ok) {
        setSaveSuccess(true);
        fetchAuditLogs();
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-xs font-semibold">
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Settings Limits Form */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-[#1F2942]/45 pb-3">
            <SettingsIcon className="h-4.5 w-4.5 text-cyan-400" /> Threshold Parameters
          </h4>

          <form onSubmit={handleSave} className="space-y-4">
            {saveSuccess && (
              <div className="p-3 bg-emerald-950/20 border border-emerald-900/30 text-emerald-450 rounded-xl">
                Configuration parameters updated successfully.
              </div>
            )}

            <div>
              <label className="block text-slate-450 mb-1.5 uppercase text-[9px] tracking-wider">Breaker Capacity Limit (CB5214 kW)</label>
              <input 
                type="number" 
                required
                value={breakerLimit} 
                onChange={(e) => setBreakerLimit(parseFloat(e.target.value))} 
                className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-200 focus:outline-none" 
              />
            </div>

            <div>
              <label className="block text-slate-450 mb-1.5 uppercase text-[9px] tracking-wider">Turbine Max Power (30MW TG-2 kW)</label>
              <input 
                type="number" 
                required
                value={tgLimit} 
                onChange={(e) => setTgLimit(parseFloat(e.target.value))} 
                className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-200 focus:outline-none" 
              />
            </div>

            <div>
              <label className="block text-slate-450 mb-1.5 uppercase text-[9px] tracking-wider">SMS Max Combine Load (SMS-1 + SMS-4 kW)</label>
              <input 
                type="number" 
                required
                value={smsLimit} 
                onChange={(e) => setSmsLimit(parseFloat(e.target.value))} 
                className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-200 focus:outline-none" 
              />
            </div>

            <div>
              <label className="block text-slate-450 mb-1.5 uppercase text-[9px] tracking-wider">Modbus Polling Sampling Interval (s)</label>
              <input 
                type="number" 
                required
                value={samplingRate} 
                onChange={(e) => setSamplingRate(parseInt(e.target.value))} 
                className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-200 focus:outline-none" 
              />
            </div>

            <button 
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-extrabold py-3.5 rounded-xl uppercase tracking-wider transition-all shadow-lg shadow-blue-600/10"
            >
              Update Config Thresholds
            </button>
          </form>
        </div>

        {/* Audit Log Table Column */}
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur flex flex-col justify-between">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 mb-4 border-b border-[#1F2942]/45 pb-3">
            <BookOpen className="h-4.5 w-4.5 text-cyan-400" /> Operational System Audit Trail
          </h4>

          <div className="flex-1 overflow-y-auto max-h-96 space-y-2.5 pr-1">
            {auditLogs.length === 0 ? (
              <p className="text-slate-500 text-center py-12">No audit actions recorded.</p>
            ) : (
              <div className="space-y-2 text-xs">
                {auditLogs.map(log => (
                  <div key={log.id} className="p-3.5 bg-[#131930] border border-[#1F2942]/45 rounded-xl flex justify-between items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-cyan-400 font-mono uppercase text-[10px]">{log.action}</span>
                        <span className="text-[9px] text-slate-500 font-mono">{new Date(log.time).toLocaleString()}</span>
                      </div>
                      <p className="text-slate-350 mt-1">{log.details}</p>
                    </div>
                    {log.ip_address && (
                      <span className="text-[9px] bg-[#1F2942]/50 text-slate-400 font-mono px-2 py-0.5 rounded">
                        IP: {log.ip_address}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
