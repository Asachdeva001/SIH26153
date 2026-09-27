import React from 'react';
import { BenchmarkResponse } from '@/lib/types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface BenchmarkProps {
  benchmarkData: BenchmarkResponse | null;
  isLoading: boolean;
}

export default function Benchmark({ benchmarkData, isLoading }: BenchmarkProps) {
  if (isLoading || !benchmarkData) {
    return <div className="p-8 text-center text-slate-500">Loading benchmark data...</div>;
  }

  const { world_model, baseline } = benchmarkData;

  const chartData = [
    {
      name: 'F1-Score',
      'World Model K-Step': world_model.f1,
      'Static Baseline': baseline.f1
    },
    {
      name: 'Recall',
      'World Model K-Step': world_model.recall,
      'Static Baseline': baseline.recall
    },
    {
      name: 'Lead Time (Windows)',
      'World Model K-Step': world_model.lead_time_windows,
      'Static Baseline': baseline.lead_time_windows
    }
  ];

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-2">Quantitative Performance Benchmarking</h2>
      <p className="text-slate-600 mb-6">
        Quantifies performance gains of World Model Transition Forecasting against static Logistic Regression classifiers.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h3 className="text-lg font-bold mb-4">Performance Comparison Matrix</h3>
          <div className="overflow-x-auto border border-slate-300 rounded">
            <table className="w-full text-sm text-left text-slate-600 border-collapse">
              <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300">
                <tr>
                  <th className="px-3 py-2">Model Architecture</th>
                  <th className="px-3 py-2">F1-Score</th>
                  <th className="px-3 py-2">Precision</th>
                  <th className="px-3 py-2">Recall</th>
                  <th className="px-3 py-2">FPR</th>
                  <th className="px-3 py-2">Lead Time</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-100 bg-white">
                  <td className="px-3 py-2 font-bold text-slate-900">PyTorch World Model (K-Step)</td>
                  <td className="px-3 py-2 font-medium">{world_model.f1.toFixed(3)}</td>
                  <td className="px-3 py-2">{world_model.precision.toFixed(3)}</td>
                  <td className="px-3 py-2">{world_model.recall.toFixed(3)}</td>
                  <td className="px-3 py-2">{world_model.fpr.toFixed(3)}</td>
                  <td className="px-3 py-2 font-bold text-green-600">
                    {world_model.lead_time_windows > 0 ? `+${world_model.lead_time_windows} Windows` : 'N/A'}
                  </td>
                </tr>
                <tr className="bg-slate-50">
                  <td className="px-3 py-2 font-bold text-slate-700">Static Logistic Regression Baseline</td>
                  <td className="px-3 py-2 font-medium">{baseline.f1.toFixed(3)}</td>
                  <td className="px-3 py-2">{baseline.precision.toFixed(3)}</td>
                  <td className="px-3 py-2">{baseline.recall.toFixed(3)}</td>
                  <td className="px-3 py-2">{baseline.fpr.toFixed(3)}</td>
                  <td className="px-3 py-2 text-slate-500">0.0 Windows (Static)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-bold mb-4">Lead Time & F1-Gain Metrics</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend verticalAlign="top" height={36}/>
                <Bar dataKey="World Model K-Step" fill="#0f172a" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Static Baseline" fill="#94a3b8" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
