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
    <div className="gov-card mb-3 flex h-[142px] flex-col justify-between p-5">
      <div className="text-[11px] font-extrabold uppercase tracking-[0.12em] text-slate-400">
        {titleHTML || title}
      </div>
      <div className="text-3xl font-extrabold leading-tight tracking-tight" style={{ color: valueColor }}>
        {value}
      </div>
      <div className="text-xs font-semibold text-slate-400">
        {subtitle}
      </div>
    </div>
  );
}
