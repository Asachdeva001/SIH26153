import React from 'react';

interface TabNavProps {
  tabs: string[];
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function TabNav({ tabs, activeTab, setActiveTab }: TabNavProps) {
  return (
    <div className="mb-5 flex flex-wrap gap-1.5 rounded-2xl border border-slate-200 bg-white p-2 shadow-[0_5px_18px_rgba(30,34,75,0.03)]">
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`h-10 rounded-xl border px-3 text-xs font-bold transition-colors ${
            activeTab === tab 
              ? 'border-(--purple) bg-(--purple) text-white shadow-md shadow-violet-200' 
              : 'border-transparent text-slate-500 hover:bg-(--purple-soft) hover:text-(--purple)'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
