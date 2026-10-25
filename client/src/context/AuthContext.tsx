import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { getWsUrl } from '../config';
import { User, TelemetryReading, LiveBuffer, TagLiveItem } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  connectionStatus: 'Connected' | 'Connecting' | 'Disconnected';
  liveTags: Record<string, TagLiveItem>;
  tagList: TagLiveItem[];
  liveReadings: Record<string, TelemetryReading>;
  liveBuffer: LiveBuffer;
  authError: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('token');
  });
  const [user, setUser] = useState<User | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'Connected' | 'Connecting' | 'Disconnected'>('Disconnected');
  const [liveTags, setLiveTags] = useState<Record<string, TagLiveItem>>({});
  const [tagList, setTagList] = useState<TagLiveItem[]>([]);
  const [liveReadings, setLiveReadings] = useState<Record<string, TelemetryReading>>({});
  const [liveBuffer, setLiveBuffer] = useState<LiveBuffer>({
    time: [],
    importPower: [],
    generationPower: []
  });
  const [authError, setAuthError] = useState<string | null>(null);

  const backoffRef = useRef(1000);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<any>(null);

  // Attempt to load profile on mount if token exists
  useEffect(() => {
    if (token) {
      fetchProfile(token);
      fetchInitialLiveTelemetry(token);
    }
  }, [token]);

  const fetchProfile = async (authToken: string) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser({
          id: data.id || 1,
          username: data.username,
          email: `${data.username}@ieip-platform.com`,
          role: data.role,
          permissions: []
        });
        setAuthError(null);
      } else {
        // Token invalid or expired
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
      }
    } catch {
      // Fallback
    }
  };

  const fetchInitialLiveTelemetry = async (authToken: string) => {
    try {
      const res = await fetch('/api/live', {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.tags && Array.isArray(data.tags)) {
          processIncomingTags(data.tags, data.ts);
        }
      }
    } catch {
      // Ignore initial poll error
    }
  };

  const processIncomingTags = (tags: TagLiveItem[], ts: string) => {
    const tagMap: Record<string, TagLiveItem> = {};
    const legacyReadings: Record<string, TelemetryReading> = {};

    let importKw = 0;
    let genKw = 0;

    tags.forEach(t => {
      tagMap[t.tag] = t;
      legacyReadings[t.tag] = {
        name: t.tag,
        value: t.value,
        unit: t.unit,
        status: t.status,
        quality: 'GOOD'
      };

      if (t.tag.includes('Power') || t.tag.includes('Active_Power')) {
        if (t.tag.startsWith('EAF1') || t.tag.startsWith('TR1') || t.tag.startsWith('TR2')) {
          importKw += t.value;
        } else {
          genKw += t.value;
        }
      }
    });

    setLiveTags(tagMap);
    setTagList(tags);
    setLiveReadings(legacyReadings);

    const timeLabel = new Date(ts).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    setLiveBuffer(prev => {
      const nextTime = [...prev.time, timeLabel].slice(-30);
      const nextImport = [...prev.importPower, Math.round(importKw)].slice(-30);
      const nextGen = [...prev.generationPower, Math.round(genKw)].slice(-30);
      return { time: nextTime, importPower: nextImport, generationPower: nextGen };
    });
  };

  // WebSocket Connection with Exponential Backoff
  useEffect(() => {
    if (!token) {
      setConnectionStatus('Disconnected');
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    let isMounted = true;

    const connectWebSocket = () => {
      if (!isMounted || !token) return;

      const wsUrl = getWsUrl(token);
      setConnectionStatus('Connecting');

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionStatus('Connected');
          backoffRef.current = 1000; // Reset backoff on successful connection
        };

        ws.onmessage = event => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            if (data.tags && Array.isArray(data.tags)) {
              processIncomingTags(data.tags, data.ts || new Date().toISOString());
            }
          } catch (e) {
            console.error('[WS]: Parse error', e);
          }
        };

        ws.onclose = event => {
          if (!isMounted) return;
          setConnectionStatus('Disconnected');
          wsRef.current = null;

          // If closed with auth failure (4401 or policy violation 1008), stop reconnecting and clear token
          if (event.code === 4401 || event.code === 1008) {
            console.warn('[WS]: Authentication rejected. Clearing stale token.');
            localStorage.removeItem('token');
            setToken(null);
            setUser(null);
            return;
          }

          // Exponential backoff reconnect
          const delay = backoffRef.current;
          backoffRef.current = Math.min(backoffRef.current * 1.5, 10000);
          console.log(`[WS]: Disconnected. Reconnecting in ${Math.round(delay)}ms...`);
          reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
        };

        ws.onerror = () => {
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
          }
        };
      } catch (err) {
        setConnectionStatus('Disconnected');
        const delay = backoffRef.current;
        backoffRef.current = Math.min(backoffRef.current * 1.5, 10000);
        reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
      }
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [token]);

  const login = async (username: string, password: string): Promise<boolean> => {
    setAuthError(null);
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser({
          id: 1,
          username: data.username,
          email: `${data.username}@ieip-platform.com`,
          role: data.role,
          permissions: []
        });
        await fetchProfile(data.access_token);
        await fetchInitialLiveTelemetry(data.access_token);
        return true;
      } else {
        const errData = await response.json();
        setAuthError(errData.detail || 'Authentication failed');
        return false;
      }
    } catch {
      setAuthError('Server unreachable. Please check connection.');
      return false;
    }
  };

  const logout = async () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setLiveTags({});
    setTagList([]);
    setLiveReadings({});
    setLiveBuffer({ time: [], importPower: [], generationPower: [] });
    setConnectionStatus('Disconnected');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        connectionStatus,
        liveTags,
        tagList,
        liveReadings,
        liveBuffer,
        authError
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
};
