import React from 'react';
import { CloudRain, TrendingUp } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function RainfallCard({ rainfall, isLive }) {
  const current = rainfall?.current_intensity_mm_hr || 86.4;
  const peak = rainfall?.peak_24h_mm_hr || 102.0;

  return (
    <div className="detail-item-card" style={{ gap: '6px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="detail-lbl" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CloudRain size={13} style={{ color: 'var(--cyan-bright)' }} /> Rainfall Intensity
        </span>
        <StatusBadge status={isLive ? "LIVE" : "DEMO"} />
      </div>
      <div style={{ fontSize: '1.4rem', fontWeight: 900, color: 'var(--text-bright)' }}>
        {current} <span style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', fontWeight: 400 }}>mm/hr</span>
      </div>
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
        <TrendingUp size={12} style={{ color: 'var(--amber-bright)' }} /> Trend: <strong>{rainfall?.trend || 'increasing'}</strong> (Peak: {peak} mm/hr)
      </div>
    </div>
  );
}
