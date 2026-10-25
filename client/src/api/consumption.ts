import { api } from './client';

export interface ConsumptionTag {
  tag_id: number;
  tag_name: string;
  register: string;
  unit: string;
  value: number;
  avg_value: number;
  max_value: number;
  min_value: number;
  sparkline: number[];
}

export interface ConsumptionGroup {
  machine_id: number;
  group_name: string;
  equipment_type: string;
  status: string;
  tags: ConsumptionTag[];
}

export interface ConsumptionResponse {
  date: string;
  shift: string;
  summary: {
    total_active_kwh: number;
    total_apparent_kvah: number;
    total_reactive_kvarh: number;
    peak_demand_kw: number;
    avg_power_factor: number;
    estimated_cost_inr: number;
    carbon_emissions_kg: number;
  };
  equipment_groups: ConsumptionGroup[];
}

export function getConsumption(date?: string, shift?: string) {
  const params = new URLSearchParams();
  if (date) params.append('date', date);
  if (shift) params.append('shift', shift);
  const q = params.toString();
  return api.get<ConsumptionResponse>(`/api/consumption${q ? `?${q}` : ''}`);
}

export function importPdfReport(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/api/reports/import-pdf', formData);
}
