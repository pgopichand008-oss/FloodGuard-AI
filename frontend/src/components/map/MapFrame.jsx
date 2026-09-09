import React, { useState } from 'react';
import LeafletMapComponent from './LeafletMapComponent';
import MapToolbar from './MapToolbar';
import MapLegend from './MapLegend';
import MapLayers from './MapLayers';
import { ShieldCheck, Search } from 'lucide-react';

export default function MapFrame({
  zones,
  layers,
  onToggleLayer,
  selectedObject,
  onSelectObject,
  activeWorkspace,
  setActiveWorkspace
}) {
  const [coords, setCoords] = useState({ lat: '13.0827', lng: '80.2707', zoom: 13 });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);

  const searchResults = [
    { id: 'Z03', name: 'Station Road Corridor', type: 'High-Risk Zone' },
    { id: 'N21', name: 'Station Junction Sump (N21)', type: 'Drainage Node' },
    { id: 'Z05', name: 'City General Hospital (Z05)', type: 'Emergency Target' }
  ].filter(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const handleSelectSearchResult = (result) => {
    onSelectObject({
      type: result.type,
      id: result.id,
      name: result.name,
      details: { flood_depth_cm: 47.5, risk_level: 'CRITICAL', peak_depth_cm: 58.0, onset_minutes: 25, bottleneck_node: 'N21' }
    });
    setSearchQuery('');
    setSearchOpen(false);
  };

  return (
    <div className="map-frame-container">
      {/* Map Header */}
      <header className="map-frame-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={14} style={{ color: 'var(--cyan-bright)' }} />
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-bright)', letterSpacing: '0.04em' }}>
            CENTRAL GIS COMMAND VIEWPORT
          </span>
          <span className="status-chip chip-nominal" style={{ padding: '1px 6px', fontSize: '0.58rem' }}>
            ● DEMO BASEMAP (OPENSTREETMAP 2D)
          </span>
        </div>

        {/* GIS Search Bar */}
        <div className="map-search-container" style={{ position: 'relative' }}>
          <div className="search-input-wrapper">
            <Search size={12} style={{ color: 'var(--text-subtle)' }} />
            <input
              type="text"
              className="map-search-input"
              placeholder="Search Zone, Node, Street..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setSearchOpen(true); }}
              onFocus={() => setSearchOpen(true)}
            />
          </div>

          {searchOpen && searchQuery && (
            <div className="map-search-dropdown">
              <div className="dropdown-header">GIS SEARCH RESULTS</div>
              {searchResults.length > 0 ? (
                searchResults.map(res => (
                  <div key={res.id} className="search-result-item" onClick={() => handleSelectSearchResult(res)}>
                    <span>📍</span>
                    <span>{res.name}</span>
                    <span style={{ fontSize: '0.58rem', color: 'var(--text-subtle)', marginLeft: 'auto' }}>{res.type}</span>
                  </div>
                ))
              ) : (
                <div className="search-no-results">No matching GIS feature found</div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Leaflet Viewport Canvas */}
      <div className="map-frame-viewport">
        <LeafletMapComponent
          zones={zones}
          layers={layers}
          selectedObject={selectedObject}
          onSelectObject={onSelectObject}
          onCoordsChange={setCoords}
        />

        {/* Floating Map Controls & Mode Toggles */}
        <MapToolbar
          activeWorkspace={activeWorkspace}
          setActiveWorkspace={setActiveWorkspace}
          layers={layers}
          onToggleLayer={onToggleLayer}
        />

        {/* Dynamic GIS Legend */}
        <MapLegend />

        {/* Floating Layers Panel Drawer */}
        {activeWorkspace === 'layers' && (
          <MapLayers layers={layers} onToggleLayer={onToggleLayer} onClose={() => setActiveWorkspace(null)} />
        )}
      </div>

      {/* Map Footer Status */}
      <footer className="map-frame-footer">
        <div>
          <span>PROJECTION: <strong>EPSG:4326 (WGS84)</strong></span>
          <span className="coord-sep" style={{ margin: '0 8px' }}>|</span>
          <span>TILES: <strong>OpenStreetMap Standard</strong></span>
        </div>
        <div className="map-coordinate-box" style={{ position: 'static', background: 'transparent', border: 'none', padding: 0 }}>
          <span>LAT: <strong>{coords.lat}° N</strong></span>
          <span className="coord-sep">|</span>
          <span>LNG: <strong>{coords.lng}° E</strong></span>
          <span className="coord-sep">|</span>
          <span>ZOOM: <strong>{coords.zoom}x</strong></span>
        </div>
      </footer>
    </div>
  );
}
