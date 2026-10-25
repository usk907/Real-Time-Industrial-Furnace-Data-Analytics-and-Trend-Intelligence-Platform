import React, { useState, useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import { TrendingUp, Download, BarChart2, RefreshCw } from 'lucide-react';

const EChartsWrapper: React.FC<{ options: any; className?: string; onChartRef?: (c: echarts.ECharts) => void }> = ({ options, className, onChartRef }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      chartRef.current = echarts.init(containerRef.current, 'dark', { renderer: 'svg' });
      onChartRef?.(chartRef.current);
    }
    const handleResize = () => chartRef.current?.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chartRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (chartRef.current && options) chartRef.current.setOption(options, true);
  }, [options]);

  return <div ref={containerRef} className={className || "w-full h-full"} />;
};

const DEVICES = [
  { id: 1, name: "CB5214 (Grid Input Power)", unit: "kW" },
  { id: 19, name: "SMS-1 Running Power", unit: "kW" },
  { id: 22, name: "SMS-4 Running Power", unit: "kW" },
  { id: 41, name: "TG-2 Generator Power", unit: "kW" },
  { id: 51, name: "SMS-1 Furnace Temperature", unit: "°C" },
  { id: 52, name: "SMS-1 Furnace Pressure", unit: "bar" },
  { id: 53, name: "SMS-1 Cooling Water Flow", unit: "m³/h" },
  { id: 54, name: "TG-2 Turbine RPM", unit: "RPM" },
  { id: 55, name: "CB5214 Voltage", unit: "V" },
  { id: 56, name: "CB5214 Current", unit: "A" }
];

export const Trends: React.FC = () => {
  const { token } = useAuth();
  const [selectedDevice, setSelectedDevice] = useState(1);
  const [selectedShift, setSelectedShift] = useState('All');
  const [quickFilter, setQuickFilter] = useState('1h');
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar' | 'scatter'>('line');
  const [compareMode, setCompareMode] = useState('none');
  const [loading, setLoading] = useState(false);
  const [chartRef, setChartRef] = useState<echarts.ECharts | null>(null);

  const [trendsData, setTrendsData] = useState<{ readings: any[]; statistics: any }>({
    readings: [],
    statistics: { avg: 0, min: 0, max: 0, median: 0, std_dev: 0, variance: 0, total_consumption: 0, running_hours: 0, downtime_hours: 0, efficiency: 0 }
  });
  const [compareReadings, setCompareReadings] = useState<any[]>([]);

  const activeDevice = useMemo(() => DEVICES.find(d => d.id === selectedDevice) || DEVICES[0], [selectedDevice]);

  const compareTarget = useMemo(() => {
    const map: Record<string, { id: number; label: string; unit: string }> = {
      mach_a_b: { id: selectedDevice === 19 ? 22 : 19, label: selectedDevice === 19 ? "SMS-4 Load" : "SMS-1 Load", unit: "kW" },
      volt_curr: { id: 56, label: "CB5214 Current", unit: "A" },
      power_temp: { id: 51, label: "SMS-1 Temperature", unit: "°C" }
    };
    return map[compareMode];
  }, [compareMode, selectedDevice]);

  useEffect(() => {
    let active = true;
    const fetchAll = async () => {
      setLoading(true);
      const shiftParam = selectedShift !== 'All' ? `&shift=${selectedShift}` : '';
      const headers = { 'Authorization': `Bearer ${token}` };
      try {
        const [res, compRes] = await Promise.all([
          fetch(`/api/trends?sensor_id=${selectedDevice}&quick_filter=${quickFilter}${shiftParam}`, { headers }),
          compareTarget ? fetch(`/api/trends?sensor_id=${compareTarget.id}&quick_filter=${quickFilter}${shiftParam}`, { headers }) : Promise.resolve(null)
        ]);
        if (!active) return;
        if (res.ok) setTrendsData(await res.json());
        if (compRes?.ok) setCompareReadings((await compRes.json()).readings);
        else setCompareReadings([]);
      } catch (e) {
        console.error(e);
      }
      if (active) setLoading(false);
    };
    fetchAll();
    return () => { active = false; };
  }, [selectedDevice, quickFilter, selectedShift, compareTarget, token]);

  const chartOption = useMemo(() => {
    const xAxisData = trendsData.readings.map(r => new Date(r.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    const isArea = chartType === 'area';
    const type = isArea ? 'line' : chartType;

    const series: any[] = [{
      name: activeDevice.name,
      type,
      data: trendsData.readings.map(r => r.value),
      smooth: true,
      showSymbol: trendsData.readings.length < 50,
      lineStyle: { width: 2.5, color: '#3B82F6' },
      itemStyle: { color: '#3B82F6' },
      areaStyle: isArea ? { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.3)' }, { offset: 1, color: 'transparent' }]) } : undefined
    }];

    if (compareTarget && compareReadings.length > 0) {
      series.push({
        name: compareTarget.label,
        type,
        data: compareReadings.map(r => r.value),
        smooth: true,
        showSymbol: compareReadings.length < 50,
        lineStyle: { width: 2.5, color: '#F59E0B' },
        itemStyle: { color: '#F59E0B' },
        yAxisIndex: ['volt_curr', 'power_temp'].includes(compareMode) ? 1 : 0,
        areaStyle: isArea ? { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245,158,11,0.3)' }, { offset: 1, color: 'transparent' }]) } : undefined
      });
    }

    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: '#0F1424', borderColor: '#1F2942', axisPointer: { type: 'cross', lineStyle: { color: '#3B82F6', type: 'dashed' } } },
      legend: { textStyle: { color: '#9CA3AF', fontSize: 10 } },
      grid: { left: '4%', right: '4%', bottom: '12%', top: '15%', containLabel: true },
      dataZoom: [{ type: 'inside' }, { type: 'slider', textStyle: { color: '#9CA3AF' }, handleColor: '#3B82F6' }],
      xAxis: { type: 'category', data: xAxisData, axisLabel: { color: '#9CA3AF', fontSize: 9 } },
      yAxis: [
        { type: 'value', name: activeDevice.unit, axisLabel: { color: '#9CA3AF', fontSize: 9 }, splitLine: { lineStyle: { color: '#1F2942' } } },
        { type: 'value', name: compareTarget?.unit || '', show: ['volt_curr', 'power_temp'].includes(compareMode), axisLabel: { color: '#9CA3AF', fontSize: 9 }, splitLine: { show: false } }
      ],
      series
    };
  }, [trendsData, compareReadings, activeDevice, compareTarget, chartType, compareMode]);

  const handleExportCSV = () => {
    const csv = ["Timestamp,Value", ...trendsData.readings.map(r => `${r.time},${r.value}`)].join("\n");
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: `trends_sensor_${selectedDevice}.csv` });
    a.click();
    URL.revokeObjectURL(url);
  };

  const s = trendsData.statistics;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Search & Filter Toolbar */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur grid grid-cols-1 md:grid-cols-5 gap-4 text-xs font-semibold">
        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Signal / Parameter</label>
          <select value={selectedDevice} onChange={e => setSelectedDevice(Number(e.target.value))} className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none">
            {DEVICES.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Work Shift</label>
          <select value={selectedShift} onChange={e => setSelectedShift(e.target.value)} className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none">
            {['All', 'Morning', 'Afternoon', 'Night'].map(s => <option key={s} value={s}>{s} {s === 'All' ? '(24 Hours)' : ''}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Comparison</label>
          <select value={compareMode} onChange={e => setCompareMode(e.target.value)} className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none">
            <option value="none">None</option>
            <option value="mach_a_b">SMS-1 vs SMS-4</option>
            <option value="volt_curr">Current vs Voltage</option>
            <option value="power_temp">Power vs Temp</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Time Window</label>
          <div className="flex gap-1.5">
            {['1h', '24h', '7d', '30d'].map(f => (
              <button key={f} onClick={() => setQuickFilter(f)} className={`flex-1 py-2.5 rounded-lg border font-bold text-center transition ${quickFilter === f ? 'bg-blue-600 border-blue-500 text-white' : 'bg-[#0D1227] border-[#1F2942]/60 text-slate-400'}`}>
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-end gap-2">
          <button onClick={handleExportCSV} className="flex-1 bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942] text-slate-200 py-3 rounded-xl flex items-center justify-center gap-2 transition">
            <Download className="h-4 w-4" /> CSV
          </button>
          <button onClick={() => chartRef?.dispatchAction({ type: 'dataZoom', start: 0, end: 100 })} className="p-3 bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942] text-slate-400 hover:text-white rounded-xl transition" title="Reset Zoom">
            <RefreshCw className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>

      {/* Main Chart + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur space-y-4 text-xs font-semibold">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-[#1F2942]/40 pb-3">
            <BarChart2 className="h-4 w-4 text-cyan-400" /> Stats Rollup
          </h4>
          <div className="divide-y divide-[#1F2942]/30 space-y-2.5">
            {[
              ["Average", `${s.avg?.toLocaleString()} ${activeDevice.unit}`],
              ["Minimum", `${s.min?.toLocaleString()} ${activeDevice.unit}`],
              ["Maximum", `${s.max?.toLocaleString()} ${activeDevice.unit}`],
              ["Median", `${s.median?.toLocaleString()} ${activeDevice.unit}`],
              ["Std Dev", s.std_dev?.toFixed(2)],
              ["Running Hours", `${s.running_hours} Hrs`, "text-cyan-400 font-bold"],
              ["Total Energy", `${Math.round(s.total_consumption || 0).toLocaleString()} kWh`, "text-blue-400 font-bold"],
              ["Efficiency", `${s.efficiency}%`, "text-emerald-400 font-bold"]
            ].map(([label, val, cls], i) => (
              <div key={i} className="flex justify-between pt-2.5">
                <span className="text-slate-400">{label}:</span>
                <span className={cls || "text-white"}>{val}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-[420px] backdrop-blur relative">
          {loading && (
            <div className="absolute inset-0 bg-[#0F1424]/75 backdrop-blur-sm flex items-center justify-center rounded-2xl z-10">
              <span className="text-cyan-400 font-bold uppercase tracking-widest animate-pulse">Loading telemetry...</span>
            </div>
          )}
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <TrendingUp className="h-4.5 w-4.5 text-blue-500" /> Interactive Plotter
            </h4>
            <div className="flex gap-1">
              {(['line', 'area', 'bar', 'scatter'] as const).map(t => (
                <button key={t} onClick={() => setChartType(t)} className={`px-3 py-1 rounded text-[10px] font-bold uppercase transition ${chartType === t ? 'bg-cyan-500 text-[#0F1424]' : 'bg-[#131930] text-slate-400 border border-[#1F2942]/60'}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[310px]">
            <EChartsWrapper options={chartOption} onChartRef={setChartRef} />
          </div>
        </div>
      </div>

      {/* Historical Log */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur">
        <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36]/50">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Historical Telemetry Log</h4>
        </div>
        <div className="max-h-60 overflow-y-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0A0E1A] text-[#556994] font-bold uppercase tracking-wider border-b border-[#1F2942]/50 text-[10px]">
                <th className="p-4 pl-6">Timestamp</th>
                <th className="p-4">Sensor ID</th>
                <th className="p-4">Parameter</th>
                <th className="p-4 text-right pr-6">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2942]/40 font-medium">
              {trendsData.readings.slice(-15).reverse().map((r, idx) => (
                <tr key={idx} className="hover:bg-[#151C36]/20 transition">
                  <td className="p-4 pl-6 font-mono text-slate-400">{new Date(r.time).toLocaleString()}</td>
                  <td className="p-4 font-mono text-[#556994]">#{selectedDevice}</td>
                  <td className="p-4 font-bold text-slate-200">{activeDevice.name}</td>
                  <td className="p-4 text-cyan-400 font-mono font-bold text-right pr-6">{r.value?.toLocaleString()} {activeDevice.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
