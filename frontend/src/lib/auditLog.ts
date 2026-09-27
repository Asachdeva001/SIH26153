export interface AuditAction {
  id: string;
  timestamp: string;
  isoDate: string;
  operator: string;
  targetIp: string;
  subnet: string;
  actionType: 'NETWORK_ISOLATION' | 'FIREWALL_BLOCK' | 'TOKEN_REVOCATION' | 'CONFIG_CHANGE' | 'ALERT_ACK';
  title: string;
  mitreRef?: string;
  status: 'ACTIVE' | 'REVERTED' | 'COMPLETED';
  riskBefore: number;
  riskAfter: number;
  notes: string;
}

const STORAGE_KEY = 'soc_audit_action_history_v1';

export const INITIAL_AUDIT_LOGS: AuditAction[] = [
  {
    id: 'act-101',
    timestamp: '27 Sep 2026, 16:45:12 IST',
    isoDate: '2026-09-27T11:15:12.000Z',
    operator: 'Analyst (JD)',
    targetIp: '198.51.100.44',
    subnet: '198.51.100.0/24 (DMZ Perimeter)',
    actionType: 'NETWORK_ISOLATION',
    title: 'Quarantine Perimeter Gateway',
    mitreRef: 'T1071.001 - C2 Beaconing',
    status: 'ACTIVE',
    riskBefore: 0.88,
    riskAfter: 0.14,
    notes: 'Blocked egress beacon traffic to suspected malicious C2 node. Port 443 egress severed.'
  },
  {
    id: 'act-102',
    timestamp: '27 Sep 2026, 16:32:05 IST',
    isoDate: '2026-09-27T11:02:05.000Z',
    operator: 'SOAR Automation Agent',
    targetIp: '10.0.0.15',
    subnet: '10.0.0.0/24 (Corp Core)',
    actionType: 'FIREWALL_BLOCK',
    title: 'SMB Port 445 Lateral Ingress Drop',
    mitreRef: 'T1021.002 - SMB/Admin Shares',
    status: 'ACTIVE',
    riskBefore: 0.74,
    riskAfter: 0.22,
    notes: 'Inbound SMB traffic from developer subnet dropped after abnormal volume surge.'
  },
  {
    id: 'act-103',
    timestamp: '27 Sep 2026, 16:10:48 IST',
    isoDate: '2026-09-27T10:40:48.000Z',
    operator: 'Analyst (JD)',
    targetIp: '10.0.0.50',
    subnet: '10.0.0.0/24 (Corp Core)',
    actionType: 'TOKEN_REVOCATION',
    title: 'Revoke Kerberos TGT Ticket',
    mitreRef: 'T1134 - Access Token Manipulation',
    status: 'COMPLETED',
    riskBefore: 0.65,
    riskAfter: 0.18,
    notes: 'Invalidated active Kerberos tickets for compromised Service Account svc_sql_exec.'
  },
  {
    id: 'act-104',
    timestamp: '27 Sep 2026, 15:48:20 IST',
    isoDate: '2026-09-27T10:18:20.000Z',
    operator: 'Analyst (JD)',
    targetIp: '192.168.1.100',
    subnet: '192.168.1.0/24 (Endpoints)',
    actionType: 'ALERT_ACK',
    title: 'Developer Endpoint Scan Acknowledged',
    mitreRef: 'T1046 - Network Service Scanning',
    status: 'COMPLETED',
    riskBefore: 0.38,
    riskAfter: 0.38,
    notes: 'Verified as legitimate scheduled vulnerability scanner (Nessus internal scan).'
  }
];

export function getAuditLogs(): AuditAction[] {
  if (typeof window === 'undefined') return INITIAL_AUDIT_LOGS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_AUDIT_LOGS));
      return INITIAL_AUDIT_LOGS;
    }
    return JSON.parse(raw);
  } catch (err) {
    console.error('Failed reading audit logs:', err);
    return INITIAL_AUDIT_LOGS;
  }
}

export function saveAuditLogs(logs: AuditAction[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
    window.dispatchEvent(new CustomEvent('soc-audit-log-updated', { detail: logs }));
  } catch (err) {
    console.error('Failed saving audit logs:', err);
  }
}

export function addAuditLog(entry: Omit<AuditAction, 'id' | 'timestamp' | 'isoDate'>): AuditAction {
  const current = getAuditLogs();
  const now = new Date();
  const newAction: AuditAction = {
    ...entry,
    id: `act-${Date.now().toString(36)}`,
    timestamp: `${now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}, ${now.toLocaleTimeString('en-GB')} IST`,
    isoDate: now.toISOString()
  };
  const updated = [newAction, ...current];
  saveAuditLogs(updated);
  return newAction;
}

export function revertAction(id: string): AuditAction[] {
  const current = getAuditLogs();
  const updated = current.map(item => 
    item.id === id 
      ? { ...item, status: 'REVERTED' as const, notes: `${item.notes} [REVERTED by Operator on ${new Date().toLocaleTimeString('en-GB')}]` } 
      : item
  );
  saveAuditLogs(updated);
  return updated;
}

export function clearAuditLogs(): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
  window.dispatchEvent(new CustomEvent('soc-audit-log-updated', { detail: [] }));
}
