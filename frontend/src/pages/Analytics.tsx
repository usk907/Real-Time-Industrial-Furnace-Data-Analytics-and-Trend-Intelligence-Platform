import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import { 
  TrendingUp, 
  Percent, 
  Award, 
  Target
} from 'lucide-react';

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

export const Analytics: React.FC = () => {
  const { token } = useAuth();
  const [analyticsData, setAnalyticsData] = useState<any>({
    highest_energy_machine: { name: "SMS-1 Electric Arc Furnace", current_load_kw: 51135 },
    lowest_power_factor: 0.929,
    peak_demand_kw: 42748,
    hourly_consumption: [],
    shift_wise_consumption: [],
    load_distribution: [],
    machine_utilization: [],
    energy_cost_usd: 11208,
    carbon_footprint_kg_co2: 35492,
    efficiency_score: 88.4
  });

  useEffect(() => {
    fetchAnalytics();
  }, [token]);

  const fetchAnalytics = async () => {
    try {
      const res = await fetch('/api/analytics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAnalyticsData(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const ad = analyticsData;

  // Chart 1: Hourly Load Profiling (Bar Chart)
  const hourlyOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#0F1424', borderColor: '#1F2942' },
    xAxis: { 
      type: 'category', 
      data: ad.hourly_consumption.map((h: any) => h.hour),
      axisLabel: { color: '#9CA3AF', fontSize: 9 }
    },
    yAxis: { 
      type: 'value', 
      axisLabel: { color: '#9CA3AF', fontSize: 9 },
      splitLine: { lineStyle: { color: '#1F2942' } } 
    },
    grid: { left: '3%', right: '3%', bottom: '5%', top: '10%', containLabel: true },
    series: [{
      name: 'Load (kWh)',
      type: 'bar',
      data: ad.hourly_consumption.map((h: any) => h.value),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#3B82F6' },
          { offset: 1, color: '#06B6D4' }
        ]),
        borderRadius: [4, 4, 0, 0]
      }
    }]
  };

  // Chart 2: Load Distribution proportion (Pie Chart)
  const pieOptions = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#0F1424', borderColor: '#1F2942' },
    legend: { bottom: '0', textStyle: { color: '#9CA3AF', fontSize: 9 } },
    series: [
      {
        name: 'Load Proportion',
        type: 'pie',
        radius: ['40%', '75%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#0A0D1A', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: false } },
        labelLine: { show: false },
        data: ad.load_distribution.map((d: any) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: d.name.includes("SMS-1") ? '#3B82F6' : (d.name.includes("SMS-4") ? '#06B6D4' : '#F59E0B') }
        }))
      }
    ]
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Row 1: KPI Analytics widgets */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur">
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Highest Consuming Machine</p>
          <h3 className="text-sm font-black mt-2 text-white overflow-hidden text-ellipsis whitespace-nowrap">
            {ad.highest_energy_machine.name}
          </h3>
          <p className="text-cyan-400 font-bold text-lg mt-1 font-mono">{Math.round(ad.highest_energy_machine.current_load_kw).toLocaleString()} kW</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur">
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Lowest System Power Factor</p>
          <h3 className="text-lg font-black mt-2 text-red-400 font-mono">
            {ad.lowest_power_factor.toFixed(3)}
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Target requirement: &gt; 0.900</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur">
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Peak Demand Level</p>
          <h3 className="text-lg font-black mt-2 text-white font-mono">
            {Math.round(ad.peak_demand_kw).toLocaleString()} kW
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Substation capacity load limit</p>
        </div>

        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-5 backdrop-blur">
          <p className="text-[10px] uppercase text-[#556994] font-bold tracking-wider">Plant Energy Efficiency</p>
          <h3 className="text-lg font-black mt-2 text-emerald-400 font-mono">
            {ad.efficiency_score}%
          </h3>
          <p className="text-[9px] text-slate-500 mt-2">Operational benchmark standard</p>
        </div>
      </div>

      {/* Row 2: Diagrams */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Hourly Profiling Bar Chart */}
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-80 backdrop-blur">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-cyan-400" /> Hourly Load Profiling (Last 24 Hours)
          </h4>
          <div className="h-[210px]">
            <EChartsWrapper options={hourlyOptions} />
          </div>
        </div>

        {/* Load distribution chart */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 h-80 backdrop-blur flex flex-col justify-between">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Percent className="h-4 w-4 text-cyan-400" /> Load Allocation Profile
          </h4>
          <div className="h-48 w-full">
            <EChartsWrapper options={pieOptions} />
          </div>
          <div className="text-center text-[9px] text-[#556994] font-bold uppercase pb-1">
            Furnace melt allocations vs Auxiliaries
          </div>
        </div>
      </div>

      {/* Row 3: Machine Utilizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Shift consumption summaries */}
        <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Target className="h-4.5 w-4.5 text-blue-400" /> Shift Performance
          </h4>
          <div className="space-y-3.5 text-xs">
            {ad.shift_wise_consumption.map((s: any, idx: number) => (
              <div key={idx} className="p-3 bg-[#131930] border border-[#1F2942]/40 rounded-xl flex justify-between items-center">
                <div>
                  <p className="font-bold text-slate-300">{s.shift}</p>
                  <p className="text-[9px] text-slate-500 mt-1">Average shift demand</p>
                </div>
                <span className="font-mono font-bold text-white text-right">{s.value.toLocaleString()} kWh</span>
              </div>
            ))}
          </div>
        </div>

        {/* Machine utilization indicators */}
        <div className="lg:col-span-2 bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl p-6 backdrop-blur space-y-4">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest flex items-center gap-2">
            <Award className="h-4.5 w-4.5 text-emerald-400" /> Machine Utilization Index
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {ad.machine_utilization.map((mu: any, idx: number) => (
              <div key={idx} className="p-4 bg-[#131930]/60 border border-[#1F2942]/40 rounded-xl space-y-2">
                <div className="flex justify-between items-center font-bold">
                  <span className="text-slate-200">{mu.machine}</span>
                  <span className={mu.utilization > 0 ? 'text-emerald-400' : 'text-slate-500'}>
                    {mu.utilization > 0 ? `${mu.utilization}% Active` : 'Inactive'}
                  </span>
                </div>
                <div className="w-full bg-[#070913] h-2 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-300 ${mu.utilization > 80 ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-gradient-to-r from-blue-600 to-cyan-400'}`}
                    style={{ width: `${mu.utilization}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};
