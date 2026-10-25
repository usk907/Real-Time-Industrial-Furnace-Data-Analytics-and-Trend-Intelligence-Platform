import React, { useEffect, useState, useRef } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import {
  Zap,
  AlertOctagon,
  Activity,
  Flame
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

  return <div ref={containerRef} className={className || 'w-full h-full'} />;
};

export const Dashboard: React.FC = () => {
  const { liveTags, liveBuffer, token, connectionStatus } = useAuth();
  const [activeAlarmsCount, setActiveAlarmsCount] = useState<number>(0);

  useEffect(() => {
    if (!token) return;
    const fetchAlarmsCount = async () => {
      try {
        const res = await fetch('/api/alarms?active=true&limit=100', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const alarms = await res.json();
          setActiveAlarmsCount(alarms.length);
        }
      } catch {
        // Fallback
      }
    };

    fetchAlarmsCount();
    const interval = setInterval(fetchAlarmsCount, 5000);
    return () => clearInterval(interval);
  }, [token]);

  // Derive metrics dynamically from real-time 60 tags
  const tr1Power = liveTags['TR1_Active_Power']?.value || 44500.0;
  const tr2Power = liveTags['TR2_Active_Power']?.value || 16800.0;
  const currentGridPower = Math.round(tr1Power + tr2Power);

  const eafPower = liveTags['EAF1_Active_Power']?.value || 42000.0;
  const lrfPower = liveTags['LRF2_Active_Power']?.value || 14500.0;
  const currentFurnacePower = Math.round(eafPower + lrfPower);

  const pf = liveTags['TR1_Power_Factor']?.value || 0.91;
  const cumulativeEnergy = liveTags['Grid_Import_Cumulative_Energy']?.value || 4892100.0;
  const eafBathTemp = liveTags['EAF1_Bath_Temp']?.value || 1580.0;
  const lrfBathTemp = liveTags['LRF2_Bath_Temp']?.value || 1620.0;

  // Chart: Live Power Line Chart
  const liveChartOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#0F1424', borderColor: '#1F2942' },
    legend: {
      data: ['Grid Substation Import (kW)', 'Furnace Load Combined (kW)'],
      textStyle: { color: '#9CA3AF', fontSize: 10 }
    },
    grid: { left: '4%', right: '4%', bottom: '8%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: liveBuffer.time,
      axisLabel: { color: '#9CA3AF', fontSize: 9 }
    },
    yAxis: {
      type: 'value',
      name: 'kW',
      axisLabel: { color: '#9CA3AF', fontSize: 9 },
      splitLine: { lineStyle: { color: '#1F2942' } }
    },
    series: [
      {
        name: 'Grid Substation Import (kW)',
        type: 'line',
        showSymbol: false,
        data: liveBuffer.importPower,
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
        name: 'Furnace Load Combined (kW)',
        type: 'line',
        showSymbol: false,
        data: liveBuffer.generationPower,
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
    series: [
      {
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
            color: [
              [0.5, '#EF4444'],
              [0.8, '#F59E0B'],
              [1, '#10B981']
            ]
          }
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,20.1c0.6,1,0.3,2.3-0.7,2.9c-0.4,0.2-0.8,0.3-1.2,0.3H0.9c-1.1,0-2-0.9-2-2c0-0.4,0.1-0.8,0.3-1.2l12-20.1C11.8-0.2,12.5-0.2,12.8,0.7z',
          length: '75%',
          width: 5,
          offsetCenter: [0, '5%'],
          itemStyle: { color: '#ffffff' }
        },
        axisTick: { show: false },
        splitLine: { length: 8, lineStyle: { width: 2, color: '#9CA3AF' } },
        axisLabel: { color: '#9CA3AF', fontSize: 9, distance: -35 },
        title: { offsetCenter: [0, '25%'], color: '#9CA3AF', fontSize: 9, fontWeight: 'bold' },
        detail: {
          fontSize: 16,
          offsetCenter: [0, '-10%'],
          valueAnimation: true,
          formatter: '{value}',
          color: '#ffffff'
        },
        data: [{ value: parseFloat(pf.toFixed(3)), name: 'Power Factor' }]
      }
    ]
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Row 1: KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Grid Import */}
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl hover:border-blue-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Total Grid Power
            </span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <Zap className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono tracking-tight">
              {currentGridPower.toLocaleString()}
            </span>
            <span className="text-xs font-bold text-slate-400">kW</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>TR-1 ({Math.round(tr1Power)} kW) + TR-2 ({Math.round(tr2Power)} kW)</span>
          </p>
        </div>

        {/* Card 2: Combined Furnace Power */}
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl hover:border-cyan-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Furnace Running Load
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Flame className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono tracking-tight">
              {currentFurnacePower.toLocaleString()}
            </span>
            <span className="text-xs font-bold text-slate-400">kW</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400">
            EAF-1: {Math.round(eafPower)} kW • LRF-2: {Math.round(lrfPower)} kW
          </p>
        </div>

        {/* Card 3: Furnace Bath Temperature */}
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl hover:border-amber-500/50 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              EAF-1 Bath Temp
            </span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Activity className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono tracking-tight">
              {Math.round(eafBathTemp)}
            </span>
            <span className="text-xs font-bold text-slate-400">°C</span>
          </div>
          <p className="mt-2 text-[10px] text-slate-400">
            Target: 1,580°C • LRF-2: {Math.round(lrfBathTemp)}°C
          </p>
        </div>

        {/* Card 4: Active Alarms */}
        <Link
          to="/alarms"
          className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl hover:border-red-500/50 transition-all group block"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Active Alarms
            </span>
            <div className="p-2 rounded-xl bg-red-500/10 text-red-400 group-hover:scale-110 transition-transform">
              <AlertOctagon className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono tracking-tight">
              {activeAlarmsCount}
            </span>
            <span className="text-xs font-bold text-slate-400">Unresolved</span>
          </div>
          <p className="mt-2 text-[10px] text-cyan-400 font-bold group-hover:underline">
            View Live Incident Queue →
          </p>
        </Link>
      </div>

      {/* Row 2: Charts (Live Power Stream + Power Factor Gauge) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Line Chart (Live 30-Point Moving Telemetry) */}
        <div className="lg:col-span-2 bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Live Substation & Furnace Power Stream
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Real-time WebSocket feed updating every second
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  connectionStatus === 'Connected'
                    ? 'bg-emerald-400 animate-pulse'
                    : 'bg-amber-400'
                }`}
              />
              <span className="text-[10px] font-mono text-slate-300 uppercase">
                {connectionStatus}
              </span>
            </div>
          </div>
          <div className="h-72 w-full">
            <EChartsWrapper options={liveChartOptions} />
          </div>
        </div>

        {/* Right Card: Power Factor & Cumulative Energy */}
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-1">
              Electrical Efficiency & Power Factor
            </h3>
            <p className="text-[11px] text-slate-400">Main Substation TR-1 Status</p>
            <div className="h-44 w-full mt-2">
              <EChartsWrapper options={pfGaugeOptions} />
            </div>
          </div>

          <div className="pt-4 border-t border-[#1F2B50]/60 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Grid Cumulative Energy:</span>
              <span className="font-bold text-white font-mono">
                {Math.round(cumulativeEnergy).toLocaleString()} kWh
              </span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">EAF-1 Energy:</span>
              <span className="font-bold text-cyan-400 font-mono">
                {Math.round(liveTags['EAF1_Cumulative_Energy']?.value || 1284500).toLocaleString()} kWh
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
