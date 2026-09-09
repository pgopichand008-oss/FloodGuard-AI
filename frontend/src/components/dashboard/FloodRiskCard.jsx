import React from 'react';
import { Waves, AlertTriangle } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function FloodRiskCard({ riskLevel = 'HIGH', maxDepth = 47.5, affectedZones = 5 }) {
  return (
    <div className="detail-item-card" style={{ gap: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="detail-lbl" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Waves size={13} style={{ color: 'var(--crimson-bright)' }} /> Hazard Risk Assessment
        </span>
        <StatusBadge status={riskLevel} />
      </div>
      <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--text-bright)' }}>
        {maxDepth} <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 400 }}>cm max depth</span>
      </div>
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
        <AlertTriangle size={12} style={{ color: 'var(--crimson-bright)' }} /> {affectedZones} Catchment Zones Exceed Warning Thresholds
      </div>
    </div>
  );
}
