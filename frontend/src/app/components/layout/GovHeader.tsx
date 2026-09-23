import React from 'react';

export default function GovHeader({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  return (
    <div className="gov-header px-7 py-5 mb-6 flex justify-between items-center rounded-md shadow-[0_4px_12px_rgba(15,23,42,0.1)]">
      <div className="flex items-center gap-4">
        <button 
          onClick={onToggleSidebar}
          className="bg-slate-800 text-white border-2 border-[var(--color-gov-saffron)] px-3.5 py-2 rounded-md font-extrabold text-sm flex items-center gap-2 shadow-md transition-colors hover:bg-[var(--color-gov-saffron)] cursor-pointer"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="3" x2="9" y2="21"></line>
            <path d="M13 15l3-3-3-3"></path>
          </svg>
          <span>SIDEBAR</span>
        </button>
        <div>
          <div className="text-white text-2xl font-extrabold tracking-wide m-0">
            NATIONAL CYBER DEFENSE <span className="text-[var(--color-gov-saffron)]">OPERATIONS</span>
          </div>
          <div className="text-slate-300 text-sm tracking-wide mt-1 font-medium">
            GOVERNMENT OF INDIA • PREDICTIVE CYBER DEFENSE & ATTACK FORECASTING PORTAL (SIH26153)
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="bg-green-500/15 border border-green-500 text-green-400 px-3 py-1.5 text-xs font-extrabold rounded-md tracking-wide">
          🟢 LIVE THREAT STREAM
        </span>
        <div className="border border-white/40 px-4 py-2 text-xs font-extrabold tracking-widest text-white bg-slate-800 uppercase rounded">
          OFFICIAL USE ONLY
        </div>
      </div>
    </div>
  );
}
