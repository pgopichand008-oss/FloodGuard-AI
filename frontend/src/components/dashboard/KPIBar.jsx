import React from 'react';
import { CloudRain, AlertTriangle, Waves, Route, Network, Cpu } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function KPIBar({ summary, rainfall, drainageData, mlPredictData, mlStatus, isLive, loading, error, onCardClick }) {
  if (loading && !summary && !rainfall) {
    return (
      <div className="kpi-telemetry-strip" style={{ opacity: 0.75 }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Loading live KPI telemetry...</span>
      </div>
    );
  }

  // 1. Rainfall (/api/rainfall)
  const rainVal = rainfall?.current_intensity_mm_per_hr ?? rainfall?.current_intensity_mm_hr;
  const rainText = rainVal !== undefined ? `${rainVal} mm/hr` : '--';

  // 2. Hazard Risk, Peak Depth, Corridors (/api/flood)
  let hazardLevel = summary?.overall_hazard_level;
  if (!hazardLevel && summary) {
    if ((summary.severe_risk_zones || 0) > 0) hazardLevel = "SEVERE";
    else if ((summary.high_risk_zones || 0) > 0) hazardLevel = "HIGH";
    else if ((summary.moderate_risk_zones || 0) > 0) hazardLevel = "MODERATE";
    else if ((summary.low_risk_zones || 0) > 0) hazardLevel = "LOW";
  }
  if (!hazardLevel) hazardLevel = "HIGH";

  const affectedZones = summary?.affected_zones_count ??
    (summary ? ((summary.high_risk_zones || 0) + (summary.severe_risk_zones || 0) + (summary.moderate_risk_zones || 0)) : '--');
  const totalZones = summary?.total_evaluated_zones ?? summary?.total_zones ?? '--';
  const maxDepth = summary?.max_flood_depth_cm !== undefined ? `${summary.max_flood_depth_cm} cm` : '--';
  const critCount = summary?.critical_zones_count ??
    (summary ? ((summary.high_risk_zones || 0) + (summary.severe_risk_zones || 0)) : '--');
  const criticalCorridors = `${critCount} Affected`;

  // 3. Drain Surcharge (/api/drainage)
  const surchargedDrain = drainageData?.drains?.find(d => d.is_surcharged || d.utilization_percent > 100);
  const maxDrain = drainageData?.drains?.reduce((max, d) => (d.utilization_percent > (max?.utilization_percent || 0) ? d : max), null);
  const drainSurchargeText = surchargedDrain
    ? `Node ${surchargedDrain.from_node} (${Math.round(surchargedDrain.utilization_percent)}%)`
    : maxDrain
    ? `Edge ${maxDrain.edge_id} (${Math.round(maxDrain.utilization_percent)}%)`
    : drainageData?.summary
    ? `${drainageData.summary.surcharged_drains || 0} Surcharged (${Math.round(drainageData.summary.max_utilization_percent || 0)}%)`
    : '--';

  // 4. ML Confidence (/api/ml/predict)
  let mlConfidenceText = '--';
  if (mlPredictData?.predictions && mlPredictData.predictions.length > 0) {
    const totalConf = mlPredictData.predictions.reduce((sum, p) => sum + (p.model_confidence ?? 0), 0);
    const avgConf = totalConf / mlPredictData.predictions.length;
    mlConfidenceText = `${(avgConf * 100).toFixed(1)}%`;
  } else if (mlStatus?.validation_metrics?.accuracy_risk ?? mlStatus?.validation_metrics?.accuracy ?? mlStatus?.metrics?.accuracy_risk) {
    const acc = mlStatus.validation_metrics?.accuracy_risk ?? mlStatus.validation_metrics?.accuracy ?? mlStatus.metrics.accuracy_risk;
    mlConfidenceText = `${Math.round(acc * 100)}%`;
  }

  return (
    <div className="kpi-telemetry-strip">
      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('forecast')} title="Click to view Rainfall & Forecast Panel">
        <CloudRain size={13} style={{ color: 'var(--cyan-bright)' }} />
        <span className="kpi-lbl">Rainfall:</span>
        <span className="kpi-val">{rainText}</span>
      </div>

      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('analysis')} title="Click to view Hazard Risk Analysis">
        <AlertTriangle size={13} style={{ color: 'var(--amber-bright)' }} />
        <span className="kpi-lbl">Hazard Risk:</span>
        <StatusBadge status={hazardLevel} />
        <span className="kpi-sub">({affectedZones}/{totalZones} Zones)</span>
      </div>

      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('analysis')} title="Click to view Flood Depth Analysis">
        <Waves size={13} style={{ color: 'var(--crimson-bright)' }} />
        <span className="kpi-lbl">Peak Depth:</span>
        <span className="kpi-val" style={{ color: 'var(--crimson-bright)' }}>{maxDepth}</span>
      </div>

      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('routing')} title="Click to view Affected Transport Corridors">
        <Route size={13} style={{ color: 'var(--amber-bright)' }} />
        <span className="kpi-lbl">Corridors:</span>
        <span className="kpi-val">{criticalCorridors}</span>
      </div>

      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('drainage')} title="Click to view Drainage Surcharge Intelligence">
        <Network size={13} style={{ color: 'var(--cyan-bright)' }} />
        <span className="kpi-lbl">Drain Surcharge:</span>
        <span className="kpi-val">{drainSurchargeText}</span>
      </div>

      <div className="kpi-chip" onClick={() => onCardClick && onCardClick('analysis')} title="Click to view ML Model Predictions & Status">
        <Cpu size={13} style={{ color: 'var(--purple)' }} />
        <span className="kpi-lbl">ML Confidence:</span>
        <span className="kpi-val">{mlConfidenceText}</span>
        <span className="kpi-sub">({isLive ? 'Live' : 'Demo'})</span>
      </div>
    </div>
  );
}
