// Client for the FastAPI backend (backend/app). In development, Vite proxies
// /api to the backend; set VITE_API_URL to call a backend on another origin.
const API_URL = import.meta.env.VITE_API_URL ?? '';

export const apiUrl = (path: string) => `${API_URL}${path}`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = typeof body?.detail === 'string' ? body.detail : res.statusText;
    throw new Error(`${res.status} ${detail}`);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

const get = <T>(path: string) => request<T>(path);
const send = <T>(method: string, path: string, body?: unknown) =>
  request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });

export interface SensorReading {
  recorded_at: string;
  voltage: number | null;
  current: number | null;
  wattage: number | null;
  temperature: number | null;
  humidity: number | null;
}

export type SensorOffsets = Record<'voltage' | 'current' | 'wattage' | 'temperature' | 'humidity', number>;

export interface Angles {
  yaw: number;
  roll: number;
}

export interface PanelRange {
  yaw: [number, number];
  roll: [number, number];
}

export interface PanelState {
  realtime: Angles;
  expected: Angles;
  range: PanelRange;
  offset: Angles;
}

export interface CurvePoint extends Angles {
  time: string; // "HH:MM"
}

export interface OptimalPoint extends CurvePoint {
  invert: boolean;
}

export interface TrackingStatus {
  enabled: boolean;
  running: boolean;
}

export type SystemStatusValue = 'active' | 'sleep' | 'reboot' | 'shutdown';

export interface SystemStatus {
  status: string;
  uptime_seconds: number;
  firmware_version: string;
}

export const api = {
  sensor: {
    latest: () => get<SensorReading>('/api/sensor/realtime'),
    recent: (limit = 20) => get<SensorReading[]>(`/api/sensor/recent?limit=${limit}`),
    offsets: () => get<SensorOffsets>('/api/sensor/offsets'),
    updateOffsets: (offsets: SensorOffsets) => send<SensorOffsets>('POST', '/api/sensor/offsets', offsets),
    exportUrl: () => apiUrl('/api/sensor/readings/export'),
  },
  panel: {
    state: () => get<PanelState>('/api/panel/state'),
    setAngle: (angles: Angles) => send<Angles>('POST', '/api/panel/angle', angles),
    setOffset: (offset: Angles) => send<Angles>('POST', '/api/panel/offset', offset),
    curves: () => get<CurvePoint[]>('/api/panel/curves'),
    replaceCurves: (points: CurvePoint[]) => send<CurvePoint[]>('PUT', '/api/panel/curves', points),
    upsertCurvePoint: (point: CurvePoint) => send<CurvePoint>('POST', '/api/panel/curves', point),
    deleteCurvePoint: (time: string) => send<void>('DELETE', `/api/panel/curves/${encodeURIComponent(time)}`),
    applyCurrentCurve: () => send<Angles>('POST', '/api/panel/curves/apply'),
    optimal: () => get<OptimalPoint[]>('/api/panel/optimal'),
  },
  system: {
    status: () => get<SystemStatus>('/api/system/status'),
    setStatus: (status: SystemStatusValue) => send<SystemStatus>('POST', '/api/system/status', { status }),
    tracking: () => get<TrackingStatus>('/api/system/tracking'),
    setTracking: (enable: boolean) => send<TrackingStatus>('POST', `/api/system/tracking?enable=${enable}`),
  },
  config: {
    apiServer: () => get<{ value: string }>('/api/config/api-server'),
    setApiServer: (value: string) => send<{ value: string }>('POST', '/api/config/api-server', { value }),
  },
};
