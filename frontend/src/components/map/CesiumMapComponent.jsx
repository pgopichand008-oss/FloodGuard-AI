import React, { useEffect, useRef, useState } from 'react';
import { Box, Layers, ShieldCheck, ExternalLink, RotateCw, AlertCircle, Compass } from 'lucide-react';

export default function CesiumMapComponent({
  zones = [],
  terrainData,
  runoffData,
  drainageData,
  mlPredictData,
  selectedObject,
  onSelectObject,
  onSwitchTo2D,
  onMapReady,
  searchTarget
}) {
  const containerRef = useRef(null);
  const [cesiumStatus, setCesiumStatus] = useState('CHECKING'); // 'CHECKING', 'READY', 'UNCONFIGURED', 'ERROR'
  const [statusMessage, setStatusMessage] = useState('');
  const viewerRef = useRef(null);

  const cesiumToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

  useEffect(() => {
    let isMounted = true;

    // Set global CESIUM_BASE_URL for asset and worker resolution
    window.CESIUM_BASE_URL = 'https://cdn.jsdelivr.net/npm/cesium@1.115.0/Build/Cesium/';

    // Ensure Cesium CSS is present in head
    const styleId = 'cesium-css-cdn';
    if (!document.getElementById(styleId)) {
      const link = document.createElement('link');
      link.id = styleId;
      link.rel = 'stylesheet';
      link.href = 'https://cdn.jsdelivr.net/npm/cesium@1.115.0/Build/Cesium/Widgets/widgets.css';
      document.head.appendChild(link);
    }

    async function initCesium() {
      try {
        if (window.Cesium) {
          if (cesiumToken && cesiumToken.trim() !== '' && cesiumToken !== 'YOUR_CESIUM_ION_TOKEN') {
            window.Cesium.Ion.defaultAccessToken = cesiumToken;
          }
          setupViewer(window.Cesium);
        } else {
          // Load Cesium JS from primary CDN (jsDelivr), with unpkg fallback
          const scriptId = 'cesium-script-cdn';
          let script = document.getElementById(scriptId);

          if (!script) {
            script = document.createElement('script');
            script.id = scriptId;
            script.src = 'https://cdn.jsdelivr.net/npm/cesium@1.115.0/Build/Cesium/Cesium.js';
            document.body.appendChild(script);
          }

          const onScriptLoad = () => {
            if (isMounted && window.Cesium) {
              if (cesiumToken && cesiumToken.trim() !== '' && cesiumToken !== 'YOUR_CESIUM_ION_TOKEN') {
                window.Cesium.Ion.defaultAccessToken = cesiumToken;
              }
              setupViewer(window.Cesium);
            }
          };

          if (window.Cesium) {
            onScriptLoad();
          } else {
            script.addEventListener('load', onScriptLoad);
            script.addEventListener('error', () => {
              // Primary CDN failed, attempt unpkg fallback
              script.remove();
              const fallbackScript = document.createElement('script');
              fallbackScript.id = scriptId + '-fallback';
              window.CESIUM_BASE_URL = 'https://unpkg.com/cesium@1.115.0/Build/Cesium/';
              fallbackScript.src = 'https://unpkg.com/cesium@1.115.0/Build/Cesium/Cesium.js';
              fallbackScript.onload = () => {
                if (isMounted && window.Cesium) {
                  if (cesiumToken && cesiumToken.trim() !== '' && cesiumToken !== 'YOUR_CESIUM_ION_TOKEN') {
                    window.Cesium.Ion.defaultAccessToken = cesiumToken;
                  }
                  setupViewer(window.Cesium);
                }
              };
              fallbackScript.onerror = () => {
                if (isMounted) {
                  setCesiumStatus('ERROR');
                  setStatusMessage('CesiumJS library failed to load from CDN. 2D Map remains fully functional.');
                }
              };
              document.body.appendChild(fallbackScript);
            });
          }
        }
      } catch (err) {
        if (isMounted) {
          setCesiumStatus('ERROR');
          setStatusMessage(`Cesium initialization error: ${err.message}`);
        }
      }
    }

    function setupViewer(Cesium) {
      if (!containerRef.current || viewerRef.current) return;

      try {
        let baseLayerOption = undefined;
        if (Cesium.UrlTemplateImageryProvider && Cesium.ImageryLayer) {
          const osmProvider = new Cesium.UrlTemplateImageryProvider({
            url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            maximumLevel: 19,
            credit: 'OpenStreetMap contributors'
          });
          baseLayerOption = new Cesium.ImageryLayer(osmProvider);
        }

        const viewerOptions = {
          animation: false,
          timeline: false,
          baseLayerPicker: false,
          fullscreenButton: false,
          geocoder: false,
          homeButton: false,
          sceneModePicker: false,
          navigationHelpButton: false,
          infoBox: true,
          selectionIndicator: true
        };

        if (baseLayerOption) {
          viewerOptions.baseLayer = baseLayerOption;
        }

        const viewer = new Cesium.Viewer(containerRef.current, viewerOptions);
        viewerRef.current = viewer;

        // Fly camera to Chennai Catchment Area (13.0827, 80.2707) with 3D Tilt Perspective
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(80.2707, 13.0827, 4500.0),
          orientation: {
            heading: Cesium.Math.toRadians(0.0),
            pitch: Cesium.Math.toRadians(-35.0),
            roll: 0.0
          },
          duration: 1.5
        });

        // Add 3D Zone Pins & Inundation Polygons
        const defaultZones = zones.length > 0 ? zones : [
          { zone_id: 'Z01', name: 'Central Commercial (Z01)', lat: 13.0875, lng: 80.2700, depth: 40.4, risk: 'HIGH' },
          { zone_id: 'Z03', name: 'Station Road Sump (Z03)', lat: 13.0825, lng: 80.2700, depth: 47.5, risk: 'CRITICAL' },
          { zone_id: 'Z05', name: 'City General Hospital (Z05)', lat: 13.0980, lng: 80.2800, depth: 11.1, risk: 'LOW' }
        ];

        defaultZones.forEach(z => {
          const isCritical = z.risk === 'CRITICAL' || z.risk === 'HIGH';
          const pinColor = isCritical ? Cesium.Color.RED : Cesium.Color.LIGHTBLUE;

          viewer.entities.add({
            name: `3D Zone: ${z.name || z.zone_id}`,
            position: Cesium.Cartesian3.fromDegrees(z.lng || 80.2707, z.lat || 13.0827, 150),
            point: {
              pixelSize: 12,
              color: pinColor,
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 2
            },
            label: {
              text: `${z.zone_id || 'Z'}: ${z.depth || 30}cm (${z.risk || 'MODERATE'})`,
              font: '12px sans-serif',
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              outlineWidth: 2,
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              pixelOffset: new Cesium.Cartesian2(0, -15)
            }
          });
        });

        if (isMounted) setCesiumStatus('READY');

        // Create unified map controller interface wrapper for Cesium viewer
        const cesiumController = {
          zoomIn: () => {
            if (viewer && !viewer.isDestroyed()) {
              const currentHeight = viewer.camera.positionCartographic.height;
              viewer.camera.zoomIn(currentHeight * 0.35);
            }
          },
          zoomOut: () => {
            if (viewer && !viewer.isDestroyed()) {
              const currentHeight = viewer.camera.positionCartographic.height;
              viewer.camera.zoomOut(currentHeight * 0.5);
            }
          },
          setView: (latLng) => {
            if (viewer && !viewer.isDestroyed()) {
              const lat = Array.isArray(latLng) ? latLng[0] : latLng.lat;
              const lng = Array.isArray(latLng) ? latLng[1] : latLng.lng;
              viewer.camera.flyTo({
                destination: window.Cesium.Cartesian3.fromDegrees(lng, lat, 2200.0),
                orientation: {
                  heading: window.Cesium.Math.toRadians(0.0),
                  pitch: window.Cesium.Math.toRadians(-35.0),
                  roll: 0.0
                },
                duration: 1.5
              });
            }
          },
          fitBounds: () => {
            if (viewer && !viewer.isDestroyed()) {
              viewer.camera.flyTo({
                destination: window.Cesium.Cartesian3.fromDegrees(80.2707, 13.0827, 7500.0),
                orientation: {
                  heading: window.Cesium.Math.toRadians(0.0),
                  pitch: window.Cesium.Math.toRadians(-45.0),
                  roll: 0.0
                },
                duration: 1.5
              });
            }
          }
        };

        if (onMapReady) {
          onMapReady(cesiumController);
        }
      } catch (err) {
        if (isMounted) {
          setCesiumStatus('ERROR');
          setStatusMessage(`Cesium viewer setup exception: ${err.message}`);
        }
      }
    }

    initCesium();

    return () => {
      isMounted = false;
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        try {
          viewerRef.current.destroy();
        } catch {
          // cleanup
        }
        viewerRef.current = null;
      }
      if (onMapReady) {
        onMapReady(null);
      }
    };
  }, [cesiumToken]);

  // Handle search target navigation in 3D mode
  useEffect(() => {
    if (!searchTarget || !viewerRef.current || viewerRef.current.isDestroyed() || !window.Cesium) return;

    const { lat, lng } = searchTarget;
    if (lat && lng) {
      viewerRef.current.camera.flyTo({
        destination: window.Cesium.Cartesian3.fromDegrees(lng, lat, 1800.0),
        orientation: {
          heading: window.Cesium.Math.toRadians(0.0),
          pitch: window.Cesium.Math.toRadians(-35.0),
          roll: 0.0
        },
        duration: 1.5
      });

      if (searchTarget.label) {
        viewerRef.current.entities.add({
          name: `Search Target: ${searchTarget.label}`,
          position: window.Cesium.Cartesian3.fromDegrees(lng, lat, 100),
          point: {
            pixelSize: 14,
            color: window.Cesium.Color.CYAN,
            outlineColor: window.Cesium.Color.WHITE,
            outlineWidth: 2
          },
          label: {
            text: `📍 ${searchTarget.label}`,
            font: '13px bold sans-serif',
            style: window.Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineWidth: 2,
            verticalOrigin: window.Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new window.Cesium.Cartesian2(0, -18)
          }
        });
      }
    }
  }, [searchTarget]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#070b14', overflow: 'hidden' }}>
      {/* Container for active Cesium 3D Canvas */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', inset: 0 }} />

      {/* Unconfigured / Error Fallback State Card */}
      {(cesiumStatus === 'UNCONFIGURED' || cesiumStatus === 'ERROR') && (
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at center, rgba(13, 20, 32, 0.95) 0%, rgba(6, 8, 16, 0.98) 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          zIndex: 10
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: cesiumStatus === 'ERROR' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(168, 85, 247, 0.15)',
            border: cesiumStatus === 'ERROR' ? '1px solid var(--red-bright)' : '1px solid var(--purple)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: cesiumStatus === 'ERROR' ? '#f87171' : '#c084fc',
            marginBottom: '16px',
            boxShadow: cesiumStatus === 'ERROR' ? '0 0 20px rgba(239, 68, 68, 0.3)' : '0 0 20px rgba(168, 85, 247, 0.3)'
          }}>
            {cesiumStatus === 'ERROR' ? <AlertCircle size={24} /> : <Box size={24} />}
          </div>

          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-bright)', marginBottom: '6px', textAlign: 'center' }}>
            {cesiumStatus === 'ERROR' ? '3D CESIUMJS ENGINE INITIALIZATION ERROR' : '3D CESIUMJS VIEWPORT READY'}
          </h3>

          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: '440px', textAlign: 'center', lineHeight: '1.5', marginBottom: '16px' }}>
            {statusMessage || 'The 3D photogrammetry and terrain viewport requires an active Cesium Ion access token configured in environment variables.'}
          </p>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="inspector-btn"
              onClick={onSwitchTo2D}
              style={{ padding: '6px 14px', width: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Compass size={14} />
              <span>Switch Back to 2D Leaflet View</span>
            </button>
          </div>
        </div>
      )}

      {/* Floating 3D Controls Badge when active */}
      {cesiumStatus === 'READY' && (
        <div style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          background: 'rgba(10, 15, 26, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--purple)',
          borderRadius: '6px',
          padding: '6px 12px',
          color: '#c084fc',
          fontSize: '0.72rem',
          fontWeight: 800,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          zIndex: 15,
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
        }}>
          <RotateCw size={13} className="spin" />
          <span>3D CESIUM TERRAIN VIEW ACTIVE</span>
        </div>
      )}
    </div>
  );
}
