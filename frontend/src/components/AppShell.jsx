import React, { useState, useEffect } from 'react';
import TopBar from './layout/TopBar';
import LeftToolRail from './layout/LeftToolRail';
import RightInspector from './layout/RightInspector';
import BottomTimeline from './layout/BottomTimeline';
import DiagnosticDock from './layout/DiagnosticDock';
import KPIBar from './dashboard/KPIBar';
import MapFrame from './map/MapFrame';

import ForecastPanel from './panels/ForecastPanel';
import DrainagePanel from './panels/DrainagePanel';
import AnalysisPanel from './panels/AnalysisPanel';
import RoutingPanel from './panels/RoutingPanel';
import WhatIfPanel from './panels/WhatIfPanel';
import AlertsPanel from './panels/AlertsPanel';
import PropagationPanel from './analysis/PropagationPanel';
import { Radio, X } from 'lucide-react';

export default function AppShell({
  floodState,
  rainfallData,
  terrainData,
  runoffData,
  drainageData,
  mlStatusData,
  mlPredictData,
  explanationsData,
  onRefresh,
  activeWorkspace,
  setActiveWorkspace,
  selectedObject,
  setSelectedObject,
  selectedTimeIndex,
  setSelectedTimeIndex,
  layers,
  onToggleLayer
}) {
  const data = floodState?.data || {};
  const summary = data.summary || {
    overall_hazard_level: "HIGH",
    total_evaluated_zones: 8,
    affected_zones_count: 5,
    critical_zones_count: 2,
    max_flood_depth_cm: 47.5,
    average_flood_depth_cm: 22.8
  };

  const [leftWidth, setLeftWidth] = useState(176);
  const [rightWidth, setRightWidth] = useState(328);
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);

  const startResizeLeft = (e) => {
    e.preventDefault();
    setIsResizingLeft(true);
  };

  const startResizeRight = (e) => {
    e.preventDefault();
    setIsResizingRight(true);
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isResizingLeft) {
        const newWidth = Math.min(Math.max(e.clientX, 140), 280);
        setLeftWidth(newWidth);
        window.dispatchEvent(new Event('resize'));
      } else if (isResizingRight) {
        const newWidth = Math.min(Math.max(window.innerWidth - e.clientX, 260), 480);
        setRightWidth(newWidth);
        window.dispatchEvent(new Event('resize'));
      }
    };

    const handleMouseUp = () => {
      if (isResizingLeft || isResizingRight) {
        setIsResizingLeft(false);
        setIsResizingRight(false);
        window.dispatchEvent(new Event('resize'));
      }
    };

    if (isResizingLeft || isResizingRight) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeft, isResizingRight]);

  return (
    <div className="app-shell-container">
      {/* Top Bar Header */}
      <TopBar
        floodState={floodState}
        onRefresh={onRefresh}
        activeWorkspace={activeWorkspace}
        onNavClick={(ws) => setActiveWorkspace(activeWorkspace === ws ? null : ws)}
        onOpenSitRep={() => setActiveWorkspace('analysis')}
      />

      {/* Resilience Warning Notice when API is offline */}
      {floodState?.error && (
        <div className="resilience-notice-bar">
          <span>⚠️ {floodState.error} — Displaying Resilient Local Simulation Data</span>
        </div>
      )}

      {/* Center Viewport Grid */}
      <main className="center-viewport-grid">
        {/* Left Tool Navigation Rail */}
        <div style={{ width: `${leftWidth}px`, height: '100%', flexShrink: 0, display: 'flex' }}>
          <LeftToolRail
            activeWorkspace={activeWorkspace}
            setActiveWorkspace={setActiveWorkspace}
          />
        </div>

        {/* Drag Handle Left */}
        <div
          className={`panel-resize-handle ${isResizingLeft ? 'active' : ''}`}
          onMouseDown={startResizeLeft}
          title="Drag to resize Left Tool Panel width"
        />

        {/* Main Central GIS Workspace */}
        <section className="gis-main-container">
          {/* Top KPI Telemetry Bar */}
          <KPIBar
            summary={summary}
            rainfall={rainfallData}
            drainageData={drainageData}
            mlPredictData={mlPredictData}
            mlStatus={mlStatusData}
            isLive={floodState?.isLive}
            loading={floodState?.loading}
            error={floodState?.error}
            onCardClick={(workspace) => setActiveWorkspace(workspace)}
          />

          {/* Central Map Frame Container */}
          <MapFrame
            zones={data.zones}
            terrainData={terrainData}
            runoffData={runoffData}
            drainageData={drainageData}
            mlPredictData={mlPredictData}
            layers={layers}
            onToggleLayer={onToggleLayer}
            selectedObject={selectedObject}
            onSelectObject={setSelectedObject}
            activeWorkspace={activeWorkspace}
            setActiveWorkspace={setActiveWorkspace}
          />
        </section>

        {/* Drag Handle Right */}
        {selectedObject && (
          <div
            className={`panel-resize-handle ${isResizingRight ? 'active' : ''}`}
            onMouseDown={startResizeRight}
            title="Drag to resize Right Inspector Panel width"
          />
        )}

        {/* Right Contextual Object Inspector Drawer */}
        {selectedObject && (
          <div style={{ width: `${rightWidth}px`, height: '100%', flexShrink: 0, display: 'flex' }}>
            <RightInspector
              selectedObject={selectedObject}
              onClose={() => setSelectedObject(null)}
              onActionClick={(workspace) => setActiveWorkspace(workspace)}
            />
          </div>
        )}
      </main>

      {/* Workspace Overlay Modals */}
      {activeWorkspace === 'forecast' && (
        <ForecastPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'drainage' && (
        <DrainagePanel drainageData={drainageData} onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'analysis' && (
        <AnalysisPanel
          selectedZoneId={selectedObject?.id || 'Z03'}
          onClose={() => setActiveWorkspace(null)}
        />
      )}

      {activeWorkspace === 'routing' && (
        <RoutingPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'whatif' && (
        <WhatIfPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'alerts' && (
        <AlertsPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'feed' && (
        <AlertsPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'propagation' && (
        <div className="workspace-overlay-backdrop" onClick={() => setActiveWorkspace(null)}>
          <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
            <div className="workspace-header">
              <div className="title-group">
                <Radio size={18} />
                <h3 className="workspace-title">FLOOD PROPAGATION & CORRIDOR CASCADE</h3>
              </div>
              <button className="workspace-close-btn" onClick={() => setActiveWorkspace(null)}><X size={18} /></button>
            </div>
            <div className="workspace-body">
              <PropagationPanel selectedZoneId={selectedObject?.id || 'Z03'} />
            </div>
          </div>
        </div>
      )}

      {/* Bottom Temporal Timeline Strip */}
      <BottomTimeline
        selectedTimeIndex={selectedTimeIndex}
        setSelectedTimeIndex={setSelectedTimeIndex}
      />

      {/* Collapsible System Diagnostic & Telemetry Dock */}
      <DiagnosticDock floodState={floodState} />
    </div>
  );
}
