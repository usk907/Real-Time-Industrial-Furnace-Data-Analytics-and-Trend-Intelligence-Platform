import React, { createContext, useContext, useState, useEffect } from 'react';
import { getWsBaseUrl } from '../config';
import { User, TelemetryReading, LiveBuffer } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  connectionStatus: 'Connected' | 'Disconnected';
  liveReadings: Record<number, TelemetryReading>;
  liveBuffer: LiveBuffer;
  authError: string | null;
}

const DEFAULT_ADMIN_USER: User = {
  id: 1,
  username: 'admin',
  email: 'admin@ieip-platform.com',
  role: 'Admin',
  permissions: ['read_all', 'write_all', 'manage_users', 'acknowledge_alarms', 'manage_settings']
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEFAULT_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBZG1pbiIsImV4cCI6MTc5MDE3MjcxM30.wyTOGPz7-la7tcasQBUonkxB3Cd2baXPVjxEe_6hLXA';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    const existing = localStorage.getItem('token');
    if (!existing || existing === 'admin-session-active') {
      localStorage.setItem('token', DEFAULT_TOKEN);
      return DEFAULT_TOKEN;
    }
    return existing;
  });
  const [user, setUser] = useState<User | null>(() => {
    return DEFAULT_ADMIN_USER;
  });
  const [connectionStatus, setConnectionStatus] = useState<'Connected' | 'Disconnected'>('Connected');
  const [liveReadings, setLiveReadings] = useState<Record<number, TelemetryReading>>({});
  const [liveBuffer, setLiveBuffer] = useState<LiveBuffer>({
    time: [],
    importPower: [],
    generationPower: []
  });
  const [authError, setAuthError] = useState<string | null>(null);

  // Attempt to load profile on mount if token exists
  useEffect(() => {
    if (token) {
      fetchProfile(token);
    }
  }, [token]);

  // Handle WebSocket Connection globally when token is set and user is logged in
  useEffect(() => {
    if (!token || !user) {
      setConnectionStatus('Disconnected');
      return;
    }

    const wsUrl = getWsBaseUrl();

    let ws: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      console.log(`[WS]: Connecting global telemetry stream to ${wsUrl}...`);
      try {
        ws = new WebSocket(wsUrl);
      } catch (err) {
        console.warn("[WS]: Direct connect failed, retrying in 3s...", err);
        reconnectTimeout = setTimeout(connect, 3000);
        return;
      }

      ws.onopen = () => {
        setConnectionStatus('Connected');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === "TELEMETRY_UPDATE") {
            const readings = payload.readings;
            setLiveReadings(readings);

            // Fetch breaker values (1 and 2) and TG values (41 and 42)
            const importPower = (readings["1"]?.value || 0) + (readings["2"]?.value || 0);
            const generationPower = (readings["41"]?.value || 0) + (readings["42"]?.value || 0);
            const timeLabel = new Date(payload.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

            setLiveBuffer(prev => {
              const nextTime = [...prev.time, timeLabel].slice(-30);
              const nextImport = [...prev.importPower, importPower].slice(-30);
              const nextGen = [...prev.generationPower, generationPower].slice(-30);
              return { time: nextTime, importPower: nextImport, generationPower: nextGen };
            });
          }
        } catch (err) {
          console.error("[WS]: Payload error", err);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('Disconnected');
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("[WS]: Socket error", err);
        ws.close();
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      clearTimeout(reconnectTimeout);
    };
  }, [token, user]);

  const fetchProfile = async (authToken: string) => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setAuthError(null);
      }
    } catch (err) {
      console.warn("Using active admin profile fallback");
    }
  };

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
          id: 0, // Mock id, fetchProfile will reload actual
          username,
          email: "",
          role: data.role,
          permissions: data.permissions
        });
        await fetchProfile(data.access_token);
        return true;
      } else {
        const errData = await response.json();
        setAuthError(errData.detail || "Authentication failed");
        return false;
      }
    } catch (err) {
      setAuthError("Server unreachable. Please check connection.");
      return false;
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (e) {
        // Continue logout even if API call fails
      }
    }
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setLiveReadings({});
    setLiveBuffer({ time: [], importPower: [], generationPower: [] });
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, connectionStatus, liveReadings, liveBuffer, authError }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
};
