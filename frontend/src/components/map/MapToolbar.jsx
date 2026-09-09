import React from 'react';
import { Layers, Plus, Minus, RotateCcw, Crosshair, Maximize2, Minimize2, ZoomIn, LineChart } from 'lucide-react';
import MapCompass from './MapCompass';

export default function MapToolbar({
  activeWorkspace,
  setActiveWorkspace,
  onZoomIn,
  onZoomOut,
  onRecenter,
  onFitBounds,
  onLocateSelected,
  isFullscreen,
  onToggleFullscreen,
  showGraphTools,
  onToggleGraphTools
}) {
  return (
    <div className="map-controls-row">
      {/* Viewmode & Layer Quick Tools - Vertical Navigation Bar */}
      <div className="map-floating-toolbar" style={{ flexDirection: 'column', gap: '4px', padding: '5px' }}>
        <button
          className="map-tool-btn"
          onClick={onZoomIn}
          title="Zoom In (+)"
        >
          <Plus size={14} />
        </button>

        <button
          className="map-tool-btn"
          onClick={onZoomOut}
          title="Zoom Out (-)"
        >
          <Minus size={14} />
        </button>

        <div style={{ height: '1px', background: 'var(--border)', width: '100%', margin: '2px 0' }} />

        <button
          className="map-tool-btn"
          onClick={onRecenter}
          title="Reset Map Home View"
        >
          <RotateCcw size={13} />
        </button>

        <button
          className="map-tool-btn"
          onClick={onFitBounds}
          title="Fit View to Flood Extent"
        >
          <ZoomIn size={13} />
        </button>

        <button
          className="map-tool-btn"
          onClick={onLocateSelected}
          title="Locate Selected Feature"
        >
          <Crosshair size={13} />
        </button>

        <div style={{ height: '1px', background: 'var(--border)', width: '100%', margin: '2px 0' }} />

        <button
          className={`map-tool-btn ${showGraphTools ? 'active' : ''}`}
          onClick={onToggleGraphTools}
          title="Toggle GIS Graph & Analytics Tools"
        >
          <LineChart size={14} />
        </button>

        <button
          className={`map-tool-btn ${activeWorkspace === 'layers' ? 'active' : ''}`}
          onClick={() => setActiveWorkspace(activeWorkspace === 'layers' ? null : 'layers')}
          title="Toggle GIS Layer Controls"
        >
          <Layers size={14} />
        </button>
      </div>

      {/* Right Top Navigation Widgets */}
      <div className="map-viewmode-controls" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <MapCompass onResetView={onRecenter} />

        <button
          className="fullscreen-toggle-btn"
          onClick={onToggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen GIS Workspace" : "Enter Fullscreen GIS Workspace"}
        >
          {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
          <span>{isFullscreen ? "EXIT FULLSCREEN" : "FULLSCREEN"}</span>
        </button>
      </div>
    </div>
  );
}
