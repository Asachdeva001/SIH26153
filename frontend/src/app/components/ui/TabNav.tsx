import React from 'react';

interface TabNavProps {
  tabs: string[];
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export default function TabNav({ tabs, activeTab, setActiveTab }: TabNavProps) {
  return (
    <div className="flex flex-wrap gap-2 bg-white p-2 border border-slate-300 rounded-lg shadow-sm mb-5">
      {tabs.map(tab => (
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`h-11 px-4 rounded-md font-bold text-sm uppercase transition-colors border ${
            activeTab === tab 
              ? 'bg-slate-900 text-white border-slate-900 shadow-md' 
              : 'text-slate-600 border-transparent hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
