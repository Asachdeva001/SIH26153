import React from 'react';
import { MitreResponse } from '@/lib/types';

interface MitreTrackerProps {
  currentStage: MitreResponse;
  futureStage: MitreResponse;
  kSteps: number;
}

const STAGES = [
  { name: "Benign", id: "TA0000", description: "Normal network behavior with no clear attack signal." },
  { name: "Reconnaissance", id: "TA0043", description: "The attacker is learning the environment and identifying targets." },
  { name: "Initial Access", id: "TA0001", description: "An attacker is establishing an entry point into the environment." },
  { name: "Lateral Movement", id: "TA0008", description: "The attacker is moving through internal systems to reach valuable assets." },
  { name: "Command & Control", id: "TA0011", description: "The attacker is maintaining remote communication with compromised systems." },
  { name: "Exfiltration", id: "TA0010", description: "Sensitive data is being transferred out of the environment." }
];

export default function MitreTracker({ currentStage, futureStage, kSteps }: MitreTrackerProps) {
  const currentIdx = STAGES.findIndex(s => s.name === currentStage.name);
  const futureIdx = STAGES.findIndex(s => s.name === futureStage.name);

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">MITRE ATT&CK Kill-Chain Progress</h2>
      <p className="text-slate-600 mb-4">
        This view explains the attack lifecycle in plain language. It helps the SOC team understand whether the environment is in discovery, compromise, movement, or data theft.
      </p>

      <div className="bg-blue-50 text-blue-800 p-3 rounded-md text-sm mb-6 flex gap-2 items-start">
        <span className="text-xl leading-none">ℹ️</span>
        <div>
          <strong>Important:</strong> This mapping is a rule-based analyst layer that interprets the model output into attack phases. It is not the neural network itself.
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        {STAGES.map((stage, idx) => {
          let statusStr = "CLEAR";
          let bgClass = "bg-white";
          let borderClass = "border-slate-200";
          let textClass = "text-slate-400";
          let titleClass = "text-slate-400";

          if (idx < currentIdx) {
            statusStr = "COMPLETED";
            bgClass = "bg-slate-50";
            borderClass = "border-slate-300";
            textClass = "text-slate-500";
            titleClass = "text-slate-800";
          } else if (idx === currentIdx) {
            statusStr = "ACTIVE NOW";
            bgClass = "bg-slate-900";
            borderClass = "border-slate-900";
            textClass = "text-white";
            titleClass = "text-white";
          } else if (idx <= futureIdx) {
            statusStr = "FORECASTED";
            bgClass = "bg-red-50";
            borderClass = "border-red-300";
            textClass = "text-red-700";
            titleClass = "text-red-900";
          }

          const stageMeta = STAGES.find(s => s.name === stage.name);

          return (
            <div key={stage.name} className={`${bgClass} border-[1.5px] ${borderClass} p-3 text-center rounded-md`}>
              <div className={`text-[0.65rem] font-black uppercase ${textClass}`}>{statusStr}</div>
              <div className={`text-sm font-black mt-1 ${titleClass}`}>{stage.name}</div>
              <div className={`text-[0.65rem] mt-1 ${textClass}`}>{stage.id}</div>
              <div className={`mt-2 text-[10px] leading-relaxed ${textClass}`}>{stageMeta?.description}</div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-2">Current phase</div>
          <div className="text-xl font-black text-slate-900">{currentStage.name}</div>
          <div className="text-sm text-slate-600 mt-1">{currentStage.technique}</div>
          <div className="mt-3 text-sm text-slate-700">This is the phase the system believes the environment is currently in based on live telemetry.</div>
        </div>
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-red-700 mb-2">Forecasted phase (+{kSteps} steps)</div>
          <div className="text-xl font-black text-red-900">{futureStage.name}</div>
          <div className="text-sm text-red-700 mt-1">{futureStage.technique}</div>
          <div className="mt-3 text-sm text-red-800">This is the next likely attack stage if the current risk pattern continues.</div>
        </div>
      </div>
    </div>
  );
}
