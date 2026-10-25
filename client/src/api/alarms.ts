/**
 * Alarms API Client
 * Query active/cleared alarms and acknowledge incidents.
 */
import { apiFetch } from './client';

export interface ServerAlarm {
  id: number;
  ts: string;
  tag: string;
  value: number;
  threshold: number;
  severity: 'CRITICAL' | 'WARNING';
  acknowledged: boolean;
  acknowledged_by?: string | null;
  resolved_at?: string | null;
}

export async function getAlarms(active?: boolean, limit: number = 100): Promise<ServerAlarm[]> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (active !== undefined) {
    params.append('active', active ? 'true' : 'false');
  }
  return apiFetch<ServerAlarm[]>(`/api/alarms?${params.toString()}`);
}

export async function acknowledgeAlarm(alarmId: number): Promise<{ success: boolean; id: number; acknowledged_by: string; status: string }> {
  return apiFetch(`/api/alarms/${alarmId}/ack`, {
    method: 'POST'
  });
}
