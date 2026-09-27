import React, { useState } from 'react';
import { 
  X, AlertTriangle, ShieldAlert, ShieldCheck, ChevronRight, 
  Flame, Radio, CheckCircle2, Ban, ExternalLink, Bell 
} from 'lucide-react';

export interface AlertItem {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  mitreTechnique: string;
  mitreId: string;
  targetIp: string;
  timestamp: string;
  description: string;
  status: 'ACTIVE' | 'ISOLATED' | 'RESOLVED';
  suggestedAction: string;
  targetTab: string;
}

interface AlertDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alerts: AlertItem[];
  onInvestigate: (alert: AlertItem) => void;
  onIsolateHost: (ip: string, alertId: string) => void;
  onDismissAlert: (id: string) => void;
  onClearAll: () => void;
}

export default function AlertDrawer({
  isOpen,
  onClose,
  alerts,
  onInvestigate,
  onIsolateHost,
  onDismissAlert,
  onClearAll
}: AlertDrawerProps) {
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH'>('ALL');

  if (!isOpen) return null;

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'CRITICAL') return a.severity === 'CRITICAL';
    if (filter === 'HIGH') return a.severity === 'HIGH' || a.severity === 'CRITICAL';
    return true;
  });

  const getSeverityBadge = (sev: AlertItem['severity']) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-600 border-rose-200 dark:border-rose-900/40';
      case 'HIGH':
        return 'bg-amber-500/10 text-amber-600 border-amber-200 dark:border-amber-900/40';
      case 'MEDIUM':
        return 'bg-sky-500/10 text-sky-600 border-sky-200 dark:border-sky-900/40';
      default:
        return 'bg-slate-500/10 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end transition-opacity duration-300">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity" 
        onClick={onClose} 
      />

      {/* Drawer Container */}
      <div className="relative z-10 flex h-full w-full max-w-md flex-col bg-white shadow-2xl transition-transform duration-300 border-l border-slate-200 font-sans">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-rose-50 text-rose-600 border border-rose-100 shadow-xs">
              <ShieldAlert size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 font-roboto">SOC Incident Feed</h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-100 text-rose-700">
                  {alerts.length} Active
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Real-time predictive telemetry alerts</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Filters & Actions */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-5 py-2.5 text-xs">
          <div className="flex items-center gap-1.5 font-medium">
            <button 
              onClick={() => setFilter('ALL')} 
              className={`rounded-md px-2.5 py-1 transition ${filter === 'ALL' ? 'bg-white font-bold text-slate-900 shadow-xs border border-slate-200/80' : 'text-slate-500 hover:text-slate-800'}`}
            >
              All ({alerts.length})
            </button>
            <button 
              onClick={() => setFilter('CRITICAL')} 
              className={`rounded-md px-2.5 py-1 transition ${filter === 'CRITICAL' ? 'bg-white font-bold text-rose-600 shadow-xs border border-slate-200/80' : 'text-slate-500 hover:text-rose-600'}`}
            >
              Critical ({alerts.filter(a => a.severity === 'CRITICAL').length})
            </button>
          </div>
          {alerts.length > 0 && (
            <button 
              onClick={onClearAll}
              className="text-xs text-slate-400 hover:text-slate-700 font-medium transition"
            >
              Acknowledge All
            </button>
          )}
        </div>

        {/* Alert List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 no-scrollbar">
          {filteredAlerts.length === 0 ? (
            <div className="flex h-64 flex-col items-center justify-center text-center p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 mb-3">
                <CheckCircle2 size={24} />
              </div>
              <h4 className="text-sm font-bold text-slate-800">All Clear</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                No active threats matching the filter criteria. Real-time telemetry is running nominally.
              </p>
            </div>
          ) : (
            filteredAlerts.map(alert => (
              <div 
                key={alert.id}
                className="group relative rounded-xl border border-slate-200/80 bg-white p-4 shadow-xs transition hover:shadow-md hover:border-slate-300"
              >
                {/* Header row */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-bold ${getSeverityBadge(alert.severity)}`}>
                      <Flame size={11} /> {alert.severity}
                    </span>
                    <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-mono font-semibold text-slate-600">
                      {alert.mitreId}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {alert.timestamp}
                  </span>
                </div>

                {/* Title */}
                <h4 className="text-xs font-bold text-slate-900 group-hover:text-indigo-600 transition">
                  {alert.title}
                </h4>
                
                {/* Description */}
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                  {alert.description}
                </p>

                {/* Target Asset Pill */}
                <div className="mt-3 flex items-center justify-between text-[11px] bg-slate-50 rounded-lg p-2 border border-slate-100">
                  <span className="text-slate-500 font-medium">Target Host:</span>
                  <span className="font-mono font-bold text-slate-800">{alert.targetIp}</span>
                </div>

                {/* Actions */}
                <div className="mt-3 flex items-center gap-2 pt-2 border-t border-slate-100">
                  <button 
                    onClick={() => onInvestigate(alert)}
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 py-1.5 text-xs font-bold transition shadow-xs"
                  >
                    Investigate <ExternalLink size={12} />
                  </button>
                  {alert.status === 'ISOLATED' ? (
                    <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-100">
                      <CheckCircle2 size={13} /> Isolated
                    </span>
                  ) : (
                    <button 
                      onClick={() => onIsolateHost(alert.targetIp, alert.id)}
                      className="flex items-center gap-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 px-3 py-1.5 text-xs font-bold transition border border-rose-100"
                    >
                      <Ban size={12} /> Isolate
                    </button>
                  )}
                  <button 
                    onClick={() => onDismissAlert(alert.id)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
                    title="Dismiss alert"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-100 bg-slate-50/70 p-3.5 text-center">
          <div className="flex items-center justify-center gap-2 text-[11px] text-slate-500 font-medium">
            <Radio size={13} className="text-emerald-500 animate-pulse" />
            <span>Listening on Telemetry Window Stream</span>
          </div>
        </div>
      </div>
    </div>
  );
}
