import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, AlertCircle, Mail, ArrowRight } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, authError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [email, setEmail] = useState('');
  const [forgotMessage, setForgotMessage] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [forgotLoading, setForgotLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    await login(username, password);
    setLoading(false);
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setForgotLoading(true);
    setForgotError(null);
    setForgotMessage(null);

    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Unable to request reset link');
      }
      setForgotMessage(data.reset_link_mock || data.message || 'Reset link generated.');
    } catch (err: any) {
      setForgotError(err.message || 'Unable to request password reset.');
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#070913] relative overflow-hidden font-sans select-none justify-center items-center">
      {/* Dynamic background lights */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[60%] rounded-full bg-blue-600/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[60%] rounded-full bg-cyan-600/10 blur-[150px] pointer-events-none" />

      {/* Main Glass Box Container */}
      <div className="w-full max-w-4xl grid md:grid-cols-2 rounded-3xl border border-[#1F2942]/60 overflow-hidden bg-[#0A0E1C]/80 backdrop-blur-md shadow-2xl relative z-10 mx-4">
        {/* Card 1: Banner Context */}
        <div className="bg-gradient-to-br from-[#101730] to-[#0E101F] p-10 flex flex-col justify-between border-r border-[#1F2942]/40 relative">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent pointer-events-none" />
          
          <div className="flex items-center gap-3 relative z-10">
            <Shield className="h-8 w-8 text-cyan-400" />
            <div>
              <h1 className="font-black text-sm tracking-widest text-white">IEIP ENTERPRISE</h1>
              <p className="text-[9px] text-[#556994] font-bold uppercase tracking-widest">Energy Intelligence</p>
            </div>
          </div>

          <div className="my-10 relative z-10">
            <h2 className="text-2xl font-black text-white leading-tight">
              SCADA Analytics & prediction controls.
            </h2>
            <p className="text-xs text-slate-400 mt-3 leading-relaxed">
              Real-time monitoring, AI forecasting models, and energy consumption rollups for industrial melt shops.
            </p>
          </div>

          {/* Seed credentials guide box */}
          <div className="p-4 bg-[#141C38]/60 border border-blue-500/20 rounded-2xl relative z-10 text-xs">
            <p className="font-bold text-cyan-400 uppercase tracking-wider text-[10px] mb-2">Seed credentials for verification</p>
            <div className="space-y-1 text-slate-300 font-mono text-[11px]">
              <p>Username: <span className="text-white font-bold">admin</span></p>
              <p>Password: <span className="text-white font-bold">admin123</span></p>
            </div>
            <p className="text-[10px] text-slate-500 mt-2 italic">Role: Admin privileges</p>
          </div>
        </div>

        {/* Card 2: Login Form */}
        <div className="p-12 flex flex-col justify-center bg-[#090C1A]">
          <h3 className="text-xl font-extrabold text-white">Platform Access</h3>
          <p className="text-xs text-slate-400 mt-1">Authenticate using your credentials</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {authError && (
              <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 rounded-xl text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            <div>
              <label className="block text-slate-400 text-[11px] font-bold uppercase tracking-wider mb-2">Username</label>
              <div className="relative">
                <User className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
                <input 
                  type="text"
                  required
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#0D1227] border border-[#1F2942]/60 hover:border-slate-700 focus:border-blue-500 rounded-xl p-3.5 pl-11 text-slate-100 placeholder-slate-600 focus:outline-none transition text-xs font-semibold"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 text-[11px] font-bold uppercase tracking-wider mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
                <input 
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#0D1227] border border-[#1F2942]/60 hover:border-slate-700 focus:border-blue-500 rounded-xl p-3.5 pl-11 text-slate-100 placeholder-slate-600 focus:outline-none transition text-xs font-semibold"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white font-extrabold py-3.5 px-4 rounded-xl shadow-lg shadow-blue-600/20 text-xs uppercase tracking-wider transition-all duration-300 disabled:opacity-50 mt-2"
            >
              {loading ? "Authenticating..." : "Sign In to Console"}
            </button>
          </form>

          <button
            type="button"
            onClick={() => setShowForgot((prev) => !prev)}
            className="mt-4 text-left text-[11px] font-bold uppercase tracking-wider text-cyan-400 hover:text-cyan-300"
          >
            {showForgot ? 'Hide password recovery' : 'Forgot password?'}
          </button>

          {showForgot && (
            <form onSubmit={handleForgotPassword} className="mt-4 space-y-3 rounded-2xl border border-[#1F2942]/50 bg-[#0D1227] p-4">
              <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <Mail className="h-4 w-4 text-cyan-400" />
                Request reset link
              </div>
              {forgotError && (
                <div className="rounded-xl border border-red-900/30 bg-red-950/20 p-3 text-xs text-red-400">
                  {forgotError}
                </div>
              )}
              {forgotMessage && (
                <div className="rounded-xl border border-emerald-900/30 bg-emerald-950/20 p-3 text-xs text-emerald-400 break-all">
                  {forgotMessage}
                </div>
              )}
              <div className="relative">
                <Mail className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
                <input
                  type="email"
                  required
                  placeholder="Enter account email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#0A0E1C] border border-[#1F2942]/60 rounded-xl p-3.5 pl-11 text-slate-100 placeholder-slate-600 focus:border-cyan-400 focus:outline-none transition text-xs font-semibold"
                />
              </div>
              <button
                type="submit"
                disabled={forgotLoading}
                className="w-full bg-[#101730] hover:bg-[#142144] text-cyan-300 font-extrabold py-3 px-4 rounded-xl border border-[#24406d] text-[11px] uppercase tracking-wider transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {forgotLoading ? 'Generating...' : 'Send Recovery Link'}
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
