import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom Map Marker Icons using HTML divIcons for high resolution GIS rendering
const createNodeIcon = (status) => {
  const isCritical = status === 'CRITICAL' || status === 'SURCHARGED';
  const color = isCritical ? '#ef4444' : status === 'WARNING' ? '#f59e0b' : '#10b981';
  return L.divIcon({
    className: 'custom-gis-marker',
    html: `<div style="width: 14px; height: 14px; background: ${color}; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 0 10px ${color}; cursor: pointer;"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

const createFacilityIcon = (name) => {
  return L.divIcon({
    className: 'custom-facility-marker',
    html: `<div style="background: #0d1420; border: 1px solid #38bdf8; border-radius: 4px; padding: 2px 6px; color: #38bdf8; font-size: 10px; font-weight: 800; white-space: nowrap; box-shadow: 0 2px 8px rgba(0,0,0,0.6); cursor: pointer;">🏥 ${name}</div>`,
    iconAnchor: [30, 10]
  });
};

const DEFAULT_CENTER = [13.0827, 80.2707];
const DEFAULT_ZOOM = 13;

export default function LeafletMapComponent({
  zones,
  layers = {},
  terrainData,
  runoffData,
  drainageData,
  mlPredictData,
  selectedObject,
  onSelectObject,
  onCoordsChange,
  onMapReady,
  searchTarget
}) {
  const containerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);
  const searchMarkerRef = useRef(null);
  const coordsCbRef = useRef(onCoordsChange);
  const selectCbRef = useRef(onSelectObject);
  const readyCbRef = useRef(onMapReady);

  useEffect(() => {
    coordsCbRef.current = onCoordsChange;
  }, [onCoordsChange]);

  useEffect(() => {
    selectCbRef.current = onSelectObject;
  }, [onSelectObject]);

  useEffect(() => {
    readyCbRef.current = onMapReady;
  }, [onMapReady]);

  // Initialize Map Instance
  useEffect(() => {
    if (!containerRef.current || mapInstanceRef.current) return;

    const map = L.map(containerRef.current, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: false,
      dragging: true,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      boxZoom: true,
      keyboard: true,
      touchZoom: true,
      attributionControl: false
    });

    // OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: ''
    }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;
    mapInstanceRef.current = map;

    if (readyCbRef.current) {
      readyCbRef.current(map);
    }

    // Track mouse position coordinates
    map.on('mousemove', (e) => {
      if (coordsCbRef.current) {
        coordsCbRef.current({
          lat: e.latlng.lat.toFixed(4),
          lng: e.latlng.lng.toFixed(4),
          zoom: map.getZoom()
        });
      }
    });

    // Track zoom changes
    map.on('zoomend', () => {
      if (coordsCbRef.current) {
        const center = map.getCenter();
        coordsCbRef.current({
          lat: center.lat.toFixed(4),
          lng: center.lng.toFixed(4),
          zoom: map.getZoom()
        });
      }
    });

    // Initial resize trigger after DOM paint
    requestAnimationFrame(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });

    // Handle container resize automatically
    const resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(() => {
        if (mapInstanceRef.current) {
          mapInstanceRef.current.invalidateSize();
        }
      });
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Handle Search FlyTo and Location Marker
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !searchTarget) return;

    if (searchMarkerRef.current) {
      map.removeLayer(searchMarkerRef.current);
      searchMarkerRef.current = null;
    }

    const { lat, lng, zoom = 14, label = 'Search Location' } = searchTarget;

    map.flyTo([lat, lng], zoom, { duration: 1.2 });

    const searchIcon = L.divIcon({
      className: 'custom-search-marker',
      html: `<div style="width: 18px; height: 18px; background: #38bdf8; border: 3px solid #ffffff; border-radius: 50%; box-shadow: 0 0 14px #38bdf8; cursor: pointer;"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });

    const marker = L.marker([lat, lng], { icon: searchIcon }).addTo(map);
    marker.bindPopup(`<b>📍 ${label}</b><br/>Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`).openPopup();
    searchMarkerRef.current = marker;
  }, [searchTarget]);

  // Update GIS Layers when prop data or layer toggle options change
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    // 1. Catchment Zones & Flood Inundation Heat Polygons
    if (layers.riskZones || layers.floodDepth) {
      const rawZoneList = [
        { id: "Z01", name: "Central Commercial District", coords: [[13.085, 80.265], [13.090, 80.265], [13.090, 80.275], [13.085, 80.275]], risk: "HIGH", depth: 42.5 },
        { id: "Z02", name: "North Market Area", coords: [[13.090, 80.265], [13.095, 80.265], [13.095, 80.275], [13.090, 80.275]], risk: "HIGH", depth: 38.0 },
        { id: "Z03", name: "Station Road Corridor", coords: [[13.080, 80.265], [13.085, 80.265], [13.085, 80.275], [13.080, 80.275]], risk: "SEVERE", depth: 47.5 },
        { id: "Z04", name: "South Suburban Lowland", coords: [[13.075, 80.265], [13.080, 80.265], [13.080, 80.275], [13.075, 80.275]], risk: "MODERATE", depth: 21.0 },
        { id: "Z05", name: "Hospital Relief Zone", coords: [[13.095, 80.275], [13.100, 80.275], [13.100, 80.285], [13.095, 80.285]], risk: "LOW", depth: 6.0 }
      ];

      const zoneGeoData = rawZoneList.map(z => {
        const liveMatch = Array.isArray(zones) ? zones.find(b => b.zone_id === z.id || b.id === z.id) : null;
        const mlMatch = Array.isArray(mlPredictData?.predictions) ? mlPredictData.predictions.find(p => p.zone_id === z.id) : null;

        const liveDepth = liveMatch?.flood_depth_cm ?? liveMatch?.current_flood_depth_cm ?? mlMatch?.predicted_depth_cm ?? z.depth;
        const liveRisk = liveMatch?.risk_level ?? liveMatch?.hazard_risk_level ?? mlMatch?.risk_level ?? z.risk;
        return {
          ...z,
          depth: liveDepth,
          risk: liveRisk
        };
      });

      zoneGeoData.forEach(z => {
        const isSelected = selectedObject?.id === z.id;
        const color = z.risk === 'SEVERE' || z.risk === 'CRITICAL' ? '#ef4444' : z.risk === 'HIGH' ? '#f87171' : z.risk === 'MODERATE' ? '#f59e0b' : '#10b981';

        const polygon = L.polygon(z.coords, {
          color: color,
          weight: isSelected ? 3 : 1.5,
          fillColor: color,
          fillOpacity: isSelected ? 0.45 : 0.25
        });

        polygon.bindTooltip(`<b>${z.name} (${z.id})</b><br/>Flood Depth: ${z.depth} cm<br/>Risk: ${z.risk}`, { sticky: true });
        polygon.on('click', () => {
          if (selectCbRef.current) {
            selectCbRef.current({
              type: 'ZONE',
              id: z.id,
              name: z.name,
              details: { flood_depth_cm: z.depth, risk_level: z.risk, peak_depth_cm: z.depth + 10, onset_minutes: 30, bottleneck_node: 'N21' }
            });
          }
        });

        layerGroup.addLayer(polygon);
      });
    }

    // 2. Drainage Network Nodes & Conduits
    if (layers.drainageNetwork) {
      const nodesData = drainageData?.nodes ? drainageData.nodes.map(n => ({
        id: n.node_id,
        name: n.name,
        lat: n.latitude || (n.node_id === 'N21' ? 13.0827 : n.node_id === 'N14' ? 13.0920 : 13.0980),
        lng: n.longitude || (n.node_id === 'N21' ? 80.2707 : n.node_id === 'N14' ? 80.2700 : 80.2800),
        status: n.status || (n.is_surcharged ? 'SURCHARGED' : 'NORMAL'),
        utilization: n.utilization_pct || (n.is_surcharged ? 122 : 85)
      })) : [
        { id: "N21", name: "Station Junction Sump", lat: 13.0827, lng: 80.2707, status: "SURCHARGED", utilization: 122 },
        { id: "N14", name: "North Market Culvert", lat: 13.0920, lng: 80.2700, status: "CRITICAL", utilization: 112 },
        { id: "N01", name: "Hospital Outfall Sump", lat: 13.0980, lng: 80.2800, status: "NORMAL", utilization: 32 }
      ];

      nodesData.forEach(node => {
        const marker = L.marker([node.lat, node.lng], { icon: createNodeIcon(node.status) });
        marker.bindPopup(`<b>Node ${node.id}: ${node.name}</b><br/>Status: ${node.status}<br/>Utilization: ${node.utilization}%`);
        marker.on('click', () => {
          if (selectCbRef.current) {
            selectCbRef.current({
              type: 'DRAINAGE NODE',
              id: node.id,
              name: node.name,
              details: { flood_depth_cm: 47.5, risk_level: node.status === 'SURCHARGED' ? 'CRITICAL' : 'HIGH', peak_depth_cm: 58.0, onset_minutes: 15, bottleneck_node: node.id }
            });
          }
        });
        layerGroup.addLayer(marker);
      });

      // Drainage Pipe Line Conduits
      const pipeLine = L.polyline([[13.0827, 80.2707], [13.0920, 80.2700], [13.0980, 80.2800]], {
        color: '#06b6d4',
        weight: 3,
        dashArray: '6, 6'
      });
      pipeLine.bindTooltip('Main Trunk Drain Conduit E21 (Utilization: 118%)');
      layerGroup.addLayer(pipeLine);
    }

    // 3. Critical Facilities (Hospital, Emergency Station)
    if (layers.criticalFacilities) {
      const hospitalMarker = L.marker([13.0980, 80.2800], { icon: createFacilityIcon('City General Hospital') });
      hospitalMarker.bindPopup('<b>City General Hospital</b><br/>Emergency Relief Access Hub');
      layerGroup.addLayer(hospitalMarker);
    }

    // 4. Safe Bypass Route Polyline Overlay
    if (layers.roads) {
      const safeRoute = L.polyline([
        [13.0827, 80.2707],
        [13.0890, 80.2650],
        [13.0950, 80.2750],
        [13.0980, 80.2800]
      ], {
        color: '#10b981',
        weight: 4,
        opacity: 0.9
      });
      safeRoute.bindTooltip('<b>Route B (Recommended Safe Route)</b><br/>Max Depth: 6 cm (Safe)', { permanent: false });
      layerGroup.addLayer(safeRoute);
    }

    requestAnimationFrame(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
      }
    });
  }, [layers, selectedObject]);

  return (
    <div className="leaflet-map-wrapper">
      <div ref={containerRef} className="leaflet-map-container" />
    </div>
  );
}
