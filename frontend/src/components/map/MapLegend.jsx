import React, { useState } from 'react';
import { BarChart2, ChevronDown, ChevronUp } from 'lucide-react';

export default function MapLegend() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`map-legend-hud ${expanded ? 'expanded' : 'collapsed'}`}>
      {!expanded ? (
        <button
          type="button"
          className="legend-toggle-btn"
          onClick={() => setExpanded(true)}
          title="Expand Inundation Legend"
        >
          <BarChart2 size={13} style={{ color: 'var(--cyan-bright)' }} />
          <span>FLOOD LEGEND</span>
          <ChevronUp size={12} style={{ color: 'var(--text-subtle)' }} />
        </button>
      ) : (
        <div className="legend-card-body">
          <div className="legend-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <BarChart2 size={13} style={{ color: 'var(--cyan-bright)' }} />
              <span className="legend-title">INUNDATION SCALE</span>
            </div>
            <button className="legend-close-btn" onClick={() => setExpanded(false)}>
              <ChevronDown size={14} />
            </button>
          </div>

          <div className="legend-scale-grid">
            <div className="legend-chip">
              <span className="legend-color" style={{ background: '#10b981' }}></span>
              <span>0–15cm <small>(Low)</small></span>
            </div>
            <div className="legend-chip">
              <span className="legend-color" style={{ background: '#f59e0b' }}></span>
              <span>15–30cm <small>(Mod)</small></span>
            </div>
            <div className="legend-chip">
              <span className="legend-color" style={{ background: '#f87171' }}></span>
              <span>30–50cm <small>(High)</small></span>
            </div>
            <div className="legend-chip">
              <span className="legend-color" style={{ background: '#ef4444' }}></span>
              <span>&gt;50cm <small>(Severe)</small></span>
            </div>
          </div>

          <div className="legend-meta-symbols">
            <span>🔴 Surcharged Conduit</span>
            <span>🟢 Safe Bypass</span>
            <span>🏥 Emergency Hub</span>
          </div>
        </div>
      )}
    </div>
  );
}
