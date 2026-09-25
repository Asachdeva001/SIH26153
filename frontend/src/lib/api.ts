import {
  TelemetryWindow,
  MitreCustomThresholds,
  MitreResponse,
  SOCResponse,
  BenchmarkResponse,
  XAIResponse
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function fetchScenario(name: string = "APT Multi-Stage Campaign") {
  const params = new URLSearchParams({
    name,
    num_windows: "20",
    window_size_sec: "10.0"
  });
  
  const res = await fetch(`${API_BASE_URL}/scenario?${params.toString()}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error('Failed to fetch scenario');
  return res.json();
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload file');
  return res.json();
}

export async function fetchForecast(windows: TelemetryWindow[], kSteps: number, currentWindowId: number) {
  const res = await fetch(`${API_BASE_URL}/forecast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ windows, K: kSteps })
  });
  if (!res.ok) throw new Error('Failed to fetch forecast');
  return res.json();
}

export async function fetchMitre(state_dict: any, custom_thresholds: MitreCustomThresholds): Promise<MitreResponse> {
  const res = await fetch(`${API_BASE_URL}/mitre`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state_dict, custom_thresholds })
  });
  if (!res.ok) throw new Error('Failed to fetch MITRE stage');
  return res.json();
}

export async function fetchSoc(forecast_risk: number, asset_ip: string, mitre_stage: MitreResponse): Promise<SOCResponse> {
  const res = await fetch(`${API_BASE_URL}/soc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ forecast_risk, asset_ip, mitre_stage })
  });
  if (!res.ok) throw new Error('Failed to fetch SOC response');
  return res.json();
}

export async function fetchXai(windows: TelemetryWindow[], asset_ip: string): Promise<XAIResponse> {
  const res = await fetch(`${API_BASE_URL}/xai`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ windows, asset_ip })
  });
  if (!res.ok) throw new Error('Failed to fetch XAI attribution');
  return res.json();
}

export async function fetchBenchmark(windows: TelemetryWindow[], risk_trajectory: number[], kSteps: number, threshold: number): Promise<BenchmarkResponse> {
  const res = await fetch(`${API_BASE_URL}/benchmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ windows, risk_trajectory, K: kSteps, threshold })
  });
  if (!res.ok) throw new Error('Failed to fetch benchmark');
  return res.json();
}
