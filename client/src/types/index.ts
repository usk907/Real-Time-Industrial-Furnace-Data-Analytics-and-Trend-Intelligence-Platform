// Centralized TypeScript Type Definitions for IEIP Frontend

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
}

export interface TelemetryReading {
  name: string;
  value: number;
  unit: string;
  status: string;
  quality: string;
}

export interface LiveBuffer {
  time: string[];
  importPower: number[];
  generationPower: number[];
}

export interface NotificationItem {
  id: number;
  message: string;
  type: string;
  read: boolean;
  created_at: string;
}

export interface Plant {
  id: number;
  name: string;
  location?: string;
  timezone?: string;
  description?: string;
  status: 'ACTIVE' | 'MAINTENANCE' | 'INACTIVE';
}

export interface Department {
  id: number;
  plant_id: number;
  name: string;
  description?: string;
}

export interface Machine {
  id: number;
  department_id: number;
  name: string;
  type: string;
  rated_capacity: number;
  status: 'RUNNING' | 'STOPPED' | 'MAINTENANCE' | 'ALARM';
}

export interface Device {
  id: number;
  machine_id: number;
  name: string;
  type: string;
  register_address: string;
  unit: string;
  nominal_min?: number;
  nominal_max?: number;
  communication_status: 'ONLINE' | 'OFFLINE' | 'FAULTY';
  is_active: boolean;
}

export interface AlarmItem {
  id: number;
  time: string;
  end_time?: string;
  sensor_id: number;
  alarm_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  trigger_value: number;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'CLEARED';
  acknowledged_by?: string;
  comments?: string;
}

export interface ReportItem {
  id: number;
  created_at: string;
  name: string;
  report_type: string;
  format: string;
  file_path: string;
}

export interface SystemSettingItem {
  key: string;
  value: string;
  description?: string;
  updated_at?: string;
}

export interface AuditLogEntry {
  id: number;
  time: string;
  user_id?: number;
  action: string;
  details?: string;
  ip_address?: string;
}

export interface TagLiveItem {
  tag: string;
  value: number;
  unit: string;
  equipment?: string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
  min?: number;
  max?: number;
  ts: string;
}

export interface LiveTelemetryResponse {
  ts: string;
  tags: TagLiveItem[];
}

export interface HistoryPoint {
  ts: string;
  value: number;
  min_value?: number;
  max_value?: number;
  count?: number;
}

export interface HistoryResponse {
  tag: string;
  bucket: string;
  from_ts: string;
  to_ts: string;
  count: number;
  points: HistoryPoint[];
}

