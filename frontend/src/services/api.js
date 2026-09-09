/**
 * Centralized API Service for FloodGuard AI
 * Connects React frontend to FastAPI backend (Default: http://127.0.0.1:8000/api)
 * Implements resilient offline fallbacks clearly marked as DEMO / OFFLINE SIMULATION.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';
const TIMEOUT_MS = 5000;

// Helper function to execute fetch with timeout
async function fetchWithTimeout(endpoint, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return { data, isLive: true, error: null };
  } catch (err) {
    clearTimeout(timeoutId);
    return { data: null, isLive: false, error: err.message || 'API request failed' };
  }
}

/* ==========================================================================
   FALLBACK / DEMO DATASETS (Used when backend is offline)
   ========================================================================== */

export const FALLBACK_FLOOD_DATA = {
  summary: {
    overall_hazard_level: "HIGH",
    total_evaluated_zones: 8,
    affected_zones_count: 5,
    critical_zones_count: 2,
    max_flood_depth_cm: 47.5,
    average_flood_depth_cm: 22.8,
    total_population_affected: 34200,
    timestamp: new Date().toISOString()
  },
  zones: [
    { zone_id: "Z01", zone_name: "Central Commercial District", risk_level: "HIGH", flood_depth_cm: 42.5, onset_minutes: 35, peak_depth_cm: 53.0, runoff_m3_s: 18.4, drainage_utilization_pct: 118, bottleneck_node: "N21", primary_cause: "High Runoff + Conduit Blockage" },
    { zone_id: "Z02", zone_name: "North Market Area", risk_level: "HIGH", flood_depth_cm: 38.0, onset_minutes: 40, peak_depth_cm: 45.0, runoff_m3_s: 15.2, drainage_utilization_pct: 105, bottleneck_node: "N14", primary_cause: "Drainage Utilization Overflow" },
    { zone_id: "Z03", zone_name: "Station Road Corridor", risk_level: "SEVERE", flood_depth_cm: 47.5, onset_minutes: 25, peak_depth_cm: 58.0, runoff_m3_s: 22.1, drainage_utilization_pct: 135, bottleneck_node: "N21", primary_cause: "Surcharge Sump Overflow" },
    { zone_id: "Z04", zone_name: "South Suburban Lowland", risk_level: "MODERATE", flood_depth_cm: 21.0, onset_minutes: 60, peak_depth_cm: 28.0, runoff_m3_s: 9.8, drainage_utilization_pct: 82, bottleneck_node: "N08", primary_cause: "Terrain Flow Accumulation" },
    { zone_id: "Z05", zone_name: "Hospital Relief Zone", risk_level: "LOW", flood_depth_cm: 6.0, onset_minutes: 120, peak_depth_cm: 10.0, runoff_m3_s: 4.2, drainage_utilization_pct: 45, bottleneck_node: "N01", primary_cause: "High Terrain Elevation" },
    { zone_id: "Z06", zone_name: "West Industrial Park", risk_level: "MODERATE", flood_depth_cm: 18.5, onset_minutes: 75, peak_depth_cm: 24.0, runoff_m3_s: 11.0, drainage_utilization_pct: 78, bottleneck_node: "N11", primary_cause: "High Impervious Surface" },
    { zone_id: "Z07", zone_name: "East Riverfront Canal", risk_level: "HIGH", flood_depth_cm: 34.0, onset_minutes: 45, peak_depth_cm: 42.0, runoff_m3_s: 16.8, drainage_utilization_pct: 112, bottleneck_node: "N30", primary_cause: "Downstream Outfall Backwater" },
    { zone_id: "Z08", zone_name: "Highland Residential", risk_level: "LOW", flood_depth_cm: 2.0, onset_minutes: 180, peak_depth_cm: 4.0, runoff_m3_s: 2.1, drainage_utilization_pct: 25, bottleneck_node: "N05", primary_cause: "Steep Slope Natural Discharge" }
  ],
  is_simulated: true
};

export const FALLBACK_RAINFALL = {
  current_intensity_mm_hr: 86.4,
  peak_24h_mm_hr: 102.0,
  trend: "increasing",
  status: "CRITICAL_STORM",
  observation_series: [
    { timestamp: "-60m", intensity_mm_hr: 32.0 },
    { timestamp: "-45m", intensity_mm_hr: 48.5 },
    { timestamp: "-30m", intensity_mm_hr: 65.0 },
    { timestamp: "-15m", intensity_mm_hr: 78.2 },
    { timestamp: "NOW", intensity_mm_hr: 86.4 }
  ],
  is_demo_data: true
};

export const FALLBACK_FORECAST = {
  forecast_horizon_minutes: 180,
  peak_forecast_intensity_mm_hr: 105.0,
  peak_arrival_minutes: 90,
  time_series: [
    { minutes: 0, rainfall_mm_hr: 86.4, depth_cm: 18.0 },
    { minutes: 30, rainfall_mm_hr: 94.0, depth_cm: 27.5 },
    { minutes: 60, rainfall_mm_hr: 101.2, depth_cm: 36.0 },
    { minutes: 90, rainfall_mm_hr: 105.0, depth_cm: 47.5 },
    { minutes: 120, rainfall_mm_hr: 82.0, depth_cm: 43.0 },
    { minutes: 150, rainfall_mm_hr: 54.0, depth_cm: 32.0 },
    { minutes: 180, rainfall_mm_hr: 28.0, depth_cm: 21.0 }
  ],
  is_demo_data: true
};

export const FALLBACK_DRAINAGE = {
  network_summary: {
    total_nodes: 12,
    total_drains: 15,
    critical_conduits: 4,
    surcharged_conduits: 2,
    average_utilization_pct: 88.5
  },
  nodes: [
    { node_id: "N21", name: "Station Junction Sump", elevation_m: 4.2, capacity_m3_s: 15.0, current_flow_m3_s: 18.4, status: "SURCHARGED", utilization_pct: 122.6 },
    { node_id: "N14", name: "North Market Culvert", elevation_m: 6.8, capacity_m3_s: 12.0, current_flow_m3_s: 13.5, status: "CRITICAL", utilization_pct: 112.5 },
    { node_id: "N01", name: "Hospital Relief Outfall", elevation_m: 14.5, capacity_m3_s: 25.0, current_flow_m3_s: 8.0, status: "NORMAL", utilization_pct: 32.0 }
  ],
  drains: [
    { edge_id: "E21", from_node: "N21", to_node: "N14", conduit_type: "BOX_CULVERT", max_capacity_m3_s: 15.0, current_flow_m3_s: 18.4, utilization_pct: 122.6, blockage_pct: 35.0, status: "SURCHARGED" },
    { edge_id: "E14", from_node: "N14", to_node: "N01", conduit_type: "OPEN_CANAL", max_capacity_m3_s: 20.0, current_flow_m3_s: 16.5, utilization_pct: 82.5, blockage_pct: 10.0, status: "WARNING" }
  ]
};

export const FALLBACK_ML_STATUS = {
  is_model_fitted: true,
  model_type: "RandomForestRegressor + Classifier",
  n_estimators: 100,
  training_sample_count: 5000,
  feature_names: ["rainfall_intensity", "elevation", "slope", "imperviousness", "drainage_utilization", "blockage_ratio"],
  metrics: {
    r2_score: 0.942,
    mae_cm: 1.85,
    rmse_cm: 2.41,
    accuracy_risk: 0.965
  }
};

/* ==========================================================================
   API ENDPOINT CALLS
   ========================================================================== */

/** 1. Health Check */
export async function fetchHealth() {
  const result = await fetchWithTimeout('/health');
  if (result.isLive) return result;
  return { data: { status: "offline", message: "Backend offline — running local fallback" }, isLive: false, error: result.error };
}

/** 2. Integrated Flood Hazard Data */
export async function fetchFloodData(zoneId = null, riskLevel = null, rainfallMmHr = null) {
  let queryParams = new URLSearchParams();
  if (zoneId) queryParams.append('zone_id', zoneId);
  if (riskLevel) queryParams.append('risk_level', riskLevel);
  if (rainfallMmHr !== null && rainfallMmHr !== undefined) queryParams.append('rainfall_mm_hr', rainfallMmHr);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/flood${queryString}`);

  if (result.isLive && result.data) {
    return { data: result.data, isLive: true, error: null, lastSyncTimestamp: new Date().toLocaleTimeString() };
  }

  return {
    data: FALLBACK_FLOOD_DATA,
    isLive: false,
    error: 'Backend API Offline — Local Demo Mode Active',
    lastSyncTimestamp: new Date().toLocaleTimeString()
  };
}

/** 3. Current Rainfall */
export async function fetchRainfallData() {
  const result = await fetchWithTimeout('/rainfall');
  if (result.isLive && result.data) {
    return { data: result.data, isLive: true, error: null };
  }
  return { data: FALLBACK_RAINFALL, isLive: false, error: 'Offline Fallback' };
}

/** 4. Rainfall Forecast */
export async function fetchForecastData(horizonMinutes = 180) {
  const result = await fetchWithTimeout(`/forecast?horizon_minutes=${horizonMinutes}`);
  if (result.isLive && result.data) {
    return { data: result.data, isLive: true, error: null };
  }
  return { data: FALLBACK_FORECAST, isLive: false, error: 'Offline Fallback' };
}

/** 5. Terrain Overview */
export async function fetchTerrainData() {
  const result = await fetchWithTimeout('/terrain');
  if (result.isLive && result.data) {
    return { data: result.data, isLive: true, error: null };
  }
  return {
    data: {
      catchment_zones: FALLBACK_FLOOD_DATA.zones,
      total_zones: 8,
      average_elevation_m: 12.4,
      lowest_zone_id: "Z03",
      highest_vulnerability_zone_id: "Z03"
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 6. Surface Runoff */
export async function fetchRunoffData(rainfallMmHr = null, zoneId = null) {
  let queryParams = new URLSearchParams();
  if (rainfallMmHr) queryParams.append('rainfall_mm_hr', rainfallMmHr);
  if (zoneId) queryParams.append('zone_id', zoneId);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/runoff${queryString}`);
  if (result.isLive && result.data) return result;

  return {
    data: {
      total_catchment_runoff_m3_s: 110.1,
      highest_runoff_zone_id: "Z03",
      critical_runoff_zones_count: 3,
      catchment_runoff_records: FALLBACK_FLOOD_DATA.zones
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 7. Drainage Network */
export async function fetchDrainageData(nodeId = null, edgeId = null, statusFilter = null) {
  let queryParams = new URLSearchParams();
  if (nodeId) queryParams.append('node_id', nodeId);
  if (edgeId) queryParams.append('edge_id', edgeId);
  if (statusFilter) queryParams.append('status_filter', statusFilter);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/drainage${queryString}`);
  if (result.isLive && result.data) return result;

  return { data: FALLBACK_DRAINAGE, isLive: false, error: 'Offline Fallback' };
}

/** 8. ML Prediction */
export async function fetchMLPredict(zoneId = null, rainfallMmHr = null) {
  let queryParams = new URLSearchParams();
  if (zoneId) queryParams.append('zone_id', zoneId);
  if (rainfallMmHr) queryParams.append('rainfall_mm_hr', rainfallMmHr);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/ml/predict${queryString}`);
  if (result.isLive && result.data) return result;

  return {
    data: {
      model_type: "RandomForest Ensemble",
      predictions: FALLBACK_FLOOD_DATA.zones.map(z => ({
        zone_id: z.zone_id,
        predicted_depth_cm: z.flood_depth_cm + 1.2,
        hazard_probability: z.risk_level === 'CRITICAL' || z.risk_level === 'HIGH' ? 0.89 : 0.24,
        risk_level: z.risk_level,
        confidence_score: 0.92
      })),
      summary: { average_confidence: 0.92, high_risk_zones_count: 3 }
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 9. ML Operational Status */
export async function fetchMLStatus() {
  const result = await fetchWithTimeout('/ml/status');
  if (result.isLive && result.data) return result;
  return { data: FALLBACK_ML_STATUS, isLive: false, error: 'Offline Fallback' };
}

/** 10. WHY-FLOOD Explanations */
export async function fetchExplanations(zoneId = null, rainfallMmHr = null) {
  let queryParams = new URLSearchParams();
  if (zoneId) queryParams.append('zone_id', zoneId);
  if (rainfallMmHr) queryParams.append('rainfall_mm_hr', rainfallMmHr);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/explanations${queryString}`);
  if (result.isLive && result.data) return result;

  return {
    data: {
      explanations: FALLBACK_FLOOD_DATA.zones.map(z => ({
        zone_id: z.zone_id,
        zone_name: z.zone_name,
        primary_cause: z.primary_cause,
        factors: [
          { factor_name: "Rainfall Intensity", weight: 0.35, description: "Heavy nowcast rate exceeding infiltration capacity" },
          { factor_name: "Elevation Depression", weight: 0.25, description: "Low-lying topographic sump area" },
          { factor_name: "Drainage Surcharge", weight: 0.40, description: `Pipe utilization ${z.drainage_utilization_pct}% around node ${z.bottleneck_node}` }
        ],
        causal_chain: [
          { step: 1, title: "Extreme Rainfall", description: "Cloudburst intensity 86.4 mm/hr", severity: "CRITICAL" },
          { step: 2, title: "Surface Runoff Accumulation", description: `Runoff volume ${z.runoff_m3_s} m³/s`, severity: "HIGH" },
          { step: 3, title: "Hydraulic Conduit Surcharge", description: `Node ${z.bottleneck_node} exceeds capacity`, severity: "CRITICAL" },
          { step: 4, title: "Street Inundation", description: `Inundation depth reaches ${z.flood_depth_cm} cm`, severity: z.risk_level }
        ]
      }))
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 11. WHAT-IF Simulation Execution */
export async function executeSimulation(payload) {
  const result = await fetchWithTimeout('/simulate', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (result.isLive && result.data) return result;

  // Fallback dynamic calculation simulation
  const rainfallMult = (payload.scenario_rainfall_mm_hr || 86.4) / 86.4;
  const blockageAdd = (payload.drainage_blockage_pct || 0) * 0.25;

  return {
    data: {
      baseline_rainfall_mm_hr: payload.baseline_rainfall_mm_hr || 86.4,
      scenario_rainfall_mm_hr: payload.scenario_rainfall_mm_hr || 86.4,
      drainage_blockage_pct: payload.drainage_blockage_pct || 0,
      cleared_nodes: payload.cleared_nodes || [],
      zone_simulations: FALLBACK_FLOOD_DATA.zones.map(z => {
        const newDepth = Math.max(0, Math.round((z.flood_depth_cm * rainfallMult + blockageAdd) * 10) / 10);
        return {
          zone_id: z.zone_id,
          zone_name: z.zone_name,
          baseline_depth_cm: z.flood_depth_cm,
          simulated_depth_cm: newDepth,
          depth_delta_cm: Math.round((newDepth - z.flood_depth_cm) * 10) / 10,
          baseline_risk: z.risk_level,
          simulated_risk: newDepth > 40 ? "SEVERE" : newDepth > 25 ? "HIGH" : newDepth > 10 ? "MODERATE" : "LOW",
          impact_summary: newDepth > z.flood_depth_cm ? "Increased inundation threat" : "Mitigated flood risk"
        };
      }),
      overall_summary: {
        total_zones_evaluated: 8,
        zones_worsened: payload.drainage_blockage_pct > 0 || payload.scenario_rainfall_mm_hr > 86.4 ? 4 : 0,
        zones_improved: payload.cleared_nodes && payload.cleared_nodes.length > 0 ? 3 : 0
      }
    },
    isLive: false,
    error: 'Offline Simulation Mode'
  };
}

/** 12. Action Priorities */
export async function fetchPriorities(zoneId = null, rainfallMmHr = null) {
  let queryParams = new URLSearchParams();
  if (zoneId) queryParams.append('zone_id', zoneId);
  if (rainfallMmHr) queryParams.append('rainfall_mm_hr', rainfallMmHr);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/priorities${queryString}`);
  if (result.isLive && result.data) return result;

  return {
    data: {
      top_priority_zone_id: "Z03",
      critical_zones_count: 2,
      priorities: [
        { rank: 1, zone_id: "Z03", priority_level: "CRITICAL", score: 96.5, target_location: "Station Road Sump N21", recommended_action: "Deploy High-Capacity Debris Pump & Clear Conduit E21", urgency_window_minutes: 15 },
        { rank: 2, zone_id: "Z01", priority_level: "CRITICAL", score: 88.2, target_location: "Central Commercial N21/N14", recommended_action: "Clear Drain Blockage at N21 Junction", urgency_window_minutes: 25 },
        { rank: 3, zone_id: "Z02", priority_level: "HIGH", score: 78.4, target_location: "North Market Culvert N14", recommended_action: "Inspect Culvert Intake & Issue Traffic Diversion", urgency_window_minutes: 40 },
        { rank: 4, zone_id: "Z05", priority_level: "HIGH", score: 72.0, target_location: "Hospital Access Corridor", recommended_action: "Deploy Flood Barriers to Protect Emergency Entrance", urgency_window_minutes: 30 }
      ]
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 13. Flood Propagation */
export async function fetchPropagation(zoneId = null, rainfallMmHr = null) {
  let queryParams = new URLSearchParams();
  if (zoneId) queryParams.append('zone_id', zoneId);
  if (rainfallMmHr) queryParams.append('rainfall_mm_hr', rainfallMmHr);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  const result = await fetchWithTimeout(`/propagation${queryString}`);
  if (result.isLive && result.data) return result;

  return {
    data: {
      primary_source_zone_id: zoneId || "Z03",
      corridor_sequence: ["N21 Sump", "Station Road", "Market Junction", "Bus Terminal", "Hospital Approach"],
      total_propagated_zones: 4,
      affected_zones: [
        { zone_id: "Z03", depth_cm: 47.5, arrival_offset_min: 0, transmission_mechanism: "Surcharge Sump Overflow" },
        { zone_id: "Z01", depth_cm: 42.5, arrival_offset_min: 15, transmission_mechanism: "Surface Overland Runoff" },
        { zone_id: "Z02", depth_cm: 38.0, arrival_offset_min: 30, transmission_mechanism: "Conduit Backwater Flow" },
        { zone_id: "Z05", depth_cm: 6.0, arrival_offset_min: 60, transmission_mechanism: "Downstream Spillover" }
      ]
    },
    isLive: false,
    error: 'Offline Fallback'
  };
}

/** 14. Flood-Aware Safe Routing */
export async function computeRoute({ origin = "Z03", destination = "Z05", emergency = false, rainfallMmHr = null }) {
  const payload = { origin, destination, emergency, rainfall_mm_hr: rainfallMmHr };
  const result = await fetchWithTimeout('/route', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (result.isLive && result.data) return result;

  // Resilient Fallback Safe Route calculation
  return {
    data: {
      origin: origin,
      destination: destination,
      emergency_mode: emergency,
      is_passable: true,
      route_summary: {
        recommended_route_name: "Route B (Via Highland Bypass)",
        travel_time_minutes: 16,
        max_flood_depth_cm: 6.0,
        distance_km: 4.8,
        hazard_risk_level: "LOW"
      },
      recommended_route: {
        id: "route-b",
        name: "Highland Elevated Bypass",
        travel_time_minutes: 16,
        distance_km: 4.8,
        max_depth_cm: 6.0,
        risk_level: "LOW",
        is_recommended: true,
        description: "Avoids flooded Station Road Sump (N21). 100% safe for all vehicles.",
        waypoints: [
          { lat: 13.0827, lng: 80.2707, label: "Origin (Z03)" },
          { lat: 13.0890, lng: 80.2650, label: "Highland Elevated Flyover" },
          { lat: 13.0950, lng: 80.2750, label: "Hospital Relief Approach" },
          { lat: 13.0980, lng: 80.2800, label: "Destination Hospital (Z05)" }
        ]
      },
      alternative_routes: [
        {
          id: "route-a",
          name: "Direct Corridor (Station Road)",
          travel_time_minutes: 12,
          distance_km: 3.2,
          max_depth_cm: 47.5,
          risk_level: "CRITICAL",
          is_recommended: false,
          description: "UNSAFE: Crosses 47.5 cm flood waters at N21 Sump. High risk of vehicle engine stall.",
          waypoints: [
            { lat: 13.0827, lng: 80.2707, label: "Origin (Z03)" },
            { lat: 13.0850, lng: 80.2720, label: "Flooded Station Road (47.5cm)" },
            { lat: 13.0980, lng: 80.2800, label: "Destination Hospital (Z05)" }
          ]
        }
      ]
    },
    isLive: false,
    error: 'Offline Fallback Safe Routing'
  };
}
