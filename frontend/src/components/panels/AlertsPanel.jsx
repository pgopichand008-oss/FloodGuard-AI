import React from 'react';
import { X, Bell } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function AlertsPanel({ onClose }) {
  const alerts = [
    { id: 1, title: "FLASH FLOOD WARNING: Station Road (Z03)", time: "10 min ago", level: "CRITICAL", desc: "Flood depth 47.5 cm exceeds vehicle passability threshold (30cm). Node N21 sump surcharged by 22%." },
    { id: 2, title: "DRAINAGE SURCHARGE: Node N14 Culvert", time: "25 min ago", level: "HIGH", desc: "North Market Culvert intake utilization reaches 112%. Secondary spillover threatening commercial zone." },
    { id: 3, title: "EMERGENCY ROUTE CLEARANCE: Hospital Approach", time: "45 min ago", level: "NOMINAL", desc: "Route B (Highland Bypass) verified 100% safe (6 cm depth). Access to City General Hospital maintained." }
  ];

  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <Bell size={18} />
            <h3 className="workspace-title">EMERGENCY INCIDENT & ALERT FEED</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {alerts.map(a => (
              <div key={a.id} className="priority-card" style={{ borderLeftColor: a.level === 'CRITICAL' ? 'var(--crimson)' : a.level === 'HIGH' ? 'var(--amber)' : 'var(--emerald)' }}>
                <div className="priority-card-main">
                  <div className="priority-top-row">
                    <span className="priority-target">{a.title}</span>
                    <StatusBadge status={a.level} />
                  </div>
                  <div className="priority-issue" style={{ marginTop: 4 }}>
                    {a.desc}
                  </div>
                  <div className="priority-window" style={{ color: 'var(--text-subtle)', marginTop: 4 }}>
                    Issued: {a.time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
