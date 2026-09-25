import React, { useMemo } from 'react';

interface NetworkTopologyProps {
  rawPackets: any[];
}

export default function NetworkTopology({ rawPackets }: NetworkTopologyProps) {
  
  // Aggregate flow counts
  const flowSummary = useMemo(() => {
    const counts: Record<string, number> = {};
    rawPackets.forEach(pkt => {
      const key = `${pkt.src_ip}|${pkt.dst_ip}|${pkt.dst_port}`;
      counts[key] = (counts[key] || 0) + 1;
    });
    
    return Object.entries(counts).map(([key, count]) => {
      const [src_ip, dst_ip, dst_port] = key.split('|');
      return { src_ip, dst_ip, dst_port, packet_count: count };
    }).sort((a, b) => b.packet_count - a.packet_count);
  }, [rawPackets]);

  return (
    <div className="dashboard-panel p-6">
      <h2 className="text-xl font-bold mb-6">Host Communication Topology & Packet Telemetry Logs</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <h4 className="font-bold text-slate-800 mb-3">Host Communications Summary</h4>
          <div className="overflow-auto border border-slate-300 rounded max-h-[400px]">
            <table className="w-full text-sm text-left text-slate-600 border-collapse">
              <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300 sticky top-0 shadow-sm">
                <tr>
                  <th className="px-3 py-2">Source IP</th>
                  <th className="px-3 py-2">Dest IP</th>
                  <th className="px-3 py-2">Dest Port</th>
                  <th className="px-3 py-2 text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {flowSummary.map((flow, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2">{flow.src_ip}</td>
                    <td className="px-3 py-2">{flow.dst_ip}</td>
                    <td className="px-3 py-2">{flow.dst_port}</td>
                    <td className="px-3 py-2 text-right font-bold">{flow.packet_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="lg:col-span-3">
          <h4 className="font-bold text-slate-800 mb-3">Raw Telemetry Packets Log (Top 50)</h4>
          <div className="overflow-auto border border-slate-300 rounded max-h-[400px]">
            <table className="w-full text-xs text-left text-slate-600 border-collapse">
              <thead className="text-xs text-slate-700 uppercase bg-slate-50 border-b border-slate-300 sticky top-0 shadow-sm">
                <tr>
                  <th className="px-2 py-2">Rel Sec</th>
                  <th className="px-2 py-2">Src IP</th>
                  <th className="px-2 py-2">Dst IP</th>
                  <th className="px-2 py-2">DPort</th>
                  <th className="px-2 py-2">Proto</th>
                  <th className="px-2 py-2 text-right">Bytes</th>
                  <th className="px-2 py-2 text-center">SYN</th>
                  <th className="px-2 py-2 text-center">ACK</th>
                </tr>
              </thead>
              <tbody>
                {rawPackets.map((pkt, idx) => (
                  <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50 font-mono text-[0.7rem]">
                    <td className="px-2 py-1">{(pkt.relative_sec || 0).toFixed(3)}</td>
                    <td className="px-2 py-1 text-slate-800">{pkt.src_ip}</td>
                    <td className="px-2 py-1 text-slate-800">{pkt.dst_ip}</td>
                    <td className="px-2 py-1">{pkt.dst_port}</td>
                    <td className="px-2 py-1">{pkt.protocol}</td>
                    <td className="px-2 py-1 text-right">{pkt.tot_bytes}</td>
                    <td className="px-2 py-1 text-center">{pkt.syn_flag}</td>
                    <td className="px-2 py-1 text-center">{pkt.ack_flag}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
