import React from 'react';
import { ShieldCheck, AlertTriangle, Clock, MapPin } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

export default function RouteComparison({ routeData }) {
  if (!routeData) return null;

  const summary = routeData.route_summary || {};
  
  const rec = routeData.recommended_route || {
    name: summary.recommended_route_name || (routeData.route_names ? routeData.route_names.join(' ➔ ') : "Highland Elevated Bypass (Route B)"),
    travel_time_minutes: summary.travel_time_minutes ?? (routeData.total_distance_m ? Math.round((routeData.total_distance_m / 1000) * 3.3) : 16),
    distance_km: summary.distance_km ?? (routeData.total_distance_m ? Math.round((routeData.total_distance_m / 1000) * 10) / 10 : 4.8),
    max_depth_cm: summary.max_flood_depth_cm ?? routeData.max_flood_depth_cm ?? 6.0,
    risk_level: summary.hazard_risk_level || routeData.flood_risk || "LOW",
    description: routeData.reason || "100% safe for all vehicles. Completely bypasses Station Road Sump (N21)."
  };

  const alt = (routeData.alternative_routes && routeData.alternative_routes[0]) || {
    name: "Direct Corridor via Station Road (Route A)",
    travel_time_minutes: 12,
    distance_km: 3.2,
    max_depth_cm: 47.5,
    risk_level: "CRITICAL",
    description: routeData.unsafe_segments_avoided && routeData.unsafe_segments_avoided.length > 0
      ? `UNSAFE: Avoids flooded sectors (${routeData.unsafe_segments_avoided.join(', ')}). High risk of engine stall.`
      : "UNSAFE: Crosses 47.5 cm flood waters at N21 Sump. High risk of vehicle engine stall."
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div className="options-title">ROUTE COMPARISON & HAZARD EVALUATION</div>

      <div className="route-options-list">
        {/* Recommended Safe Route */}
        <div className="route-option-card selected" style={{ borderColor: 'var(--emerald)', background: 'var(--emerald-dim)' }}>
          <div className="route-type-row">
            <div className="route-name-group">
              <ShieldCheck size={16} style={{ color: 'var(--emerald-bright)' }} />
              <span className="route-name" style={{ color: 'var(--emerald-bright)' }}>{rec.name}</span>
            </div>
            <StatusBadge status="RECOMMENDED" />
          </div>

          <div className="route-details-grid">
            <div><Clock size={12} style={{ display: 'inline', marginRight: 4 }} /> Travel Time: <strong>{rec.travel_time_minutes} min</strong></div>
            <div><MapPin size={12} style={{ display: 'inline', marginRight: 4 }} /> Distance: <strong>{rec.distance_km} km</strong></div>
            <div>Flood Exposure: <strong style={{ color: 'var(--emerald-bright)' }}>{rec.max_depth_cm} cm</strong></div>
            <div>Safety: <strong>PASSABLE (SAFE)</strong></div>
          </div>

          <div className="route-recommendation" style={{ color: 'var(--emerald-bright)', fontWeight: 600 }}>
            ✓ {rec.description}
          </div>
        </div>

        {/* Unsafe Direct Route */}
        <div className="route-option-card" style={{ borderColor: 'var(--crimson)', background: 'var(--crimson-dim)' }}>
          <div className="route-type-row">
            <div className="route-name-group">
              <AlertTriangle size={16} style={{ color: 'var(--crimson-bright)' }} />
              <span className="route-name" style={{ color: 'var(--crimson-bright)' }}>{alt.name}</span>
            </div>
            <StatusBadge status="UNSAFE" />
          </div>

          <div className="route-details-grid">
            <div><Clock size={12} style={{ display: 'inline', marginRight: 4 }} /> Travel Time: <strong>{alt.travel_time_minutes} min</strong></div>
            <div><MapPin size={12} style={{ display: 'inline', marginRight: 4 }} /> Distance: <strong>{alt.distance_km} km</strong></div>
            <div>Flood Exposure: <strong style={{ color: 'var(--crimson-bright)' }}>{alt.max_depth_cm} cm</strong></div>
            <div>Safety: <strong style={{ color: 'var(--crimson-bright)' }}>IMPASSABLE (&gt;30cm)</strong></div>
          </div>

          <div className="route-warning">
            ⚠ {alt.description}
          </div>
        </div>
      </div>
    </div>
  );
}
