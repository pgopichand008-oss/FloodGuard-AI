import React from 'react';
import { Network } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function DrainageStatus({ summary }) {
  const surcharged = summary?.surcharged_conduits || 2;
  const critical = summary?.critical_conduits || 4;

  return (
    <div className="detail-item-card" style={{ gap: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="detail-lbl" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Network size={13} style={{ color: 'var(--cyan-bright)' }} /> Drainage System Status
        </span>
        <StatusBadge status={surcharged > 0 ? "SURCHARGED" : "NORMAL"} />
      </div>
      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-bright)' }}>
        {surcharged} Surcharged Pipes
      </div>
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
        {critical} Critical Conduits Near 100% Capacity Sump (Node N21)
      </div>
    </div>
  );
}
