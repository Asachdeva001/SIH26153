import React from 'react';

interface TabNavProps {
  tabs: string[];
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function TabNav({ tabs, activeTab, setActiveTab }: TabNavProps) {
  return (
    <div className="mb-6 flex flex-wrap gap-2 rounded-2xl border border-slate-200/80 bg-slate-50/50 p-2 shadow-inner">
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`h-10 rounded-xl px-4 text-xs font-semibold transition-all duration-200 ${
            activeTab === tab 
              ? 'bg-white text-indigo-700 shadow-[0_2px_10px_rgba(0,0,0,0.06)] border border-slate-200' 
              : 'border border-transparent text-slate-500 hover:bg-slate-200/50 hover:text-slate-700'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
