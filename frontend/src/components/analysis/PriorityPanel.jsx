import React, { useState, useEffect } from 'react';
import { ListOrdered, Clock } from 'lucide-react';
import { fetchPriorities } from '../../services/api';
import LoadingState from '../common/LoadingState';
import StatusBadge from '../common/StatusBadge';

export default function PriorityPanel({ onSelectZone }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPriorities() {
      setLoading(true);
      const res = await fetchPriorities();
      setData(res.data);
      setLoading(false);
    }
    loadPriorities();
  }, []);

  if (loading) return <LoadingState message="Ranking emergency intervention priorities..." />;

  const priorities = data?.priorities || [
    { rank: 1, zone_id: "Z03", priority_level: "CRITICAL", score: 96.5, target_location: "Station Road Sump N21", recommended_action: "Deploy High-Capacity Debris Pump & Clear Conduit E21", urgency_window_minutes: 15 },
    { rank: 2, zone_id: "Z01", priority_level: "CRITICAL", score: 88.2, target_location: "Central Commercial N21/N14", recommended_action: "Clear Drain Blockage at N21 Junction", urgency_window_minutes: 25 },
    { rank: 3, zone_id: "Z02", priority_level: "HIGH", score: 78.4, target_location: "North Market Culvert N14", recommended_action: "Inspect Culvert Intake & Issue Traffic Diversion", urgency_window_minutes: 40 },
    { rank: 4, zone_id: "Z05", priority_level: "HIGH", score: 72.0, target_location: "Hospital Access Corridor", recommended_action: "Deploy Flood Barriers to Protect Emergency Entrance", urgency_window_minutes: 30 }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="priority-header-tag">
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 800, color: 'var(--cyan-bright)' }}>
          <ListOrdered size={16} /> FIELD INTERVENTION DECISION BOARD
        </span>
        <StatusBadge status="RANKED BY URGENCY" />
      </div>

      <div className="priority-cards-stack">
        {priorities.map((item) => {
          const isCritical = item.priority_level === 'CRITICAL';
          return (
            <div
              key={item.rank}
              className={`priority-card ${isCritical ? 'rank-critical' : 'rank-high'}`}
              style={{ cursor: 'pointer' }}
              onClick={() => onSelectZone && onSelectZone(item.zone_id)}
            >
              <div className="priority-rank-badge">#{item.rank}</div>
              <div className="priority-card-main">
                <div className="priority-top-row">
                  <div className="priority-title-group">
                    <span className="priority-target">Zone {item.zone_id}: {item.target_location}</span>
                  </div>
                  <div className="priority-window" style={{ color: isCritical ? 'var(--crimson-bright)' : 'var(--amber-bright)' }}>
                    <Clock size={12} /> {item.urgency_window_minutes}m window
                  </div>
                </div>

                <div className="priority-issue">
                  Urgency Score: <strong>{item.score} / 100</strong>
                </div>

                <div className="priority-action-box">
                  <span className="action-lbl">RECOMMENDED:</span>
                  <span className="action-text">{item.recommended_action}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
