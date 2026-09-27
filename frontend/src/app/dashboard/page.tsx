"use client";

import React, { useState, useEffect, useCallback } from 'react';
import GovHeader from '../components/layout/GovHeader';
import ControlPanel from '../components/layout/ControlPanel';
import TabNav from '../components/ui/TabNav';
import MetricCard from '../components/cards/MetricCard';
import BootLoader from '../components/ui/BootLoader';
import AlertDrawer, { AlertItem } from '../components/ui/AlertDrawer';
import { addAuditLog } from '@/lib/auditLog';

// Tab Components
import ForecastTimeline from '../components/tabs/ForecastTimeline';
import MitreTracker from '../components/tabs/MitreTracker';
import XaiAttribution from '../components/tabs/XaiAttribution';
import KStepSimulator from '../components/tabs/KStepSimulator';
import SocResponse from '../components/tabs/SocResponse';
import Benchmark from '../components/tabs/Benchmark';
import NetworkTopology from '../components/tabs/NetworkTopology';
import AuditReport from '../components/tabs/AuditReport';

import {
  fetchScenario, uploadFile, fetchForecast, fetchMitre, fetchXai, fetchSoc, fetchBenchmark
} from '@/lib/api';
import {
  TelemetryWindow, MitreResponse, XAIResponse, SOCResponse, BenchmarkResponse, MitreCustomThresholds
} from '@/lib/types';

const TABS = [
  "Forecast timeline",
  "MITRE ATT&CK tracker",
  "XAI feature attribution",
  "K-step simulator",
  "SOC response",
  "Model benchmarking",
  "Network topology",
  "Audit report"
];

const INITIAL_ALERTS: AlertItem[] = [
  {
    id: 'alert-1',
    severity: 'CRITICAL',
    title: 'Potential C2 Heartbeat & Payload Staging',
    mitreTechnique: 'Command and Control Beaconing',
    mitreId: 'T1071.001',
    targetIp: '198.51.100.44',
    timestamp: '1m ago',
    description: 'Periodic beaconing traffic to suspected hostile IP with abnormal payload size variance.',
    status: 'ACTIVE',
    suggestedAction: 'Apply egress filter and quarantine gateway node.',
    targetTab: 'MITRE ATT&CK tracker'
  },
  {
    id: 'alert-2',
    severity: 'HIGH',
    title: 'Anomalous Lateral Port Sweeps',
    mitreTechnique: 'Network Service Scanning',
    mitreId: 'T1046',
    targetIp: '10.0.0.15',
    timestamp: '4m ago',
    description: 'Rapid high-port sweep directed at Domain Controller / Active Directory instance.',
    status: 'ACTIVE',
    suggestedAction: 'Isolate internal subnet 10.0.0.0/24.',
    targetTab: 'XAI feature attribution'
  },
  {
    id: 'alert-3',
    severity: 'HIGH',
    title: 'Privilege Escalation Vector Predicted',
    mitreTechnique: 'Access Token Manipulation',
    mitreId: 'T1134',
    targetIp: '10.0.0.5',
    timestamp: '8m ago',
    description: 'K-Step world model forecasts high-confidence token manipulation within next 3 windows.',
    status: 'ACTIVE',
    suggestedAction: 'Revoke active Kerberos ticket-granting tokens.',
    targetTab: 'SOC response'
  }
];

export default function DashboardPage() {
  // UI State
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState(TABS[0]);
  const [isLoading, setIsLoading] = useState(true);

  // Live Telemetry & Alert State
  const [isLiveStreaming, setIsLiveStreaming] = useState(false);
  const [isAlertDrawerOpen, setIsAlertDrawerOpen] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>(INITIAL_ALERTS);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Control Panel State
  const [dataSource, setDataSource] = useState("Synthetic Demo Scenario");
  const [scenario, setScenario] = useState("APT Multi-Stage Campaign");
  const [assetIp, setAssetIp] = useState("10.0.0.15");
  const [kSteps, setKSteps] = useState(5);
  const [currentWindowId, setCurrentWindowId] = useState(10);
  const [riskThreshold, setRiskThreshold] = useState(0.60);

  // Data State
  const [windows, setWindows] = useState<TelemetryWindow[]>([]);
  const [rawPackets, setRawPackets] = useState<any[]>([]);
  const [forecastDf, setForecastDf] = useState<TelemetryWindow[]>([]);
  const [riskTrajectory, setRiskTrajectory] = useState<number[]>([]);
  
  const [mitreCurrent, setMitreCurrent] = useState<MitreResponse | null>(null);
  const [mitreFuture, setMitreFuture] = useState<MitreResponse | null>(null);
  
  const [socPriority, setSocPriority] = useState<SOCResponse | null>(null);
  
  const [xaiData, setXaiData] = useState<XAIResponse | null>(null);
  const [isXaiLoading, setIsXaiLoading] = useState(false);
  
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);

  // Load Base Data
  const loadBaseData = useCallback(async (file?: File) => {
    try {
      setIsLoading(true);
      const data = file ? await uploadFile(file) : await fetchScenario(scenario);
      setWindows(data.windows);
      setRawPackets(data.raw_packets);
      setCurrentWindowId(Math.min(10, data.windows.length - 1));
      setXaiData(null); // Reset lazy-loaded XAI
    } catch (error) {
      console.error("Failed to load base data:", error);
      alert("Error loading data. Check backend connection.");
    } finally {
      setIsLoading(false);
    }
  }, [scenario]);

  useEffect(() => {
    if (dataSource === "Synthetic Demo Scenario") {
      loadBaseData();
    }
  }, [scenario, dataSource, loadBaseData]);

  // Derived Values
  const maxWindowId = Math.max(3, windows.length - 1);
  const validCurrentId = Math.min(currentWindowId, maxWindowId);
  const dfWinSub = windows.slice(0, validCurrentId + 1);
  const currentRow = dfWinSub[dfWinSub.length - 1];
  const currRisk = currentRow?.target_risk_score ?? 0.15;
  const peakForecastRisk = riskTrajectory.length > 0 ? Math.max(...riskTrajectory) : 0;

  // Run Models on State Change
  useEffect(() => {
    if (!dfWinSub.length || !currentRow) return;

    const runModels = async () => {
      try {
        // 1. Forecast
        const forecast = await fetchForecast(dfWinSub, kSteps, validCurrentId);
        setForecastDf(forecast.forecast_df);
        setRiskTrajectory(forecast.risk_trajectory);
        const peakRisk = forecast.risk_trajectory.length > 0 ? Math.max(...forecast.risk_trajectory) : 0;

        // 2. MITRE
        const customThresholds: MitreCustomThresholds = {
          exfil_tot_bytes: 50000, exfil_bytes_pkt: 1200, c2_iat_var: 0.005,
          c2_unique_dsts: 2, c2_tot_bytes: 1000, lateral_unique_dsts: 3,
          lateral_high_port_ratio: 0.4, initial_syn_ratio: 0.3,
          initial_bytes_pkt: 300, recon_port_scan_score: 3.0,
          recon_syn_ratio: 0.5, recon_bytes_pkt: 150
        };
        const mCurr = await fetchMitre(currentRow, customThresholds);
        setMitreCurrent(mCurr);

        let mFut = mCurr;
        if (forecast.forecast_df.length > 0) {
          mFut = await fetchMitre(forecast.forecast_df[forecast.forecast_df.length - 1], customThresholds);
        }
        setMitreFuture(mFut);

        // 3. SOC
        const soc = await fetchSoc(peakRisk, assetIp, mCurr);
        setSocPriority(soc);

        // 4. Benchmark (always run to keep it fresh)
        const bench = await fetchBenchmark(dfWinSub, forecast.risk_trajectory, kSteps, riskThreshold);
        setBenchmarkData(bench);

        // Reset XAI on state change because input changed
        setXaiData(null);
      } catch (err) {
        console.error("Error running models:", err);
      }
    };
    
    // We debounce this slightly in a real app, but for now just call it
    runModels();
  }, [validCurrentId, kSteps, riskThreshold, assetIp, currentRow]); // dependencies don't include windows entirely to prevent loop

  // Toast Helper
  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    const timer = setTimeout(() => {
      setToastMessage(prev => (prev === msg ? null : prev));
    }, 4000);
    return () => clearTimeout(timer);
  }, []);

  // Live Stream auto-step timer
  useEffect(() => {
    if (!isLiveStreaming) return;

    const timer = setInterval(() => {
      setCurrentWindowId((prev) => {
        const next = prev + 1;
        if (next > maxWindowId) {
          return 3;
        }
        return next;
      });
    }, 3500);

    return () => clearInterval(timer);
  }, [isLiveStreaming, maxWindowId]);

  // Dynamic alert trigger when risk exceeds threshold
  useEffect(() => {
    if (peakForecastRisk >= riskThreshold && mitreCurrent && mitreCurrent.name !== "Benign Activity") {
      const alertId = `dyn-${validCurrentId}-${mitreCurrent.id}`;
      setAlerts(prev => {
        if (prev.some(a => a.id === alertId)) return prev;
        const newAlert: AlertItem = {
          id: alertId,
          severity: peakForecastRisk > 0.75 ? 'CRITICAL' : 'HIGH',
          title: `Projected Phase: ${mitreCurrent.name}`,
          mitreTechnique: mitreCurrent.name,
          mitreId: mitreCurrent.id,
          targetIp: assetIp,
          timestamp: 'Just now',
          description: `Telemetry Window T${validCurrentId} detected ${mitreCurrent.name} with ${(peakForecastRisk * 100).toFixed(0)}% projected peak risk.`,
          status: 'ACTIVE',
          suggestedAction: `Engage ${socPriority?.playbook_actions?.[0]?.action || 'containment playbook'} on ${assetIp}.`,
          targetTab: 'MITRE ATT&CK tracker'
        };
        return [newAlert, ...prev.slice(0, 7)];
      });
    }
  }, [validCurrentId, peakForecastRisk, riskThreshold, mitreCurrent, assetIp, socPriority]);

  const handleToggleLiveStream = () => {
    setIsLiveStreaming(prev => {
      const next = !prev;
      showToast(next ? "Live telemetry stream started. Stepping windows..." : "Live telemetry stream paused.");
      return next;
    });
  };

  const handleInvestigateAlert = (alert: AlertItem) => {
    setActiveTab(alert.targetTab);
    setIsAlertDrawerOpen(false);
    showToast(`Investigating: ${alert.title} in ${alert.targetTab}`);
  };

  const handleIsolateHost = (ip: string, alertId: string) => {
    const alert = alerts.find(a => a.id === alertId);
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'ISOLATED' } : a));
    
    // Automatically record into the audit log!
    const subnet = ip.startsWith('10.0.0') 
      ? '10.0.0.0/24 (Corp Core)' 
      : ip.startsWith('198.51') 
      ? '198.51.100.0/24 (DMZ Perimeter)' 
      : '192.168.1.0/24 (Endpoints)';

    addAuditLog({
      operator: 'Analyst (JD)',
      targetIp: ip,
      subnet,
      actionType: 'NETWORK_ISOLATION',
      title: `Emergency Isolation of ${ip}`,
      mitreRef: alert ? `${alert.mitreId} - ${alert.mitreTechnique}` : 'T1021 - Lateral Movement',
      status: 'ACTIVE',
      riskBefore: peakForecastRisk || 0.82,
      riskAfter: 0.12,
      notes: `Host isolated from subnet via SDN firewall rule. Port egress blocked.`
    });

    showToast(`Target host ${ip} isolated. Recorded to Action History.`);
  };

  const handleDismissAlert = (id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const handleClearAllAlerts = () => {
    alerts.forEach(a => {
      addAuditLog({
        operator: 'Analyst (JD)',
        targetIp: a.targetIp,
        subnet: a.targetIp.startsWith('10.0.0') ? '10.0.0.0/24 (Corp Core)' : '198.51.100.0/24 (DMZ Perimeter)',
        actionType: 'ALERT_ACK',
        title: `Acknowledged Alert: ${a.title}`,
        mitreRef: `${a.mitreId} - ${a.mitreTechnique}`,
        status: 'COMPLETED',
        riskBefore: peakForecastRisk || 0.60,
        riskAfter: peakForecastRisk || 0.60,
        notes: `Alert reviewed and acknowledged by operator.`
      });
    });
    setAlerts([]);
    showToast("All incident alerts acknowledged and recorded in audit trail.");
  };

  const handleRunXai = async () => {
    setIsXaiLoading(true);
    try {
      const data = await fetchXai(dfWinSub, assetIp);
      setXaiData(data);
    } catch (err) {
      console.error(err);
      alert("Failed to run XAI.");
    } finally {
      setIsXaiLoading(false);
    }
  };

  if (isLoading && windows.length === 0) {
    return <BootLoader />;
  }

  return (
    <div className="flex h-screen w-full bg-gov-blue p-2 pr-2 gap-2 overflow-hidden transition-colors duration-300">
      {/* Sidebar */}
      <ControlPanel 
        isOpen={isSidebarOpen}
        dataSource={dataSource} setDataSource={setDataSource}
        scenario={scenario} setScenario={setScenario}
        onFileUpload={(f) => loadBaseData(f)}
        assetIp={assetIp} setAssetIp={setAssetIp}
        kSteps={kSteps} setKSteps={setKSteps}
        currentWindowId={validCurrentId} setCurrentWindowId={setCurrentWindowId}
        maxWindowId={maxWindowId}
        riskThreshold={riskThreshold} setRiskThreshold={setRiskThreshold}
      />

      {/* Main Content */}
      <div className="no-scrollbar flex-1 overflow-y-auto bg-[var(--color-gov-bg)] rounded-[2rem] shadow-2xl border border-white/5 px-4 py-4 sm:px-6 sm:py-6 lg:px-8 relative transition-all duration-300">
        <GovHeader 
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} 
          isLiveStreaming={isLiveStreaming}
          onToggleLiveStream={handleToggleLiveStream}
          peakRiskScore={peakForecastRisk}
          alertCount={alerts.filter(a => a.status === 'ACTIVE').length}
          onOpenAlerts={() => setIsAlertDrawerOpen(true)}
        />

        {/* Executive Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          <MetricCard 
            titleHTML={<span>OBSERVED RISK (T<sub>{validCurrentId}</sub>)</span>}
            title="OBSERVED RISK"
            value={`${(currRisk * 100).toFixed(1)}%`}
            subtitle="CURRENT TELEMETRY WINDOW STATE"
          />
          <MetricCard 
            titleHTML={<span>PROJECTED PEAK RISK (T<sub>{validCurrentId}+{kSteps}</sub>)</span>}
            title="PROJECTED PEAK RISK"
            value={`${(peakForecastRisk * 100).toFixed(1)}%`}
            valueColor={peakForecastRisk >= riskThreshold ? 'var(--color-gov-saffron)' : 'var(--color-gov-blue)'}
            subtitle="K-STEP WORLD MODEL SIMULATION"
          />
          {mitreCurrent ? (
            <MetricCard 
              title="DETECTED MITRE STAGE"
              value={mitreCurrent.name.toUpperCase()}
              subtitle={`${mitreCurrent.id} (${(mitreCurrent.confidence * 100).toFixed(0)}% CONFIDENCE)`}
            />
          ) : <MetricCard title="DETECTED MITRE STAGE" value="--" subtitle="--" />}
          
          {socPriority ? (
            <MetricCard 
              title="SOC RISK PRIORITY LEVEL"
              value={socPriority.priority_level}
              valueColor={socPriority.priority_color}
              subtitle={`${socPriority.asset_tier} (${assetIp})`}
            />
          ) : <MetricCard title="SOC RISK PRIORITY LEVEL" value="--" subtitle="--" />}
        </div>

        {/* Tabs */}
        <TabNav tabs={TABS} activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Tab Content */}
        <div className="flex-1 pb-10">
          {activeTab === TABS[0] && (
            <ForecastTimeline 
              historicalRisks={windows.map(w => w.target_risk_score || 0.15)}
              forecastRisks={riskTrajectory}
              currentWindowId={validCurrentId}
              kSteps={kSteps}
              riskThreshold={riskThreshold}
              peakForecastRisk={peakForecastRisk}
              assetName={socPriority?.asset_name || assetIp}
            />
          )}
          {activeTab === TABS[1] && mitreCurrent && mitreFuture && (
            <MitreTracker currentStage={mitreCurrent} futureStage={mitreFuture} kSteps={kSteps} />
          )}
          {activeTab === TABS[2] && (
            <XaiAttribution xaiData={xaiData} isLoading={isXaiLoading} onRunAnalysis={handleRunXai} />
          )}
          {activeTab === TABS[3] && (
            <KStepSimulator forecastData={forecastDf} />
          )}
          {activeTab === TABS[4] && socPriority && (
            <SocResponse socData={socPriority} assetIp={assetIp} />
          )}
          {activeTab === TABS[5] && (
            <Benchmark benchmarkData={benchmarkData} isLoading={!benchmarkData} />
          )}
          {activeTab === TABS[6] && (
            <NetworkTopology rawPackets={rawPackets} />
          )}
          {activeTab === TABS[7] && (
            <AuditReport 
              socData={socPriority}
              assetIp={assetIp}
              scenario={scenario}
              currentWindowId={validCurrentId}
              currentRiskScore={currRisk}
              projectedPeakRiskScore={peakForecastRisk}
              mitreCurrentPhase={mitreCurrent}
              mitrePredictedPhase={mitreFuture}
              forecastHorizonK={kSteps}
              xaiPrimaryDriver={xaiData?.primary_driver || ''}
              xaiNarrative={xaiData?.narrative || ''}
            />
          )}
        </div>
      </div>

      {/* Real-time Alert Slide-Over Drawer */}
      <AlertDrawer 
        isOpen={isAlertDrawerOpen}
        onClose={() => setIsAlertDrawerOpen(false)}
        alerts={alerts}
        onInvestigate={handleInvestigateAlert}
        onIsolateHost={handleIsolateHost}
        onDismissAlert={handleDismissAlert}
        onClearAll={handleClearAllAlerts}
      />

      {/* Floating SOC Action Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl bg-slate-900/95 px-5 py-3 text-white shadow-2xl backdrop-blur-md border border-white/10 transition-all duration-300">
          <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-xs font-semibold tracking-wide font-roboto">{toastMessage}</span>
        </div>
      )}
    </div>
  );
}

