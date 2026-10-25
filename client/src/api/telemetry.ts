/**
 * Telemetry API Client
 * Endpoints for Live SCADA Cache and Historical Bucket Downsampling.
 */
import { apiFetch } from './client';
import { LiveTelemetryResponse, HistoryResponse } from '../types';

export async function getLiveTelemetry(): Promise<LiveTelemetryResponse> {
  return apiFetch<LiveTelemetryResponse>('/api/live');
}

export async function getHistory(
  tag: string,
  bucket: 'raw' | '1m' | '5m' | '1h' = 'raw',
  fromTs?: string,
  toTs?: string
): Promise<HistoryResponse> {
  const params = new URLSearchParams({ tag, bucket });
  if (fromTs) params.append('from', fromTs);
  if (toTs) params.append('to', toTs);
  return apiFetch<HistoryResponse>(`/api/history?${params.toString()}`);
}

export async function checkServerHealth(): Promise<{ status: string; db_ok: boolean; server_time: string }> {
  return apiFetch('/api/health');
}
