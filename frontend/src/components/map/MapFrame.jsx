import React, { useState, useEffect, useRef } from 'react';
import LeafletMapComponent from './LeafletMapComponent';
import CesiumMapComponent from './CesiumMapComponent';
import MapToolbar from './MapToolbar';
import MapLegend from './MapLegend';
import MapLayers from './MapLayers';
import MapGraphTools from './MapGraphTools';
import { ShieldCheck, Search, Loader2, X, Box, Layers } from 'lucide-react';

export default function MapFrame({
  zones,
  terrainData,
  runoffData,
  drainageData,
  mlPredictData,
  layers,
  onToggleLayer,
  selectedObject,
  onSelectObject,
  activeWorkspace,
  setActiveWorkspace
}) {
  const [viewMode, setViewMode] = useState('2D'); // '2D' or '3D'
  const [mapInstance, setMapInstance] = useState(null);
  const [cesiumController, setCesiumController] = useState(null);
  const [showGraphTools, setShowGraphTools] = useState(false);
  const [coords, setCoords] = useState({ lat: '13.0827', lng: '80.2707', zoom: 13 });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const [geoResults, setGeoResults] = useState([]);
  const [searchTarget, setSearchTarget] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const mapFrameRef = useRef(null);

  // Internal FloodGuard GIS items catalog
  const internalItems = [
    { id: 'Z01', name: 'Central Commercial District (Z01)', category: 'INTERNAL', type: 'High-Risk Zone', lat: 13.0875, lng: 80.2700, zoom: 15 },
    { id: 'Z03', name: 'Station Road Corridor (Z03)', category: 'INTERNAL', type: 'Severe Risk Zone', lat: 13.0825, lng: 80.2700, zoom: 15 },
    { id: 'N21', name: 'Station Junction Sump (N21)', category: 'INTERNAL', type: 'Surcharged Sump Node', lat: 13.0827, lng: 80.2707, zoom: 16 },
    { id: 'N14', name: 'North Market Culvert (N14)', category: 'INTERNAL', type: 'Critical Culvert Node', lat: 13.0920, lng: 80.2700, zoom: 16 },
    { id: 'Z05', name: 'City General Hospital (Z05)', category: 'INTERNAL', type: 'Emergency Hospital Hub', lat: 13.0980, lng: 80.2800, zoom: 16 },
    { id: 'N01', name: 'Hospital Outfall Sump (N01)', category: 'INTERNAL', type: 'Normal Drainage Node', lat: 13.0980, lng: 80.2800, zoom: 16 },
    { id: 'LOC01', name: 'Chennai Central Station', category: 'INTERNAL', type: 'Transit Hub', lat: 13.0827, lng: 80.2707, zoom: 15 },
    { id: 'LOC02', name: 'Anna Salai Arterial Corridor', category: 'INTERNAL', type: 'Primary Highway', lat: 13.0600, lng: 80.2500, zoom: 14 },
    { id: 'LOC03', name: 'Velachery Lowland Lake Zone', category: 'INTERNAL', type: 'Inundation Basin', lat: 12.9750, lng: 80.2200, zoom: 14 },
    { id: 'LOC04', name: 'Adyar River Outfall Basin', category: 'INTERNAL', type: 'Drainage Channel', lat: 13.0080, lng: 80.2570, zoom: 14 },
    { id: 'LOC05', name: 'Egmore Relief Operations Center', category: 'INTERNAL', type: 'Emergency Hub', lat: 13.0780, lng: 80.2600, zoom: 15 },
    { id: 'LOC06', name: 'Marina Coastal Drainage Outfall', category: 'INTERNAL', type: 'Coastal Outfall', lat: 13.0500, lng: 80.2820, zoom: 14 }
  ];

  const matchedInternal = internalItems.filter(item =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // OpenStreetMap Nominatim Geocoding Fetch (Debounced)
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 3) {
      return;
    }

    const timer = setTimeout(() => {
      setSearching(true);
      fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=4`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            const formatted = data.map(item => ({
              id: item.place_id,
              name: item.display_name,
              category: 'GEOGRAPHIC',
              type: item.type ? item.type.toUpperCase() : 'LOCATION',
              lat: parseFloat(item.lat),
              lng: parseFloat(item.lon),
              zoom: 14
            }));
            setGeoResults(formatted);
          }
          setSearching(false);
        })
        .catch(() => {
          setGeoResults([]);
          setSearching(false);
        });
    }, 350);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectSearchResult = (result) => {
    if (result.category === 'INTERNAL') {
      onSelectObject({
        type: result.type,
        id: result.id,
        name: result.name,
        details: { flood_depth_cm: 47.5, risk_level: 'CRITICAL', peak_depth_cm: 58.0, onset_minutes: 25, bottleneck_node: result.id === 'N21' ? 'N21' : 'N21' }
      });
    }

    const target = {
      lat: result.lat,
      lng: result.lng,
      zoom: result.zoom || 15,
      label: result.name
    };

    setSearchTarget(target);

    if (viewMode === '3D' && cesiumController) {
      cesiumController.setView([result.lat, result.lng]);
    }

    setSearchQuery('');
    setSearchOpen(false);
  };

  const handleZoomIn = () => {
    if (viewMode === '2D' && mapInstance) {
      mapInstance.zoomIn();
    } else if (viewMode === '3D' && cesiumController) {
      cesiumController.zoomIn();
    }
  };

  const handleZoomOut = () => {
    if (viewMode === '2D' && mapInstance) {
      mapInstance.zoomOut();
    } else if (viewMode === '3D' && cesiumController) {
      cesiumController.zoomOut();
    }
  };

  const handleRecenter = () => {
    if (viewMode === '2D' && mapInstance) {
      mapInstance.setView([13.0827, 80.2707], 13);
    } else if (viewMode === '3D' && cesiumController) {
      cesiumController.setView([13.0827, 80.2707]);
    }
  };

  const handleFitBounds = () => {
    if (viewMode === '2D' && mapInstance) {
      mapInstance.fitBounds([
        [13.075, 80.265],
        [13.100, 80.285]
      ]);
    } else if (viewMode === '3D' && cesiumController) {
      cesiumController.fitBounds();
    }
  };

  const handleLocateSelected = () => {
    let targetLat = 13.0827;
    let targetLng = 80.2707;
    let targetZoom = 14;

    if (selectedObject?.id === 'Z03' || selectedObject?.id === 'N21') {
      targetLat = 13.0827;
      targetLng = 80.2707;
      targetZoom = 15;
    } else if (selectedObject?.id === 'Z01') {
      targetLat = 13.0875;
      targetLng = 80.2700;
      targetZoom = 15;
    } else if (selectedObject?.id === 'Z05') {
      targetLat = 13.0980;
      targetLng = 80.2800;
      targetZoom = 15;
    }

    if (viewMode === '2D' && mapInstance) {
      mapInstance.setView([targetLat, targetLng], targetZoom);
    } else if (viewMode === '3D' && cesiumController) {
      cesiumController.setView([targetLat, targetLng]);
    }
  };

  const handleToggleFullscreen = () => {
    if (!mapFrameRef.current) return;
    if (!document.fullscreenElement) {
      mapFrameRef.current.requestFullscreen().then(() => {
        setIsFullscreen(true);
        if (mapInstance) mapInstance.invalidateSize();
      }).catch(() => {
        setIsFullscreen(!isFullscreen);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
        if (mapInstance) mapInstance.invalidateSize();
      }).catch(() => {
        setIsFullscreen(false);
      });
    }
  };

  const allSearchResults = [...matchedInternal, ...geoResults];

  return (
    <div
      ref={mapFrameRef}
      className={`map-frame-container ${isFullscreen ? 'gis-fullscreen-active' : ''}`}
    >
      {/* Map Header */}
      <header className="map-frame-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={14} style={{ color: 'var(--cyan-bright)' }} />
          <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-bright)', letterSpacing: '0.04em' }}>
            CENTRAL GIS COMMAND VIEWPORT
          </span>

          {/* 2D / 3D View Mode Toggle Switch */}
          <div className="view-mode-toggle" style={{ display: 'flex', alignItems: 'center', background: 'rgba(10, 15, 26, 0.8)', border: '1px solid var(--border)', borderRadius: '4px', padding: '2px', marginLeft: '12px' }}>
            <button
              className={`view-mode-btn ${viewMode === '2D' ? 'active' : ''}`}
              onClick={() => setViewMode('2D')}
              style={{
                background: viewMode === '2D' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
                border: viewMode === '2D' ? '1px solid var(--cyan-bright)' : '1px solid transparent',
                color: viewMode === '2D' ? 'var(--cyan-bright)' : 'var(--text-muted)',
                borderRadius: '3px',
                padding: '2px 8px',
                fontSize: '0.66rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 150ms ease',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Layers size={11} />
              <span>2D View</span>
            </button>
            <button
              className={`view-mode-btn ${viewMode === '3D' ? 'active' : ''}`}
              onClick={() => setViewMode('3D')}
              style={{
                background: viewMode === '3D' ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
                border: viewMode === '3D' ? '1px solid var(--purple)' : '1px solid transparent',
                color: viewMode === '3D' ? '#c084fc' : 'var(--text-muted)',
                borderRadius: '3px',
                padding: '2px 8px',
                fontSize: '0.66rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 150ms ease',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Box size={11} />
              <span>3D View (Cesium)</span>
            </button>
          </div>
        </div>

        {/* GIS Search Bar */}
        <div className="map-search-container" style={{ position: 'relative' }}>
          <div className="search-input-wrapper">
            {searching ? <Loader2 size={12} className="spin" style={{ color: 'var(--cyan-bright)' }} /> : <Search size={12} style={{ color: 'var(--text-subtle)' }} />}
            <input
              type="text"
              className="map-search-input"
              placeholder="Search Place, Zone, Node, Street..."
              value={searchQuery}
              onChange={(e) => {
                const val = e.target.value;
                setSearchQuery(val);
                if (val.trim().length < 3) setGeoResults([]);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && allSearchResults.length > 0) {
                  e.preventDefault();
                  handleSelectSearchResult(allSearchResults[0]);
                }
              }}
            />
            {searchQuery && (
              <X
                size={12}
                style={{ color: 'var(--text-subtle)', cursor: 'pointer', flexShrink: 0 }}
                onClick={() => {
                  setSearchQuery('');
                  setGeoResults([]);
                  setSearchOpen(false);
                }}
              />
            )}
          </div>

          {searchOpen && searchQuery && (
            <div className="map-search-dropdown">
              <div className="dropdown-header">GIS & GEOGRAPHIC RESULTS</div>
              {allSearchResults.length > 0 ? (
                allSearchResults.map(res => (
                  <div key={res.id + res.name} className="search-result-item" onClick={() => handleSelectSearchResult(res)}>
                    <span>{res.category === 'INTERNAL' ? '🔴' : '📍'}</span>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '170px' }}>{res.name}</span>
                    <span style={{ fontSize: '0.55rem', color: res.category === 'INTERNAL' ? 'var(--cyan-bright)' : 'var(--text-subtle)', marginLeft: 'auto', flexShrink: 0 }}>{res.type}</span>
                  </div>
                ))
              ) : (
                <div className="search-no-results">
                  {searching ? 'Querying GIS directory...' : 'No matching location or feature found'}
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Map Viewport Canvas */}
      <div className="map-frame-viewport">
        {viewMode === '2D' ? (
          <LeafletMapComponent
            zones={zones}
            terrainData={terrainData}
            runoffData={runoffData}
            drainageData={drainageData}
            mlPredictData={mlPredictData}
            layers={layers}
            selectedObject={selectedObject}
            onSelectObject={onSelectObject}
            onCoordsChange={setCoords}
            onMapReady={setMapInstance}
            searchTarget={searchTarget}
          />
        ) : (
          <CesiumMapComponent
            zones={zones}
            terrainData={terrainData}
            runoffData={runoffData}
            drainageData={drainageData}
            mlPredictData={mlPredictData}
            selectedObject={selectedObject}
            onSelectObject={onSelectObject}
            onSwitchTo2D={() => setViewMode('2D')}
            onMapReady={setCesiumController}
            searchTarget={searchTarget}
          />
        )}

        {/* Floating Map Controls & Navigation Toolkit */}
        <MapToolbar
          activeWorkspace={activeWorkspace}
          setActiveWorkspace={setActiveWorkspace}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onRecenter={handleRecenter}
          onFitBounds={handleFitBounds}
          onLocateSelected={handleLocateSelected}
          isFullscreen={isFullscreen}
          onToggleFullscreen={handleToggleFullscreen}
          showGraphTools={showGraphTools}
          onToggleGraphTools={() => setShowGraphTools(!showGraphTools)}
        />

        {/* Dynamic GIS Legend */}
        <MapLegend />

        {/* Floating Layers Panel Drawer */}
        {activeWorkspace === 'layers' && (
          <MapLayers layers={layers} onToggleLayer={onToggleLayer} onClose={() => setActiveWorkspace(null)} />
        )}

        {/* Floating Graph & Analytics Toolkit Drawer */}
        {showGraphTools && (
          <MapGraphTools zones={zones} onClose={() => setShowGraphTools(false)} />
        )}
      </div>

      {/* Map Footer Status */}
      <footer className="map-frame-footer">
        <div>
          <span>PROJECTION: <strong>EPSG:4326 (WGS84)</strong></span>
          <span className="coord-sep" style={{ margin: '0 8px' }}>|</span>
          <span>TILES: <strong>{viewMode === '2D' ? 'OpenStreetMap Standard 2D' : 'Cesium 3D Globe View'}</strong></span>
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
