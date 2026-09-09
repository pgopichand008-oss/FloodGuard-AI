import React from 'react';
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

export default function AppShell({
  floodState,
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

  return (
    <div className="app-shell-container">
      {/* Top Bar Header */}
      <TopBar
        floodState={floodState}
        onRefresh={onRefresh}
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
        <LeftToolRail
          activeWorkspace={activeWorkspace}
          setActiveWorkspace={setActiveWorkspace}
        />

        {/* Main Central GIS Workspace */}
        <section className="gis-main-container">
          {/* Top KPI Telemetry Bar */}
          <KPIBar
            summary={summary}
            rainfall={{ current_intensity_mm_hr: 86.4, peak_24h_mm_hr: 102.0, trend: 'increasing' }}
            isLive={floodState?.isLive}
            onCardClick={(workspace) => setActiveWorkspace(workspace)}
          />

          {/* Central Map Frame Container */}
          <MapFrame
            zones={data.zones}
            layers={layers}
            onToggleLayer={onToggleLayer}
            selectedObject={selectedObject}
            onSelectObject={setSelectedObject}
            activeWorkspace={activeWorkspace}
            setActiveWorkspace={setActiveWorkspace}
          />
        </section>

        {/* Right Contextual Object Inspector Drawer */}
        {selectedObject && (
          <RightInspector
            selectedObject={selectedObject}
            onClose={() => setSelectedObject(null)}
            onActionClick={(workspace) => setActiveWorkspace(workspace)}
          />
        )}
      </main>

      {/* Workspace Overlay Modals */}
      {activeWorkspace === 'forecast' && (
        <ForecastPanel onClose={() => setActiveWorkspace(null)} />
      )}

      {activeWorkspace === 'drainage' && (
        <DrainagePanel onClose={() => setActiveWorkspace(null)} />
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
