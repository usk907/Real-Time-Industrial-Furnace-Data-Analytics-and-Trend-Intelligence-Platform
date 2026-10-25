import React, { useEffect, useState, useRef } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import {
  Zap,
  TrendingUp,
  AlertOctagon,
  ShieldCheck,
  Cpu,
  DollarSign,
  Leaf,
  Activity
} from 'lucide-react';
import { Link } from 'react-router-dom';

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

export const Dashboard: React.FC = () => {
  const { liveReadings, liveBuffer, token } = useAuth();
  const [dbData, setDbData] = useState<any>({
    kpis: {
      grid_power_combined: 0.0,
      generation_combined: 0.0,
      running_furnace_count: 0,
      total_machines: 5,
      running_machines: 4,
      offline_machines: 1,
      faulty_machines: 0,
      avg_pf: 0.929,
      load_factor: 23.279,
      today_energy_kwh: 93400.0,
      monthly_energy_kwh: 2802000.0,
      carbon_emission: 35492.0,
      energy_cost: 11208.0
    },
    active_alarms_count: 0,
    predictions: []
  });

  useEffect(() => {
    fetchDashboardSummary();
    const interval = setInterval(fetchDashboardSummary, 3000);
    return () => clearInterval(interval);
  }, [token]);

  const fetchDashboardSummary = async () => {
    try {
      const res = await fetch('/api/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDbData(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Derive metrics dynamically
  const kpis = dbData.kpis;
  const currentGridPower = (liveReadings[1]?.value || 0) + (liveReadings[2]?.value || 0) || kpis.grid_power_combined;
  const currentGenPower = (liveReadings[41]?.value || 0) + (liveReadings[42]?.value || 0) || kpis.generation_combined;
  const runningFurnaces = kpis.running_furnace_count;

  // Chart: Live Power Line Chart
  const liveChartOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#0F1424', borderColor: '#1F2942' },
    legend: { data: ['Grid import', 'Active generation'], textStyle: { color: '#9CA3AF', fontSize: 10 } },
    grid: { left: '4%', right: '4%', bottom: '8%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: liveBuffer.time, axisLabel: { color: '#9CA3AF', fontSize: 9 } },
    yAxis: { type: 'value', name: 'kW', axisLabel: { color: '#9CA3AF', fontSize: 9 }, splitLine: { lineStyle: { color: '#1F2942' } } },
    series: [
      {
        name: 'Grid import',
        type: 'line',
        showSymbol: false,
        data: liveBuffer.importPower.map(v => Math.round(v)),
        lineStyle: { color: '#3B82F6', width: 2.5 },
        itemStyle: { color: '#3B82F6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.25)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ])
        }
      },
      {
        name: 'Active generation',
        type: 'line',
        showSymbol: false,
        data: liveBuffer.generationPower.map(v => Math.round(v)),
        lineStyle: { color: '#06B6D4', width: 2.5 },
        itemStyle: { color: '#06B6D4' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(6, 182, 212, 0.25)' },
            { offset: 1, color: 'rgba(6, 182, 212, 0)' }
          ])
        }
      }
    ]
  };

  // Chart: Power Factor Gauge Options
  const pfGaugeOptions = {
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0.8,
      max: 1.0,
      splitNumber: 4,
      radius: '100%',
      center: ['50%', '70%'],
      axisLine: {
        lineStyle: {
          width: 6,
          color: [[0.5, '#EF4444'], [0.8, '#F59E0B'], [1, '#10B981']]
        }
      },
      pointer: { icon: 'path://M12.8,0.7l12,20.1c0.6,1,0.3,2.3-0.7,2.9c-0.4,0.2-0.8,0.3-1.2,0.3H0.9c-1.1,0-2-0.9-2-2c0-0.4,0.1-0.8,0.3-1.2l12-20.1C11.8-0.2,12.5-0.2,12.8,0.7z', length: '75%', width: 5, offsetCenter: [0, '5%'], itemStyle: { color: '#ffffff' } },
      axisTick: { show: false },
      splitLine: { length: 8, lineStyle: { width: 2, color: '#9CA3AF' } },
      axisLabel: { color: '#9CA3AF', fontSize: 9, distance: -35 },
      title: { offsetCenter: [0, '25%'], color: '#9CA3AF', fontSize: 9, fontWeight: 'bold' },
      detail: { fontSize: 16, offsetCenter: [0, '-10%'], valueAnimation: true, formatter: '{value}', color: '#ffffff' },
      data: [{ value: parseFloat(liveReadings[47]?.value?.toFixed(3) || kpis.avg_pf.toFixed(3)), name: 'Power Factor' }]
    }]
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <Zap className="h-16 w-16 text-blue-500" />
          </div>
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Total Grid Import</p>
          <h3 className="text-2xl font-black mt-2 text-blue-400">
            {Math.round(currentGridPower).toLocaleString()} <span className="text-xs font-normal text-slate-400">kW</span>
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Active substation power limits</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <TrendingUp className="h-16 w-16 text-cyan-400" />
          </div>
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Comb. Generation</p>
          <h3 className="text-2xl font-black mt-2 text-cyan-400">
            {Math.round(currentGenPower).toLocaleString()} <span className="text-xs font-normal text-slate-400">kW</span>
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Turbines TG-2 + TG-3 combined output</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <DollarSign className="h-16 w-16 text-emerald-400" />
          </div>
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Accum. Cost (Today)</p>
          <h3 className="text-2xl font-black mt-2 text-emerald-400">
            ₹ {Math.round(kpis.energy_cost).toLocaleString()}
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Calculated rate: $0.12 / kWh</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 relative overflow-hidden backdrop-blur">
          <div className="absolute top-0 right-0 p-4 opacity-5">
            <Leaf className="h-16 w-16 text-teal-400" />
          </div>
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Carbon Footprint</p>
          <h3 className="text-2xl font-black mt-2 text-teal-400">
            {Math.round(kpis.carbon_emission).toLocaleString()} <span className="text-xs font-normal text-slate-400">kg</span>
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Conversion factor: 0.38 kg/kWh</p>
        </div>
      </div>

      {/* Row 2: Charts and Gauges */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-80 backdrop-blur">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" /> Live Power Demand Stream
            </h4>
            <span className="text-[9px] bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider animate-pulse">1 Hz rate</span>
          </div>
          <EChartsWrapper options={liveChartOptions} />
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-80 flex flex-col justify-between backdrop-blur">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cyan-400" /> Grid Power Factor
          </h4>
          <div className="h-40 w-full">
            <EChartsWrapper options={pfGaugeOptions} />
          </div>
          <div className="text-center pb-2 text-xs">
            <p className="text-[#556994] font-bold uppercase text-[9px] tracking-wider">System Target Level</p>
            <p className="text-white font-extrabold mt-0.5">&gt; 0.90 Lagging</p>
          </div>
        </div>
      </div>

      {/* Row 3: Machine Status & Active Alarms */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Machine Statuses */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">Melt Shop Machines</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-[#131930] rounded-xl border border-[#1F2942]/40">
              <p className="text-[#556994] font-bold text-[9px] uppercase">Active Furnaces</p>
              <h5 className="text-lg font-black text-white mt-1">{runningFurnaces} <span className="text-[10px] font-normal text-slate-400">/ 5</span></h5>
            </div>
            <div className="p-3 bg-[#131930] rounded-xl border border-[#1F2942]/40">
              <p className="text-[#556994] font-bold text-[9px] uppercase">Alarm State</p>
              <h5 className={`text-lg font-black mt-1 ${dbData.active_alarms_count > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {dbData.active_alarms_count > 0 ? 'ALARM' : 'NORMAL'}
              </h5>
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            {[
              { name: "SMS-1 Electric Arc Furnace", id: 19, limit: 70000 },
              { name: "SMS-4 Refining Furnace", id: 22, limit: 30000 }
            ].map(f => {
              const currentLoad = Math.round(liveReadings[f.id]?.value || 0);
              const pct = Math.min(100, Math.round((currentLoad / f.limit) * 100)) || 0;
              return (
                <div key={f.id} className="p-3.5 bg-[#131930]/60 border border-[#1F2942]/40 rounded-xl space-y-2">
                  <div className="flex justify-between font-bold">
                    <span className="text-slate-300">{f.name}</span>
                    <span className="text-white">{currentLoad.toLocaleString()} kW</span>
                  </div>
                  <div className="w-full bg-[#070913] h-1.5 rounded-full overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
                  </div>
                  <div className="flex justify-between text-[10px] text-[#556994] font-semibold">
                    <span>Horizon Utilization</span>
                    <span>{pct}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Alarms log summary */}
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
              <AlertOctagon className="h-4.5 w-4.5 text-red-500 animate-pulse" /> Active Critical Alarms
            </h4>
            <Link to="/alarms" className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider hover:underline">
              View Log &rarr;
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto max-h-48 space-y-2.5 pr-1 text-xs">
            {dbData.active_alarms_count === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-500 gap-2">
                <ShieldCheck className="h-8 w-8 text-emerald-500 opacity-60" />
                <p className="font-semibold text-slate-400 text-xs">No active anomalies recorded. System secure.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Active alarm warnings */}
                {Object.keys(liveReadings).map((id: any) => {
                  const r = liveReadings[id];
                  if (r && r.status === "HIGH_LIMIT") {
                    return (
                      <div key={id} className="p-3 bg-red-950/20 border border-red-900/30 rounded-xl flex items-center justify-between animate-pulse">
                        <div>
                          <p className="font-extrabold text-red-400">{r.name} High Limit Surge</p>
                          <p className="text-[10px] text-slate-500 font-medium">Telemetry status: {r.status} (Value: {Math.round(r.value)} {r.unit})</p>
                        </div>
                        <span className="bg-red-900/30 text-red-400 text-[9px] font-bold px-2 py-0.5 rounded border border-red-800/40 uppercase">Critical</span>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
