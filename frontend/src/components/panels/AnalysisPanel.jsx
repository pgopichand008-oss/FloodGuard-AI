import React, { useState } from 'react';
import { X, HelpCircle, GitCommit, ListOrdered } from 'lucide-react';
import WhyFloodPanel from '../analysis/WhyFloodPanel';
import PropagationPanel from '../analysis/PropagationPanel';
import PriorityPanel from '../analysis/PriorityPanel';

export default function AnalysisPanel({ onClose, selectedZoneId = 'Z03' }) {
  const [activeTab, setActiveTab] = useState('why'); // 'why', 'propagation', 'priority'

  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <HelpCircle size={18} />
            <h3 className="workspace-title">INTELLIGENCE & EXPLAINABILITY CONSOLE</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Tab Strip */}
        <div className="analysis-tab-strip">
          <button
            className={`tab-btn ${activeTab === 'why' ? 'active' : ''}`}
            onClick={() => setActiveTab('why')}
          >
            <HelpCircle size={13} style={{ display: 'inline', marginRight: 4 }} /> WHY-FLOOD DIAGNOSTIC
          </button>
          <button
            className={`tab-btn ${activeTab === 'propagation' ? 'active' : ''}`}
            onClick={() => setActiveTab('propagation')}
          >
            <GitCommit size={13} style={{ display: 'inline', marginRight: 4 }} /> CORRIDOR PROPAGATION
          </button>
          <button
            className={`tab-btn ${activeTab === 'priority' ? 'active' : ''}`}
            onClick={() => setActiveTab('priority')}
          >
            <ListOrdered size={13} style={{ display: 'inline', marginRight: 4 }} /> ACTION PRIORITIES
          </button>
        </div>

        <div className="workspace-body">
          {activeTab === 'why' && <WhyFloodPanel selectedZoneId={selectedZoneId} />}
          {activeTab === 'propagation' && <PropagationPanel selectedZoneId={selectedZoneId} />}
          {activeTab === 'priority' && <PriorityPanel />}
        </div>
      </div>
    </div>
  );
}
