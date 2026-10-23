import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Calendar, 
  Clock, 
  Download, 
  UploadCloud, 
  TrendingUp, 
  DollarSign, 
  Leaf, 
  Activity, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  Search
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

const Sparkline: React.FC<SparklineProps> = ({ data, color = '#22d3ee', height = 24, width = 90 }) => {
  if (!data || data.length < 2) return <span className="text-slate-600 text-xs">—</span>;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((d, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((d - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible inline-block">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

export const Consumption: React.FC = () => {
  const { token } = useAuth();
  const [date, setDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [shift, setShift] = useState<string>('ALL');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // PDF Upload state
  const [uploadModalOpen, setUploadModalOpen] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const fetchConsumption = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `http://127.0.0.1:8000/api/consumption?date=${date}&shift=${shift}`;
      const res = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        throw new Error(`Failed to load consumption ledger (Status ${res.status})`);
      }
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error fetching energy consumption');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsumption();
  }, [date, shift]);

  const handlePdfUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadLoading(true);
    setUploadMessage(null);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/reports/import-pdf', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.detail || 'Failed to parse PDF report');
      }
      setUploadMessage(`Success: ${json.message}`);
      fetchConsumption();
    } catch (err: any) {
      setUploadMessage(`Error: ${err.message}`);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleExportCsv = () => {
    if (!data || !data.equipment_groups) return;

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Equipment Group,Type,Status,Tag Name,Register,Value,Unit,Min,Avg,Max\n";

    data.equipment_groups.forEach((group: any) => {
      group.tags.forEach((tag: any) => {
        csvContent += `"${group.group_name}","${group.equipment_type}","${group.status}","${tag.tag_name}","${tag.register}","${tag.value}","${tag.unit}","${tag.min_value}","${tag.avg_value}","${tag.max_value}"\n`;
      });
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Energy_Consumption_${date}_Shift_${shift}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredGroups = data?.equipment_groups?.map((group: any) => {
    const matchedTags = group.tags.filter((t: any) => 
      t.tag_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      group.group_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.unit.toLowerCase().includes(searchQuery.toLowerCase())
    );
    return { ...group, tags: matchedTags };
  }).filter((group: any) => group.tags.length > 0) || [];

  return (
    <div className="space-y-6">
      {/* HEADER BAR */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-[#0F1424] border border-[#1F2942]/80 p-5 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
              Daily Energy Consumption Ledger
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                PowerPlus Engine
              </span>
            </h1>
            <p className="text-xs text-slate-400">Cumulative unit meterings, shift breakdowns, and SCADA CrystalEView audits</p>
          </div>
        </div>

        {/* CONTROLS */}
        <div className="flex flex-wrap items-center gap-3">
          {/* DATE SELECTOR */}
          <div className="flex items-center gap-2 bg-[#141B2D] border border-[#232F4D] px-3 py-1.5 rounded-xl text-xs text-slate-300">
            <Calendar className="h-4 w-4 text-cyan-400" />
            <input 
              type="date" 
              value={date} 
              onChange={(e) => setDate(e.target.value)}
              className="bg-transparent border-none text-white focus:outline-none text-xs"
            />
          </div>

          {/* SHIFT PICKER */}
          <div className="flex items-center gap-1 bg-[#141B2D] border border-[#232F4D] p-1 rounded-xl text-xs">
            <Clock className="h-3.5 w-3.5 text-amber-400 ml-1.5 mr-0.5" />
            {[
              { id: 'ALL', label: 'All Day' },
              { id: 'A', label: 'Shift A (06-14)' },
              { id: 'B', label: 'Shift B (14-22)' },
              { id: 'C', label: 'Shift C (22-06)' }
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => setShift(s.id)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                  shift === s.id 
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* BUTTONS */}
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-semibold transition"
          >
            <UploadCloud className="h-4 w-4" />
            Import PDF Report
          </button>

          <button
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>

          <button
            onClick={fetchConsumption}
            disabled={loading}
            className="p-2 rounded-xl bg-[#141B2D] hover:bg-[#1C2640] border border-[#232F4D] text-slate-300 transition"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* SUMMARY KPI CARDS */}
      {data?.summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#0F1424] border border-[#1F2942] p-4 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl"></div>
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Total Active Energy</span>
              <Zap className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-white font-mono">
                {data.summary.total_active_kwh.toLocaleString()}
              </span>
              <span className="text-xs text-cyan-400 font-bold">kWh</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Total electricity delivered today</p>
          </div>

          <div className="bg-[#0F1424] border border-[#1F2942] p-4 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-xl"></div>
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Apparent / Reactive</span>
              <Activity className="h-4 w-4 text-purple-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-white font-mono">
                {data.summary.total_apparent_kvah.toLocaleString()}
              </span>
              <span className="text-xs text-purple-400 font-bold">kVAh</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Reactive: {data.summary.total_reactive_kvarh.toLocaleString()} kVArh</p>
          </div>

          <div className="bg-[#0F1424] border border-[#1F2942] p-4 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl"></div>
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Avg Power Factor & Peak</span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-emerald-400 font-mono">
                {data.summary.avg_power_factor}
              </span>
              <span className="text-xs text-slate-400">PF</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Peak Demand: {data.summary.peak_demand_kw.toLocaleString()} kW</p>
          </div>

          <div className="bg-[#0F1424] border border-[#1F2942] p-4 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl"></div>
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Cost & Footprint</span>
              <DollarSign className="h-4 w-4 text-amber-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-amber-400 font-mono">
                ₹{data.summary.estimated_cost_inr.toLocaleString()}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <Leaf className="h-3 w-3 text-emerald-400" />
              {data.summary.carbon_emissions_kg.toLocaleString()} kg CO₂
            </p>
          </div>
        </div>
      )}

      {/* SEARCH / FILTER BAR */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="h-4 w-4 absolute left-3.5 top-1/2 transform -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search tags, equipment, or units..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0F1424] border border-[#1F2942] rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
        </div>
        <div className="text-xs text-slate-400 font-medium">
          Showing <span className="text-cyan-400 font-bold">{filteredGroups.length}</span> Equipment Groups
        </div>
      </div>

      {/* ERROR & LOADING STATES */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-2xl text-red-400 text-xs flex items-center gap-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* EQUIPMENT GROUP PANELS */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-12 bg-[#0F1424] border border-[#1F2942] rounded-2xl">
          <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mb-3" />
          <p className="text-sm text-slate-400">Aggregating consumption ledger records...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredGroups.map((group: any) => (
            <div key={group.machine_id} className="bg-[#0F1424] border border-[#1F2942] rounded-2xl overflow-hidden shadow-lg">
              {/* SECTION HEADER */}
              <div className="bg-gradient-to-r from-[#141B2D] to-[#0F1424] px-5 py-3.5 border-b border-[#1F2942] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 rounded-full text-xs font-bold tracking-wide bg-amber-500/15 text-amber-400 border border-amber-500/30">
                    {group.group_name}
                  </span>
                  <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                    Type: {group.equipment_type}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${group.status === 'RUNNING' || group.status === 'ACTIVE' ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
                  <span className="text-xs text-slate-300 font-medium">{group.status}</span>
                </div>
              </div>

              {/* TABLE */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-[#090D18]/80 text-slate-400 border-b border-[#1F2942]/60 font-semibold">
                      <th className="py-3 px-5">Tag / Register Name</th>
                      <th className="py-3 px-4">Register Address</th>
                      <th className="py-3 px-4 text-right">Latest Reading</th>
                      <th className="py-3 px-4 text-center">4h Sparkline</th>
                      <th className="py-3 px-4 text-right">Min</th>
                      <th className="py-3 px-4 text-right">Avg</th>
                      <th className="py-3 px-4 text-right">Max</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1F2942]/40">
                    {group.tags.map((tag: any) => (
                      <tr key={tag.tag_id} className="hover:bg-[#141B2D]/50 transition-colors">
                        <td className="py-3 px-5 text-slate-200 font-medium">
                          {tag.tag_name}
                        </td>
                        <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                          {tag.register || '—'}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-cyan-300">
                          {tag.value.toLocaleString()} <span className="text-[10px] text-slate-500 font-normal">{tag.unit}</span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Sparkline data={tag.sparkline} color="#06b6d4" />
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-slate-400">
                          {tag.min_value}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-amber-300 font-medium">
                          {tag.avg_value}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-slate-400">
                          {tag.max_value}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}

          {filteredGroups.length === 0 && (
            <div className="text-center py-12 bg-[#0F1424] border border-[#1F2942] rounded-2xl text-slate-500 text-xs">
              No matching consumption tags found for this query.
            </div>
          )}
        </div>
      )}

      {/* PDF IMPORT MODAL */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-[#0F1424] border border-[#1F2942] rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#1F2942]">
              <div className="flex items-center gap-2 text-cyan-400 font-bold">
                <UploadCloud className="h-5 w-5" />
                <span>Import CrystalEView SCADA PDF Report</span>
              </div>
              <button 
                onClick={() => setUploadModalOpen(false)}
                className="text-slate-500 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Upload Daily or 15-Minute CrystalEView PDF export files. The PowerPlus extraction engine will automatically parse tabular columns, map headers to register tags, and store time-series records in the database.
            </p>

            <form onSubmit={handlePdfUpload} className="space-y-4">
              <div className="border-2 border-dashed border-[#1F2942] hover:border-cyan-500/50 rounded-xl p-6 text-center cursor-pointer transition">
                <input 
                  type="file" 
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/20 file:text-cyan-300 hover:file:bg-cyan-500/30"
                />
              </div>

              {selectedFile && (
                <div className="text-xs text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" />
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </div>
              )}

              {uploadMessage && (
                <div className={`p-3 rounded-xl text-xs ${uploadMessage.startsWith('Success') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                  {uploadMessage}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!selectedFile || uploadLoading}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  {uploadLoading && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
                  {uploadLoading ? 'Processing PDF...' : 'Upload & Process'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
