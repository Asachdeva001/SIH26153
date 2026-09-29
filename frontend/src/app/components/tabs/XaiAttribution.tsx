import React from 'react';
import { XAIResponse } from '@/lib/types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface XaiAttributionProps {
  xaiData: XAIResponse | null;
  isLoading: boolean;
  onRunAnalysis: () => void;
}

export default function XaiAttribution({ xaiData, isLoading, onRunAnalysis }: XaiAttributionProps) {
  const topFeature = xaiData?.attributions?.[0];

  return (
    <div className="dashboard-panel p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold mb-2">Explainable AI (XAI) Feature Attribution</h2>
          <p className="text-slate-600">
            This explains which telemetry signals are most responsible for the model’s current risk decision. It tells the analyst what the system is paying attention to.
          </p>
        </div>
        {!xaiData && (
          <button 
            onClick={onRunAnalysis}
            disabled={isLoading}
            className="bg-slate-900 text-white px-4 py-2 rounded font-bold hover:bg-[var(--color-gov-saffron)] transition-colors disabled:opacity-50"
          >
            {isLoading ? "Running XAI..." : "Run XAI Analysis"}
          </button>
        )}
      </div>

      {xaiData ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 h-[400px]">
            <h3 className="font-bold text-center mb-2 text-slate-800">Top telemetry drivers</h3>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                data={xaiData.attributions} 
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <XAxis type="number" hide />
                <YAxis dataKey="feature" type="category" width={150} tick={{fontSize: 12}} />
                <Tooltip />
                <Bar dataKey="abs_shap" fill="#0f172a" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="lg:col-span-2">
            <div className="bg-white border border-slate-300 p-4 rounded-md border-t-4 border-t-slate-900 mb-4 shadow-sm">
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 mb-2">Primary driver</div>
              <div className="font-extrabold text-slate-900 uppercase mb-2 text-sm">{xaiData.primary_driver}</div>
              <div className="text-slate-700 text-sm leading-relaxed">
                {xaiData.narrative}
              </div>
            </div>

            {topFeature && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 mb-4">
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-700 mb-2">Most important signal</div>
                <div className="text-lg font-black text-slate-900">{topFeature.feature}</div>
                <div className="text-sm text-slate-700 mt-2">
                  This metric is contributing the most to the current risk score. It is currently {topFeature.observed_value.toFixed(2)} and the model is interpreting it as a strong indicator of escalation.
                </div>
              </div>
            )}

            <h4 className="font-bold text-sm mb-2 text-slate-600 uppercase">Telemetry feature matrix</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-600 border-collapse">
                <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300">
                  <tr>
                    <th className="px-3 py-2">Metric</th>
                    <th className="px-3 py-2">Observed</th>
                    <th className="px-3 py-2">Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {xaiData.attributions.slice(0, 5).map((attr) => (
                    <tr key={attr.feature} className="border-b border-slate-100">
                      <td className="px-3 py-2 font-medium truncate max-w-[120px]" title={attr.feature}>{attr.feature}</td>
                      <td className="px-3 py-2">{attr.observed_value.toFixed(2)}</td>
                      <td className={`px-3 py-2 font-bold ${attr.shap_value > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {attr.shap_value > 0 ? '+' : ''}{attr.shap_value.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center border-2 border-dashed border-slate-300 rounded-lg bg-slate-50">
          <p className="text-slate-500 font-medium">Click "Run XAI Analysis" to explain which telemetry signals are driving the current risk decision.</p>
        </div>
      )}
    </div>
  );
}
