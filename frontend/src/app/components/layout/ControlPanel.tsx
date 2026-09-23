import React, { useRef } from 'react';

const SCENARIOS = [
  "APT Multi-Stage Campaign",
  "Ransomware Rapid Outbreak",
  "DDoS & C2 Beaconing",
  "Benign Intranet Baseline"
];

const ASSETS = [
  { ip: "10.0.0.15", name: "Domain Controller / Active Directory", tier: "Tier 1 - Mission Critical" },
  { ip: "10.0.0.5", name: "Core SQL Enterprise Database", tier: "Tier 1 - Mission Critical" },
  { ip: "198.51.100.44", name: "External Perimeter Gateway / DMZ", tier: "Tier 1 - Mission Critical" },
  { ip: "10.0.0.50", name: "Internal Payroll & HR Server", tier: "Tier 2 - Business Essential" },
  { ip: "192.168.1.100", name: "Developer Workstation Endpoint", tier: "Tier 3 - Standard Endpoint" }
];

interface ControlPanelProps {
  isOpen: boolean;
  dataSource: string;
  setDataSource: (s: string) => void;
  scenario: string;
  setScenario: (s: string) => void;
  onFileUpload: (file: File) => void;
  assetIp: string;
  setAssetIp: (ip: string) => void;
  kSteps: number;
  setKSteps: (k: number) => void;
  currentWindowId: number;
  setCurrentWindowId: (w: number) => void;
  maxWindowId: number;
  riskThreshold: number;
  setRiskThreshold: (r: number) => void;
}

export default function ControlPanel(props: ControlPanelProps) {
  const {
    isOpen, dataSource, setDataSource, scenario, setScenario, onFileUpload,
    assetIp, setAssetIp, kSteps, setKSteps, currentWindowId, setCurrentWindowId,
    maxWindowId, riskThreshold, setRiskThreshold
  } = props;

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  return (
    <div className="w-80 h-full bg-slate-100 border-r border-slate-300 p-4 overflow-y-auto flex-shrink-0 text-slate-800">
      <h3 className="font-extrabold text-slate-900 tracking-wide text-lg mb-1">
        🏛️ CYBER CONTROL <span className="text-[var(--color-gov-saffron)]">PANEL</span>
      </h3>
      <p className="text-slate-600 text-xs uppercase tracking-wide mb-4">Official Cyber Telemetry & Attack Forecasting System</p>
      
      <hr className="border-slate-300 mb-4" />
      
      <div className="mb-6">
        <label className="block text-sm font-bold mb-2">TELEMETRY INPUT DATASET</label>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" checked={dataSource === "Synthetic Demo Scenario"} onChange={() => setDataSource("Synthetic Demo Scenario")} className="accent-slate-900" />
            <span className="text-sm">Synthetic Demo Scenario</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" checked={dataSource === "Upload PCAP / CSV File"} onChange={() => setDataSource("Upload PCAP / CSV File")} className="accent-slate-900" />
            <span className="text-sm">Upload PCAP / CSV File</span>
          </label>
        </div>
      </div>

      {dataSource === "Synthetic Demo Scenario" ? (
        <div className="mb-6">
          <label className="block text-sm font-bold mb-2">Select Multi-Stage Scenario</label>
          <select 
            className="w-full p-2 border border-slate-300 rounded bg-white text-sm"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            {SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      ) : (
        <div className="mb-6">
          <label className="block text-sm font-bold mb-2">Upload PCAP or CSV File</label>
          <input 
            type="file"
            ref={fileInputRef}
            accept=".csv,.pcap,.pcapng"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                onFileUpload(e.target.files[0]);
              }
            }}
          />
          <button 
            className="w-full bg-slate-900 text-white font-bold text-sm py-2 px-4 rounded hover:bg-[var(--color-gov-saffron)] transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            Browse Files...
          </button>
        </div>
      )}

      <hr className="border-slate-300 mb-4" />
      
      <div className="mb-6">
        <h4 className="font-bold text-sm mb-2 uppercase">🎯 Asset Inventory & Criticality</h4>
        <label className="block text-xs font-semibold mb-1 text-slate-600">Target Monitored Asset IP</label>
        <select 
          className="w-full p-2 border border-slate-300 rounded bg-white text-xs"
          value={assetIp}
          onChange={(e) => setAssetIp(e.target.value)}
        >
          {ASSETS.map(a => (
            <option key={a.ip} value={a.ip}>{a.ip} - {a.name} ({a.tier.split(' - ')[0]})</option>
          ))}
        </select>
      </div>

      <hr className="border-slate-300 mb-4" />
      
      <div className="mb-6">
        <h4 className="font-bold text-sm mb-2 uppercase">Forecast Parameters</h4>
        
        <div className="mb-4">
          <label className="flex justify-between text-xs font-semibold mb-1 text-slate-600">
            <span>K-Step Forecast Horizon</span>
            <span>{kSteps}</span>
          </label>
          <input 
            type="range" min="1" max="10" value={kSteps} 
            onChange={(e) => setKSteps(parseInt(e.target.value))}
            className="w-full accent-slate-900"
          />
        </div>

        <div className="mb-4">
          <label className="flex justify-between text-xs font-semibold mb-1 text-slate-600">
            <span>Current Telemetry Window</span>
            <span>{currentWindowId}</span>
          </label>
          <input 
            type="range" min="3" max={Math.max(3, maxWindowId)} value={currentWindowId} 
            onChange={(e) => setCurrentWindowId(parseInt(e.target.value))}
            className="w-full accent-slate-900"
          />
        </div>

        <div className="mb-4">
          <label className="flex justify-between text-xs font-semibold mb-1 text-slate-600">
            <span>Alert Threshold</span>
            <span>{riskThreshold.toFixed(2)}</span>
          </label>
          <input 
            type="range" min="0.2" max="0.9" step="0.01" value={riskThreshold} 
            onChange={(e) => setRiskThreshold(parseFloat(e.target.value))}
            className="w-full accent-slate-900"
          />
        </div>
      </div>
      
    </div>
  );
}
