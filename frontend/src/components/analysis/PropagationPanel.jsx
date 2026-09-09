import React, { useState, useEffect } from 'react';
import { GitCommit, ArrowRight } from 'lucide-react';
import { fetchPropagation } from '../../services/api';
import LoadingState from '../common/LoadingState';
import StatusBadge from '../common/StatusBadge';

export default function PropagationPanel({ selectedZoneId = 'Z03' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPropagation() {
      setLoading(true);
      const res = await fetchPropagation(selectedZoneId);
      setData(res.data);
      setLoading(false);
    }
    loadPropagation();
  }, [selectedZoneId]);

  if (loading) return <LoadingState message="Tracing corridor flood propagation..." />;

  const propagation = data || {
    primary_source_zone_id: selectedZoneId,
    corridor_sequence: ["N21 Sump", "Station Road", "Market Junction", "Bus Terminal", "Hospital Approach"],
    affected_zones: [
      { zone_id: "Z03", depth_cm: 47.5, arrival_offset_min: 0, transmission_mechanism: "Surcharge Sump Overflow" },
      { zone_id: "Z01", depth_cm: 42.5, arrival_offset_min: 15, transmission_mechanism: "Surface Overland Runoff" },
      { zone_id: "Z02", depth_cm: 38.0, arrival_offset_min: 30, transmission_mechanism: "Conduit Backwater Flow" },
      { zone_id: "Z05", depth_cm: 6.0, arrival_offset_min: 60, transmission_mechanism: "Downstream Spillover" }
    ]
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="forecast-banner" style={{ background: 'var(--cyan-dim)', borderColor: 'var(--cyan)' }}>
        <GitCommit size={16} style={{ color: 'var(--cyan-bright)', flexShrink: 0 }} />
        <div>
          <div style={{ fontWeight: 800, color: 'var(--cyan-bright)' }}>CORRIDOR PROPAGATION TRAVERSAL</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
            Sequential transmission originating from <strong>{propagation.primary_source_zone_id}</strong> across connected urban corridors.
          </div>
        </div>
      </div>

      <div className="recharts-container-box">
        <div className="chart-header-row">
          <span>HYDRAULIC PROPAGATION SEQUENCE</span>
          <span>{propagation.affected_zones.length} DOWNSTREAM ZONES</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', padding: '8px 0' }}>
          {propagation.corridor_sequence.map((corridor, idx) => (
            <React.Fragment key={corridor}>
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '5px 9px', fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-bright)' }}>
                {corridor}
              </div>
              {idx < propagation.corridor_sequence.length - 1 && (
                <ArrowRight size={14} style={{ color: 'var(--cyan-bright)' }} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {propagation.affected_zones.map((zone) => (
          <div key={zone.zone_id} className="priority-card">
            <div className="priority-rank-badge">+{zone.arrival_offset_min}m</div>
            <div className="priority-card-main">
              <div className="priority-top-row">
                <span className="priority-target">Zone {zone.zone_id}</span>
                <StatusBadge status={zone.depth_cm > 30 ? 'HIGH' : 'MODERATE'} />
              </div>
              <div className="priority-issue">
                Predicted Depth: <strong>{zone.depth_cm} cm</strong> | Mechanism: {zone.transmission_mechanism}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
