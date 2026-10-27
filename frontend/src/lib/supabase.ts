import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface SensorReading {
  id: string;
  voltage: number;
  wattage: number;
  ampere: number;
  temperature: number;
  humidity: number;
  timestamp: string;
}

export interface PanelPosition {
  id: string;
  vertical_angle: number;
  horizontal_angle: number;
  timestamp: string;
}

export interface AngleCurve {
  id: string;
  time_hour: number;
  time_minute: number;
  vertical_angle: number;
  horizontal_angle: number;
  is_active: boolean;
  created_at: string;
}

export interface SystemConfig {
  id: string;
  key: string;
  value: string;
  updated_at: string;
}

export interface SensorOffset {
  id: string;
  sensor_type: string;
  offset_value: number;
  updated_at: string;
}

export interface SystemStatus {
  id: string;
  status: string;
  uptime_seconds: number;
  firmware_version: string;
  last_boot: string;
  updated_at: string;
}
