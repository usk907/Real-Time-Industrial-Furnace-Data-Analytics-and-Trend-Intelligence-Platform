import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions: string[];
}

interface TelemetryReading {
  name: string;
  value: number;
  unit: string;
  status: string;
  quality: string;
}

interface LiveBuffer {
  time: string[];
  importPower: number[];
  generationPower: number[];
}

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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>({
    id: 1,
    username: "admin",
    email: "admin@ieip-platform.com",
    role: "Admin",
    permissions: ["read_all", "write_all", "manage_users", "acknowledge_alarms", "manage_settings"]
  });
  const [token, setToken] = useState<string | null>("mock-bypass-token");
  const [connectionStatus, setConnectionStatus] = useState<'Connected' | 'Disconnected'>('Disconnected');
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

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    // Use Nginx proxy URL path. Docker Compose maps Nginx port 80.
    // In local development, port is 8000 for FastAPI, Nginx serves frontend on port 80 proxying api.
    const host = window.location.port === '3000' ? `${window.location.hostname}:8000` : window.location.host;
    const wsUrl = `${protocol}://${host}/api/ws`;

    let ws: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      console.log("[WS]: Connecting global telemetry stream...");
      ws = new WebSocket(wsUrl);

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
    if (authToken === "mock-bypass-token") return;
    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        setAuthError(null);
      } else {
        logout();
      }
    } catch (err) {
      console.error("Profile load failed", err);
      logout();
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
