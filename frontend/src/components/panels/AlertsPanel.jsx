import React from 'react';
import { X, ListOrdered } from 'lucide-react';
import PriorityPanel from '../analysis/PriorityPanel';

export default function AlertsPanel({ onClose }) {
  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <ListOrdered size={18} />
            <h3 className="workspace-title">EMERGENCY ACTION & PRIORITY CONSOLE</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          <PriorityPanel />
        </div>
      </div>
    </div>
  );
}
