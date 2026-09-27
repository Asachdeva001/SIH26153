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

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">Infiltration Risk Forecast Trajectory</h2>
      <p className="text-slate-600 mb-6">
        Visualizes historical telemetry risk score up to current window T_now along with the K-step forward World Model trajectory.
      </p>

      <div className="h-[400px] w-full mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="window" label={{ value: 'Time Window Index (T)', position: 'insideBottom', offset: -5 }} />
            <YAxis domain={[0, 1.05]} label={{ value: 'Infiltration Risk', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend verticalAlign="top" height={36}/>
            <ReferenceLine y={riskThreshold} label="Critical Threshold" stroke="#64748b" strokeDasharray="3 3" />
            <Line type="monotone" dataKey="observed" name="Observed Telemetry Risk" stroke="#0f172a" strokeWidth={3} dot={{r: 4}} activeDot={{r: 8}} connectNulls />
            <Line type="monotone" dataKey="forecast" name={`${kSteps}-Step Forecast`} stroke="#e0533c" strokeWidth={3} strokeDasharray="5 5" dot={{r: 5}} activeDot={{r: 8}} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {isWarning ? (
        <div className="bg-red-50 border border-red-300 text-red-800 p-4 font-extrabold rounded-md">
          ⚠️ OFFICIAL WARNING: World Model predicts attack escalation reaching {(peakForecastRisk*100).toFixed(1)}% risk. Target Asset: {assetName}
        </div>
      ) : (
        <div className="bg-green-50 border border-green-300 text-green-800 p-4 font-bold rounded-md">
          ✅ TELEMETRY STABLE: Risk trajectory remains within standard operational boundaries.
        </div>
      )}
    </div>
  );
}
