import React from 'react';
import { TelemetryWindow } from '@/lib/types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface KStepSimulatorProps {
  forecastData: TelemetryWindow[];
}

export default function KStepSimulator({ forecastData }: KStepSimulatorProps) {
  // Add step_k to data for chart
  const chartData = forecastData.map((d, i) => ({
    ...d,
    step_k: i + 1,
    syn_flag_ratio: d.syn_flag_ratio * 100, // Scale for better visualization
    port_scan_score: d.port_scan_score * 10
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
      <h2 className="text-xl font-bold mb-2">Autoregressive K-Step State Simulation</h2>
      <p className="text-slate-600 mb-6">
        Displays continuous telemetry state vectors projected K steps forward by the World Model neural decoder.
      </p>

      <div className="overflow-x-auto mb-8 border border-slate-300 rounded">
        <table className="w-full text-sm text-left text-slate-600 border-collapse">
          <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300">
            <tr>
              <th className="px-3 py-2">Step K</th>
              <th className="px-3 py-2">Pred Risk</th>
              <th className="px-3 py-2">Tot Bytes</th>
              <th className="px-3 py-2">Bytes/Pkt</th>
              <th className="px-3 py-2">SYN Ratio</th>
              <th className="px-3 py-2">Port Scan Score</th>
              <th className="px-3 py-2">IAT Var</th>
              <th className="px-3 py-2">High Port Ratio</th>
            </tr>
          </thead>
          <tbody>
            {forecastData.map((row, idx) => (
              <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 font-bold">{idx + 1}</td>
                <td className="px-3 py-2 text-slate-900 font-medium">{(row.target_risk_score || row.is_attack || 0).toFixed(4)}</td>
                <td className="px-3 py-2">{row.total_bytes.toFixed(1)}</td>
                <td className="px-3 py-2">{row.bytes_per_packet_mean.toFixed(1)}</td>
                <td className="px-3 py-2">{row.syn_flag_ratio.toFixed(4)}</td>
                <td className="px-3 py-2">{row.port_scan_score.toFixed(4)}</td>
                <td className="px-3 py-2">{row.iat_variance.toFixed(6)}</td>
                <td className="px-3 py-2">{row.high_port_ratio.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="font-bold text-lg mb-4 text-slate-800">Projected Telemetry Feature Drift</h3>
      <div className="h-[350px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="step_k" label={{ value: 'Step (K)', position: 'insideBottom', offset: -5 }} />
            <YAxis />
            <Tooltip />
            <Legend verticalAlign="top" height={36}/>
            <Line type="linear" dataKey="total_bytes" name="Total Bytes" stroke="#0f172a" strokeWidth={2} dot={{r: 4}} />
            <Line type="linear" dataKey="syn_flag_ratio" name="SYN Ratio (x100)" stroke="#2563eb" strokeWidth={2} dot={{r: 4}} />
            <Line type="linear" dataKey="port_scan_score" name="Port Scan Score (x10)" stroke="#e0533c" strokeWidth={2} dot={{r: 4}} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
