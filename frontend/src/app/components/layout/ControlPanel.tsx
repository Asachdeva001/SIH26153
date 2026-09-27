import React, { useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Gauge, LayoutDashboard, History, SlidersHorizontal, Upload } from 'lucide-react';

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
  dataSource?: string;
  setDataSource?: (s: string) => void;
  scenario?: string;
  setScenario?: (s: string) => void;
  onFileUpload?: (file: File) => void;
  assetIp?: string;
  setAssetIp?: (ip: string) => void;
  kSteps?: number;
  setKSteps?: (k: number) => void;
  currentWindowId?: number;
  setCurrentWindowId?: (w: number) => void;
  maxWindowId?: number;
  riskThreshold?: number;
  setRiskThreshold?: (r: number) => void;
}

export default function ControlPanel(props: ControlPanelProps) {
  const {
    isOpen, dataSource, setDataSource, scenario, setScenario, onFileUpload,
    assetIp, setAssetIp, kSteps, setKSteps, currentWindowId, setCurrentWindowId,
    maxWindowId, riskThreshold, setRiskThreshold
  } = props;

  const pathname = usePathname();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // if (!isOpen) return null; // Removed so it can transition

  return (
    <aside className={`no-scrollbar flex h-full shrink-0 flex-col overflow-y-auto bg-transparent text-white transition-all duration-300 ease-in-out ${isOpen ? 'w-64 px-4 py-5 opacity-100' : 'w-0 px-0 py-5 opacity-0 pointer-events-none'}`}>
      {/* NATIONAL EMBLEM + BRAND */}
      <div className="mb-6 px-2">
        {/* Tricolor sidebar top bar */}
        <div className="tricolor-bar rounded mb-4" />
        <div className="flex items-center gap-3">
          {/* National Emblem placeholder — circular navy badge with Ashoka spoke */}
          <div
            className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2"
            style={{ background: '#0d1e3a', borderColor: '#FF993355' }}
          >
            {/* 24-spoke Ashoka Chakra mini */}
            <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true">
              <circle cx="14" cy="14" r="12.5" fill="none" stroke="#FF9933" strokeWidth="1.2" />
              <circle cx="14" cy="14" r="2.8" fill="#FF9933" />
              {Array.from({ length: 24 }, (_, i) => {
                const a = (i * 360) / 24 * (Math.PI / 180);
                return null; // rendered as static SVG below
              })}
              {[0,15,30,45,60,75,90,105,120,135,150,165,180,195,210,225,240,255,270,285,300,315,330,345].map((deg, i) => {
                const a = deg * Math.PI / 180;
                return (
                  <line key={i}
                    x1={14 + Math.cos(a) * 3.5} y1={14 + Math.sin(a) * 3.5}
                    x2={14 + Math.cos(a) * 11.5} y2={14 + Math.sin(a) * 11.5}
                    stroke="#FF9933" strokeWidth="0.9"
                  />
                );
              })}
            </svg>
          </div>
          <div className="min-w-0">
            <div className="text-sm font-extrabold tracking-wider text-white uppercase">CYBER DEFENSE</div>
            <div className="text-[10px] font-medium tracking-wide" style={{ color: '#FF9933' }}>SOC WORLD MODEL</div>
          </div>
        </div>
      </div>

      <nav className="space-y-1.5">
        <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-white/30">Workspace</p>
        <Link
          href="/dashboard"
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-xs font-semibold transition ${
            pathname === '/dashboard' || pathname === '/'
              ? 'text-white shadow-lg'
              : 'text-white/60 hover:bg-white/5 hover:text-white'
          }`}
          style={pathname === '/dashboard' || pathname === '/' ? { background: '#FF9933', boxShadow: '0 4px 14px rgba(255,153,51,0.3)' } : {}}
        >
          <LayoutDashboard size={17} /><span>Dashboard</span>
        </Link>
        <Link
          href="/history"
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-xs font-semibold transition ${
            pathname === '/history'
              ? 'text-white shadow-lg'
              : 'text-white/60 hover:bg-white/5 hover:text-white'
          }`}
          style={pathname === '/history' ? { background: '#FF9933', boxShadow: '0 4px 14px rgba(255,153,51,0.3)' } : {}}
        >
          <History size={17} /><span>Action History</span>
        </Link>
      </nav>

      <div className="my-7 border-t border-white/10" />

      {dataSource !== undefined && setDataSource && scenario !== undefined && setScenario && assetIp !== undefined && setAssetIp && kSteps !== undefined && setKSteps && currentWindowId !== undefined && setCurrentWindowId && maxWindowId !== undefined && riskThreshold !== undefined && setRiskThreshold ? (
        <>
          <div className="mb-5 flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={15} style={{ color: '#FF9933' }} />
              <span className="text-xs font-bold text-white">Live controls</span>
            </div>
            <span className="h-2 w-2 rounded-full bg-[#138808] shadow-[0_0_0_4px_rgba(19,136,8,0.25)]" />
          </div>

          <div className="mb-6">
            <label className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-white/40">Telemetry dataset</label>
            <div className="flex flex-col gap-2">
              <label className="flex cursor-pointer items-center gap-2 text-xs text-white/70">
                <input type="radio" checked={dataSource === "Synthetic Demo Scenario"} onChange={() => setDataSource("Synthetic Demo Scenario")} style={{ accentColor: '#FF9933' }} />
                <span>Synthetic demo scenario</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2 text-xs text-white/70">
                <input type="radio" checked={dataSource === "Upload PCAP / CSV File"} onChange={() => setDataSource("Upload PCAP / CSV File")} style={{ accentColor: '#FF9933' }} />
                <span>Upload PCAP / CSV file</span>
              </label>
            </div>
          </div>

          {dataSource === "Synthetic Demo Scenario" ? (
            <div className="mb-6">
              <label className="mb-2 block text-[10px] font-bold uppercase tracking-wider text-white/40">Multi-stage scenario</label>
              <div className="relative">
                <select
                  className="w-full appearance-none rounded-lg border border-white/10 bg-white/5 py-2.5 pl-3 pr-8 text-xs font-medium text-white outline-none transition-all hover:bg-white/10 focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] cursor-pointer"
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                >
                  {SCENARIOS.map(s => <option key={s} value={s} className="bg-slate-800 text-white">{s}</option>)}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2" style={{ color: '#FF9933' }}>
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                </div>
              </div>
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
                  if (e.target.files && e.target.files[0] && onFileUpload) {
                    onFileUpload(e.target.files[0]);
                  }
                }}
              />
              <button
                className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 text-xs font-bold text-white transition-colors shadow-md"
                style={{ background: '#FF9933' }}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={14} /> Browse files
              </button>
            </div>
          )}

          <div className="mb-4 border-t border-white/10" />
          
          <div className="mb-6">
            <h4 className="mb-2 text-[10px] font-bold uppercase tracking-wider text-white/40">Target asset</h4>
            <label className="mb-1 block text-xs font-semibold text-white/50">Monitored asset IP</label>
            <div className="relative">
              <select
                className="w-full appearance-none rounded-lg border border-white/10 bg-white/5 py-2.5 pl-3 pr-8 text-xs font-medium text-white outline-none transition-all hover:bg-white/10 focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] cursor-pointer"
                value={assetIp}
                onChange={(e) => setAssetIp(e.target.value)}
              >
                {ASSETS.map(a => (
                  <option key={a.ip} value={a.ip} className="bg-slate-800 text-white">{a.ip} - {a.name} ({a.tier.split(' - ')[0]})</option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2" style={{ color: '#FF9933' }}>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
              </div>
            </div>
          </div>

          <div className="mb-4 border-t border-white/10" />
          
          <div className="mb-6">
            <h4 className="mb-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-white/40"><Gauge size={14} /> Forecast parameters</h4>
            
            <div className="mb-4">
              <label className="mb-1 flex justify-between text-xs font-semibold text-indigo-100/60">
                <span>K-Step Forecast Horizon</span>
                <span>{kSteps}</span>
              </label>
              <input 
                type="range" min="1" max="10" value={kSteps} 
                onChange={(e) => setKSteps(parseInt(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
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
                className="w-full accent-indigo-500 cursor-pointer"
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
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>
          </div>
          <div className="mt-auto border-t border-white/10 pt-4">
            {/* MeitY footer */}
            <div className="flex items-center gap-2 mb-2">
              <div className="h-5 w-5 shrink-0">
                <svg viewBox="0 0 28 28" width="20" height="20">
                  <circle cx="14" cy="14" r="12.5" fill="none" stroke="#FF9933" strokeWidth="1.4" />
                  <circle cx="14" cy="14" r="2.8" fill="#FF9933" />
                  {[0,15,30,45,60,75,90,105,120,135,150,165,180,195,210,225,240,255,270,285,300,315,330,345].map((deg, i) => {
                    const a = deg * Math.PI / 180;
                    return <line key={i} x1={14 + Math.cos(a)*3.5} y1={14 + Math.sin(a)*3.5} x2={14 + Math.cos(a)*11.5} y2={14 + Math.sin(a)*11.5} stroke="#FF9933" strokeWidth="0.9" />;
                  })}
                </svg>
              </div>
              <div>
                <div className="text-[9px] font-bold text-white/80 leading-tight">Ministry of Electronics</div>
                <div className="text-[9px] font-bold text-white/80 leading-tight">&amp; Information Technology</div>
                <div className="text-[9px] text-white/40">Government of India</div>
              </div>
            </div>
            <div className="text-[9px] font-medium" style={{ color: '#FF9933', fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
              डिजिटल सुरक्षा | सुरक्षित भविष्य
            </div>
          </div>
        </>
      ) : (
        <div className="space-y-4">
          <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-200/40">Audit Scope</p>
          <div className="rounded-xl border border-white/10 bg-white/5 p-3.5 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-indigo-200/70 font-medium">Compliance</span>
              <span className="font-mono font-bold text-emerald-400">CERT-In Ready</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-indigo-200/70 font-medium">Subnet Enclaves</span>
              <span className="font-mono font-bold text-white">3 Monitored</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-indigo-200/70 font-medium">Storage Engine</span>
              <span className="font-mono font-bold text-indigo-300">Local Immutable</span>
            </div>
          </div>
          <div className="mt-auto border-t border-white/10 pt-4 text-[10px] font-medium text-indigo-200/45">
            Audit entries are cryptographically stamped and persisted across browser sessions.
          </div>
        </div>
      )}
    </aside>
  );
}
