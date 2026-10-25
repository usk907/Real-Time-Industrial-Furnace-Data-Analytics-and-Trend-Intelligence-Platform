import React from 'react';
import { FileSpreadsheet, Info, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export const Reports: React.FC = () => {
  const { tagList } = useAuth();

  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-8 shadow-xl max-w-3xl mx-auto text-center">
        <div className="p-4 rounded-2xl bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 inline-block mb-4">
          <FileSpreadsheet className="h-10 w-10 text-cyan-400" />
        </div>

        <h2 className="text-xl font-extrabold uppercase tracking-wider text-white">
          Automated Shift & Energy Reports
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Archived During 3-Tier Modular Refactor
        </p>

        <div className="bg-[#10162B] border border-[#1F2B50] rounded-xl p-6 text-left text-xs text-slate-300 mt-6 space-y-3">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-white">Data Access Available</p>
              <p className="text-slate-400 mt-0.5">
                Legacy PDF parsing and synthetic invoice reporting have been decoupled into <code className="text-cyan-400">legacy/server_archive/reports.py</code>.
                Time-series historical data for all 60 tags is available with raw, 1m, 5m, and 1h bucket aggregation directly in the <Link to="/trends" className="text-cyan-400 underline font-bold">Trends Analysis</Link> module.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 pt-3 border-t border-[#1F2B50]/60">
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-white">Live Monitoring Channels ({tagList.length} Active)</p>
              <p className="text-slate-400 mt-0.5">
                Active energy accumulators: <code className="text-emerald-400">Grid_Import_Cumulative_Energy</code>, <code className="text-emerald-400">EAF1_Cumulative_Energy</code>, <code className="text-emerald-400">LRF2_Cumulative_Energy</code>, <code className="text-emerald-400">RM1_Cumulative_Energy</code>, <code className="text-emerald-400">WTP_Cumulative_Energy</code>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
