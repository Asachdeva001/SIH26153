import React from 'react';
import { Menu, Play, Pause, Bell } from 'lucide-react';

interface GovHeaderProps {
  onToggleSidebar: () => void;
  isLiveStreaming: boolean;
  onToggleLiveStream: () => void;
  peakRiskScore: number;
  alertCount: number;
  onOpenAlerts: () => void;
}

/** Ashoka Chakra — 24-spoke SVG, strokes in white for dark backgrounds */
function AshokaChakra({
  size = 28,
  strokeColor = '#FFFFFF',
  opacity = 1,
}: {
  size?: number;
  strokeColor?: string;
  opacity?: number;
}) {
  const cx = size / 2, cy = size / 2;
  const outerR = size / 2 - 1.5;
  const spokes = Array.from({ length: 24 }, (_, i) => {
    const angle = (i * 360 / 24) * (Math.PI / 180);
    return {
      x1: cx + Math.cos(angle) * outerR * 0.22,
      y1: cy + Math.sin(angle) * outerR * 0.22,
      x2: cx + Math.cos(angle) * outerR * 0.88,
      y2: cy + Math.sin(angle) * outerR * 0.88,
    };
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ opacity, display: 'block' }}
      aria-hidden="true"
    >
      {/* Outer ring */}
      <circle cx={cx} cy={cy} r={outerR} fill="none" stroke={strokeColor} strokeWidth="1.4" />
      {/* Inner hub */}
      <circle cx={cx} cy={cy} r={outerR * 0.16} fill={strokeColor} />
      {/* 24 spokes */}
      {spokes.map((s, i) => (
        <line key={i} x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} stroke={strokeColor} strokeWidth="0.9" />
      ))}
    </svg>
  );
}

export default function GovHeader({
  onToggleSidebar,
  isLiveStreaming,
  onToggleLiveStream,
  peakRiskScore,
  alertCount,
  onOpenAlerts,
}: GovHeaderProps) {

  const getDefconStatus = () => {
    if (peakRiskScore >= 0.75) return {
      level: 'DEFCON 1', label: 'CRITICAL THREAT',
      badgeClass: 'bg-red-50 border-red-200 text-red-700',
      dotClass: 'bg-red-500',
    };
    if (peakRiskScore >= 0.55) return {
      level: 'DEFCON 2', label: 'SEVERE RISK',
      badgeClass: 'bg-amber-50 border-amber-200 text-amber-700',
      dotClass: 'bg-amber-500',
    };
    if (peakRiskScore >= 0.35) return {
      level: 'DEFCON 3', label: 'ELEVATED RISK',
      badgeClass: 'bg-yellow-50 border-yellow-200 text-yellow-700',
      dotClass: 'bg-yellow-400',
    };
    return {
      level: 'DEFCON 4', label: 'NOMINAL BASELINE',
      badgeClass: 'bg-green-50 border-green-200 text-green-700',
      dotClass: 'bg-green-500',
    };
  };

  const defcon = getDefconStatus();

  return (
    <header className="mb-5 rounded-xl overflow-hidden shadow-sm border border-[var(--color-gov-border)]">
      {/* ── Tricolor top stripe — no border-radius, contained by parent overflow-hidden ── */}
      <div className="tricolor-bar" />

      {/* ── Main white header row ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white px-4 py-3">
        {/* LEFT: Toggle + Title */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none"
          >
            <Menu size={20} />
          </button>

          <div className="hidden sm:flex items-center gap-3 min-w-0">
            {/* सत्यमेव जयते */}
            <div className="border-r border-slate-200 pr-3">
              {/* <p
                className="text-sm font-bold leading-tight"
                style={{ color: '#FF9933', fontFamily: "'Noto Sans Devanagari', sans-serif" }}
              >
                सत्यमेव जयते
              </p> */}
              <img src="/sj.png" width={30} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Predictive Cyber Defense
              </p>
              <h1 className="text-xl font-black tracking-tight text-slate-900 mt-0.5">
                Operations Command Center
              </h1>
            </div>
          </div>
        </div>

        {/* RIGHT: Controls */}
        <div className="flex items-center gap-2">
          {/* DEFCON badge */}
          <div className={`hidden md:flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-bold font-mono ${defcon.badgeClass}`}>
            <span className="relative flex h-2 w-2 shrink-0">
              {peakRiskScore >= 0.55 && (
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${defcon.dotClass}`} />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${defcon.dotClass}`} />
            </span>
            <span>{defcon.level}: {defcon.label}</span>
          </div>

          {/* Live stream toggle */}
          <button
            onClick={onToggleLiveStream}
            className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-bold transition ${isLiveStreaming
              ? 'border-[#0e6906] text-white'
              : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            style={isLiveStreaming ? { background: '#138808' } : {}}
            title={isLiveStreaming ? 'Pause stream' : 'Start live telemetry'}
          >
            {isLiveStreaming ? (
              <>
                <Pause size={13} className="fill-current" />
                <span>LIVE STREAMING</span>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-80" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
                </span>
              </>
            ) : (
              <>
                <Play size={13} className="fill-current" style={{ color: '#138808' }} />
                <span>START STREAM</span>
              </>
            )}
          </button>

          {/* Bell */}
          <button
            onClick={onOpenAlerts}
            className="relative rounded-lg border border-slate-200 bg-white p-2.5 text-slate-600 hover:bg-slate-50 transition"
            aria-label="View security alerts"
          >
            <Bell size={17} />
            {alertCount > 0 && (
              <span
                className="absolute -top-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full px-1 text-[10px] font-black text-white shadow-md animate-pulse"
                style={{ background: '#FF9933' }}
              >
                {alertCount}
              </span>
            )}
          </button>

          {/* SOC Avatar — saffron bg with white Ashoka Chakra */}
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg cursor-pointer hover:opacity-90 transition shrink-0"
            style={{ background: '#FF9933' }}
            title="SOC Operator"
          >
            <AshokaChakra size={22} strokeColor="#FFFFFF" opacity={1} />
          </div>
        </div>
      </div>

      {/* ── Tagline strip — flush, no extra radius ── */}
      <div
        className="flex items-center justify-between px-6 py-1.5"
        style={{ background: '#0A1628' }}
      >
        <span
          className="text-sm font-semibold"
          style={{ color: '#f6b87bff', fontFamily: "'Noto Sans Devanagari', sans-serif" }}
        >
          सुरक्षित भारत &nbsp;|&nbsp; सशक्त भारत
        </span>
        <span className='text-[12px] font-semibold italic text-slate-300'>
          SIH - Smart India Hackathon'26
        </span>
      </div>
    </header>
  );
}
