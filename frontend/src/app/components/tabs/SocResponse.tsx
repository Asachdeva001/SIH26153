import React, { useState } from 'react';
import { SOCResponse } from '@/lib/types';

interface SocResponseProps {
  socData: SOCResponse;
  assetIp: string;
}

export default function SocResponse({ socData, assetIp }: SocResponseProps) {
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const handleAction = (msg: string) => {
    setActionStatus(msg);
    setTimeout(() => setActionStatus(null), 5000);
  };

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">🛡️ SOC Incident Response & Automated Playbooks</h2>
      <p className="text-slate-600 mb-6">
        Combines World Model Forecast Risk, Asset Criticality Weights, and MITRE ATT&CK Severity into an actionable SOC response framework.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div 
          className="bg-white border border-slate-300 p-5 rounded-md shadow-sm"
          style={{ borderTop: `4px solid ${socData.priority_color}` }}
        >
          <div className="text-xs font-extrabold text-slate-500 uppercase tracking-wide">COMPOSITE RISK PRIORITIZATION</div>
          <div className="text-3xl font-black my-2" style={{ color: socData.priority_color }}>
            {socData.priority_level}
          </div>
          <div className="text-sm text-slate-900 font-bold mb-1">
            Target Asset: {socData.asset_name} ({assetIp})
          </div>
          <div className="text-xs text-slate-600 mt-2">
            Asset Criticality: <b>{socData.asset_tier}</b> (Weight: {socData.asset_weight}x)
          </div>
          <div className="text-xs text-slate-600 mt-1">
            Incident Response SLA: <b>{socData.sla_response}</b>
          </div>
        </div>

        <div>
          <h4 className="font-bold text-lg mb-3">SOC Automated Action Simulator</h4>
          <div className="flex flex-col gap-3">
            <button 
              onClick={() => handleAction(`AUTOMATED ACTION EXECUTED: Isolated host ${assetIp} via EDR integration.`)}
              className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-[var(--color-gov-saffron)] transition-colors text-sm text-left flex justify-between items-center"
            >
              <span>🔴 Isolate Host Endpoint</span>
              <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
            </button>
            <button 
              onClick={() => handleAction(`FIREWALL POLICY DEPLOYED: Applied SMB 445 / RDP 3389 block rule for host ${assetIp}.`)}
              className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-[var(--color-gov-saffron)] transition-colors text-sm text-left flex justify-between items-center"
            >
              <span>🔒 Subnet Micro-Segment</span>
              <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
            </button>
            <button 
              onClick={() => handleAction(`INCIDENT ACKNOWLEDGED: Dispatched Tier-2 SOC Analyst ticket for ${assetIp}.`)}
              className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-green-600 transition-colors text-sm text-left flex justify-between items-center"
            >
              <span>✅ Acknowledge & Assign Analyst</span>
              <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
            </button>
          </div>
          {actionStatus && (
            <div className="mt-3 p-3 bg-green-50 border border-green-300 text-green-800 text-sm font-bold rounded-md animate-pulse">
              {actionStatus}
            </div>
          )}
        </div>
      </div>

      <h3 className="font-bold text-xl mb-4 text-slate-800">📋 Recommended Automated Response Playbook</h3>
      <div className="space-y-2">
        {socData.playbook_actions.map(pb => (
          <div key={pb.step} className="bg-white border border-slate-200 border-l-4 border-l-slate-900 p-4 rounded shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="font-black text-slate-900 uppercase">STEP {pb.step} [{pb.type}]</span> — <span className="text-slate-700 font-medium">{pb.action}</span>
            </div>
            <span className="whitespace-nowrap bg-slate-100 text-slate-900 font-bold text-xs px-3 py-1.5 rounded border border-slate-300 self-start sm:self-auto uppercase tracking-wide">
              STATUS: {pb.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
