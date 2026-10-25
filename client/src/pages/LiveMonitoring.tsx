import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Sliders, Shield, Power, Activity, Thermometer } from 'lucide-react';

export const LiveMonitoring: React.FC = () => {
  const { liveReadings } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState<'ALL' | 'GRID' | 'SMS1' | 'SMS4' | 'TURBINES' | 'ACCUMULATORS'>('ALL');

  const sensorGroups = {
    GRID: {
      name: "Grid & Substation Subsystem",
      ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 55, 56],
      icon: Shield
    },
    SMS1: {
      name: "SMS-1 Electric Arc Furnace",
      ids: [17, 18, 19, 51, 52, 53, 57, 58, 59],
      icon: Thermometer
    },
    SMS4: {
      name: "SMS-4 Refining Furnace",
      ids: [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 60],
      icon: Power
    },
    TURBINES: {
      name: "Turbine Co-Generation",
      ids: [40, 41, 42, 43, 44, 54],
      icon: Activity
    },
    ACCUMULATORS: {
      name: "Energy Audits & Accumulations",
      ids: [45, 46, 47, 48, 49, 50],
      icon: Sliders
    }
  };

  const allSensors = [
    // We populate descriptions for all 60 sensors
    { id: 1, name: "CB5214 kW", unit: "kW", type: "Power" },
    { id: 2, name: "CB14 kW", unit: "kW", type: "Power" },
    { id: 3, name: "CB52G4 kW", unit: "kW", type: "Power" },
    { id: 4, name: "CB52G14 kW", unit: "kW", type: "Power" },
    { id: 5, name: "CB52G24 kW", unit: "kW", type: "Power" },
    { id: 6, name: "SMS Allocated Power", unit: "kW", type: "Power" },
    { id: 7, name: "SMS Run. Power", unit: "kW", type: "Power" },
    { id: 8, name: "SMS-1 PR", unit: "", type: "Setpoint" },
    { id: 9, name: "SMS-2 PR", unit: "", type: "Setpoint" },
    { id: 10, name: "SMS-4 PR", unit: "", type: "Setpoint" },
    { id: 11, name: "SMS-1 Max Set", unit: "kW", type: "Setpoint" },
    { id: 12, name: "SMS-1 Min Set", unit: "kW", type: "Setpoint" },
    { id: 13, name: "SMS-2 Max Set", unit: "kW", type: "Setpoint" },
    { id: 14, name: "SMS-2 Min Set", unit: "kW", type: "Setpoint" },
    { id: 15, name: "SMS-4 Max Set", unit: "kW", type: "Setpoint" },
    { id: 16, name: "SMS-4 Min Set", unit: "kW", type: "Setpoint" },
    { id: 17, name: "SMS-1 Max Set", unit: "kW", type: "Setpoint" },
    { id: 18, name: "SMS-1 Avl. Power", unit: "kW", type: "Power" },
    { id: 19, name: "SMS-1 Run. Power", unit: "kW", type: "Power" },
    { id: 20, name: "SMS-4 Max Set", unit: "kW", type: "Setpoint" },
    { id: 21, name: "SMS-4 Avl. Power", unit: "kW", type: "Power" },
    { id: 22, name: "SMS-4 Run. Power", unit: "kW", type: "Power" },
    { id: 23, name: "SMS-4 Utl. Factor(%)", unit: "%", type: "KPI" },
    { id: 24, name: "SMS-4 Fur-1 SP", unit: "kW", type: "Setpoint" },
    { id: 25, name: "SMS-4 Fur-1 kW", unit: "kW", type: "Power" },
    { id: 26, name: "SMS-4 Fur-1 PP%", unit: "%", type: "Power" },
    { id: 27, name: "SMS-4 Fur-1 PR", unit: "", type: "Setpoint" },
    { id: 28, name: "SMS-4 Fur-2 SP", unit: "kW", type: "Setpoint" },
    { id: 29, name: "SMS-4 Fur-2 kW", unit: "kW", type: "Power" },
    { id: 30, name: "SMS-4 Fur-2 PP%", unit: "%", type: "Power" },
    { id: 31, name: "SMS-4 Fur-2 PR", unit: "", type: "Setpoint" },
    { id: 32, name: "SMS-4 Fur-3 SP", unit: "kW", type: "Setpoint" },
    { id: 33, name: "SMS-4 Fur-3 kW", unit: "kW", type: "Power" },
    { id: 34, name: "SMS-4 Fur-3 PP%", unit: "%", type: "Power" },
    { id: 35, name: "SMS-4 Fur-3 PR", unit: "", type: "Setpoint" },
    { id: 36, name: "SMS-4 Fur-4 SP", unit: "kW", type: "Setpoint" },
    { id: 37, name: "SMS-4 Fur-4 kW", unit: "kW", type: "Power" },
    { id: 38, name: "SMS-4 Fur-4 PP%", unit: "%", type: "Power" },
    { id: 39, name: "SMS-4 Fur-4 PR", unit: "", type: "Setpoint" },
    { id: 40, name: "30MW TG-1 kW", unit: "kW", type: "Power" },
    { id: 41, name: "30MW TG-2 kW", unit: "kW", type: "Power" },
    { id: 42, name: "33MW TG-3 kW", unit: "kW", type: "Power" },
    { id: 43, name: "30MW TG-4 kW", unit: "kW", type: "Power" },
    { id: 44, name: "40MW TG-5 kW", unit: "kW", type: "Power" },
    { id: 45, name: "Grid Import kWh", unit: "kWh", type: "Accumulator" },
    { id: 46, name: "Grid Import kVah", unit: "kVah", type: "Accumulator" },
    { id: 47, name: "Avg. P.F.", unit: "", type: "KPI" },
    { id: 48, name: "Load Factor", unit: "", type: "KPI" },
    { id: 49, name: "Grid Export kWh", unit: "kWh", type: "Accumulator" },
    { id: 50, name: "Grid Export kVah", unit: "kVah", type: "Accumulator" },
    { id: 51, name: "SMS-1 Furnace Temp", unit: "°C", type: "Temperature" },
    { id: 52, name: "SMS-1 Furnace Pressure", unit: "bar", type: "Pressure" },
    { id: 53, name: "SMS-1 Cooling Water Flow", unit: "m³/h", type: "Flow" },
    { id: 54, name: "TG-2 Turbine RPM", unit: "RPM", type: "Speed" },
    { id: 55, name: "CB5214 Voltage", unit: "V", type: "Voltage" },
    { id: 56, name: "CB5214 Current", unit: "A", type: "Current" },
    { id: 57, name: "SMS Ambient Humidity", unit: "%", type: "Humidity" },
    { id: 58, name: "SMS Carbon Dioxide (CO2)", unit: "ppm", type: "Gas" },
    { id: 59, name: "SMS-1 Production Count", unit: "heats", type: "Count" },
    { id: 60, name: "SMS-4 Gas Level (CO)", unit: "ppm", type: "Gas" }
  ];

  const categories = [
    { key: 'ALL', name: 'All Tags' },
    { key: 'GRID', name: 'Substation Grid' },
    { key: 'SMS1', name: 'Furnace SMS-1' },
    { key: 'SMS4', name: 'Furnace SMS-4' },
    { key: 'TURBINES', name: 'Turbines Gen' },
    { key: 'ACCUMULATORS', name: 'Accumulations & PF' }
  ];

  const filteredSensors = allSensors.filter(sensor => {
    if (selectedCategory === 'ALL') return true;
    return sensorGroups[selectedCategory].ids.includes(sensor.id);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 pb-2 border-b border-[#1F2942]/40">
        {categories.map(c => (
          <button
            key={c.key}
            onClick={() => setSelectedCategory(c.key as any)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 ${
              selectedCategory === c.key
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                : 'bg-[#101529]/60 text-slate-400 hover:bg-[#1A233D] hover:text-slate-200 border border-[#1F2942]/40'
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* Grid of values */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur">
        <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36]/50 flex justify-between items-center">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">
            SCADA registers map
          </h4>
          <span className="text-[10px] text-cyan-400 font-mono">Total visible parameters: {filteredSensors.length}</span>
        </div>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0A0E1A] text-[#556994] font-bold uppercase tracking-wider border-b border-[#1F2942]/50 text-[10px]">
                <th className="p-4 pl-6">Register Address</th>
                <th className="p-4">Channel Name</th>
                <th className="p-4">Sensor Type</th>
                <th className="p-4">Current Value</th>
                <th className="p-4">Unit</th>
                <th className="p-4 text-center">Quality</th>
                <th className="p-4 pr-6 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F2942]/40 font-medium">
              {filteredSensors.map(s => {
                const reading = liveReadings[s.id];
                const value = reading ? reading.value : null;
                const quality = reading ? reading.quality : 'GOOD';
                const status = reading ? reading.status : 'OK';

                return (
                  <tr key={s.id} className="hover:bg-[#151C36]/20 transition-colors duration-150">
                    <td className="p-4 pl-6 font-mono text-[#556994]">{30000 + s.id}</td>
                    <td className="p-4 font-bold text-slate-200">{s.name}</td>
                    <td className="p-4 text-slate-400">
                      <span className="bg-[#131930] px-2 py-0.5 rounded-md border border-[#1F2942]/40 text-[10px]">
                        {s.type}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-bold text-cyan-400 text-sm">
                      {value !== null ? (
                        s.type === 'Setpoint' || s.type === 'KPI' || s.type === 'Pressure' ? value.toFixed(2) : Math.round(value).toLocaleString()
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="p-4 text-slate-400 font-semibold">{s.unit || '-'}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${quality === 'GOOD' ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-900/30' : 'bg-red-950/20 text-red-400 border border-red-900/30'}`}>
                        {quality}
                      </span>
                    </td>
                    <td className="p-4 pr-6 text-right">
                      <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold ${
                        status === 'OK' 
                          ? 'bg-emerald-950/30 text-emerald-400 border border-emerald-900/20' 
                          : 'bg-red-950/30 text-red-400 border border-red-900/20 animate-pulse'
                      }`}>
                        {status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
