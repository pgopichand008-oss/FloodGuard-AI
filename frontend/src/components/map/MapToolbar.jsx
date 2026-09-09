import React from 'react';
import { Layers, Maximize2, RotateCcw, Crosshair } from 'lucide-react';

export default function MapToolbar({ activeWorkspace, setActiveWorkspace }) {
  return (
    <div className="map-controls-row">
      {/* Viewmode & Layer Quick Tools */}
      <div className="map-floating-toolbar">
        <button
          className={`map-tool-btn ${activeWorkspace === 'layers' ? 'active' : ''}`}
          onClick={() => setActiveWorkspace(activeWorkspace === 'layers' ? null : 'layers')}
          title="Toggle Layers Panel"
        >
          <Layers size={14} />
        </button>
        <button className="map-tool-btn" title="Center Map on Selected Feature">
          <Crosshair size={14} />
        </button>
        <button className="map-tool-btn" title="Reset View Bounds">
          <RotateCcw size={14} />
        </button>
        <span className="zoom-indicator">2D GIS MODE</span>
      </div>

      {/* Navigation Widgets */}
      <div className="map-viewmode-controls">
        <div className="north-arrow">
          <span className="arrow-head">▲</span>
          <span className="arrow-label">N</span>
        </div>
        <button className="fullscreen-toggle-btn" title="Toggle Fullscreen Workspace">
          <Maximize2 size={13} />
          <span>FULLSCREEN</span>
        </button>
      </div>
    </div>
  );
}
