import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { FileSpreadsheet, Plus, Download, Clock } from 'lucide-react';

interface ReportItem {
  id: number;
  created_at: string;
  name: string;
  report_type: string;
  format: string;
  file_path: string;
}

export const Reports: React.FC = () => {
  const { token } = useAuth();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [reportType, setReportType] = useState<string>('DAILY');
  const [format, setFormat] = useState<string>('CSV');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReports();
  }, [token]);

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/reports', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          report_type: reportType,
          format: format
        })
      });
      if (res.ok) {
        fetchReports();
      } else {
        const data = await res.json();
        setError(data.detail || 'Failed to generate report.');
      }
    } catch (e) {
      setError('Failed to generate report.');
    }
    setLoading(false);
  };

  const handleDownload = async (r: ReportItem) => {
    try {
      const res = await fetch(`/api/reports/download?file=${encodeURIComponent(r.name)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = r.name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        console.error("Failed to download report file from server");
      }
    } catch (e) {
      console.error("Error during report download:", e);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in text-xs font-semibold">
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Compiler Form */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Plus className="h-4.5 w-4.5 text-cyan-400" /> Compile Energy Audit
          </h4>

          <form onSubmit={handleGenerate} className="space-y-4">
            <div>
              <label className="block text-slate-400 mb-1.5 uppercase text-[9px] tracking-wider">Report Interval</label>
              <select 
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none"
              >
                <option value="DAILY">Daily Log (Current Load summary)</option>
                <option value="WEEKLY">Weekly Audit (Breaker / TG metrics)</option>
                <option value="MONTHLY">Monthly Ledger (Consumption history)</option>
                <option value="ENERGY">Energy Conservation Report</option>
                <option value="ALARM">Alarm History Analysis</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1.5 uppercase text-[9px] tracking-wider">File Format</label>
              <select 
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none"
              >
                <option value="CSV">CSV</option>
              </select>
            </div>

            <button 
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-extrabold py-3.5 rounded-xl uppercase tracking-wider transition-all shadow-lg shadow-blue-600/10"
            >
              {loading ? "Compiling..." : "Generate Report File"}
            </button>
          </form>

          {error && (
            <div className="rounded-xl border border-red-900/30 bg-red-950/20 p-3 text-xs text-red-400">
              {error}
            </div>
          )}
        </div>

        {/* Generated Reports List */}
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur flex flex-col justify-between">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <Clock className="h-4.5 w-4.5 text-cyan-400" /> Compiled Archives Log
          </h4>

          <div className="flex-1 overflow-y-auto max-h-64 space-y-2.5 pr-1">
            {reports.length === 0 ? (
              <div className="text-center py-16 text-slate-500 flex flex-col items-center gap-2">
                <FileSpreadsheet className="h-8 w-8 opacity-45" />
                <p>No compiled reports in archive folder.</p>
              </div>
            ) : (
              reports.map(r => (
                <div key={r.id} className="p-3.5 bg-[#131930] border border-[#1F2942]/45 rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-bold text-slate-200">{r.name}</p>
                    <p className="text-[9px] text-slate-500 mt-1 font-mono">
                      Type: {r.report_type} • Format: {r.format} • Compiled: {new Date(r.created_at).toLocaleString()}
                    </p>
                  </div>
                  <button 
                    onClick={() => handleDownload(r)}
                    className="p-2.5 rounded-xl bg-[#20294A] hover:bg-[#2F3D6C] border border-[#1F2942]/50 text-cyan-400"
                    title="Download File"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
