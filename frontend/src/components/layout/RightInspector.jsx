import React from 'react';
import { X, AlertTriangle, MapPin, HelpCircle } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function RightInspector({ selectedObject, onClose, onActionClick }) {
  if (!selectedObject) return null;

  const { type, id, name, details } = selectedObject;

  return (
    <aside className="context-inspector-drawer">
      <div className="inspector-header">
        <div className="header-type-wrap">
          <MapPin size={14} style={{ color: 'var(--cyan-bright)' }} />
          <span className="type-label">{type || 'GIS OBJECT'} INSPECTOR</span>
        </div>
        <button className="inspector-close-btn" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      <div className="inspector-body">
        <div className="inspector-content">
          <div className="object-title-block">
            <div className="object-main-id">{name || id || 'Selected Feature'}</div>
            <div className="object-subtitle">ID: {id || 'Z03'} | Urban Catchment Sector</div>
          </div>

          <div className="metrics-box-grid">
            <div className="metric-box">
              <span className="box-lbl">Current Depth</span>
              <span className="box-val">{details?.flood_depth_cm || 42.5} <span style={{ fontSize: '0.65rem' }}>cm</span></span>
              <span className="box-sub">Onset: +{details?.onset_minutes || 35} min</span>
            </div>
            <div className="metric-box">
              <span className="box-lbl">Peak Depth</span>
              <span className="box-val">{details?.peak_depth_cm || 53.0} <span style={{ fontSize: '0.65rem' }}>cm</span></span>
              <span className="box-sub">In 90 minutes</span>
            </div>
          </div>

          <div className="dual-status-card">
            <div className="status-subcard">
              <span className="card-lbl">Hazard Risk Level</span>
              <div style={{ marginTop: 4 }}>
                <StatusBadge status={details?.risk_level || 'HIGH'} />
              </div>
            </div>
            <div className="status-subcard">
              <span className="card-lbl">Passability Status</span>
              <span className="card-val" style={{ color: (details?.flood_depth_cm || 42) > 30 ? 'var(--crimson-bright)' : 'var(--emerald-bright)' }}>
                {(details?.flood_depth_cm || 42) > 30 ? 'IMPASSABLE FOR LIGHT VEHICLES' : 'PASSABLE WITH CAUTION'}
              </span>
              <span className="passability-note">Critical threshold is 30 cm</span>
            </div>
          </div>

          <div className="bottleneck-alert-card">
            <div className="alert-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={14} /> Bottleneck Identified: {details?.bottleneck_node || 'N21 Sump'}
            </div>
            <div className="alert-text">
              Conduit utilization exceeds 118%. Drainage surcharge causing secondary street spillover.
            </div>
          </div>

          <div className="causal-factors-card">
            <div className="factors-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <HelpCircle size={14} style={{ color: 'var(--cyan-bright)' }} /> Primary Contributing Causes
            </div>
            <ul className="factors-list">
              <li>• Heavy rainfall rate (86.4 mm/hr)</li>
              <li>• Topographic low elevation (4.2 m)</li>
              <li>• Conduit blockage at Node N21 (35%)</li>
              <li>• High impervious ground cover (82%)</li>
            </ul>
          </div>

          <div className="response-actions-card">
            <div className="actions-header">
              <span>RECOMMENDED FIELD ACTIONS</span>
              <span className="no-dispatch-tag">ACTION REQUIRED</span>
            </div>
            <div className="checkbox-stack">
              <label className="checkbox-item checked">
                <input type="checkbox" defaultChecked readOnly />
                <span>Deploy Debris Pump at Node N21</span>
              </label>
              <label className="checkbox-item">
                <input type="checkbox" />
                <span>Reroute Traffic via Highland Bypass</span>
              </label>
              <label className="checkbox-item">
                <input type="checkbox" />
                <span>Issue Public Emergency Siren Alert</span>
              </label>
            </div>
            <div className="action-buttons-row">
              <button className="inspector-btn" onClick={() => onActionClick && onActionClick('routing')}>
                Compute Safe Bypass Route
              </button>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
