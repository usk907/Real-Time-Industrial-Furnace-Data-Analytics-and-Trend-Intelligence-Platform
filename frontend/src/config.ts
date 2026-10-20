// Configuration of API Base URL and Network Routing for Local, Cloud, and Mobile APK
export function getApiBaseUrl(): string {
  if (typeof window === 'undefined') return '';

  const saved = localStorage.getItem('IEIP_API_URL');
  if (saved && saved.trim()) {
    return saved.trim().replace(/\/+$/, '');
  }

  // Support VITE_API_URL if defined in environment
  const envUrl = (import.meta as any).env?.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  // Check if running inside Android / Capacitor native app
  const isCapacitor = Boolean(
    (window as any).Capacitor?.isNativePlatform?.() ||
    window.location.protocol === 'capacitor:' ||
    window.location.protocol === 'ionic:'
  );

  // If inside Capacitor APK with no custom URL set, default to Android Emulator loopback or standard LAN fallback
  if (isCapacitor) {
    return 'http://10.0.2.2:8000';
  }

  // Running in web browser: empty string uses relative path (proxied by Vite or Nginx)
  return '';
}

export function setApiBaseUrl(url: string) {
  if (typeof window === 'undefined') return;
  if (!url || !url.trim()) {
    localStorage.removeItem('IEIP_API_URL');
  } else {
    localStorage.setItem('IEIP_API_URL', url.trim().replace(/\/+$/, ''));
  }
}

export function getWsBaseUrl(): string {
  if (typeof window === 'undefined') return 'ws://127.0.0.1:8000/api/ws';

  const apiBase = getApiBaseUrl();
  if (apiBase) {
    try {
      const parsed = new URL(apiBase);
      const wsProto = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${wsProto}//${parsed.host}/api/ws`;
    } catch {
      // Fallback if URL parsing fails
    }
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const isDev = window.location.port && window.location.port !== '80' && window.location.port !== '443';
  const host = isDev ? `${window.location.hostname || '127.0.0.1'}:8000` : window.location.host;
  return `${protocol}://${host}/api/ws`;
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

// Transparent fetch interceptor for relative /api routes
if (typeof window !== 'undefined') {
  const originalFetch = window.fetch;
  window.fetch = function (input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    if (typeof input === 'string' && input.startsWith('/api')) {
      const baseUrl = getApiBaseUrl();
      if (baseUrl) {
        input = `${baseUrl}${input}`;
      }
    }
    return originalFetch.call(this, input, init);
  };
}

export const API_BASE_URL = getApiBaseUrl();
