'use client';

import { useEffect } from 'react';

// ldrs uses web components, must be registered client-side
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'l-quantum': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & {
        size?: string; speed?: string; color?: string;
      }, HTMLElement>;
      'l-grid': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & {
        size?: string; speed?: string; color?: string;
      }, HTMLElement>;
    }
  }
}

interface BootLoaderProps {
  message?: string;
  subMessage?: string;
}

export default function BootLoader({
  message = 'Initializing Telemetry Subsystem',
  subMessage = 'Loading world model, syncing threat intelligence...',
}: BootLoaderProps) {
  useEffect(() => {
    import('ldrs').then(({ quantum }) => {
      quantum.register();
    });
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#0a0e1a] overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-20 blur-3xl"
          style={{
            width: '600px',
            height: '600px',
            background: 'radial-gradient(circle, #1a73e8 0%, #0a0e1a 70%)',
          }}
        />
        <div
          className="absolute top-1/4 left-1/4 rounded-full opacity-10 blur-2xl"
          style={{
            width: '300px',
            height: '300px',
            background: 'radial-gradient(circle, #138808 0%, transparent 70%)',
          }}
        />
      </div>

      {/* Scan-line grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-5"
        style={{
          backgroundImage:
            'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,153,51,0.2) 2px, rgba(255,153,51,0.2) 3px)',
          backgroundSize: '100% 60px',
        }}
      />

      {/* Content */}
      <div className="relative flex flex-col items-center gap-8">
        {/* Logo / Brand */}
        <div className="flex flex-col items-center gap-2 mb-4">
          <div className="flex items-center gap-3">
            <div
              className="h-3 w-3 rounded-full animate-pulse"
              style={{ background: '#FF9933', boxShadow: '0 0 12px #FF9933' }}
            />
            <span
              className="text-xs font-black tracking-[0.35em] uppercase"
              style={{ color: '#FF9933', fontFamily: "'Noto Sans Devanagari', sans-serif" }}
            >
              SOC World Model
            </span>
            <div
              className="h-3 w-3 rounded-full animate-pulse"
              style={{ background: '#138808', boxShadow: '0 0 12px #138808', animationDelay: '0.5s' }}
            />
          </div>
          <span
            className="text-xs tracking-[0.2em] uppercase"
            style={{ color: '#6b7280', fontFamily: "'Noto Sans Devanagari', sans-serif" }}
          >
            सुरक्षित भारत | सशक्त भारत
          </span>
        </div>

        {/* ldrs quantum loader */}
        {/* @ts-ignore — ldrs web components */}
        <l-quantum size="96" speed="1.75" color="#FF9933" />

        {/* Status text */}
        <div className="flex flex-col items-center gap-2 mt-2">
          <p
            className="text-sm font-bold tracking-widest uppercase animate-pulse"
            style={{ color: '#e2e8f0', fontFamily: "'Montserrat', sans-serif" }}
          >
            {message}
          </p>
          <p
            className="text-xs tracking-wide"
            style={{ color: '#4b5563', fontFamily: "'Montserrat', sans-serif" }}
          >
            {subMessage}
          </p>
        </div>

        {/* Animated progress bar */}
        <div
          className="relative mt-2 rounded-full overflow-hidden"
          style={{ width: '280px', height: '3px', background: '#1e293b' }}
        >
          <div
            className="absolute top-0 left-0 h-full rounded-full"
            style={{
              background: 'linear-gradient(90deg, transparent, #FF9933, #138808, transparent)',
              animation: 'boot-scan 1.8s ease-in-out infinite',
              width: '60%',
            }}
          />
        </div>

        {/* Boot log lines */}
        <BootLog />
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes boot-scan {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(267%); }
        }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .boot-line {
          animation: fade-in-up 0.4s ease forwards;
        }
      ` }} />
    </div>
  );
}

const BOOT_LINES = [
  { delay: 0, text: '[ OK ] Backend telemetry socket... connected' },
  { delay: 600, text: '[ OK ] World model checkpoint... loaded' },
  { delay: 1100, text: '[ OK ] MITRE ATT&CK framework... synchronized' },
  { delay: 1600, text: '[ .. ] Fetching scenario telemetry windows...' },
];

function BootLog() {
  return (
    <div
      className="font-mono text-left"
      style={{ minWidth: '340px', marginTop: '8px' }}
    >
      {BOOT_LINES.map((line, i) => (
        <BootLine key={i} text={line.text} delay={line.delay} />
      ))}
    </div>
  );
}

function BootLine({ text, delay }: { text: string; delay: number }) {
  return (
    <p
      className="boot-line text-xs"
      style={{
        color: text.includes('[ OK ]') ? '#22c55e' : '#6b7280',
        animationDelay: `${delay}ms`,
        opacity: 0,
        fontFamily: "'Courier New', monospace",
        marginBottom: '3px',
      }}
    >
      {text}
    </p>
  );
}
