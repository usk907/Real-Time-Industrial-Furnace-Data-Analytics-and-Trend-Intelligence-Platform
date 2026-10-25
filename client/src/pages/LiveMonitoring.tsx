import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Layers } from 'lucide-react';

export const LiveMonitoring: React.FC = () => {
  const { tagList, connectionStatus } = useAuth();
  const [selectedEquipment, setSelectedEquipment] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const equipmentList = [
    'ALL',
    'Electric Arc Furnace 1',
    'Ladle Refining Furnace 2',
    'Main Substation',
    'Hot Rolling Mill',
    'Water Treatment & Utilities'
  ];

  const filteredTags = tagList.filter(tag => {
    const matchesEquipment =
      selectedEquipment === 'ALL' || tag.equipment === selectedEquipment;
    const matchesSearch =
      !searchQuery.trim() ||
      tag.tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (tag.equipment && tag.equipment.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesEquipment && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      {/* Header & Equipment Filter Tabs */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-extrabold uppercase tracking-wider text-white">
              Industrial SCADA Live Telemetry
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              60-Channel Industrial Sensor Matrix • Connected via Real-Time WebSocket Feed
            </p>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Search tags or units..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-[#10162B] border border-[#1F2B50] text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
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
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 mt-5 pt-4 border-t border-[#1F2B50]/60">
          {equipmentList.map(eq => (
            <button
              key={eq}
              onClick={() => setSelectedEquipment(eq)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedEquipment === eq
                  ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20'
                  : 'bg-[#10162B] text-slate-400 hover:text-white border border-[#1F2B50]'
              }`}
            >
              {eq === 'ALL' ? `All Channels (${tagList.length})` : eq}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of 60 Live Tags */}
      {filteredTags.length === 0 ? (
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-12 text-center text-slate-500">
          <Layers className="h-8 w-8 mx-auto mb-2 text-slate-600" />
          <p className="text-sm">No telemetry channels match your filter criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredTags.map(tag => {
            const isCritical = tag.status === 'CRITICAL';
            const isWarning = tag.status === 'WARNING';

            return (
              <div
                key={tag.tag}
                className={`bg-[#0C1021] border rounded-2xl p-4 shadow-lg transition-all ${
                  isCritical
                    ? 'border-red-500/80 bg-red-950/10'
                    : isWarning
                    ? 'border-amber-500/70 bg-amber-950/10'
                    : 'border-[#1F2B50] hover:border-cyan-500/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 truncate">
                      {tag.equipment || 'General Plant'}
                    </p>
                    <h4 className="text-xs font-extrabold text-white truncate mt-0.5" title={tag.tag}>
                      {tag.tag}
                    </h4>
                  </div>
                  <span
                    className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase ${
                      isCritical
                        ? 'bg-red-500 text-white animate-pulse'
                        : isWarning
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/10 text-emerald-400'
                    }`}
                  >
                    {tag.status}
                  </span>
                </div>

                <div className="mt-3 flex items-baseline gap-1.5">
                  <span className="text-xl font-black font-mono tracking-tight text-white">
                    {tag.value.toLocaleString()}
                  </span>
                  <span className="text-xs font-bold text-slate-400">{tag.unit}</span>
                </div>

                {tag.min !== undefined && tag.max !== undefined && (
                  <div className="mt-2 text-[10px] text-slate-500 font-mono flex justify-between">
                    <span>Min: {tag.min}</span>
                    <span>Max: {tag.max}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
