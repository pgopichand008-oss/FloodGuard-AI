import React, { useState } from 'react';
import { Route, Navigation, ShieldCheck } from 'lucide-react';
import { computeRoute } from '../../services/api';
import RouteComparison from './RouteComparison';
import LoadingState from '../common/LoadingState';

export default function SafeRoutePanel() {
  const [origin, setOrigin] = useState('Z03');
  const [destination, setDestination] = useState('Z05');
  const [emergency, setEmergency] = useState(false);
  const [routeResult, setRouteResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleComputeRoute = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    const res = await computeRoute({ origin, destination, emergency });
    if (res.data) {
      setRouteResult(res.data);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    handleComputeRoute();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div className="forecast-banner" style={{ background: 'var(--emerald-dim)', borderColor: 'var(--emerald)' }}>
        <ShieldCheck size={16} style={{ color: 'var(--emerald-bright)', flexShrink: 0 }} />
        <div>
          <div style={{ fontWeight: 800, color: 'var(--emerald-bright)' }}>FLOOD-AWARE SAFE ROUTING ENGINE</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem' }}>
            Computes safest practical route avoiding impassable flooded corridors (&gt;30 cm depth).
          </div>
        </div>
      </div>

      {/* Routing Form */}
      <form onSubmit={handleComputeRoute} className="routing-form-grid">
        <div className="form-group">
          <label className="form-lbl">ORIGIN ZONE / NODE</label>
          <div className="route-input-wrap">
            <Navigation className="input-icon" size={14} />
            <select
              className="route-input"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
            >
              <option value="Z03">Z03 — Station Road (Flooded Sump)</option>
              <option value="Z01">Z01 — Central Commercial District</option>
              <option value="Z02">Z02 — North Market Area</option>
              <option value="N21">Node N21 — Sump Junction</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label className="form-lbl">DESTINATION TARGET</label>
          <div className="route-input-wrap">
            <Route className="input-icon" size={14} />
            <select
              className="route-input"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            >
              <option value="Z05">Z05 — City General Hospital</option>
              <option value="Z08">Z08 — Highland Relief Center</option>
              <option value="Z04">Z04 — South Suburban Lowland</option>
            </select>
          </div>
        </div>

        <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label className="checkbox-item" style={{ margin: 0 }}>
            <input
              type="checkbox"
              checked={emergency}
              onChange={(e) => setEmergency(e.target.checked)}
            />
            <span>Enable Emergency Vehicle Priority Dispatch</span>
          </label>

          <button className="inspector-btn" type="submit" style={{ width: 'auto', padding: '6px 16px' }}>
            Compute Safe Route
          </button>
        </div>
      </form>

      {loading && <LoadingState message="Calculating flood-safe route options..." />}

      {routeResult && !loading && (
        <RouteComparison routeData={routeResult} />
      )}
    </div>
  );
}
