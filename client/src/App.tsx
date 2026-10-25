import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { Trends } from './pages/Trends';
import { Analytics } from './pages/Analytics';
import { Alarms } from './pages/Alarms';
import { Reports } from './pages/Reports';
import { Management } from './pages/Management';
import { Settings } from './pages/Settings';
import { AiQuery } from './pages/AiQuery';
import { ResetPassword } from './pages/ResetPassword';
import { Consumption } from './pages/Consumption';


// Layout Components
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Chatbot } from './components/Chatbot';

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode; roles?: string[] }> = ({ children, roles }) => {
  const { token, user } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-[#070913] text-slate-100 font-sans overflow-hidden relative">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6 bg-[#080B18]">
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/live" element={<ProtectedRoute><LiveMonitoring /></ProtectedRoute>} />
            <Route path="/trends" element={<ProtectedRoute><Trends /></ProtectedRoute>} />
            <Route path="/consumption" element={<ProtectedRoute><Consumption /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/ai-query" element={<ProtectedRoute><AiQuery /></ProtectedRoute>} />
            <Route path="/alarms" element={<ProtectedRoute><Alarms /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute roles={['Admin', 'Plant Manager', 'Engineer', 'Operator']}><Reports /></ProtectedRoute>} />
            <Route path="/management" element={<ProtectedRoute roles={['Admin', 'Plant Manager']}><Management /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute roles={['Admin', 'Plant Manager']}><Settings /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
      <Chatbot />
    </div>
  );
};

const LoginRouteGuard: React.FC = () => {
  const { token } = useAuth();
  return token ? <Navigate to="/" replace /> : <Login />;
};

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginRouteGuard />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/*" element={<MainLayout />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
