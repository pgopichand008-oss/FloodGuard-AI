import React from 'react';
import { X, Layers } from 'lucide-react';

export default function MapLayers({ layers = {}, onToggleLayer, onClose }) {
  const layerItems = [
    { key: 'rainfall', label: 'Rainfall Intensity Raster', desc: 'Nowcast radar precipitation field' },
    { key: 'floodDepth', label: 'Inundation Depth Heatmap', desc: 'Hydrodynamic flood depth surface' },
    { key: 'dem', label: 'Digital Elevation Model (DEM)', desc: 'Topographic elevation contour lines' },
    { key: 'surfaceFlow', label: 'Surface Runoff Vectors', desc: 'Overland flow accumulation paths' },
    { key: 'drainageNetwork', label: 'Drainage Network & Sumps', desc: 'Urban conduits, junctions & pumps' },
    { key: 'roads', label: 'Road Network & Safe Routes', desc: 'Corridors and flood-safe bypasses' },
    { key: 'riskZones', label: 'Catchment Hazard Zones', desc: 'Delineated urban risk perimeters' },
    { key: 'criticalFacilities', label: 'Critical Infrastructure', desc: 'Hospitals, emergency hubs, power' }
  ];

  return (
    <div className="drawer-panel">
      <div className="drawer-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={14} style={{ color: 'var(--cyan-bright)' }} />
          <span className="drawer-title">GIS LAYER MANAGEMENT</span>
        </div>
        <button className="drawer-close-btn" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div className="drawer-body">
        <div className="checkbox-stack">
          {layerItems.map((item) => {
            const isChecked = !!layers[item.key];
            return (
              <label key={item.key} className={`checkbox-item ${isChecked ? 'checked' : ''}`}>
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => onToggleLayer(item.key)}
                />
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.72rem' }}>{item.label}</span>
                  <span style={{ fontSize: '0.62rem', color: 'var(--text-subtle)' }}>{item.desc}</span>
                </div>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
