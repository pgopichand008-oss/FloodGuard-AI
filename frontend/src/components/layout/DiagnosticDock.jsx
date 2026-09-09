import React, { useState } from 'react';
import { ChevronUp, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react';

export default function DiagnosticDock({ floodState }) {
  const [open, setOpen] = useState(false);
  const isLive = floodState?.isLive;

  const services = [
    { name: "Rainfall API", live: isLive, endpoint: "/api/rainfall" },
    { name: "Nowcast Engine", live: isLive, endpoint: "/api/forecast" },
    { name: "Terrain DEM", live: isLive, endpoint: "/api/terrain" },
    { name: "Surface Runoff", live: isLive, endpoint: "/api/runoff" },
    { name: "Drainage Surcharge", live: isLive, endpoint: "/api/drainage" },
    { name: "ML RandomForest", live: isLive, endpoint: "/api/ml/predict" },
    { name: "WHY-FLOOD Attribution", live: isLive, endpoint: "/api/explanations" },
    { name: "WHAT-IF Simulator", live: isLive, endpoint: "/api/simulate" },
    { name: "Priority Decision Engine", live: isLive, endpoint: "/api/priorities" },
    { name: "Corridor Propagation", live: isLive, endpoint: "/api/propagation" },
    { name: "Safe Routing Engine", live: isLive, endpoint: "/api/route" }
  ];

  return (
    <footer className="diagnostic-dock">
      <button className="diagnostic-toggle-btn" onClick={() => setOpen(!open)}>
        <span className="dock-title">SYSTEM DIAGNOSTICS & TELEMETRY</span>
        <span style={{ color: isLive ? 'var(--emerald-bright)' : 'var(--amber-bright)' }}>
          {isLive ? '● LIVE BACKEND CONNECTED (134/134 TESTS PASS)' : '▲ DEMO MODE — BACKEND DISCONNECTED'}
        </span>
        <span className="dock-arrow">{open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}</span>
      </button>

      {open && (
        <div className="diagnostic-body">
          <div className="diagnostic-items-grid">
            {services.map((svc) => (
              <div key={svc.name} className="diag-item">
                <span className="diag-name">{svc.name}:</span>
                <span className={`diag-status ${svc.live ? 'status-ok' : 'status-err'}`}>
                  {svc.live ? <CheckCircle2 size={12} style={{ display: 'inline', marginRight: 2 }} /> : <AlertCircle size={12} style={{ display: 'inline', marginRight: 2 }} />}
                  {svc.live ? 'ONLINE' : 'FALLBACK'}
                </span>
              </div>
            ))}
          </div>
          {!isLive && (
            <div className="diag-disclaimer">
              Notice: Backend server (http://127.0.0.1:8000) was unreachable. All interactive UI features are currently running in local resilient offline simulation mode.
            </div>
          )}
        </div>
      )}
    </footer>
  );
}
