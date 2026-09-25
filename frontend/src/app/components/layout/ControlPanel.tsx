import React, { useRef } from 'react';
import { Gauge, LayoutDashboard, ShieldCheck, SlidersHorizontal, Upload } from 'lucide-react';

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
    <aside className="no-scrollbar flex h-full w-62 shrink-0 flex-col overflow-y-auto bg-gov-blue px-4 py-5 text-white">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-(--purple) shadow-lg shadow-violet-950/30"><ShieldCheck size={22} /></div>
        <div><div className="text-base font-extrabold tracking-tight">Elevate</div><div className="text-[10px] font-medium text-indigo-200/60">Cyber operations</div></div>
      </div>

      <nav className="space-y-1">
        <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-200/40">Workspace</p>
        <div className="flex w-full items-center gap-3 rounded-xl bg-(--purple) px-3 py-2.5 text-left text-xs font-semibold text-white shadow-lg shadow-violet-950/20">
          <LayoutDashboard size={17} /><span>Dashboard</span>
        </div>
      </nav>

      <div className="my-7 border-t border-white/10" />

      <div className="mb-5 flex items-center justify-between px-2">
        <div className="flex items-center gap-2"><SlidersHorizontal size={15} className="text-indigo-200/70" /><span className="text-xs font-bold text-indigo-100">Live controls</span></div>
        <span className="h-2 w-2 rounded-full bg-(--green) shadow-[0_0_0_4px_rgba(55,185,121,0.14)]" />
      </div>
      
      <div className="mb-6">
        <label className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-indigo-200/50">Telemetry dataset</label>
        <div className="flex flex-col gap-2">
          <label className="flex cursor-pointer items-center gap-2 text-xs text-indigo-50/80">
            <input type="radio" checked={dataSource === "Synthetic Demo Scenario"} onChange={() => setDataSource("Synthetic Demo Scenario")} className="accent-(--purple)" />
            <span>Synthetic demo scenario</span>
          </label>
          <label className="flex cursor-pointer items-center gap-2 text-xs text-indigo-50/80">
            <input type="radio" checked={dataSource === "Upload PCAP / CSV File"} onChange={() => setDataSource("Upload PCAP / CSV File")} className="accent-(--purple)" />
            <span>Upload PCAP / CSV file</span>
          </label>
        </div>
      </div>

      {dataSource === "Synthetic Demo Scenario" ? (
        <div className="mb-6">
          <label className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-indigo-200/50">Multi-stage scenario</label>
          <select 
            className="w-full rounded-lg border border-white/10 bg-white/10 p-2 text-xs text-white outline-none"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
          >
            {SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      ) : (
        <div className="mb-6">
          <label className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-indigo-200/50">Upload PCAP or CSV file</label>
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
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-(--purple) px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-violet-500"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={14} /> Browse files
          </button>
        </div>
      )}

      <div className="mb-4 border-t border-white/10" />
      
      <div className="mb-6">
        <h4 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-indigo-200/50">Target asset</h4>
        <label className="mb-1 block text-xs font-semibold text-indigo-100/60">Monitored asset IP</label>
        <select 
          className="w-full rounded-lg border border-white/10 bg-white/10 p-2 text-xs text-white outline-none"
          value={assetIp}
          onChange={(e) => setAssetIp(e.target.value)}
        >
          {ASSETS.map(a => (
            <option key={a.ip} value={a.ip}>{a.ip} - {a.name} ({a.tier.split(' - ')[0]})</option>
          ))}
        </select>
      </div>

      <div className="mb-4 border-t border-white/10" />
      
      <div className="mb-6">
        <h4 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-indigo-200/50"><Gauge size={14} /> Forecast parameters</h4>
        
        <div className="mb-4">
          <label className="mb-1 flex justify-between text-xs font-semibold text-indigo-100/60">
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
          <label className="mb-1 flex justify-between text-xs font-semibold text-indigo-100/60">
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
          <label className="mb-1 flex justify-between text-xs font-semibold text-indigo-100/60">
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
      
      <div className="mt-auto border-t border-white/10 pt-4 text-[10px] font-medium text-indigo-200/45">Telemetry controls are applied live.</div>
    </aside>
  );
}
