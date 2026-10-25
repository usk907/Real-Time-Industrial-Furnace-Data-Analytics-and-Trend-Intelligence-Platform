import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Zap, TrendingUp, DollarSign } from 'lucide-react';

export const Consumption: React.FC = () => {
  const { liveTags, connectionStatus } = useAuth();

  const gridKwh = liveTags['Grid_Import_Cumulative_Energy']?.value || 4892100;
  const eafKwh = liveTags['EAF1_Cumulative_Energy']?.value || 1284500;
  const lrfKwh = liveTags['LRF2_Cumulative_Energy']?.value || 642300;
  const rmKwh = liveTags['RM1_Cumulative_Energy']?.value || 894200;
  const wtpKwh = liveTags['WTP_Cumulative_Energy']?.value || 315400;

  // Approximate industrial cost at $0.095/kWh
  const tariffRate = 0.095;
  const totalCost = gridKwh * tariffRate;

  const energyAccounts = [
    {
      equipment: 'Main Substation Grid Import',
      tag: 'Grid_Import_Cumulative_Energy',
      kwh: gridKwh,
      share: '100%',
      rate: '$0.095 / kWh',
      cost: totalCost
    },
    {
      equipment: 'Electric Arc Furnace 1 (EAF-1)',
      tag: 'EAF1_Cumulative_Energy',
      kwh: eafKwh,
      share: `${Math.round((eafKwh / gridKwh) * 100)}%`,
      rate: '$0.095 / kWh',
      cost: eafKwh * tariffRate
    },
    {
      equipment: 'Ladle Refining Furnace 2 (LRF-2)',
      tag: 'LRF2_Cumulative_Energy',
      kwh: lrfKwh,
      share: `${Math.round((lrfKwh / gridKwh) * 100)}%`,
      rate: '$0.095 / kWh',
      cost: lrfKwh * tariffRate
    },
    {
      equipment: 'Hot Rolling Mill Stand 1',
      tag: 'RM1_Cumulative_Energy',
      kwh: rmKwh,
      share: `${Math.round((rmKwh / gridKwh) * 100)}%`,
      rate: '$0.095 / kWh',
      cost: rmKwh * tariffRate
    },
    {
      equipment: 'Industrial Water Treatment (WTP-1)',
      tag: 'WTP_Cumulative_Energy',
      kwh: wtpKwh,
      share: `${Math.round((wtpKwh / gridKwh) * 100)}%`,
      rate: '$0.095 / kWh',
      cost: wtpKwh * tariffRate
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      {/* Header */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 className="text-base font-extrabold uppercase tracking-wider text-white">
            Cumulative Energy Consumption & Ledger
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-Time Energy Meter Accumulators • Live Streaming via SCADA Generator
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#10162B] border border-[#1F2B50]">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              connectionStatus === 'Connected' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
            }`}
          />
          <span className="text-[11px] font-mono uppercase text-slate-300">
            {connectionStatus}
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Total Grid Cumulative Energy
            </span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <Zap className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono">
              {Math.round(gridKwh).toLocaleString()}
            </span>
            <span className="text-xs font-bold text-slate-400">kWh</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400">Substation Main Meter Account</p>
        </div>

        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              EAF-1 Specific Energy
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono">
              {Math.round(eafKwh).toLocaleString()}
            </span>
            <span className="text-xs font-bold text-slate-400">kWh</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400">Primary Electric Arc Furnace Load</p>
        </div>

        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Estimated Energy Cost
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <DollarSign className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono">
              ${Math.round(totalCost).toLocaleString()}
            </span>
            <span className="text-xs font-bold text-slate-400">USD</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400">Industrial Tariff @ $0.095/kWh</p>
        </div>
      </div>

      {/* Energy Breakdown Table */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl shadow-xl overflow-hidden">
        <div className="p-5 border-b border-[#1F2B50] bg-[#10162B]">
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">
            Subsystem Energy Allocation Matrix
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#10162B] border-b border-[#1F2B50] text-slate-400 font-bold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Subsystem / Equipment</th>
                <th className="py-3 px-4">Meter Tag</th>
                <th className="py-3 px-4 text-right">Cumulative (kWh)</th>
                <th className="py-3 px-4 text-right">Load Share</th>
                <th className="py-3 px-4 text-right">Estimated Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2B50]/60 font-mono">
              {energyAccounts.map(account => (
                <tr key={account.tag} className="hover:bg-[#10162B]/50 transition-colors">
                  <td className="py-3 px-4 font-sans font-bold text-white">
                    {account.equipment}
                  </td>
                  <td className="py-3 px-4 text-cyan-400">{account.tag}</td>
                  <td className="py-3 px-4 text-right font-bold text-white">
                    {Math.round(account.kwh).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-400 font-sans">
                    {account.share}
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-bold">
                    ${Math.round(account.cost).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
