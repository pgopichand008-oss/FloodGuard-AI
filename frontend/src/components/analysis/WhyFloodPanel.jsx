import React, { useState, useEffect } from 'react';
import { HelpCircle } from 'lucide-react';
import { fetchExplanations } from '../../services/api';
import LoadingState from '../common/LoadingState';
import StatusBadge from '../common/StatusBadge';

export default function WhyFloodPanel({ selectedZoneId = 'Z03' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadExplanations() {
      setLoading(true);
      const res = await fetchExplanations(selectedZoneId);
      setData(res.data);
      setLoading(false);
    }
    loadExplanations();
  }, [selectedZoneId]);

  if (loading) return <LoadingState message="Computing multi-factor WHY-FLOOD attribution..." />;

  const zoneExp = (data?.explanations && data.explanations.length > 0)
    ? data.explanations[0]
    : (data?.zone_id ? data : {
        zone_id: selectedZoneId,
        zone_name: "Station Road Corridor",
        primary_cause: "Drainage Utilization Overflow + Low Elevation Sump",
        factors: [
          { factor_name: "Rainfall Intensity", weight: 0.35, description: "Extreme nowcast rate (86.4 mm/hr)" },
          { factor_name: "Terrain Elevation", weight: 0.25, description: "Low depression sump area (4.2m elevation)" },
          { factor_name: "Drainage Surcharge", weight: 0.40, description: "Conduit E21 utilization 122% at Node N21" }
        ],
        causal_chain: [
          { step: 1, title: "Extreme Cloudburst Event", description: "Rainfall intensity reaches 86.4 mm/hr, overwhelming infiltration capacity", severity: "CRITICAL" },
          { step: 2, title: "Surface Runoff Surge", description: "Catchment runoff volume surges to 22.1 m³/s into low-lying topographic sump", severity: "HIGH" },
          { step: 3, title: "Conduit Surcharge & Backwater", description: "Node N21 sump capacity exceeded by 22%, driving hydraulic backwater", severity: "CRITICAL" },
          { step: 4, title: "Street Inundation Onset", description: "Station Road surface depth reaches 47.5 cm (Impassable for vehicles)", severity: "SEVERE" }
        ]
      });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="forecast-banner">
        <HelpCircle size={16} style={{ color: 'var(--cyan-bright)', flexShrink: 0 }} />
        <div>
          <div style={{ fontWeight: 800, color: 'var(--cyan-bright)' }}>WHY-FLOOD EXPLAINABILITY DIAGNOSTIC</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
            Multi-factor attribution explaining why <strong>{zoneExp.zone_name} ({zoneExp.zone_id})</strong> is inundated.
          </div>
        </div>
      </div>

      <div className="detail-item-card">
        <span className="detail-lbl">PRIMARY INUNDATION CAUSE</span>
        <div style={{ fontSize: '1rem', fontWeight: 900, color: 'var(--crimson-bright)', marginTop: 4 }}>
          {zoneExp.primary_cause}
        </div>
      </div>

      {/* Causal Chain Timeline */}
      <div className="causal-chain-container">
        <div className="chain-header">
          <span>STEP-BY-STEP HYDRAULIC CAUSAL CHAIN</span>
          <StatusBadge status="ATTRIBUTED" />
        </div>
        <div className="causal-timeline">
          {(zoneExp?.causal_chain || []).map((chain, idx) => (
            <React.Fragment key={chain.step}>
              <div className="causal-node-card">
                <div className="step-num">{chain.step}</div>
                <div className="step-info">
                  <div className="step-title-row">
                    <span className="step-title">{chain.title}</span>
                    <StatusBadge status={chain.severity} />
                  </div>
                  <div className="step-desc">{chain.description}</div>
                </div>
              </div>
              {idx < (zoneExp?.causal_chain?.length || 0) - 1 && (
                <div className="causal-arrow">↓</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
