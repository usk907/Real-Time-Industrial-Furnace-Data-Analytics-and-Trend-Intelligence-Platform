import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import { 
  TrendingUp, 
  Download, 
  BarChart2, 
  RefreshCw 
} from 'lucide-react';

const EChartsWrapper: React.FC<{ options: any; className?: string; onChartRef?: (c: echarts.ECharts) => void }> = ({ options, className, onChartRef }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      chartRef.current = echarts.init(containerRef.current, 'dark', { renderer: 'svg' });
      if (onChartRef) onChartRef(chartRef.current);
    }
    const handleResize = () => chartRef.current?.resize();
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      chartRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (chartRef.current && options) {
      chartRef.current.setOption(options, true);
    }
  }, [options]);

  return <div ref={containerRef} className={className || "w-full h-full"} />;
};

export const Trends: React.FC = () => {
  const { token } = useAuth();
  const [selectedDevice, setSelectedDevice] = useState<number>(1); // Default to CB5214 kW
  const [selectedShift, setSelectedShift] = useState<string>('All');
  const [quickFilter, setQuickFilter] = useState<string>('1h');
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar' | 'scatter'>('line');
  const [compareMode, setCompareMode] = useState<string>('none'); // none, today_yesterday, mach_a_b, volt_curr, power_temp
  const [loading, setLoading] = useState(false);
  const [chartRef, setChartRef] = useState<echarts.ECharts | null>(null);

  const [trendsData, setTrendsData] = useState<any>({
    readings: [],
    statistics: {
      avg: 22860.0, min: 22700.0, max: 23100.0, median: 22850.0, std_dev: 90.0, variance: 8100.0,
      total_consumption: 22860.0, running_hours: 1.0, downtime_hours: 0.0, efficiency: 100.0
    }
  });

  // Secondary stream for comparisons
  const [compareReadings, setCompareReadings] = useState<any[]>([]);
  const [compareLabel, setCompareLabel] = useState<string>('');

  const devicesList = [
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

  useEffect(() => {
    fetchTrends();
  }, [selectedDevice, quickFilter, selectedShift, compareMode]);

  const fetchTrends = async () => {
    setLoading(true);
    try {
      // 1. Fetch primary target
      const res = await fetch(`/api/trends?sensor_id=${selectedDevice}&quick_filter=${quickFilter}${selectedShift !== 'All' ? `&shift=${selectedShift}` : ''}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTrendsData(data);
      }

      // 2. Handle comparison calls
      if (compareMode !== 'none') {
        let compareId = selectedDevice;
        let label = '';
        
        if (compareMode === 'mach_a_b') {
          compareId = selectedDevice === 19 ? 22 : 19;
          label = compareId === 19 ? "SMS-1 Load" : "SMS-4 Load";
        } else if (compareMode === 'volt_curr') {
          compareId = 56; // Current
          label = "CB5214 Current (A)";
        } else if (compareMode === 'power_temp') {
          compareId = 51; // Temp
          label = "SMS-1 Temperature (°C)";
        }

        const compRes = await fetch(`/api/trends?sensor_id=${compareId}&quick_filter=${quickFilter}${selectedShift !== 'All' ? `&shift=${selectedShift}` : ''}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (compRes.ok) {
          const compData = await compRes.json();
          setCompareReadings(compData.readings);
          setCompareLabel(label || `Compare Device #${compareId}`);
        }
      } else {
        setCompareReadings([]);
        setCompareLabel('');
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const primaryLabel = devicesList.find(d => d.id === selectedDevice)?.name || "Target Device";
  const primaryUnit = devicesList.find(d => d.id === selectedDevice)?.unit || "";

  // Prepare chart series
  const xAxisData = trendsData.readings.map((r: any) => {
    return new Date(r.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  });

  const seriesData = trendsData.readings.map((r: any) => r.value);
  const compSeriesData = compareReadings.map((r: any) => r.value);

  const seriesOptions: any[] = [
    {
      name: primaryLabel,
      type: chartType === 'area' ? 'line' : chartType,
      data: seriesData,
      smooth: true,
      showSymbol: trendsData.readings.length < 50,
      lineStyle: { width: 2.5, color: '#3B82F6' },
      itemStyle: { color: '#3B82F6' },
      areaStyle: chartType === 'area' ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0)' }
        ])
      } : null
    }
  ];

  if (compareMode !== 'none' && compareReadings.length > 0) {
    seriesOptions.push({
      name: compareLabel,
      type: chartType === 'area' ? 'line' : chartType,
      data: compSeriesData,
      smooth: true,
      showSymbol: compareReadings.length < 50,
      lineStyle: { width: 2.5, color: '#F59E0B' },
      itemStyle: { color: '#F59E0B' },
      yAxisIndex: compareMode === 'volt_curr' || compareMode === 'power_temp' ? 1 : 0, // Dual axis support
      areaStyle: chartType === 'area' ? {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
          { offset: 1, color: 'rgba(245, 158, 11, 0)' }
        ])
      } : null
    });
  }

  // Create ECharts option structure
  const option = {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: '#0F1424', 
      borderColor: '#1F2942', 
      axisPointer: { type: 'cross', lineStyle: { color: '#3B82F6', type: 'dashed' } } 
    },
    legend: { textStyle: { color: '#9CA3AF', fontSize: 10 } },
    grid: { left: '4%', right: '4%', bottom: '12%', top: '15%', containLabel: true },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, textStyle: { color: '#9CA3AF' }, handleColor: '#3B82F6', lineStyle: { color: '#1F2942' } }
    ],
    xAxis: { type: 'category', data: xAxisData, axisLabel: { color: '#9CA3AF', fontSize: 9 } },
    yAxis: [
      { type: 'value', name: primaryUnit, axisLabel: { color: '#9CA3AF', fontSize: 9 }, splitLine: { lineStyle: { color: '#1F2942' } } },
      // Secondary yAxis for dual scale comparisons
      { 
        type: 'value', 
        name: compareMode === 'volt_curr' ? 'A' : (compareMode === 'power_temp' ? '°C' : ''), 
        show: compareMode === 'volt_curr' || compareMode === 'power_temp', 
        axisLabel: { color: '#9CA3AF', fontSize: 9 },
        splitLine: { show: false } 
      }
    ],
    series: seriesOptions
  };

  // Client-Side CSV/Excel generation download
  const handleExportCSV = () => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Timestamp,Value\n";
    trendsData.readings.forEach((r: any) => {
      csvContent += `${r.time},${r.value}\n`;
    });
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ieip_trends_sensor_${selectedDevice}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleResetZoom = () => {
    if (chartRef) {
      chartRef.dispatchAction({
        type: 'dataZoom',
        start: 0,
        end: 100
      });
    }
  };

  const s = trendsData.statistics;

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Search and filter toolbar */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur grid grid-cols-1 md:grid-cols-5 gap-4 text-xs font-semibold">
        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Select Signal / Parameter</label>
          <select 
            value={selectedDevice} 
            onChange={(e) => setSelectedDevice(parseInt(e.target.value))}
            className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none"
          >
            {devicesList.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Work Shift Filter</label>
          <select 
            value={selectedShift} 
            onChange={(e) => setSelectedShift(e.target.value)}
            className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none"
          >
            <option value="All">All Shifts (24 Hours)</option>
            <option value="Morning">Morning (06:00 - 14:00)</option>
            <option value="Afternoon">Afternoon (14:00 - 22:00)</option>
            <option value="Night">Night (22:00 - 06:00)</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">Compare Analytics</label>
          <select 
            value={compareMode} 
            onChange={(e) => setCompareMode(e.target.value)}
            className="w-full bg-[#0D1227] border border-[#1F2942]/60 rounded-xl p-3 text-slate-200 focus:outline-none"
          >
            <option value="none">Disable Comparisons</option>
            <option value="mach_a_b">Compare Machines (SMS-1 vs SMS-4)</option>
            <option value="volt_curr">Overlay Current vs Voltage</option>
            <option value="power_temp">Compare Power vs Temperature</option>
          </select>
        </div>

        <div>
          <label className="block text-slate-400 mb-1.5 uppercase tracking-wider text-[10px]">History Window</label>
          <div className="flex gap-1.5">
            {['1h', '24h', '7d', '30d'].map(f => (
              <button 
                key={f}
                onClick={() => setQuickFilter(f)}
                className={`flex-1 py-2.5 rounded-lg border font-bold text-center transition ${quickFilter === f ? 'bg-blue-600 border-blue-500 text-white' : 'bg-[#0D1227] border-[#1F2942]/60 text-slate-400'}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-end gap-2">
          <button 
            onClick={handleExportCSV}
            className="flex-1 bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942] text-slate-200 py-3 rounded-xl flex items-center justify-center gap-2 transition"
          >
            <Download className="h-4 w-4" /> Export CSV
          </button>
          <button 
            onClick={handleResetZoom}
            className="p-3 bg-[#131930] hover:bg-[#1E2749] border border-[#1F2942] text-slate-400 hover:text-white rounded-xl transition"
            title="Reset Zoom"
          >
            <RefreshCw className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>

      {/* Main Chart Card */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Statistics panel */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur space-y-4 text-xs font-semibold">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 border-b border-[#1F2942]/40 pb-3">
            <BarChart2 className="h-4 w-4 text-cyan-400" /> Stats Rollup
          </h4>

          <div className="divide-y divide-[#1F2942]/30 space-y-2.5">
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Mean Average:</span>
              <span className="text-white">{s.avg.toLocaleString()} {primaryUnit}</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Minimum Logged:</span>
              <span className="text-white">{s.min.toLocaleString()} {primaryUnit}</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Maximum Logged:</span>
              <span className="text-white">{s.max.toLocaleString()} {primaryUnit}</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Median Value:</span>
              <span className="text-white">{s.median.toLocaleString()} {primaryUnit}</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Standard Deviation:</span>
              <span className="text-white">{s.std_dev.toFixed(2)}</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Running Hours:</span>
              <span className="text-cyan-400 font-bold">{s.running_hours} Hrs</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Total Consumption:</span>
              <span className="text-blue-400 font-bold">{Math.round(s.total_consumption).toLocaleString()} kWh</span>
            </div>
            <div className="flex justify-between pt-2.5">
              <span className="text-slate-400">Efficiency Score:</span>
              <span className="text-emerald-400 font-bold">{s.efficiency}%</span>
            </div>
          </div>
        </div>

        {/* ECharts Area */}
        <div className="lg:col-span-3 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-[420px] backdrop-blur relative">
          {loading && (
            <div className="absolute inset-0 bg-[#0F1424]/75 backdrop-blur-sm flex items-center justify-center rounded-2xl z-10">
              <span className="text-cyan-400 font-bold uppercase tracking-widest animate-pulse">Querying InfluxDB...</span>
            </div>
          )}
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <TrendingUp className="h-4.5 w-4.5 text-blue-500" /> Interactive Plotter
            </h4>
            <div className="flex gap-1">
              {['line', 'area', 'bar', 'scatter'].map(t => (
                <button
                  key={t}
                  onClick={() => setChartType(t as any)}
                  className={`px-3 py-1 rounded text-[10px] font-bold uppercase transition ${chartType === t ? 'bg-cyan-500 text-[#0F1424]' : 'bg-[#131930] text-slate-400 border border-[#1F2942]/60'}`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="h-[310px]">
            <EChartsWrapper options={option} onChartRef={(c) => setChartRef(c)} />
          </div>
        </div>
      </div>

      {/* Historical Data Table */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur">
        <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36]/50">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Historical readings query log</h4>
        </div>
        <div className="max-h-60 overflow-y-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0A0E1A] text-[#556994] font-bold uppercase tracking-wider border-b border-[#1F2942]/50 text-[10px]">
                <th className="p-4 pl-6">Timestamp</th>
                <th className="p-4">Sensor ID</th>
                <th className="p-4">Parameter Name</th>
                <th className="p-4 text-right pr-6">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2942]/40 font-medium">
              {trendsData.readings.slice(-15).reverse().map((r: any, idx: number) => (
                <tr key={idx} className="hover:bg-[#151C36]/20 transition">
                  <td className="p-4 pl-6 font-mono text-slate-400">{new Date(r.time).toLocaleString()}</td>
                  <td className="p-4 font-mono text-[#556994]">#{selectedDevice}</td>
                  <td className="p-4 font-bold text-slate-200">{primaryLabel}</td>
                  <td className="p-4 text-cyan-400 font-mono font-bold text-right pr-6">{r.value.toLocaleString()} {primaryUnit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
