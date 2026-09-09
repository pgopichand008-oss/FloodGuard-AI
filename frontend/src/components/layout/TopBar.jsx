import React from 'react';
import { Waves, RefreshCw, FileText } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function TopBar({ floodState, onRefresh, onOpenSitRep }) {
  const isLive = floodState?.isLive;
  const syncTime = floodState?.lastSyncTimestamp || new Date().toLocaleTimeString();

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <div className="brand-icon">
          <Waves size={18} />
        </div>
        <div className="brand-text-group">
          <span className="brand-name">FloodGuard AI</span>
          <span className="brand-subtitle">Urban Flood Intelligence & Safe Routing</span>
        </div>
      </div>

      <div className="top-bar-right">
        <div className="top-stat-item">
          <span className="stat-lbl">System:</span>
          <span className="system-dot pulse-emerald"></span>
          <span className="system-txt">OPERATIONAL</span>
        </div>

        <div className="top-stat-item">
          <span className="stat-lbl">Hazard:</span>
          <StatusBadge status={floodState?.data?.summary?.overall_hazard_level || 'HIGH'} />
        </div>

        <div className="top-clock">
          <span className="clock-local">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
          <span className="clock-sep">|</span>
          <span>UTC</span>
        </div>

        <div className="top-sync">
          <span className={`sync-beacon ${isLive ? 'live' : 'fallback'}`}></span>
          <span className="sync-val">{isLive ? `Live Backend (${syncTime})` : `Demo Simulation (${syncTime})`}</span>
        </div>

        <button className="top-icon-btn" onClick={onRefresh} title="Refresh API Telemetry">
          <RefreshCw size={14} className={floodState?.loading ? 'spin' : ''} />
        </button>

        <button className="sitrep-btn" onClick={onOpenSitRep}>
          <FileText size={13} />
          <span>SITREP</span>
        </button>
      </div>
    </header>
  );
}
