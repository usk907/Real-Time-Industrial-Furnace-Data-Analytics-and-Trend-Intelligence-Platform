import React from 'react';
import { Sparkles, Database, Info } from 'lucide-react';

export const AiQuery: React.FC = () => {
  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-8 shadow-xl max-w-3xl mx-auto text-center">
        <div className="p-4 rounded-2xl bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 inline-block mb-4">
          <Sparkles className="h-10 w-10 animate-pulse" />
        </div>

        <h2 className="text-xl font-extrabold uppercase tracking-wider text-white">
          AI Text-to-SQL Copilot
        </h2>
        <p className="text-sm text-cyan-400 font-bold mt-1">
          Archived & Paused During 3-Tier Modular Refactor
        </p>

        <div className="bg-[#10162B] border border-[#1F2B50] rounded-xl p-6 text-left text-xs text-slate-300 mt-6 space-y-3">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-white">Architecture Status</p>
              <p className="text-slate-400 mt-0.5">
                In accordance with the 3-Tier architectural refactor, external AI dependencies
                (Google Gemini & OpenAI LLM drivers) have been decoupled from the real-time SCADA server.
                The legacy implementation is preserved in <code className="text-cyan-400">legacy/server_archive/ai_copilot.py</code>.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 pt-3 border-t border-[#1F2B50]/60">
            <Database className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-white">Direct Live Telemetry Available</p>
              <p className="text-slate-400 mt-0.5">
                All 60 industrial furnace, turbine, and water channels are actively monitored and queryable
                via the <strong className="text-white">Dashboard</strong>, <strong className="text-white">Live Monitoring</strong>, and <strong className="text-white">Trends</strong> modules.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
