import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';

interface ForecastTimelineProps {
  historicalRisks: number[];
  forecastRisks: number[];
  currentWindowId: number;
  kSteps: number;
  riskThreshold: number;
  peakForecastRisk: number;
  assetName: string;
}

export default function ForecastTimeline({
  historicalRisks, forecastRisks, currentWindowId, kSteps, riskThreshold, peakForecastRisk, assetName
}: ForecastTimelineProps) {
  
  // Prepare data for recharts
  const data = [];
  const maxIdx = currentWindowId + kSteps;
  
  for (let i = 0; i <= maxIdx; i++) {
    data.push({
      window: i,
      observed: i <= currentWindowId ? historicalRisks[i] : null,
      forecast: i >= currentWindowId ? (i === currentWindowId ? historicalRisks[i] : forecastRisks[i - currentWindowId - 1]) : null
    });
  }

  const isWarning = peakForecastRisk >= riskThreshold;
  const interpretation = isWarning
    ? `The model expects risk to rise above the operational threshold in the next ${kSteps} windows, which suggests the system is likely moving toward an active attack stage.`
    : `Current telemetry is staying below the alert threshold. This suggests the environment remains comparatively stable for now, even though the forecast is still monitored.`;

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">Infiltration Risk Forecast Trajectory</h2>
      <p className="text-slate-600 mb-6">
        This chart shows what the system has already observed in telemetry and what it expects to happen next. Use it to understand whether risk is rising, stable, or already above the alert threshold.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Observed</div>
          <div className="mt-2 text-sm text-slate-800">Actual risk from the current and earlier telemetry windows.</div>
        </div>
        <div className="rounded-xl border border-orange-200 bg-orange-50 p-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-orange-700">Forecast</div>
          <div className="mt-2 text-sm text-slate-800">Projected attack risk for the next {kSteps} windows.</div>
        </div>
        <div className="rounded-xl border border-slate-300 bg-white p-3">
          <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Threshold</div>
          <div className="mt-2 text-sm text-slate-800">The critical danger level used by the SOC team for escalation.</div>
        </div>
      </div>

      <div className="h-[400px] w-full mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="window" label={{ value: 'Time Window Index (T)', position: 'insideBottom', offset: -5 }} />
            <YAxis domain={[0, 1.05]} label={{ value: 'Infiltration Risk', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend verticalAlign="top" height={36}/>
            <ReferenceLine y={riskThreshold} label="Critical Threshold" stroke="#64748b" strokeDasharray="3 3" />
            <Line type="monotone" dataKey="observed" name="Observed telemetry risk" stroke="#0f172a" strokeWidth={3} dot={{r: 4}} activeDot={{r: 8}} connectNulls />
            <Line type="monotone" dataKey="forecast" name={`${kSteps}-step forecast`} stroke="#e0533c" strokeWidth={3} strokeDasharray="5 5" dot={{r: 5}} activeDot={{r: 8}} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 mb-4">
        <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-2">What this means</div>
        <div className="text-sm leading-6 text-slate-800">{interpretation}</div>
      </div>

      {isWarning ? (
        <div className="bg-red-50 border border-red-300 text-red-800 p-4 font-extrabold rounded-md">
          ⚠️ Risk escalation likely: the model projects attack risk of {(peakForecastRisk*100).toFixed(1)}% for {assetName}. This should be treated as a high-priority escalation condition.
        </div>
      ) : (
        <div className="bg-green-50 border border-green-300 text-green-800 p-4 font-bold rounded-md">
          ✅ Risk remains within normal operational boundaries. The environment is currently stable, though the forecast is being monitored.
        </div>
      )}
    </div>
  );
}
