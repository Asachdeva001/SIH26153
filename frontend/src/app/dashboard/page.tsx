"use client";

import React, { useState, useEffect, useCallback } from 'react';
import GovHeader from '../components/layout/GovHeader';
import ControlPanel from '../components/layout/ControlPanel';
import TabNav from '../components/ui/TabNav';
import MetricCard from '../components/cards/MetricCard';
import Spinner from '../components/ui/Spinner';

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

export default function DashboardPage() {
  // UI State
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState(TABS[0]);
  const [isLoading, setIsLoading] = useState(true);

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
    return (
      <div className="h-full w-full flex flex-col items-center justify-center bg-[var(--color-gov-bg)]">
        <Spinner />
        <p className="mt-4 text-slate-500 font-bold tracking-widest uppercase">Initializing Telemetry Subsystem...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-[var(--color-gov-bg)]">
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
      <div className="no-scrollbar flex-1 overflow-y-auto px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        <GovHeader onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />

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
    </div>
  );
}
