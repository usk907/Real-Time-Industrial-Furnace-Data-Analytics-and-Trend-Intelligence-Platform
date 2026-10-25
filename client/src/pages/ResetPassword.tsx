import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Lock, Shield, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';

export const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!token) {
      setError('Reset token is missing from the link.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Password reset failed');
      }

      setMessage(data.message || 'Password updated successfully.');
      setPassword('');
      setConfirmPassword('');
      setTimeout(() => navigate('/login', { replace: true }), 1600);
    } catch (err: any) {
      setError(err.message || 'Unable to reset password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#070913] px-4 text-slate-100">
      <div className="w-full max-w-lg rounded-3xl border border-[#1F2942]/60 bg-[#0A0E1C]/90 p-8 shadow-2xl backdrop-blur">
        <div className="flex items-center gap-3">
          <Shield className="h-8 w-8 text-cyan-400" />
          <div>
            <h1 className="text-lg font-black uppercase tracking-widest">Reset Password</h1>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Set a new credential for your account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && (
            <div className="flex items-start gap-2 rounded-xl border border-red-900/30 bg-red-950/20 p-3 text-xs text-red-400">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="flex items-start gap-2 rounded-xl border border-emerald-900/30 bg-emerald-950/20 p-3 text-xs text-emerald-400">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{message}</span>
            </div>
          )}

          <div>
            <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-400">New Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-[#1F2942]/60 bg-[#0D1227] p-3.5 pl-11 text-sm text-slate-100 placeholder-slate-600 focus:border-cyan-400 focus:outline-none"
                placeholder="Enter new password"
                autoComplete="new-password"
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-400">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3.5 h-4.5 w-4.5 text-slate-500" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-xl border border-[#1F2942]/60 bg-[#0D1227] p-3.5 pl-11 text-sm text-slate-100 placeholder-slate-600 focus:border-cyan-400 focus:outline-none"
                placeholder="Confirm new password"
                autoComplete="new-password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 px-4 py-3.5 text-xs font-extrabold uppercase tracking-wider text-white transition hover:from-blue-700 hover:to-cyan-600 disabled:opacity-50"
          >
            {loading ? 'Updating...' : 'Update Password'}
          </button>
        </form>

        <Link to="/login" className="mt-5 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400 hover:text-cyan-300">
          <ArrowLeft className="h-4 w-4" />
          Back to login
        </Link>
      </div>
    </div>
  );
};
