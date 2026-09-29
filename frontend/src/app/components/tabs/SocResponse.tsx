import React, { useState } from 'react';
import { SOCResponse } from '@/lib/types';
import { addAuditLog, AuditAction } from '@/lib/auditLog';

interface SocResponseProps {
  socData: SOCResponse;
  assetIp: string;
}

export default function SocResponse({ socData, assetIp }: SocResponseProps) {
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const handleAction = (
    msg: string,
    auditEntry: Omit<AuditAction, 'id' | 'timestamp' | 'isoDate'>
  ) => {
    setActionStatus(msg);
    setTimeout(() => setActionStatus(null), 5000);
    addAuditLog(auditEntry);
  };

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">SOC Incident Response & Playbook</h2>
      <p className="text-slate-600 mb-6">
        This panel translates the forecast and threat context into a prioritised response. It answers: how severe is the situation, which asset matters most, and what should the analyst do next?
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div 
          className="bg-white border border-slate-300 p-5 rounded-md shadow-sm"
          style={{ borderTop: `4px solid ${socData.priority_color}` }}
        >
          <div className="text-xs font-extrabold text-slate-500 uppercase tracking-wide">Priority outcome</div>
          <div className="text-3xl font-black my-2" style={{ color: socData.priority_color }}>
            {socData.priority_level}
          </div>
          <div className="text-sm text-slate-900 font-bold mb-1">
            Target Asset: {socData.asset_name} ({assetIp})
          </div>
          <div className="text-xs text-slate-600 mt-2">
            Asset criticality: <b>{socData.asset_tier}</b> (weight {socData.asset_weight}x)
          </div>
          <div className="text-xs text-slate-600 mt-1">
            Response SLA: <b>{socData.sla_response}</b>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-2">Interpretation</div>
          <div className="text-sm leading-6 text-slate-700">
            The system combines projected risk, asset value, and the current attack stage. A higher priority means the team should act faster and with more containment pressure.
          </div>
        </div>
      </div>

      <div>
        <h4 className="font-bold text-lg mb-3">SOC action simulator</h4>
        <div className="flex flex-col gap-3">
          <button 
            onClick={() => handleAction(
              `Automated action executed: isolated host ${assetIp} via EDR integration.`,
              {
                operator: 'SOC Analyst (You)',
                targetIp: assetIp,
                subnet: `${assetIp.split('.').slice(0, 3).join('.')}.0/24`,
                actionType: 'NETWORK_ISOLATION',
                title: `Isolate Host Endpoint — ${socData.asset_name}`,
                mitreRef: socData.playbook_actions[0]?.mitre_ref ?? 'T1071 - Application Layer Protocol',
                status: 'ACTIVE',
                riskBefore: socData.composite_risk_score ?? 0.9,
                riskAfter: 0.15,
                notes: `EDR-triggered network isolation applied to ${socData.asset_name} (${assetIp}). Asset tier: ${socData.asset_tier}. SLA: ${socData.sla_response}.`
              }
            )}
            className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-[var(--color-gov-saffron)] transition-colors text-sm text-left flex justify-between items-center"
          >
            <span>🔴 Isolate host endpoint</span>
            <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
          </button>
          <button 
            onClick={() => handleAction(
              `Firewall policy deployed: SMB 445 / RDP 3389 block rule applied for host ${assetIp}.`,
              {
                operator: 'SOC Analyst (You)',
                targetIp: assetIp,
                subnet: `${assetIp.split('.').slice(0, 3).join('.')}.0/24`,
                actionType: 'FIREWALL_BLOCK',
                title: `Subnet micro-segmentation — ${socData.asset_name}`,
                mitreRef: 'T1021.002 - SMB/Admin Shares',
                status: 'ACTIVE',
                riskBefore: socData.composite_risk_score ?? 0.75,
                riskAfter: 0.25,
                notes: `Firewall micro-segmentation applied: SMB 445 and RDP 3389 block rules deployed for ${assetIp}. Asset tier: ${socData.asset_tier}.`
              }
            )}
            className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-[var(--color-gov-saffron)] transition-colors text-sm text-left flex justify-between items-center"
          >
            <span>🔒 Apply network containment</span>
            <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
          </button>
          <button 
            onClick={() => handleAction(
              `Incident acknowledged and escalated to Tier-2 response team for ${assetIp}.`,
              {
                operator: 'SOC Analyst (You)',
                targetIp: assetIp,
                subnet: `${assetIp.split('.').slice(0, 3).join('.')}.0/24`,
                actionType: 'ALERT_ACK',
                title: `Acknowledge & assign analyst — ${socData.asset_name}`,
                mitreRef: socData.playbook_actions[0]?.mitre_ref,
                status: 'COMPLETED',
                riskBefore: socData.composite_risk_score ?? 0.6,
                riskAfter: socData.composite_risk_score ?? 0.6,
                notes: `Incident for ${socData.asset_name} (${assetIp}) acknowledged and escalated to Tier-2 SOC Analyst. Priority: ${socData.priority_level}. SLA: ${socData.sla_response}.`
              }
            )}
            className="bg-slate-900 text-white font-bold py-2 px-4 rounded hover:bg-green-600 transition-colors text-sm text-left flex justify-between items-center"
          >
            <span>✅ Acknowledge and assign analyst</span>
            <span className="text-xs bg-white/20 px-2 py-1 rounded">EXECUTE</span>
          </button>
        </div>
        {actionStatus && (
          <div className="mt-3 p-3 bg-green-50 border border-green-300 text-green-800 text-sm font-bold rounded-md animate-pulse">
            {actionStatus}
          </div>
        )}
      </div>

      <h3 className="font-bold text-xl mt-8 mb-4 text-slate-800">Recommended response playbook</h3>
      <div className="space-y-2">
        {socData.playbook_actions.map(pb => (
          <div key={pb.step} className="bg-white border border-slate-200 border-l-4 border-l-slate-900 p-4 rounded shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="font-black text-slate-900 uppercase">Step {pb.step} [{pb.type}]</span> — <span className="text-slate-700 font-medium">{pb.action}</span>
            </div>
            <span className="whitespace-nowrap bg-slate-100 text-slate-900 font-bold text-xs px-3 py-1.5 rounded border border-slate-300 self-start sm:self-auto uppercase tracking-wide">
              Status: {pb.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
