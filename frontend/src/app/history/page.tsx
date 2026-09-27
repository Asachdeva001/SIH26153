"use client";

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { 
  Menu, Download, ShieldCheck, ShieldAlert, Ban, RotateCcw, 
  Search, Filter, ArrowUpRight, ArrowDownRight, CheckCircle2, 
  Clock, Server, Network, FileSpreadsheet, Trash2, ExternalLink
} from 'lucide-react';
import ControlPanel from '../components/layout/ControlPanel';
import { 
  AuditAction, getAuditLogs, revertAction, clearAuditLogs, INITIAL_AUDIT_LOGS, saveAuditLogs 
} from '@/lib/auditLog';

export default function HistoryPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [logs, setLogs] = useState<AuditAction[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubnet, setSelectedSubnet] = useState<string>('ALL');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Load from localStorage and listen to real-time events
  useEffect(() => {
    const refresh = () => setLogs(getAuditLogs());
    refresh();

    window.addEventListener('soc-audit-log-updated', refresh);
    window.addEventListener('storage', refresh);
    document.addEventListener('visibilitychange', refresh);

    return () => {
      window.removeEventListener('soc-audit-log-updated', refresh);
      window.removeEventListener('storage', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(prev => (prev === msg ? null : prev));
    }, 4000);
  };

  // Revert / Rollback Handler
  const handleRevert = (id: string, ip: string) => {
    const updated = revertAction(id);
    setLogs(updated);
    showToast(`Quarantine lifted for ${ip}. Subnet route restored.`);
  };

  // Clear / Reset Handler
  const handleClear = () => {
    if (confirm("Are you sure you want to clear the audit history?")) {
      clearAuditLogs();
      setLogs([]);
      showToast("Audit history log cleared.");
    }
  };

  const handleResetSample = () => {
    saveAuditLogs(INITIAL_AUDIT_LOGS);
    setLogs(INITIAL_AUDIT_LOGS);
    showToast("Restored baseline certified audit trail.");
  };

  // Export CSV
  const handleExportCSV = () => {
    if (logs.length === 0) {
      showToast("No audit logs to export.");
      return;
    }
    const headers = ["ID", "Timestamp", "Operator", "Target IP", "Subnet", "Action Type", "Title", "MITRE Ref", "Status", "Risk Before", "Risk After", "Notes"];
    const rows = logs.map(l => [
      l.id,
      `"${l.timestamp}"`,
      `"${l.operator}"`,
      l.targetIp,
      `"${l.subnet}"`,
      l.actionType,
      `"${l.title}"`,
      `"${l.mitreRef || ''}"`,
      l.status,
      `${(l.riskBefore * 100).toFixed(1)}%`,
      `${(l.riskAfter * 100).toFixed(1)}%`,
      `"${l.notes.replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `soc_subnet_audit_report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Exported audit trail as CSV.");
  };

  // Export JSON
  const handleExportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(logs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `soc_subnet_audit_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast("Exported audit trail as JSON.");
  };

  // Subnets list
  const subnets = useMemo(() => {
    const set = new Set(logs.map(l => l.subnet));
    return Array.from(set);
  }, [logs]);

  // Filtered Logs
  const filteredLogs = useMemo(() => {
    return logs.filter(item => {
      const matchesSearch = 
        item.targetIp.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.subnet.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.operator.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.mitreRef && item.mitreRef.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesSubnet = selectedSubnet === 'ALL' || item.subnet === selectedSubnet;
      const matchesType = selectedType === 'ALL' || item.actionType === selectedType;
      const matchesStatus = selectedStatus === 'ALL' || item.status === selectedStatus;

      return matchesSearch && matchesSubnet && matchesType && matchesStatus;
    });
  }, [logs, searchQuery, selectedSubnet, selectedType, selectedStatus]);

  // Statistics
  const stats = useMemo(() => {
    const total = logs.length;
    const activeQuarantines = logs.filter(l => l.status === 'ACTIVE').length;
    const uniqueSubnets = new Set(logs.map(l => l.subnet)).size;
    const avgReduction = logs.length > 0
      ? (logs.reduce((acc, l) => acc + (l.riskBefore - l.riskAfter), 0) / logs.length) * 100
      : 0;

    return { total, activeQuarantines, uniqueSubnets, avgReduction };
  }, [logs]);

  const getActionBadge = (type: AuditAction['actionType']) => {
    switch (type) {
      case 'NETWORK_ISOLATION':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'FIREWALL_BLOCK':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'TOKEN_REVOCATION':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'ALERT_ACK':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getStatusBadge = (status: AuditAction['status']) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-rose-100 text-rose-800 font-bold border-rose-200';
      case 'COMPLETED':
        return 'bg-emerald-100 text-emerald-800 font-bold border-emerald-200';
      case 'REVERTED':
        return 'bg-slate-100 text-slate-600 font-bold border-slate-200';
    }
  };

  return (
    <div className="flex h-screen w-full bg-gov-blue p-2 pr-2 gap-2 overflow-hidden transition-colors duration-300">
      {/* Sidebar Navigation */}
      <ControlPanel isOpen={isSidebarOpen} />

      {/* Main Content Area */}
      <div className="no-scrollbar flex-1 overflow-y-auto bg-[var(--color-gov-bg)] rounded-[2rem] shadow-2xl border border-white/5 px-4 py-4 sm:px-6 sm:py-6 lg:px-8 relative transition-all duration-300">
        
        {/* Header Bar */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/70 pb-5 pt-2">
          <div className="flex min-w-0 items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              aria-label="Toggle sidebar" 
              className="rounded-xl p-2.5 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-300"
            >
              <Menu size={20} />
            </button>
            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-[11px] font-bold text-indigo-600 uppercase tracking-widest font-roboto">
                Compliance & Governance
              </p>
              <h1 className="truncate text-2xl font-black tracking-tight text-slate-900 mt-0.5 font-roboto">
                Subnet Action History & Audit Trail
              </h1>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 shadow-xs hover:bg-slate-50 transition"
              title="Download CSV formatted for CERT-In / ISO 27001 audit submissions"
            >
              <FileSpreadsheet size={14} className="text-emerald-600" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 shadow-xs hover:bg-slate-50 transition"
            >
              <Download size={14} className="text-indigo-600" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={handleResetSample}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 shadow-xs hover:bg-slate-50 transition"
              title="Restore standard certified logs"
            >
              <RotateCcw size={14} />
              <span>Reset</span>
            </button>
            {logs.length > 0 && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-700 shadow-xs hover:bg-rose-100 transition"
                title="Clear all logs"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </header>

        {/* Forensic KPI Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider font-roboto">Recorded Interventions</span>
              <ShieldCheck size={18} className="text-indigo-600" />
            </div>
            <div className="text-3xl font-black text-slate-900 font-roboto">{stats.total}</div>
            <p className="mt-1 text-xs text-slate-500 font-medium">Logged operational events</p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider font-roboto">Active Quarantines</span>
              <Ban size={18} className="text-rose-600" />
            </div>
            <div className="text-3xl font-black text-rose-600 font-roboto">{stats.activeQuarantines}</div>
            <p className="mt-1 text-xs text-slate-500 font-medium">Isolated hosts on monitored subnets</p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider font-roboto">Protected Subnets</span>
              <Network size={18} className="text-emerald-600" />
            </div>
            <div className="text-3xl font-black text-slate-900 font-roboto">{stats.uniqueSubnets}</div>
            <p className="mt-1 text-xs text-slate-500 font-medium">Enclaves under telemetry monitoring</p>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider font-roboto">Mean Risk Delta</span>
              <ArrowDownRight size={18} className="text-emerald-600" />
            </div>
            <div className="text-3xl font-black text-emerald-600 font-roboto">
              -{stats.avgReduction.toFixed(1)}%
            </div>
            <p className="mt-1 text-xs text-slate-500 font-medium">Average post-remediation drop</p>
          </div>
        </div>

        {/* Subnet Enclave Status Cards */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-white to-slate-50/50 p-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server size={16} className="text-indigo-600" />
                <span className="font-mono text-xs font-bold text-slate-900">10.0.0.0/24</span>
              </div>
              <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-extrabold text-indigo-700">Tier 1 Core</span>
            </div>
            <p className="mt-2 text-xs font-medium text-slate-600">Active Directory & SQL Database Enclave</p>
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-[11px]">
              <span className="text-slate-500">Quarantined Hosts:</span>
              <span className="font-bold text-slate-800">
                {logs.filter(l => l.subnet.includes('10.0.0.0/24') && l.status === 'ACTIVE').length} Active
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-white to-slate-50/50 p-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Network size={16} className="text-amber-600" />
                <span className="font-mono text-xs font-bold text-slate-900">198.51.100.0/24</span>
              </div>
              <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-extrabold text-amber-700">Perimeter DMZ</span>
            </div>
            <p className="mt-2 text-xs font-medium text-slate-600">External Gateway & Egress Reverse Proxy</p>
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-[11px]">
              <span className="text-slate-500">Quarantined Hosts:</span>
              <span className="font-bold text-slate-800">
                {logs.filter(l => l.subnet.includes('198.51.100.0/24') && l.status === 'ACTIVE').length} Active
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-gradient-to-br from-white to-slate-50/50 p-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span className="font-mono text-xs font-bold text-slate-900">192.168.1.0/24</span>
              </div>
              <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-700">Endpoints</span>
            </div>
            <p className="mt-2 text-xs font-medium text-slate-600">Internal Developer & Staff Workstations</p>
            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2 text-[11px]">
              <span className="text-slate-500">Quarantined Hosts:</span>
              <span className="font-bold text-slate-800">
                {logs.filter(l => l.subnet.includes('192.168.1.0/24') && l.status === 'ACTIVE').length} Active
              </span>
            </div>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white p-3 shadow-xs">
          {/* Search box */}
          <div className="relative min-w-64 flex-1">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search by IP, Subnet, Operator, or MITRE Technique..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/50 py-2 pl-9 pr-4 text-xs font-medium text-slate-900 placeholder:text-slate-400 outline-none focus:border-indigo-500 focus:bg-white focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>

          {/* Subnet Filter Dropdown */}
          <div className="flex items-center gap-2">
            <select
              value={selectedSubnet}
              onChange={(e) => setSelectedSubnet(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-semibold text-slate-700 outline-none hover:bg-slate-100 transition cursor-pointer"
            >
              <option value="ALL">All Subnets</option>
              {subnets.map(s => <option key={s} value={s}>{s}</option>)}
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2 text-xs font-semibold text-slate-700 outline-none hover:bg-slate-100 transition cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Quarantines</option>
              <option value="COMPLETED">Completed</option>
              <option value="REVERTED">Reverted</option>
            </select>
          </div>
        </div>

        {/* Forensic Audit Log Table */}
        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/75 text-[11px] font-bold uppercase tracking-wider text-slate-500 font-roboto">
                  <th className="py-3 px-4">Timestamp & Operator</th>
                  <th className="py-3 px-4">Target IP / Subnet</th>
                  <th className="py-3 px-4">Action & Technique</th>
                  <th className="py-3 px-4 text-center">Risk Delta</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Intervention</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No audit events match the current filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60 transition group">
                      
                      {/* Timestamp & Operator */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 font-roboto">{log.timestamp}</div>
                        <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                          <span>Operator:</span>
                          <span className="font-medium text-indigo-600">{log.operator}</span>
                        </div>
                      </td>

                      {/* Target IP & Subnet */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="font-bold text-slate-900">{log.targetIp}</div>
                        <div className="text-[11px] font-sans text-slate-500 mt-0.5">{log.subnet}</div>
                      </td>

                      {/* Action & Technique */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold ${getActionBadge(log.actionType)}`}>
                            {log.actionType.replace('_', ' ')}
                          </span>
                          <span className="font-bold text-slate-900">{log.title}</span>
                        </div>
                        {log.mitreRef && (
                          <div className="text-[11px] text-slate-500 font-mono mt-1">
                            MITRE: {log.mitreRef}
                          </div>
                        )}
                        <div className="text-[11px] text-slate-500 mt-1 max-w-md line-clamp-1 group-hover:line-clamp-none transition">
                          {log.notes}
                        </div>
                      </td>

                      {/* Risk Delta */}
                      <td className="py-3.5 px-4 text-center">
                        <div className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700 border border-emerald-100">
                          <ArrowDownRight size={13} />
                          <span>{(log.riskBefore * 100).toFixed(0)}% → {(log.riskAfter * 100).toFixed(0)}%</span>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 text-center">
                        <span className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-[10px] ${getStatusBadge(log.status)}`}>
                          {log.status}
                        </span>
                      </td>

                      {/* Intervention Actions */}
                      <td className="py-3.5 px-4 text-right">
                        {log.status === 'ACTIVE' ? (
                          <button
                            onClick={() => handleRevert(log.id, log.targetIp)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50 hover:text-rose-600 transition shadow-xs"
                            title="Un-isolate host and restore normal routing"
                          >
                            <RotateCcw size={12} />
                            <span>Lift Quarantine</span>
                          </button>
                        ) : log.status === 'REVERTED' ? (
                          <span className="text-[11px] text-slate-400 italic">Quarantine Lifted</span>
                        ) : (
                          <span className="text-[11px] text-emerald-600 font-semibold flex items-center justify-end gap-1">
                            <CheckCircle2 size={13} /> Stamped
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-6 text-center text-xs text-slate-400 font-medium">
          Logged under CERT-In Incident Response Guidelines & RFC 5424 Syslog Protocol.
        </div>
      </div>

      {/* Floating Action Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl bg-slate-900/95 px-5 py-3 text-white shadow-2xl backdrop-blur-md border border-white/10 transition-all duration-300">
          <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-xs font-semibold tracking-wide font-roboto">{toastMessage}</span>
        </div>
      )}
    </div>
  );
}
