import { api } from './client';

export interface AlarmItem {
  id: number;
  time: string;
  end_time?: string | null;
  sensor_id: number;
  alarm_type: string;
  severity: string;
  trigger_value: number;
  status: string;
  comments?: string | null;
  acknowledged_by?: string | null;
}

export interface NotificationItem {
  id: number;
  message: string;
  type: string;
  read: boolean;
  created_at: string;
}

export function getAlarms(status?: string, severity?: string) {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (severity) params.append('severity', severity);
  const q = params.toString();
  return api.get<AlarmItem[]>(`/api/alarms${q ? `?${q}` : ''}`);
}

export function acknowledgeAlarm(alarmId: number, comments: string, acknowledgedBy: string) {
  return api.put(`/api/alarms/${alarmId}/acknowledge`, { comments, acknowledged_by: acknowledgedBy });
}

export function getNotifications() {
  return api.get<NotificationItem[]>('/api/notifications');
}

export function markNotificationRead(noteId: number) {
  return api.put(`/api/notifications/${noteId}/read`);
}
