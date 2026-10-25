import { api } from './client';

export interface DashboardResponse {
  kpis: {
    grid_power_combined: number;
    generation_combined: number;
    cb5214_kw: number;
    cb14_kw: number;
    cb52g4_kw: number;
    sms_allocated_power: number;
    sms_run_power: number;
    sms_1_run_power: number;
    sms_4_run_power: number;
    sms_4_utl_pct: number;
    running_furnace_count: number;
    total_machines: number;
    running_machines: number;
    offline_machines: number;
    faulty_machines: number;
    avg_pf: number;
    load_factor: number;
    today_energy_kwh: number;
    monthly_energy_kwh: number;
    carbon_emission: number;
    energy_cost: number;
  };
  active_alarms_count: number;
  predictions: Array<{
    horizon: number;
    sensor_id: number;
    predicted: number;
    upper: number;
    lower: number;
  }>;
}

export function getDashboard() {
  return api.get<DashboardResponse>('/api/dashboard');
}

export function getTrends(sensorId: number, quickFilter = '1h', shift?: string) {
  const shiftParam = shift ? `&shift=${encodeURIComponent(shift)}` : '';
  return api.get(`/api/trends?sensor_id=${sensorId}&quick_filter=${quickFilter}${shiftParam}`);
}

export function getAnalytics() {
  return api.get('/api/analytics');
}

export function getTapStatus() {
  return api.get('/api/tap/status');
}

export function getDevices() {
  return api.get('/api/devices');
}
