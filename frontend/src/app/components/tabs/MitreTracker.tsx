import React from 'react';
import { MitreResponse } from '@/lib/types';

interface MitreTrackerProps {
  currentStage: MitreResponse;
  futureStage: MitreResponse;
  kSteps: number;
}

const STAGES = [
  { name: "Benign", id: "TA0000" },
  { name: "Reconnaissance", id: "TA0043" },
  { name: "Initial Access", id: "TA0001" },
  { name: "Lateral Movement", id: "TA0008" },
  { name: "Command & Control", id: "TA0011" },
  { name: "Exfiltration", id: "TA0010" }
];

export default function MitreTracker({ currentStage, futureStage, kSteps }: MitreTrackerProps) {
  const currentIdx = STAGES.findIndex(s => s.name === currentStage.name);
  const futureIdx = STAGES.findIndex(s => s.name === futureStage.name);

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
      <h2 className="text-xl font-bold mb-2">MITRE ATT&CK Kill-Chain Progress Matrix</h2>
      <p className="text-slate-600 mb-4">
        Tracks telemetry kill-chain phase evolution and maps predicted upcoming phases from the K-step forward state simulation.
      </p>
      
      <div className="bg-blue-50 text-blue-800 p-3 rounded-md text-sm mb-6 flex gap-2 items-start">
        <span className="text-xl leading-none">ℹ️</span>
        <div>
          <strong>Disclaimer:</strong> This mapping uses a Rule-Based Post-Processing Layer with SOC Analyst Tunable Parameters. It is explicitly separated from the underlying World Model neural network.
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

          return (
            <div key={stage.name} className={`${bgClass} border-[1.5px] ${borderClass} p-3 text-center rounded-md`}>
              <div className={`text-[0.65rem] font-black uppercase ${textClass}`}>{statusStr}</div>
              <div className={`text-sm font-black mt-1 ${titleClass}`}>{stage.name}</div>
              <div className={`text-[0.65rem] mt-1 ${textClass}`}>{stage.id}</div>
            </div>
          );
        })}
      </div>

      <ul className="list-disc pl-5 space-y-2 text-slate-800">
        <li><strong>CURRENT ACTIVE PHASE:</strong> <strong>{currentStage.name.toUpperCase()} ({currentStage.id})</strong> — <em>{currentStage.technique}</em></li>
        <li><strong>FORECASTED PHASE (+{kSteps} STEPS):</strong> <strong>{futureStage.name.toUpperCase()} ({futureStage.id})</strong> — <em>{futureStage.technique}</em></li>
      </ul>
    </div>
  );
}
