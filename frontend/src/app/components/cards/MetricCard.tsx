import React from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  valueColor?: string;
  titleHTML?: React.ReactNode;
}

export default function MetricCard({ title, value, subtitle, valueColor = 'var(--color-gov-blue)', titleHTML }: MetricCardProps) {
  return (
    <div className="gov-card p-4 mb-3 rounded-md h-[145px] flex flex-col justify-between box-border">
      <div className="text-slate-600 text-xs font-extrabold uppercase tracking-wide mb-1">
        {titleHTML || title}
      </div>
      <div className="text-3xl font-extrabold tracking-tight leading-tight" style={{ color: valueColor }}>
        {value}
      </div>
      <div className="text-xs text-slate-500 mt-1 font-semibold">
        {subtitle}
      </div>
    </div>
  );
}
