import React from 'react';
import { XAIResponse } from '@/lib/types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface XaiAttributionProps {
  xaiData: XAIResponse | null;
  isLoading: boolean;
  onRunAnalysis: () => void;
}

export default function XaiAttribution({ xaiData, isLoading, onRunAnalysis }: XaiAttributionProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-bold mb-2">Explainable AI (XAI) Telemetry Feature Attribution</h2>
          <p className="text-slate-600">
            SHAP feature attribution analysis identifying driving network telemetry metrics responsible for risk escalation.
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
            <h3 className="font-bold text-center mb-2 text-slate-800">Top Driving Telemetry Features (SHAP Impact)</h3>
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
            <h3 className="text-lg font-bold mb-3">📝 OFFICIAL CYBER RATIONALE</h3>
            <div className="bg-white border border-slate-300 p-4 rounded-md border-t-4 border-t-slate-900 mb-6 shadow-sm">
              <div className="font-extrabold text-slate-900 uppercase mb-2 text-sm">
                Primary Driver: {xaiData.primary_driver}
              </div>
              <div className="text-slate-700 text-sm leading-relaxed">
                {xaiData.narrative}
              </div>
            </div>

            <h4 className="font-bold text-sm mb-2 text-slate-600 uppercase">TELEMETRY FEATURE MATRIX</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-slate-600 border-collapse">
                <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300">
                  <tr>
                    <th className="px-3 py-2">Metric</th>
                    <th className="px-3 py-2">Observed</th>
                    <th className="px-3 py-2">Net Directional</th>
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
          <p className="text-slate-500 font-medium">Click "Run XAI Analysis" to calculate SHAP feature attributions.</p>
        </div>
      )}
    </div>
  );
}
