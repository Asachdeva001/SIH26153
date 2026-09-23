import React, { useState } from 'react';
import { SOCResponse, MitreResponse } from '@/lib/types';

interface AuditReportProps {
  socData: SOCResponse | null;
  assetIp: string;
  scenario: string;
  currentWindowId: number;
  currentRiskScore: number;
  projectedPeakRiskScore: number;
  mitreCurrentPhase: MitreResponse | null;
  mitrePredictedPhase: MitreResponse | null;
  forecastHorizonK: number;
  xaiPrimaryDriver: string;
  xaiNarrative: string;
}

export default function AuditReport(props: AuditReportProps) {
  const [reportJson, setReportJson] = useState<string | null>(null);

  const generateReport = () => {
    if (!props.socData || !props.mitreCurrentPhase || !props.mitrePredictedPhase) return;

    const reportData = {
      organization: "National Cyber Defense Operations",
      classification: "OFFICIAL USE ONLY",
      timestamp: new Date().toISOString().replace('T', ' ').split('.')[0] + ' UTC',
      target_asset: {
        ip: props.assetIp,
        name: props.socData.asset_name,
        criticality_tier: props.socData.asset_tier,
        weight: props.socData.asset_weight
      },
      soc_risk_prioritization: {
        priority_level: props.socData.priority_level,
        composite_score: props.socData.soc_priority_score,
        sla_response: props.socData.sla_response
      },
      scenario: props.scenario,
      current_window_id: props.currentWindowId,
      current_risk_score: props.currentRiskScore,
      projected_peak_risk_score: props.projectedPeakRiskScore,
      mitre_current_phase: props.mitreCurrentPhase.name,
      mitre_predicted_phase: props.mitrePredictedPhase.name,
      forecast_horizon_k: props.forecastHorizonK,
      primary_driver: props.xaiPrimaryDriver || "None",
      narrative: props.xaiNarrative || "Run XAI analysis for insights.",
      recommended_playbook: props.socData.playbook_actions
    };

    setReportJson(JSON.stringify(reportData, null, 2));
  };

  const downloadReport = () => {
    if (!reportJson) return;
    const blob = new Blob([reportJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Cyber_Forecast_Report_T${props.currentWindowId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
      <h2 className="text-xl font-bold mb-2">📄 Security Audit & Threat Forecast Exporter</h2>
      <p className="text-slate-600 mb-6">
        Generate official threat intelligence summary report for SOC incident responders.
      </p>

      {!reportJson ? (
        <button 
          onClick={generateReport}
          disabled={!props.socData}
          className="bg-slate-900 text-white px-6 py-3 rounded font-bold hover:bg-[var(--color-gov-saffron)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {props.socData ? 'Generate JSON Report' : 'Awaiting SOC Data...'}
        </button>
      ) : (
        <div>
          <button 
            onClick={downloadReport}
            className="bg-[var(--color-gov-saffron)] text-white px-6 py-3 rounded font-bold hover:bg-slate-900 transition-colors mb-4 flex items-center gap-2"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            DOWNLOAD OFFICIAL SECURITY AUDIT REPORT (JSON)
          </button>
          
          <pre className="bg-slate-900 text-green-400 p-4 rounded-md overflow-x-auto text-sm font-mono border border-slate-700 shadow-inner max-h-[500px]">
            {reportJson}
          </pre>
        </div>
      )}
    </div>
  );
}
