import React, { useState, useEffect } from 'react';
import { Server, Wifi, WifiOff, RefreshCw, CheckCircle2, AlertTriangle, X, Globe, Smartphone } from 'lucide-react';
import { getApiBase, setApiBase, getDeviceType } from '../config';

interface ServerSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ServerSettingsModal: React.FC<ServerSettingsModalProps> = ({ isOpen, onClose }) => {
  const [url, setUrl] = useState('');
  const [testing, setTesting] = useState(false);
  const [pingStatus, setPingStatus] = useState<{
    ok: boolean;
    latencyMs?: number;
    error?: string;
  } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setUrl(getApiBase());
      setPingStatus(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestConnection = async (targetUrl: string) => {
    setTesting(true);
    setPingStatus(null);
    const start = performance.now();
    try {
      const trimmed = targetUrl.trim().replace(/\/+$/, '');
      const testEndpoint = trimmed ? `${trimmed}/api/health` : '/api/health';
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);

      const res = await fetch(testEndpoint, { signal: controller.signal });
      clearTimeout(timeout);
      const latency = Math.round(performance.now() - start);

      if (res.ok) {
        setPingStatus({ ok: true, latencyMs: latency });
      } else {
        setPingStatus({ ok: false, error: `HTTP ${res.status}` });
      }
    } catch (err: any) {
      setPingStatus({
        ok: false,
        error: err.name === 'AbortError' ? 'Connection timed out (>5s)' : 'Cannot reach backend'
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    setApiBase(url.trim());
    window.location.reload();
  };

  const handleResetDefault = () => {
    setApiBase('');
    setUrl('');
    setPingStatus(null);
    window.location.reload();
  };

  const setPreset = (presetUrl: string) => {
    setUrl(presetUrl);
    handleTestConnection(presetUrl);
  };

  const device = getDeviceType();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#0C1021] border border-[#1F2B50] rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-[#1F2B50] bg-[#10162E] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/60 border border-cyan-800/40 text-cyan-400">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">Backend Connection Settings</h3>
              <p className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                {device === 'app' ? (
                  <>
                    <Smartphone className="h-3 w-3 text-cyan-400" />
                    <span>Native Android Client</span>
                  </>
                ) : (
                  <>
                    <Globe className="h-3 w-3 text-emerald-400" />
                    <span>Web Browser Client</span>
                  </>
                )}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1A2346] transition-all"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5 text-xs">
          <div>
            <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              API Server Base URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="e.g. http://192.168.1.10:8000 or https://tunnel.trycloudflare.com"
                className="flex-1 bg-[#131A38] border border-[#23305A] rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono transition-all"
              />
              <button
                onClick={() => handleTestConnection(url)}
                disabled={testing}
                className="px-4 py-2.5 rounded-xl bg-[#1C274E] hover:bg-[#253468] border border-[#2B3B70] text-cyan-300 font-bold flex items-center gap-2 transition-all disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${testing ? 'animate-spin' : ''}`} />
                <span>{testing ? 'Pinging...' : 'Ping'}</span>
              </button>
            </div>
            <p className="text-[10px] text-slate-500 mt-1.5">
              Leave blank to use the default relative proxy (<code className="text-cyan-400">/api</code> on port 5173).
            </p>
          </div>

          {/* Test Status Banner */}
          {pingStatus && (
            <div className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
              pingStatus.ok 
                ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300' 
                : 'bg-red-950/40 border-red-800/60 text-red-300'
            }`}>
              <div className="flex items-center gap-2.5">
                {pingStatus.ok ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
                )}
                <span className="font-medium text-[11px]">
                  {pingStatus.ok 
                    ? `Connected! Backend online (${pingStatus.latencyMs}ms latency)` 
                    : `Connection failed: ${pingStatus.error}`}
                </span>
              </div>
              {pingStatus.ok ? (
                <Wifi className="h-4 w-4 text-emerald-400" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-400" />
              )}
            </div>
          )}

          {/* One-Click Presets */}
          <div>
            <span className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
              Quick Presets
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPreset('http://localhost:8000')}
                className="p-2.5 rounded-xl bg-[#121833] hover:bg-[#1A2348] border border-[#212E55] text-left transition-all"
              >
                <div className="font-bold text-[11px] text-slate-200">Local PC</div>
                <div className="text-[10px] text-slate-500 font-mono">http://localhost:8000</div>
              </button>

              <button
                type="button"
                onClick={() => setPreset('http://10.0.2.2:8000')}
                className="p-2.5 rounded-xl bg-[#121833] hover:bg-[#1A2348] border border-[#212E55] text-left transition-all"
              >
                <div className="font-bold text-[11px] text-slate-200">Android Emulator</div>
                <div className="text-[10px] text-slate-500 font-mono">http://10.0.2.2:8000</div>
              </button>
            </div>
          </div>

          <div className="p-3 bg-[#111730] border border-[#1E294B] rounded-xl text-[11px] text-slate-400 leading-relaxed">
            <span className="font-bold text-cyan-400">Mobile Phone Setup:</span> Run <code className="text-white bg-[#0A0D1B] px-1.5 py-0.5 rounded font-mono">tunnel.bat</code> on your PC to generate a free public URL, then enter the <code className="text-amber-300 font-mono">https://*.trycloudflare.com</code> address above to monitor your furnaces live from anywhere.
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#1F2B50] bg-[#10162E] flex items-center justify-between">
          <button
            onClick={handleResetDefault}
            className="px-3.5 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1A2348] transition-all text-xs"
          >
            Reset to Default
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1A2348] transition-all text-xs"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold transition-all text-xs shadow-lg shadow-cyan-900/30"
            >
              Save & Apply
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
