import React, { useState, useEffect } from 'react';
import { X, Network, AlertTriangle } from 'lucide-react';
import { fetchDrainageData } from '../../services/api';
import LoadingState from '../common/LoadingState';
import StatusBadge from '../common/StatusBadge';

export default function DrainagePanel({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDrainage() {
      setLoading(true);
      const res = await fetchDrainageData();
      setData(res.data);
      setLoading(false);
    }
    loadDrainage();
  }, []);

  const nodes = data?.nodes || [
    { node_id: "N21", name: "Station Junction Sump", capacity_m3_s: 15.0, current_flow_m3_s: 18.4, status: "SURCHARGED", utilization_pct: 122.6 },
    { node_id: "N14", name: "North Market Culvert", capacity_m3_s: 12.0, current_flow_m3_s: 13.5, status: "CRITICAL", utilization_pct: 112.5 },
    { node_id: "N01", name: "Hospital Outfall Sump", capacity_m3_s: 25.0, current_flow_m3_s: 8.0, status: "NORMAL", utilization_pct: 32.0 }
  ];

  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <Network size={18} />
            <h3 className="workspace-title">URBAN DRAINAGE NETWORK HYDRAULIC CONSOLE</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          {loading ? (
            <LoadingState message="Evaluating conduit capacity and pipe surcharge..." />
          ) : (
            <>
              <div className="bottleneck-highlight-banner">
                <AlertTriangle size={20} style={{ color: 'var(--crimson-bright)', flexShrink: 0 }} />
                <div>
                  <div className="banner-title">BOTTLENECK DETECTED: SUMP NODE N21 OVER CAPACITY</div>
                  <div className="banner-text">
                    Node N21 flow rate (18.4 m³/s) exceeds maximum hydraulic conduit capacity (15.0 m³/s). 35% debris blockage identified in Trunk Drain E21.
                  </div>
                </div>
              </div>

              <div className="network-graph-container">
                <div className="graph-header">DRAINAGE NODE CAPACITY UTILIZATION ({nodes.length} NODES)</div>
                <div className="drainage-nodes-grid">
                  {nodes.map(node => {
                    const isOver = node.utilization_pct > 100;
                    return (
                      <div key={node.node_id} className={`node-analysis-card ${isOver ? 'critical' : ''}`}>
                        <div className="node-card-header">
                          <span className="node-id">Node {node.node_id}</span>
                          <StatusBadge status={node.status} />
                        </div>
                        <div className="node-name">{node.name}</div>
                        <div className="node-capacity-row">
                          <span>Flow: {node.current_flow_m3_s} / {node.capacity_m3_s} m³/s</span>
                          <strong>{node.utilization_pct}%</strong>
                        </div>
                        <div className="cap-progress-track">
                          <div
                            className={`cap-fill ${isOver ? 'bg-danger' : node.utilization_pct > 80 ? 'bg-amber' : 'bg-emerald'}`}
                            style={{ width: `${Math.min(100, node.utilization_pct)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
