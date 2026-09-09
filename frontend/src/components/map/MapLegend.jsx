import React from 'react';

export default function MapLegend() {
  return (
    <div className="map-legend-box">
      <div className="legend-title">FLOOD INUNDATION SCALE</div>
      <div className="legend-scale-row">
        <div className="legend-chip">
          <span className="legend-color" style={{ background: '#10b981' }}></span> 0–15 cm (Low)
        </div>
        <div className="legend-chip">
          <span className="legend-color" style={{ background: '#f59e0b' }}></span> 15–30 cm (Mod)
        </div>
        <div className="legend-chip">
          <span className="legend-color" style={{ background: '#f87171' }}></span> 30–50 cm (High)
        </div>
        <div className="legend-chip">
          <span className="legend-color" style={{ background: '#ef4444' }}></span> &gt;50 cm (Severe)
        </div>
      </div>
      <div style={{ display: 'flex', gap: '12px', fontSize: '0.6rem', color: 'var(--text-subtle)', borderTop: '1px solid var(--border)', paddingTop: '4px' }}>
        <span>🔴 Surcharged Conduit</span>
        <span>🟢 Safe Route Bypass</span>
        <span>🏥 Emergency Target</span>
      </div>
    </div>
  );
}
