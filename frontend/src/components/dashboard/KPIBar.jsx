import React from 'react';
import { CloudRain, AlertTriangle, Waves, Route, Network, Cpu } from 'lucide-react';
import MetricCard from '../common/MetricCard';
import StatusBadge from '../common/StatusBadge';

export default function KPIBar({ summary, rainfall, mlStatus, isLive, onCardClick }) {
  if (!summary) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px', marginBottom: '8px' }}>
      <MetricCard
        label="Rainfall Intensity"
        value={rainfall?.current_intensity_mm_hr || '86.4'}
        unit="mm/hr"
        subtext={`Peak 24h: ${rainfall?.peak_24h_mm_hr || 102} mm/hr`}
        icon={CloudRain}
        color="cyan"
        onClick={() => onCardClick && onCardClick('forecast')}
      />
      <div className="metric-box" onClick={() => onCardClick && onCardClick('analysis')}>
        <div className="box-lbl"><AlertTriangle size={12} style={{ display: 'inline', marginRight: 4, color: 'var(--amber-bright)' }} /> Flood Risk</div>
        <div className="box-val" style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
          <StatusBadge status={summary.overall_hazard_level || 'HIGH'} />
        </div>
        <div className="box-sub">{summary.affected_zones_count || 5} of {summary.total_evaluated_zones || 8} Zones Affected</div>
      </div>
      <MetricCard
        label="Peak Flood Depth"
        value={summary.max_flood_depth_cm || 47.5}
        unit="cm"
        subtext={`Avg: ${summary.average_flood_depth_cm || 22.8} cm`}
        icon={Waves}
        color="crimson"
        onClick={() => onCardClick && onCardClick('analysis')}
      />
      <MetricCard
        label="Affected Corridors"
        value={summary.critical_zones_count || 2}
        unit="corridors"
        subtext="Roads & Access Paths"
        icon={Route}
        color="amber"
        onClick={() => onCardClick && onCardClick('routing')}
      />
      <MetricCard
        label="Critical Drains"
        value="4 / 12"
        unit="nodes"
        subtext="N21 & N14 Surcharged"
        icon={Network}
        color="blue"
        onClick={() => onCardClick && onCardClick('drainage')}
      />
      <MetricCard
        label="ML Hazard Confidence"
        value={mlStatus?.metrics ? `${Math.round(mlStatus.metrics.accuracy_risk * 100)}%` : '96.5%'}
        unit="r² 0.94"
        subtext={isLive ? "Live RF Inference" : "Simulated Model"}
        icon={Cpu}
        color="purple"
        onClick={() => onCardClick && onCardClick('analysis')}
      />
    </div>
  );
}
