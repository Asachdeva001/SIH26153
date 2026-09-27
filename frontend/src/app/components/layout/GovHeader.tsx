import React from 'react';
import { Menu, Search } from 'lucide-react';

export default function GovHeader({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  return (
    <header className="gov-header mb-7 flex items-center justify-between gap-4 rounded-lg px-5 py-3">
      <div className="flex min-w-0 items-center gap-4">
        <button onClick={onToggleSidebar} aria-label="Toggle sidebar" className="rounded-md p-2 text-slate-500 transition hover:bg-[var(--purple-soft)] hover:text-[var(--purple)]">
          <Menu size={20} />
        </button>
        <div className="hidden min-w-0 sm:block">
          <p className="truncate text-xs font-medium text-slate-500">Predictive cyber defense</p>
          <h1 className="truncate text-lg font-medium tracking-tight text-[var(--ink)]">Operations overview</h1>
        </div>
        <div className="flex w-full max-w-xs items-center gap-2 rounded-xl bg-[#f7f7fb] px-3 py-2 text-sm text-slate-400 sm:ml-4">
          <Search size={17} />
          <span>Search anything...</span>
          <span className="ml-auto hidden rounded bg-white px-1.5 py-0.5 text-[10px] font-bold text-slate-400 shadow-sm md:inline">⌘ K</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-full bg-[#eaf9f1] px-3 py-1.5 text-xs font-medium text-[#24935e] sm:flex"><span className="h-2 w-2 rounded-full bg-[var(--green)]" /> Live telemetry</div>
      </div>
    </header>
  );
}
