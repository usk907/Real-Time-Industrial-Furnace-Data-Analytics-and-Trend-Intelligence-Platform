/**
 * Industrial Energy Intelligence Platform (IEIP)
 * Central Client Network Configuration Module (Part 3)
 */

export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('api_base') || localStorage.getItem('IEIP_API_URL');
    if (saved && saved.trim()) {
      return saved.trim().replace(/\/+$/, '');
    }
  }

  const envBase = (import.meta as any).env?.VITE_API_BASE || (import.meta as any).env?.VITE_API_URL;
  if (envBase && typeof envBase === 'string' && envBase.trim()) {
    return envBase.trim().replace(/\/+$/, '');
  }

  // Check if running inside Android / Capacitor native app
  const isCapacitor = Boolean(
    typeof window !== 'undefined' &&
    ((window as any).Capacitor?.isNativePlatform?.() ||
      window.location.protocol === 'capacitor:' ||
      window.location.protocol === 'ionic:')
  );

  if (isCapacitor) {
    return 'http://10.0.2.2:8001';
  }

  return 'http://localhost:8001';
}

export function setApiBase(url: string) {
  if (typeof window === 'undefined') return;
  const clean = url.trim().replace(/\/+$/, '');
  if (!clean) {
    localStorage.removeItem('api_base');
    localStorage.removeItem('IEIP_API_URL');
  } else {
    localStorage.setItem('api_base', clean);
    localStorage.setItem('IEIP_API_URL', clean);
  }
}

export function getWsUrl(token?: string): string {
  const apiBase = getApiBase();
  let baseWs = 'ws://localhost:8000/api/ws';
  try {
    const parsed = new URL(apiBase);
    const wsProto = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    baseWs = `${wsProto}//${parsed.host}/api/ws`;
  } catch {
    baseWs = apiBase.replace(/^http/, 'ws') + '/api/ws';
  }

  if (token) {
    return `${baseWs}?token=${encodeURIComponent(token)}`;
  }
  return baseWs;
}

export function getDeviceType(): 'web' | 'app' {
  if (typeof window !== 'undefined') {
    if (
      (window as any).Capacitor?.isNativePlatform?.() ||
      window.location.protocol === 'capacitor:' ||
      window.location.protocol === 'ionic:' ||
      /Android.*IEIP/i.test(navigator.userAgent)
    ) {
      return 'app';
    }
  }
  return 'web';
}

export const API_BASE = getApiBase();
export const WS_URL = getWsUrl();

// Transparent fetch interceptor so relative /api routes are routed to API_BASE
if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;
  window.fetch = function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    if (typeof input === 'string' && input.startsWith('/api')) {
      const base = getApiBase();
      input = `${base}${input}`;
    }
    return originalFetch.call(this, input, init);
  };
}

// Backward-compatible alias helpers
export const getApiBaseUrl = getApiBase;
export const setApiBaseUrl = setApiBase;
export const getWsBaseUrl = getWsUrl;
export const API_BASE_URL = API_BASE;
