"""Integrated flood intelligence engine coupling rainfall nowcasting, terrain runoff, and drainage surcharge."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from backend.engines.drainage_engine import (
    DrainageEngine,
    default_drainage_engine,
)
from backend.engines.rainfall_engine import (
    RainfallEngine,
    default_rainfall_engine,
)
from backend.engines.terrain_engine import (
    TerrainEngine,
    default_terrain_engine,
)
from backend.models.flood_models import (
    FloodPredictionResponse,
    FloodRiskLevel,
    FloodSummaryModel,
    ForecastTimePoint,
    ZoneFloodPrediction,
)
from backend.models.terrain_models import TerrainZoneModel


class FloodEngine:
    """Core physics-informed engine combining rainfall, terrain runoff, and pipe surcharge."""

    # Centralized transparent modeling constants
    BASE_RUNOFF_DEPTH_CM: float = 14.0
    SURCHARGE_DEPTH_FACTOR: float = 10.0
    BACKPRESSURE_FACTOR: float = 6.0
    HAZARD_THRESHOLD_DEPTH_CM: float = 15.0

    ASSUMPTIONS = [
        "Surface flood depth combines direct runoff accumulation and uncontained drainage surcharge.",
        "Drainage surcharge overflow is triggered when incoming conduit flow exceeds effective capacity post-blockage.",
        "Backpressure retardation effect occurs when conduit utilization exceeds 70% in low-lying depressions.",
        "Low-lying terrain depressions exhibit reduced gravity dewatering rates and greater ponding retention.",
        "Peak flood depths dynamically scale with nowcast rainfall forecast intensity across the 0-3 hour storm window."
    ]

    def __init__(
        self,
        rainfall_engine: Optional[RainfallEngine] = None,
        terrain_engine: Optional[TerrainEngine] = None,
        drainage_engine: Optional[DrainageEngine] = None,
    ):
        self.rainfall_engine = rainfall_engine or default_rainfall_engine
        self.terrain_engine = terrain_engine or default_terrain_engine
        self.drainage_engine = drainage_engine or default_drainage_engine

    @staticmethod
    def classify_flood_risk(depth_cm: float) -> FloodRiskLevel:
        """
        Centralized deterministic flood risk thresholds:
        depth < 15 cm        -> LOW
        15 cm <= depth < 30  -> MODERATE
        30 cm <= depth < 50  -> HIGH
        depth >= 50 cm       -> SEVERE
        """
        if depth_cm < 15.0:
            return FloodRiskLevel.LOW
        elif depth_cm < 30.0:
            return FloodRiskLevel.MODERATE
        elif depth_cm < 50.0:
            return FloodRiskLevel.HIGH
        else:
            return FloodRiskLevel.SEVERE

    def calculate_zone_flood_depth(
        self,
        rainfall_mm_hr: float,
        flood_prone_index: float,
        accumulation_index: float,
        excess_flow_m3s: float,
        utilization_percent: float,
        blockage_percent: float,
    ) -> float:
        """
        Calculates surface flood depth (cm) from terrain runoff and drainage surcharge.
        Monotonically responsive to rainfall, drainage utilization, blockage, and terrain vulnerability.
        """
        if rainfall_mm_hr <= 0.0:
            return 0.0

        # 1. Direct surface runoff accumulation (cm)
        d_runoff = self.BASE_RUNOFF_DEPTH_CM * flood_prone_index * (rainfall_mm_hr / 100.0)

        # 2. Drainage surcharge overflow component (cm)
        d_surcharge = self.SURCHARGE_DEPTH_FACTOR * excess_flow_m3s * (1.0 + accumulation_index)

        # 3. Conduit backpressure retardation (utilization > 70% slows surface drainage)
        if utilization_percent > 70.0:
            backpressure_ratio = min(1.0, (utilization_percent - 70.0) / 30.0)
            d_backpressure = self.BACKPRESSURE_FACTOR * backpressure_ratio * flood_prone_index
        else:
            d_backpressure = 0.0

        # 4. Blockage impediment adjustment
        blockage_factor = 1.0 + (blockage_percent / 200.0)

        total_depth = (d_runoff + d_surcharge + d_backpressure) * blockage_factor
        return round(max(0.0, total_depth), 1)

    def evaluate_zone_prediction(
        self,
        zone: TerrainZoneModel,
        rainfall_mm_hr: float,
        peak_rainfall_mm_hr: float,
        drainage_nodes_map: Dict[str, Any],
        drainage_edges_map: Dict[str, Any],
    ) -> ZoneFloodPrediction:
        """Evaluates integrated flood prediction for an individual catchment zone."""
        # 1. Runoff calculation from TerrainEngine
        runoff_res = self.terrain_engine.calculate_zone_runoff(zone, rainfall_mm_hr)

        # 2. Match associated drainage node and connected conduits
        matched_node = None
        for n in drainage_nodes_map.values():
            if n.associated_zone_id and n.associated_zone_id.upper() == zone.zone_id.upper():
                matched_node = n
                break

        # Find primary conduit for this zone
        matched_edge = None
        if matched_node:
            for e in drainage_edges_map.values():
                if e.from_node == matched_node.node_id or e.to_node == matched_node.node_id:
                    matched_edge = e
                    break

        if matched_edge:
            cap = matched_edge.capacity_m3s
            eff_cap = matched_edge.effective_capacity_m3s
            flow = matched_edge.current_flow_m3s
            util = matched_edge.utilization_percent
            blockage = matched_edge.blockage_percent
            excess = matched_edge.excess_flow_m3s
            surcharged = matched_edge.is_surcharged
        elif matched_node:
            cap = matched_node.outflow_capacity_m3s
            eff_cap = matched_node.outflow_capacity_m3s
            flow = matched_node.inflow_m3s
            util = (flow / eff_cap * 100.0) if eff_cap > 0 else 0.0
            blockage = 0.0
            excess = max(0.0, flow - eff_cap)
            surcharged = matched_node.is_surcharged
        else:
            # Zone with overland shedding only
            cap = 0.0
            eff_cap = 0.0
            flow = 0.0
            util = 0.0
            blockage = 0.0
            excess = 0.0
            surcharged = False

        # 3. Calculate current surface flood depth
        depth_cm = self.calculate_zone_flood_depth(
            rainfall_mm_hr=rainfall_mm_hr,
            flood_prone_index=runoff_res.flood_prone_index,
            accumulation_index=runoff_res.accumulation_index,
            excess_flow_m3s=excess,
            utilization_percent=util,
            blockage_percent=blockage,
        )

        # 4. Calculate predicted peak depth during storm progression
        if peak_rainfall_mm_hr > rainfall_mm_hr and rainfall_mm_hr > 0.0:
            scale_ratio = (peak_rainfall_mm_hr / rainfall_mm_hr) ** 0.85
            peak_depth_cm = round(depth_cm * scale_ratio, 1)
        else:
            peak_depth_cm = depth_cm

        # 5. Onset time to hazardous ponding (> 15 cm)
        if depth_cm >= self.HAZARD_THRESHOLD_DEPTH_CM:
            onset_min = 0
        else:
            depression_offset = 15 if zone.is_low_lying else 0
            remaining_margin = max(0.0, self.HAZARD_THRESHOLD_DEPTH_CM - depth_cm)
            onset_min = int(max(5, (remaining_margin * 2.5) - depression_offset))

        # 6. Risk classification
        risk_level = self.classify_flood_risk(peak_depth_cm)

        # Coordinates lookup (from matched node or default grid)
        lat = matched_node.latitude if matched_node else (17.3850 + (zone.elevation_m * 0.0005))
        lon = matched_node.longitude if matched_node else (78.4860 + (zone.slope_percent * 0.001))

        return ZoneFloodPrediction(
            zone_id=zone.zone_id,
            name=zone.name,
            latitude=round(lat, 5),
            longitude=round(lon, 5),
            elevation_m=zone.elevation_m,
            slope_percent=zone.slope_percent,
            is_low_lying=zone.is_low_lying,
            rainfall_intensity_mm_hr=rainfall_mm_hr,
            runoff_discharge_m3s=runoff_res.peak_discharge_m3_s,
            drainage_capacity_m3s=cap,
            drainage_effective_capacity_m3s=eff_cap,
            drainage_utilization_percent=util,
            blockage_percent=blockage,
            excess_flow_m3s=excess,
            is_surcharged=surcharged,
            flood_depth_cm=depth_cm,
            peak_depth_cm=peak_depth_cm,
            onset_minutes=onset_min,
            risk_level=risk_level,
            confidence=0.88,
            data_source="MODEL-DERIVED FROM DEMO-SIMULATED INPUTS",
            source_note="Coupled model output from rainfall, terrain runoff, and pipe surcharge calculations."
        )

    def generate_flood_prediction(
        self,
        rainfall_override_mm_hr: Optional[float] = None,
        zone_id: Optional[str] = None,
        risk_level_filter: Optional[FloodRiskLevel] = None,
    ) -> FloodPredictionResponse:
        """Executes full multi-system integration to calculate urban flood predictions."""
        # 1. Fetch rainfall nowcast and forecast
        current_rain = self.rainfall_engine.get_current_rainfall()
        applied_rainfall = (
            float(rainfall_override_mm_hr)
            if rainfall_override_mm_hr is not None
            else current_rain.current_intensity_mm_per_hr
        )
        forecast_data = self.rainfall_engine.get_forecast()
        peak_forecast_rain = forecast_data.peak_forecast_intensity_mm_per_hr

        # 2. Fetch all catchment zones from Terrain
        all_zones = self.terrain_engine.terrain_service.get_all_zones()

        # 3. Fetch drainage network evaluation
        drainage_resp = self.drainage_engine.evaluate_entire_network()
        drainage_nodes_map = {n.node_id: n for n in drainage_resp.nodes}
        drainage_edges_map = {e.edge_id: e for e in drainage_resp.drains}

        # 4. Evaluate each zone
        zone_predictions: List[ZoneFloodPrediction] = []
        for z in all_zones:
            pred = self.evaluate_zone_prediction(
                zone=z,
                rainfall_mm_hr=applied_rainfall,
                peak_rainfall_mm_hr=peak_forecast_rain,
                drainage_nodes_map=drainage_nodes_map,
                drainage_edges_map=drainage_edges_map,
            )
            zone_predictions.append(pred)

        # Apply filtering if requested
        filtered_zones = zone_predictions
        if zone_id:
            filtered_zones = [zp for zp in filtered_zones if zp.zone_id.upper() == zone_id.strip().upper()]
        if risk_level_filter:
            filtered_zones = [zp for zp in filtered_zones if zp.risk_level == risk_level_filter]

        # 5. Compute dynamic aggregated summary metrics across all evaluated zones
        low_cnt = sum(1 for zp in zone_predictions if zp.risk_level == FloodRiskLevel.LOW)
        mod_cnt = sum(1 for zp in zone_predictions if zp.risk_level == FloodRiskLevel.MODERATE)
        high_cnt = sum(1 for zp in zone_predictions if zp.risk_level == FloodRiskLevel.HIGH)
        sev_cnt = sum(1 for zp in zone_predictions if zp.risk_level == FloodRiskLevel.SEVERE)

        max_depth = max((zp.peak_depth_cm for zp in zone_predictions), default=0.0)
        avg_depth = round(sum(zp.flood_depth_cm for zp in zone_predictions) / max(1, len(zone_predictions)), 1)
        max_util = max((zp.drainage_utilization_percent for zp in zone_predictions), default=0.0)
        surcharged_segs = sum(1 for zp in zone_predictions if zp.is_surcharged)
        affected_roads = sum(1 for zp in zone_predictions if zp.peak_depth_cm >= self.HAZARD_THRESHOLD_DEPTH_CM)
        critical_nodes = sum(1 for n in drainage_resp.nodes if n.is_surcharged or n.status.value in ["CRITICAL", "SURCHARGED"])

        summary = FloodSummaryModel(
            total_zones=len(zone_predictions),
            low_risk_zones=low_cnt,
            moderate_risk_zones=mod_cnt,
            high_risk_zones=high_cnt,
            severe_risk_zones=sev_cnt,
            max_flood_depth_cm=max_depth,
            avg_flood_depth_cm=avg_depth,
            max_drainage_utilization_percent=round(max_util, 2),
            surcharged_segments_count=surcharged_segs,
            affected_roads_count=affected_roads,
            critical_drainage_nodes_count=critical_nodes,
        )

        # Overall urban risk level
        overall_risk = "LOW"
        if sev_cnt > 0:
            overall_risk = "SEVERE"
        elif high_cnt > 0:
            overall_risk = "HIGH"
        elif mod_cnt > 0:
            overall_risk = "MODERATE"

        # 6. Build dynamic nowcast flood depth forecast sequence across 0-180 minutes
        # Steps through the nowcast rainfall curve
        forecast_points: List[ForecastTimePoint] = []
        for pt in forecast_data.forecast_series:
            # Scaled catchment average depth proportional to rainfall at time t
            step_rain = pt.intensity_mm_per_hr
            step_depth = round(avg_depth * (step_rain / max(1.0, applied_rainfall)), 1) if applied_rainfall > 0 else 0.0
            forecast_points.append(ForecastTimePoint(minutes=pt.offset_minutes, depth_cm=step_depth))

        now_iso = datetime.now(timezone.utc).isoformat()

        # Backward compatibility contract dictionaries
        rainfall_contract = {
            "current_mm_per_hr": applied_rainfall,
            "peak_mm_per_hr": peak_forecast_rain,
            "trend": current_rain.trend
        }
        flood_contract = {
            "risk": overall_risk,
            "peak_depth_cm": round(max_depth),
            "affected_roads": affected_roads,
            "critical_drainage_nodes": critical_nodes
        }

        return FloodPredictionResponse(
            location=current_rain.location,
            timestamp=now_iso,
            data_type="MODEL-DERIVED FROM DEMO-SIMULATED INPUTS",
            rainfall=rainfall_contract,
            flood=flood_contract,
            forecast=forecast_points,
            summary=summary,
            zones=filtered_zones,
            methodology="Physics-informed coupling: Rational Method Runoff + Surcharge Capacity Balance",
            assumptions=self.ASSUMPTIONS,
            limitation_note="Prototype flood intelligence model for demonstration. Surcharge depth uses capacity thresholding; not 2D hydrodynamic wave routing."
        )


# Global singleton instance
default_flood_engine = FloodEngine()
