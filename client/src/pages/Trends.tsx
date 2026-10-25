import React, { useState, useEffect, useRef, useMemo } from 'react';
import * as echarts from 'echarts';
import { useAuth } from '../context/AuthContext';
import { RefreshCw, AlertCircle, Activity } from 'lucide-react';
import { HistoryPoint } from '../types';

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
    if (chartRef.current && options) chartRef.current.setOption(options, true);
  }, [options]);

  return <div ref={containerRef} className={className || 'w-full h-full'} />;
};

export const Trends: React.FC = () => {
  const { token, tagList } = useAuth();
  const [selectedTag, setSelectedTag] = useState<string>('EAF1_Active_Power');
  const [bucket, setBucket] = useState<'raw' | '1m' | '5m' | '1h'>('1m');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyPoints, setHistoryPoints] = useState<HistoryPoint[]>([]);

  // Default tag options if tagList is empty initially
  const availableTags = useMemo(() => {
    if (tagList.length > 0) return tagList.map(t => t.tag);
    return [
      'EAF1_Active_Power',
      'EAF1_Bath_Temp',
      'EAF1_Shell_Temp',
      'EAF1_Cooling_Water_Flow',
      'LRF2_Active_Power',
      'LRF2_Bath_Temp',
      'TR1_Active_Power',
      'TR1_Winding_Temp',
      'TR2_Active_Power',
      'RM1_Stand1_Drive_Power',
      'WTP_Main_Pump1_Power',
      'Grid_Import_Cumulative_Energy'
    ];
  }, [tagList]);

  const fetchHistory = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/history?tag=${encodeURIComponent(selectedTag)}&bucket=${bucket}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistoryPoints(data.points || []);
      } else {
        const errJson = await res.json();
        setError(errJson.detail || 'Failed to fetch historical telemetry.');
        setHistoryPoints([]);
      }
    } catch {
      setError('Network error while querying historical records.');
      setHistoryPoints([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [selectedTag, bucket, token]);

  // Derive summary statistics
  const stats = useMemo(() => {
    if (historyPoints.length === 0) return { min: 0, max: 0, avg: 0, count: 0 };
    const vals = historyPoints.map(p => p.value);
    const sum = vals.reduce((a, b) => a + b, 0);
    return {
      min: Math.min(...vals),
      max: Math.max(...vals),
      avg: Math.round((sum / vals.length) * 100) / 100,
      count: historyPoints.length
    };
  }, [historyPoints]);

  const chartOption = useMemo(() => {
    const xData = historyPoints.map(p => {
      const d = new Date(p.ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    });
    const yData = historyPoints.map(p => p.value);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0F1424',
        borderColor: '#1F2942',
        textStyle: { color: '#E2E8F0', fontSize: 11 }
      },
      grid: { left: '4%', right: '4%', bottom: '10%', top: '12%', containLabel: true },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: { color: '#9CA3AF', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#9CA3AF', fontSize: 9 },
        splitLine: { lineStyle: { color: '#1F2942' } }
      },
      series: [
        {
          name: selectedTag,
          type: 'line',
          smooth: true,
          showSymbol: historyPoints.length < 50,
          data: yData,
          lineStyle: { color: '#06B6D4', width: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(6, 182, 212, 0.3)' },
              { offset: 1, color: 'rgba(6, 182, 212, 0)' }
            ])
          }
        }
      ]
    };
  }, [historyPoints, selectedTag]);

  return (
    <div className="space-y-6 animate-fade-in text-slate-200">
      {/* Control Toolbar */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl flex flex-wrap gap-4 items-center justify-between">
        <div>
          <h2 className="text-base font-extrabold uppercase tracking-wider text-white">
            Historical Trend Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            SQL Downsampled Historical Telemetry • Up to 5,000 Points with Bucket Aggregation
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Tag Selector */}
          <div>
            <label className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Channel Tag</label>
            <select
              value={selectedTag}
              onChange={e => setSelectedTag(e.target.value)}
              className="bg-[#10162B] border border-[#1F2B50] rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
            >
              {availableTags.map(tag => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>

          {/* Bucket Selector */}
          <div>
            <label className="block text-[9px] uppercase font-bold text-slate-400 mb-1">Downsampling Bucket</label>
            <div className="flex rounded-xl bg-[#10162B] border border-[#1F2B50] p-0.5">
              {(['raw', '1m', '5m', '1h'] as const).map(b => (
                <button
                  key={b}
                  onClick={() => setBucket(b)}
                  className={`px-3 py-1 text-xs font-bold rounded-lg uppercase transition-all ${
                    bucket === b
                      ? 'bg-cyan-500 text-slate-950 shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={fetchHistory}
            disabled={loading}
            className="self-end p-2 rounded-xl bg-[#10162B] hover:bg-[#161F3D] border border-[#1F2B50] text-cyan-400 transition-all"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats Summary Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-4">
          <p className="text-[10px] uppercase font-bold text-slate-400">Sample Count</p>
          <p className="text-xl font-bold font-mono text-white mt-1">{stats.count.toLocaleString()}</p>
        </div>
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-4">
          <p className="text-[10px] uppercase font-bold text-slate-400">Average Value</p>
          <p className="text-xl font-bold font-mono text-cyan-400 mt-1">{stats.avg.toLocaleString()}</p>
        </div>
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-4">
          <p className="text-[10px] uppercase font-bold text-slate-400">Minimum Value</p>
          <p className="text-xl font-bold font-mono text-emerald-400 mt-1">{stats.min.toLocaleString()}</p>
        </div>
        <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-4">
          <p className="text-[10px] uppercase font-bold text-slate-400">Maximum Value</p>
          <p className="text-xl font-bold font-mono text-rose-400 mt-1">{stats.max.toLocaleString()}</p>
        </div>
      </div>

      {/* Main Trend Chart */}
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl p-5 shadow-xl">
        {error ? (
          <div className="py-20 text-center text-amber-400">
            <AlertCircle className="h-8 w-8 mx-auto mb-2 text-amber-500" />
            <p className="text-sm font-bold">{error}</p>
          </div>
        ) : historyPoints.length === 0 && !loading ? (
          <div className="py-20 text-center text-slate-500">
            <Activity className="h-8 w-8 mx-auto mb-2 text-slate-600" />
            <p className="text-sm">No historical points recorded for this tag in the selected range.</p>
          </div>
        ) : (
          <div className="h-96 w-full">
            <EChartsWrapper options={chartOption} />
          </div>
        )}
      </div>
    </div>
  );
};
