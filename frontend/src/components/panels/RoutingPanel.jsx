import React from 'react';
import { X, Route } from 'lucide-react';
import SafeRoutePanel from '../routing/SafeRoutePanel';

export default function RoutingPanel({ onClose }) {
  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <Route size={18} />
            <h3 className="workspace-title">FLOOD-AWARE SAFE ROUTING CONSOLE</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          <SafeRoutePanel />
        </div>
      </div>
    </div>
  );
}
