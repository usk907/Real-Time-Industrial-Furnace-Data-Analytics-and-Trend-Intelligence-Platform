import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { 
  Activity, 
  TrendingUp, 
  FileText, 
  Sliders, 
  Settings, 
  FileSpreadsheet,
  CheckCircle,
  AlertTriangle,
  RotateCw,
  Search,
  Filter,
  X
} from 'lucide-react';

// Reusable ECharts Component
const EChartsWrapper: React.FC<{ options: any; className?: string }> = ({ options, className }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      chartRef.current = echarts.init(containerRef.current, 'dark', { renderer: 'svg' });
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

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'monitor' | 'trends' | 'consumption' | 'alarms' | 'settings'>('dashboard');
  const [connectionStatus, setConnectionStatus] = useState<'Connected' | 'Disconnected'>('Disconnected');
  const [activeAlarms, setActiveAlarms] = useState<any[]>([]);
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [alarmSettings, setAlarmSettings] = useState<any>({});
  
  // High-density dynamic values from simulator
  const [liveReadings, setLiveReadings] = useState<Record<number, any>>({});
  const [dashboardData, setDashboardData] = useState<any>({
    kpis: {
      grid_power_combined: 0.0,
      generation_combined: 0.0,
      running_furnace_count: 0,
      avg_pf: 0.929,
      load_factor: 23.279
    },
    alarms: [],
    predictions: []
  });

  // Trends parameters checkboxes modal state
  const [isTrendsModalOpen, setIsTrendsModalOpen] = useState(false);
  const [selectedTrendParams, setSelectedTrendParams] = useState<Record<string, boolean>>({
    "Grid kW": true,
    "30MW TG-2 kW": true,
    "CB5214 kW": false,
    "CB14 kW": false
  });

  // Telemetry buffer for ECharts plotting
  const [liveChartBuffer, setLiveChartBuffer] = useState<{ time: string[]; importPower: number[]; generationPower: number[] }>({
    time: [],
    importPower: [],
    generationPower: []
  });

  // Fetch initial configs
  useEffect(() => {
    fetchSummary();
    fetchAlarms();
    fetchReports();
    fetchSettings();

    // Initalize WebSocket stream
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.hostname}:8000/api/ws`;
    const connect = () => {
      console.log("[WS]: Connecting local telemetry stream...");
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => setConnectionStatus('Connected');
      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.event === "TELEMETRY_UPDATE") {
          const readings = payload.readings;
          setLiveReadings(readings);

          const importPower = (readings["1"]?.value || 0) + (readings["2"]?.value || 0);
          const generationPower = (readings["41"]?.value || 0) + (readings["42"]?.value || 0);
          const timeLabel = new Date(payload.timestamp).toLocaleTimeString();

          // Append to chart buffer
          setLiveChartBuffer(prev => {
            const nextTime = [...prev.time, timeLabel].slice(-30);
            const nextImport = [...prev.importPower, importPower].slice(-30);
            const nextGen = [...prev.generationPower, generationPower].slice(-30);
            return { time: nextTime, importPower: nextImport, generationPower: nextGen };
          });

          // Inline update numeric dashboard states
          setDashboardData(prev => ({
            ...prev,
            kpis: {
              grid_power_combined: importPower,
              generation_combined: generationPower,
              running_furnace_count: (readings["25"]?.value > 50 ? 1 : 0) + (readings["29"]?.value > 50 ? 1 : 0) + (readings["19"]?.value > 100 ? 1 : 0),
              avg_pf: readings["47"]?.value || prev.kpis.avg_pf,
              load_factor: readings["48"]?.value || prev.kpis.load_factor
            }
          }));
        }
      };
      
      ws.onclose = () => {
        setConnectionStatus('Disconnected');
        setTimeout(connect, 3000);
      };
    };

    connect();
  }, []);

  const fetchSummary = () => {
    fetch('http://localhost:8000/api/dashboard')
      .then(res => res.json())
      .then(data => setDashboardData(data))
      .catch(err => console.error("Error fetching stats:", err));
  };

  const fetchAlarms = () => {
    fetch('http://localhost:8000/api/alarms')
      .then(res => res.json())
      .then(data => setActiveAlarms(data))
      .catch(err => console.error("Error fetching alarms:", err));
  };

  const fetchReports = () => {
    fetch('http://localhost:8000/api/reports')
      .then(res => res.json())
      .then(data => setRecentReports(data))
      .catch(err => console.error("Error listing reports:", err));
  };

  const fetchSettings = () => {
    fetch('http://localhost:8000/api/settings')
      .then(res => res.json())
      .then(data => setAlarmSettings(data))
      .catch(err => console.error("Error retrieving settings:", err));
  };

  const handleAcknowledge = (alarmId: number) => {
    fetch(`http://localhost:8000/api/alarms/${alarmId}/acknowledge`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        acknowledged_by: "kushal_engineer",
        comments: "Grid checkup logged. Status cleared."
      })
    })
      .then(res => res.json())
      .then(() => {
        fetchAlarms();
        fetchSummary();
      });
  };

  const handleGenerateReport = (type: string) => {
    fetch(`http://localhost:8000/api/reports/generate?report_type=${type}`, { method: 'POST' })
      .then(res => res.json())
      .then(() => fetchReports());
  };

  // Chart options definitions
  const liveChartOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { data: ['Grid import power', 'Active generation power'], textStyle: { color: '#9CA3AF' } },
    xAxis: { type: 'category', data: liveChartBuffer.time, axisLabel: { color: '#9CA3AF' } },
    yAxis: { type: 'value', name: 'kW', axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#1F2937' } } },
    series: [
      {
        name: 'Grid import power',
        type: 'line',
        showSymbol: false,
        data: liveChartBuffer.importPower,
        lineStyle: { color: '#3B82F6', width: 2 }
      },
      {
        name: 'Active generation power',
        type: 'line',
        showSymbol: false,
        data: liveChartBuffer.generationPower,
        lineStyle: { color: '#10B981', width: 2 }
      }
    ]
  };

  // Trend page selections ECharts mapping
  const trendPageOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: liveChartBuffer.time, axisLabel: { color: '#9CA3AF' } },
    yAxis: { type: 'value', axisLabel: { color: '#9CA3AF' }, splitLine: { lineStyle: { color: '#1F2937' } } },
    series: Object.keys(selectedTrendParams).filter(k => selectedTrendParams[k]).map(param => ({
      name: param,
      type: 'line',
      smooth: true,
      data: param.includes("Generation") || param.includes("TG-2") ? liveChartBuffer.generationPower : liveChartBuffer.importPower
    }))
  };

  return (
    <div className="flex h-screen bg-[#0B0F19] text-slate-100 font-sans">
      
      {/* 1. SIDEBAR NAVIGATION */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between hidden md:flex">
        <div>
          <div className="flex items-center gap-2.5 p-6 border-b border-slate-800">
            <Activity className="h-6 w-6 text-blue-500 animate-pulse" />
            <div>
              <h1 className="font-bold text-xs leading-tight tracking-wider text-white">REALTIME ANALYTICS</h1>
              <p className="text-[9px] text-slate-500 tracking-widest uppercase">Steel Melting Shop Platform</p>
            </div>
          </div>

          <nav className="p-4 space-y-1 text-xs">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'dashboard' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Activity className="h-4 w-4" />
              Live Dashboard
            </button>
            <button 
              onClick={() => setActiveTab('monitor')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'monitor' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Sliders className="h-4 w-4" />
              Data Monitor
            </button>
            <button 
              onClick={() => setActiveTab('trends')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'trends' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <TrendingUp className="h-4 w-4" />
              Trends View
            </button>
            <button 
              onClick={() => setActiveTab('consumption')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'consumption' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <FileSpreadsheet className="h-4 w-4" />
              Consumption Audit
            </button>
            <button 
              onClick={() => setActiveTab('alarms')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'alarms' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <AlertTriangle className="h-4 w-4" />
              Alarms Log
            </button>
            <button 
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${activeTab === 'settings' ? 'bg-blue-600/10 text-blue-400 font-medium' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Settings className="h-4 w-4" />
              Configurations
            </button>
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${connectionStatus === 'Connected' ? 'bg-emerald-500 animate-ping' : 'bg-red-500'}`} />
            <span className="text-slate-400">Status: {connectionStatus}</span>
          </div>
        </div>
      </aside>

      {/* 2. MAIN APP FRAME */}
      <main className="flex-1 flex flex-col overflow-hidden">
        
        {/* Header bar */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              {activeTab === 'monitor' ? 'Data Monitor' : (activeTab === 'trends' ? 'Trends Panel' : activeTab)}
            </h2>
            <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">Gary Steel Works</span>
          </div>
          
          {/* Quick Tab switcher for mobile screens */}
          <div className="flex md:hidden gap-1.5 text-[10px] font-bold">
            <button onClick={() => setActiveTab('dashboard')} className={`px-2 py-1 rounded ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Home</button>
            <button onClick={() => setActiveTab('monitor')} className={`px-2 py-1 rounded ${activeTab === 'monitor' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Monitor</button>
            <button onClick={() => setActiveTab('trends')} className={`px-2 py-1 rounded ${activeTab === 'trends' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Trends</button>
            <button onClick={() => setActiveTab('consumption')} className={`px-2 py-1 rounded ${activeTab === 'consumption' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>Audit</button>
          </div>
        </header>

        {/* Scrollable Layout Container */}
        <div className="flex-1 overflow-y-auto p-6">
          
          {/* TAB 1: LIVE DASHBOARD SUMMARY */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              
              {/* Row 1: KPI Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-5">
                  <p className="text-[10px] uppercase text-slate-400 tracking-wider">Total Grid Import</p>
                  <h3 className="text-xl font-bold mt-1 text-blue-500">
                    {dashboardData.kpis.grid_power_combined.toFixed(0)} <span className="text-xs font-normal text-slate-400">kW</span>
                  </h3>
                </div>
                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-5">
                  <p className="text-[10px] uppercase text-slate-400 tracking-wider">Total Power Generation</p>
                  <h3 className="text-xl font-bold mt-1 text-emerald-500">
                    {dashboardData.kpis.generation_combined.toFixed(0)} <span className="text-xs font-normal text-slate-400">kW</span>
                  </h3>
                </div>
                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-5">
                  <p className="text-[10px] uppercase text-slate-400 tracking-wider">Average Power Factor</p>
                  <h3 className="text-xl font-bold mt-1 text-white">
                    {dashboardData.kpis.avg_pf.toFixed(3)}
                  </h3>
                </div>
                <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-5">
                  <p className="text-[10px] uppercase text-slate-400 tracking-wider">Grid Load Factor</p>
                  <h3 className="text-xl font-bold mt-1 text-white">
                    {dashboardData.kpis.load_factor.toFixed(3)}
                  </h3>
                </div>
              </div>

              {/* Row 2: Live Plotter Chart */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-72">
                <h4 className="text-xs font-semibold text-slate-400 mb-4 tracking-wider uppercase">Live Telemetry (1 Hz Update)</h4>
                <EChartsWrapper options={liveChartOptions} />
              </div>

              {/* Row 3: Active Alerts & Forecasts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col h-48">
                  <h4 className="text-xs font-semibold text-red-500 mb-3 tracking-wider uppercase">Active Critical Alarms</h4>
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1 text-xs">
                    {activeAlarms.filter(a => a.status === 'ACTIVE').length === 0 ? (
                      <p className="text-slate-500 text-center py-8">All systems running within safety limits.</p>
                    ) : (
                      activeAlarms.filter(a => a.status === 'ACTIVE').map(alarm => (
                        <div key={alarm.id} className="p-2.5 bg-red-950/20 border border-red-900/30 rounded-lg flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-red-400">{alarm.alarm_type}</p>
                            <p className="text-[10px] text-slate-500">Value: {alarm.trigger_value?.toFixed(0)}</p>
                          </div>
                          <button onClick={() => handleAcknowledge(alarm.id)} className="bg-red-900/30 text-red-300 text-[10px] px-2.5 py-1 rounded">ACK</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col h-48">
                  <h4 className="text-xs font-semibold text-blue-400 mb-3 tracking-wider uppercase">Next Prediction Projections</h4>
                  <div className="flex-1 overflow-y-auto space-y-2 text-xs">
                    {dashboardData.predictions.length === 0 ? (
                      <p className="text-slate-500 text-center py-8">Calculating trend slope forecasts...</p>
                    ) : (
                      dashboardData.predictions.map((p: any, idx: number) => (
                        <div key={idx} className="p-2.5 bg-blue-950/20 border border-blue-950 rounded-lg flex justify-between items-center">
                          <p className="font-semibold text-blue-400">Horizon: +{p.horizon} Min (TG-2)</p>
                          <p className="font-mono text-white">{p.predicted.toFixed(1)} kW</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* TAB 2: DATA MONITOR (Exact representation of screenshots 1 and 5) */}
          {activeTab === 'monitor' && (
            <div className="space-y-6 max-w-2xl mx-auto">
              
              {/* Box 1: Distribution Parameters */}
              <div className="bg-[#161E2E] rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <div className="bg-yellow-400 text-[#161E2E] py-2.5 text-center font-bold text-sm tracking-wider uppercase">
                  Distribution Parameters
                </div>
                
                <div className="divide-y divide-[#0B0F19] text-xs font-medium">
                  {[
                    { label: "CB5214 kW", key: 1, type: "val" },
                    { label: "CB14 kW", key: 2, type: "val" },
                    { label: "CB52G4 kW", key: 3, type: "val" },
                    { label: "CB52G14 kW", key: 4, type: "val" },
                    { label: "CB52G24 kW", key: 5, type: "val" },
                    { label: "SMS Allocated Power", key: 6, type: "val" },
                    { label: "SMS Run. Power", key: 7, type: "val" },
                    { label: "SMS-1 PR", key: 8, type: "pr" },
                    { label: "SMS-2 PR", key: 9, type: "pr" },
                    { label: "SMS-4 PR", key: 10, type: "pr" },
                    { label: "SMS-1 Max Set", key: 11, type: "val" },
                    { label: "SMS-1 Min Set", key: 12, type: "val" },
                    { label: "SMS-2 Max Set", key: 13, type: "val" },
                    { label: "SMS-2 Min Set", key: 14, type: "val" },
                    { label: "SMS-4 Max Set", key: 15, type: "val" },
                    { label: "SMS-4 Min Set", key: 16, type: "val" }
                  ].map(row => (
                    <div key={row.key} className="flex justify-between px-6 py-2.5 hover:bg-slate-800/20">
                      <span className="text-slate-300 font-semibold">{row.label}</span>
                      <span className="font-mono text-white text-right">
                        {liveReadings[row.key] ? (row.type === 'pr' ? liveReadings[row.key].value : Math.round(liveReadings[row.key].value)) : (row.key === 6 ? 100000 : (row.key === 11 ? 70000 : (row.key === 15 ? 30000 : 0)))}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Box 2: SMS-1 Furnace Parameters */}
              <div className="bg-[#161E2E] rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <div className="bg-yellow-400 text-[#161E2E] py-2.5 text-center font-bold text-sm tracking-wider uppercase">
                  SMS-1 Furnace Parameters
                </div>
                
                <div className="divide-y divide-[#0B0F19] text-xs font-medium">
                  {[
                    { label: "SMS-1 Max Set", key: 17 },
                    { label: "SMS-1 Avl. Power", key: 18 },
                    { label: "SMS-1 Run. Power", key: 19 }
                  ].map(row => (
                    <div key={row.key} className="flex justify-between px-6 py-2.5">
                      <span className="text-slate-300 font-semibold">{row.label}</span>
                      <span className="font-mono text-white">
                        {liveReadings[row.key] ? Math.round(liveReadings[row.key].value) : (row.key === 19 ? 51135 : 70000)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Box 3: SMS-4 Furnace Parameters */}
              <div className="bg-[#161E2E] rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <div className="bg-yellow-400 text-[#161E2E] py-2.5 text-center font-bold text-sm tracking-wider uppercase">
                  SMS-4 Furnace Parameters
                </div>
                
                <div className="divide-y divide-[#0B0F19] text-xs font-medium">
                  {[
                    { label: "SMS-4 Max Set", key: 20, format: "val" },
                    { label: "SMS-4 Avl. Power", key: 21, format: "val" },
                    { label: "SMS-4 Run. Power", key: 22, format: "val" },
                    { label: "SMS-4 Utl. Factor(%)", key: 23, format: "pct" },
                    { label: "SMS-4 Fur-1 SP", key: 24, format: "val" },
                    { label: "SMS-4 Fur-1 kW", key: 25, format: "val" },
                    { label: "SMS-4 Fur-1 PP%", key: 26, format: "pct" },
                    { label: "SMS-4 Fur-1 PR", key: 27, format: "pr" },
                    { label: "SMS-4 Fur-2 SP", key: 28, format: "val" },
                    { label: "SMS-4 Fur-2 kW", key: 29, format: "val" },
                    { label: "SMS-4 Fur-2 PP%", key: 30, format: "pct" },
                    { label: "SMS-4 Fur-2 PR", key: 31, format: "pr" },
                    { label: "SMS-4 Fur-3 SP", key: 32, format: "val" },
                    { label: "SMS-4 Fur-3 kW", key: 33, format: "val" },
                    { label: "SMS-4 Fur-3 PP%", key: 34, format: "pct" },
                    { label: "SMS-4 Fur-3 PR", key: 35, format: "pr" },
                    { label: "SMS-4 Fur-4 SP", key: 36, format: "val" },
                    { label: "SMS-4 Fur-4 kW", key: 37, format: "val" },
                    { label: "SMS-4 Fur-4 PP%", key: 38, format: "pct" },
                    { label: "SMS-4 Fur-4 PR", key: 39, format: "pr" },
                    { label: "SMS-2 Aux-1 kW", key: 99, format: "const" } // Constant auxiliary
                  ].map(row => (
                    <div key={row.key} className="flex justify-between px-6 py-2.5">
                      <span className="text-slate-300 font-semibold">{row.label}</span>
                      <span className="font-mono text-white">
                        {row.format === "const" ? 1820 : (
                          liveReadings[row.key] ? (
                            row.format === "pct" ? liveReadings[row.key].value.toFixed(1) : 
                            (row.format === "pr" ? liveReadings[row.key].value : Math.round(liveReadings[row.key].value))
                          ) : (
                            row.key === 20 || row.key === 21 ? 30000 : 
                            (row.key === 23 ? "87.2" : 
                            (row.label.includes("SP") ? 8300 : 0))
                          )
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* TAB 3: TRENDS PANEL (Exact Parameter selector modal representation from Image 2) */}
          {activeTab === 'trends' && (
            <div className="space-y-6">
              
              <div className="flex justify-between items-center bg-slate-900 p-4 border border-slate-800 rounded-xl">
                <p className="text-xs text-slate-400 font-medium">Select signals to construct trend lines comparison:</p>
                <button 
                  onClick={() => setIsTrendsModalOpen(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 transition"
                >
                  <Filter className="h-4 w-4" /> Set Parameters Selection
                </button>
              </div>

              {/* Trend Chart View */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-[400px]">
                <EChartsWrapper options={trendPageOptions} />
              </div>

              {/* Set Parameter Dialog Modal Overlay */}
              {isTrendsModalOpen && (
                <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                  <div className="bg-white text-slate-900 rounded-lg w-full max-w-sm overflow-hidden shadow-2xl">
                    <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
                      <h3 className="font-bold text-sm text-slate-800">Set Parameter Selection</h3>
                      <button onClick={() => setIsTrendsModalOpen(false)}>
                        <X className="h-4 w-4 text-slate-500 hover:text-slate-800" />
                      </button>
                    </div>

                    <div className="p-5 max-h-[300px] overflow-y-auto space-y-2">
                      {[
                        "Set MD", "Running MD", "Grid KVA", "Grid kW", "Generation kW",
                        "30MW TG-1 kW", "30MW TG-2 kW", "33MW TG-3 kW", "30MW TG-4 kW", "40MW TG-5 kW",
                        "CB5214 kW", "CB14 kW", "CB52G4 kW", "CB52G14 kW", "CB52G24 kW"
                      ].map(param => (
                        <label key={param} className="flex items-center gap-3 p-1.5 hover:bg-slate-100 rounded cursor-pointer text-xs font-semibold text-slate-700">
                          <input 
                            type="checkbox" 
                            checked={!!selectedTrendParams[param]}
                            onChange={(e) => setSelectedTrendParams({ ...selectedTrendParams, [param]: e.target.checked })}
                            className="h-4 w-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                          />
                          {param}
                        </label>
                      ))}
                    </div>

                    <div className="grid grid-cols-2 gap-2 p-4 bg-slate-50 border-t border-slate-200 text-xs font-bold">
                      <button 
                        onClick={() => setIsTrendsModalOpen(false)}
                        className="w-full border border-slate-300 hover:bg-slate-100 text-slate-700 py-2.5 rounded-lg transition"
                      >
                        Close
                      </button>
                      <button 
                        onClick={() => setIsTrendsModalOpen(false)}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg transition"
                      >
                        Submit
                      </button>
                    </div>
                  </div>
                </div>
              )}

            </div>
          )}

          {/* TAB 4: AUDIT CONSUMPTION REPORT GRID (Exact list representation of Images 3 & 4) */}
          {activeTab === 'consumption' && (
            <div className="space-y-6 max-w-2xl mx-auto">
              
              <div className="bg-[#161E2E] rounded-2xl border border-slate-850 overflow-hidden shadow-lg">
                <div className="bg-yellow-400 text-[#161E2E] py-2.5 text-center font-bold text-sm tracking-wider">
                  24 Jun, 2026
                </div>
                
                <div className="divide-y divide-[#0B0F19] text-xs font-medium">
                  {/* Static representation of grid index consumption data */}
                  {[
                    { label: "Grid Import kWh", val: 93400 },
                    { label: "Grid Import kVah", val: 100564 },
                    { label: "Avg. P.F.", val: 0.929, format: "float" },
                    { label: "Load Factor", val: 23.279, format: "float" },
                    { label: "Grid Export kWh", val: 130136 },
                    { label: "Grid Export kVah", val: 148800 },
                    { label: "30MW TG-1 kW", val: 0 },
                    { label: "30MW TG-2 kW", val: 701608 },
                    { label: "33MW TG-3 kW", val: 781856 },
                    { label: "30MW TG-4 kW", val: 0 },
                    { label: "40MW TG-5 kW", val: 0 },
                    { label: "SMS-1 Fur-1 kWh", val: 124088 },
                    { label: "SMS-1 Fur-2 kWh", val: 131184 },
                    { label: "SMS-1 Fur-3 kWh", val: 124684 },
                    { label: "SMS-1 Fur-4 kWh", val: 127984 },
                    { label: "SMS-1 Fur-5 kWh", val: 136988 },
                    { label: "SMS-1 Aux-1 kWh", val: 35186 },
                    { label: "SMS-1 Aux-2 kWh", val: 24400 },
                    { label: "SMS-1 Sint kWh", val: 2194 },
                    { label: "SAF-1(2x9Mva) kWh", val: 179218 },
                    { label: "SMS-2 Fur-4 kWh", val: 60764 },
                    { label: "SMS-2 Fur-5 kWh", val: 60132 },
                    { label: "SMS-2 Fur-6 kWh", val: 61116 },
                    { label: "SMS-2 Fur-7 kWh", val: 61660 },
                    { label: "SMS-2 Fur-8 kWh", val: 62792 },
                    { label: "SMS-2 Fur-9 kWh", val: 58092 },
                    { label: "SMS-2 Fur-10 kWh", val: 58120 },
                    { label: "SMS-2 Fur-11 kWh", val: 68330 },
                    { label: "SMS-2 Fur-12 kWh", val: 64856 },
                    { label: "SMS-4 Fur-1 kWh", val: 103848 },
                    { label: "SMS-4 Fur-2 kWh", val: 115848 },
                    { label: "SMS-4 Fur-3 kWh", val: 129272 },
                    { label: "SMS-4 Fur-4 kWh", val: 126160 },
                    { label: "SMS-2 Aux-1 kWh", val: 39093 },
                    { label: "SMS-2 Aux-2 kWh", val: 0 },
                    { label: "SMS-4 Sint-1 kWh", val: 555 },
                    { label: "SMS-4 Sint-2 kWh", val: 4035 },
                    { label: "SMS-4 Aux kWh", val: 29248 },
                    { label: "SMS-4 TR2MVA kWh", val: 4738 },
                    { label: "SMS-4 TR6MVA kWh", val: 32176 },
                    { label: "SMS-4 TR3.6MVA kWh", val: 6670 },
                    { label: "SMS-4 TR5MVA kWh", val: 28212 }
                  ].map((row, idx) => (
                    <div key={idx} className="flex justify-between px-6 py-2.5 hover:bg-slate-800/10">
                      <span className="text-slate-300 font-semibold">{row.label}</span>
                      <span className="font-mono text-white text-right">
                        {row.format === "float" ? row.val.toFixed(3) : row.val.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* TAB 5: ALARMS LIST */}
          {activeTab === 'alarms' && (
            <div className="space-y-6">
              
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-950 border-b border-slate-850 text-slate-400">
                      <th className="p-4">Alarm ID</th>
                      <th className="p-4">Timestamp</th>
                      <th className="p-4">Anomaly Event</th>
                      <th className="p-4">Severity</th>
                      <th className="p-4">Value</th>
                      <th className="p-4">Status</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeAlarms.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-slate-500">No active alerts recorded. All systems green.</td>
                      </tr>
                    ) : (
                      activeAlarms.map(a => (
                        <tr key={a.id} className="border-b border-slate-800/80 hover:bg-slate-900/50">
                          <td className="p-4 font-mono">#{a.id}</td>
                          <td className="p-4 text-slate-400">{new Date(a.time).toLocaleString()}</td>
                          <td className="p-4 font-semibold">{a.alarm_type}</td>
                          <td className="p-4">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${a.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-900/40' : 'bg-amber-950 text-amber-400 border border-amber-900/40'}`}>
                              {a.severity}
                            </span>
                          </td>
                          <td className="p-4 font-mono">{a.trigger_value?.toFixed(1) || '-'}</td>
                          <td className="p-4 font-semibold">{a.status}</td>
                          <td className="p-4 text-right">
                            {a.status === 'ACTIVE' ? (
                              <button 
                                onClick={() => handleAcknowledge(a.id)}
                                className="bg-blue-600 hover:bg-blue-700 text-white text-[10px] px-2.5 py-1 rounded"
                              >
                                Acknowledge
                              </button>
                            ) : (
                              <span className="text-slate-500">Checked</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

            </div>
          )}

          {/* TAB 6: SETTINGS */}
          {activeTab === 'settings' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-xl text-xs space-y-4">
              <h4 className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-2">System Parameters Limits</h4>
              
              <div>
                <label className="block text-slate-400 mb-1.5">Max Breaker Limit (CB5214 kW)</label>
                <input 
                  type="number" 
                  value={alarmSettings.alarm_threshold_breaker_max || 45000} 
                  onChange={(e) => setAlarmSettings({ ...alarmSettings, alarm_threshold_breaker_max: parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1.5">Max Turbine Generator Limit (30MW TG-2 kW)</label>
                <input 
                  type="number" 
                  value={alarmSettings.alarm_threshold_tg_max || 30000} 
                  onChange={(e) => setAlarmSettings({ ...alarmSettings, alarm_threshold_tg_max: parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white focus:outline-none"
                />
              </div>

              <button 
                onClick={handleUpdateSettings}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2.5 rounded-lg transition"
              >
                Save Limits Configurations
              </button>
            </div>
          )}

        </div>

        {/* Mobile bottom tabs navigation matching screenshot bottom bars */}
        <footer className="h-14 border-t border-slate-800 bg-slate-900 flex items-center justify-around md:hidden text-[9px] font-bold text-slate-400">
          <button onClick={() => setActiveTab('dashboard')} className={`flex flex-col items-center gap-1 ${activeTab === 'dashboard' ? 'text-blue-500' : ''}`}>
            <Activity className="h-4.5 w-4.5" />
            Home
          </button>
          <button onClick={() => setActiveTab('monitor')} className={`flex flex-col items-center gap-1 ${activeTab === 'monitor' ? 'text-blue-500' : ''}`}>
            <Sliders className="h-4.5 w-4.5" />
            Monitor
          </button>
          <button onClick={() => setActiveTab('trends')} className={`flex flex-col items-center gap-1 ${activeTab === 'trends' ? 'text-blue-500' : ''}`}>
            <TrendingUp className="h-4.5 w-4.5" />
            Trends
          </button>
          <button onClick={() => setActiveTab('consumption')} className={`flex flex-col items-center gap-1 ${activeTab === 'consumption' ? 'text-blue-500' : ''}`}>
            <FileSpreadsheet className="h-4.5 w-4.5" />
            Audit
          </button>
        </footer>

      </main>

    </div>
  );
}
