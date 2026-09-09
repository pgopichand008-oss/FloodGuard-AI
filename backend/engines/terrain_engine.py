"""Terrain analysis and surface runoff calculation engine."""
from typing import List, Optional
from backend.engines.rainfall_engine import (
    RainfallEngine,
    default_rainfall_engine,
)
from backend.models.terrain_models import (
    RunoffOverviewResponse,
    RunoffTendency,
    TerrainOverviewResponse,
    TerrainZoneModel,
    ZoneRunoffResult,
)
from backend.services.terrain_service import (
    TerrainService,
    default_terrain_service,
)


class TerrainEngine:
    """Computes terrain vulnerability indices, runoff coefficients, and surface runoff discharge."""

    # Documented transparent hydrological assumptions
    ASSUMPTIONS = [
        "Hydrological runoff calculated using the standard metric Rational Method: Q = (C * I * A) / 360.",
        "Composite runoff coefficient C incorporates base soil infiltration, surface imperviousness, and slope gradient.",
        "Catchment areas are assumed uniform across individual delineated street/zone corridors.",
        "Flow accumulation and elevation values represent synthetic DEM prototype data.",
        "Infiltration rates are assumed constant across the calculation time-step without dynamic soil saturation curve."
    ]

    def __init__(
        self,
        terrain_service: Optional[TerrainService] = None,
        rainfall_engine: Optional[RainfallEngine] = None,
    ):
        self.terrain_service = terrain_service or default_terrain_service
        self.rainfall_engine = rainfall_engine or default_rainfall_engine

    def calculate_runoff_coefficient(self, imperviousness: float, slope_percent: float) -> float:
        """
        Calculates composite Rational Method runoff coefficient C.
        Formula: C = 0.15 + (0.75 * imperviousness) + (0.05 * min(1.0, slope / 5.0))
        Bounded in [0.15, 0.98].
        """
        c = 0.15 + (0.75 * imperviousness) + (0.05 * min(1.0, slope_percent / 5.0))
        return round(max(0.15, min(0.98, c)), 3)

    def classify_runoff_tendency(self, runoff_rate_mm_hr: float) -> RunoffTendency:
        """Classifies effective runoff generation rate into risk categories."""
        if runoff_rate_mm_hr < 25.0:
            return RunoffTendency.LOW
        elif runoff_rate_mm_hr < 50.0:
            return RunoffTendency.MODERATE
        elif runoff_rate_mm_hr < 75.0:
            return RunoffTendency.HIGH
        else:
            return RunoffTendency.SEVERE

    def calculate_accumulation_index(self, flow_accumulation: int) -> float:
        """Normalizes upstream drainage cell accumulation to a 0.0 - 1.0 index."""
        # Normalized against catchment reference threshold of 2500 accumulation cells
        return round(min(1.0, max(0.0, flow_accumulation / 2500.0)), 3)

    def calculate_flood_prone_index(
        self,
        elevation_m: float,
        slope_percent: float,
        flow_accumulation: int,
        imperviousness: float,
        is_low_lying: bool,
        min_elev: float = 10.0,
        max_elev: float = 40.0,
    ) -> float:
        """
        Calculates multi-criteria terrain vulnerability index (0.0 to 1.0).
        Lower elevation + flatter slope + higher accumulation + higher imperviousness -> higher score.
        """
        # 1. Elevation inverse factor (lower ground = higher accumulation tendency)
        elev_span = max(1.0, max_elev - min_elev)
        elev_factor = max(0.0, min(1.0, (max_elev - elevation_m) / elev_span))

        # 2. Flatness factor (flat slopes < 1.0% retain surface water)
        flatness_factor = max(0.0, min(1.0, 1.0 - (slope_percent / 4.0)))

        # 3. Flow accumulation factor
        accum_factor = self.calculate_accumulation_index(flow_accumulation)

        # 4. Impervious surface factor
        imp_factor = imperviousness

        # Weighted combination
        score = (
            0.35 * elev_factor
            + 0.25 * flatness_factor
            + 0.25 * accum_factor
            + 0.15 * imp_factor
        )

        if is_low_lying:
            score = max(score, 0.55)  # Enforce baseline floor for recognized low-lying depressions

        return round(min(1.0, max(0.0, score)), 3)

    def get_terrain_overview(self) -> TerrainOverviewResponse:
        """Returns registered terrain DEM zones and attributes."""
        dataset = self.terrain_service.load_dataset()
        zones = self.terrain_service.get_all_zones()

        return TerrainOverviewResponse(
            location=dataset.get("location", "Urban Catchment"),
            data_type=dataset.get("data_type", "DEMO-SIMULATED"),
            generated_at=dataset.get("generated_at", "2026-09-09T00:00:00Z"),
            zone_count=len(zones),
            zones=zones,
            source_note=dataset.get(
                "source_note",
                "Synthetic digital elevation model (DEM) and catchment data for prototype demonstration."
            )
        )

    def calculate_zone_runoff(
        self,
        zone: TerrainZoneModel,
        rainfall_intensity_mm_hr: float,
        min_elev: float = 10.0,
        max_elev: float = 40.0,
    ) -> ZoneRunoffResult:
        """Calculates surface runoff metrics and vulnerability indices for an individual zone."""
        c = self.calculate_runoff_coefficient(zone.imperviousness, zone.slope_percent)
        runoff_rate = round(c * rainfall_intensity_mm_hr, 2)

        # Rational Method: Q = (C * I * A) / 360 (m3/s)
        peak_q = round((c * rainfall_intensity_mm_hr * zone.area_hectares) / 360.0, 4)

        tendency = self.classify_runoff_tendency(runoff_rate)
        accum_index = self.calculate_accumulation_index(zone.flow_accumulation)
        flood_index = self.calculate_flood_prone_index(
            elevation_m=zone.elevation_m,
            slope_percent=zone.slope_percent,
            flow_accumulation=zone.flow_accumulation,
            imperviousness=zone.imperviousness,
            is_low_lying=zone.is_low_lying,
            min_elev=min_elev,
            max_elev=max_elev,
        )

        return ZoneRunoffResult(
            zone_id=zone.zone_id,
            name=zone.name,
            elevation_m=zone.elevation_m,
            slope_percent=zone.slope_percent,
            imperviousness=zone.imperviousness,
            area_hectares=zone.area_hectares,
            runoff_coefficient_c=c,
            rainfall_intensity_mm_hr=rainfall_intensity_mm_hr,
            runoff_rate_mm_hr=runoff_rate,
            peak_discharge_m3_s=peak_q,
            runoff_tendency=tendency,
            accumulation_index=accum_index,
            flood_prone_index=flood_index,
            is_low_lying=zone.is_low_lying,
        )

    def calculate_catchment_runoff(
        self,
        rainfall_intensity_mm_hr: Optional[float] = None,
        zone_ids: Optional[List[str]] = None,
    ) -> RunoffOverviewResponse:
        """
        Calculates surface runoff across all or requested catchment zones.
        If rainfall intensity is omitted, queries current rainfall from RainfallEngine.
        """
        dataset = self.terrain_service.load_dataset()
        all_zones = self.terrain_service.get_all_zones()

        # Determine rainfall intensity
        if rainfall_intensity_mm_hr is None:
            current_rain = self.rainfall_engine.get_current_rainfall()
            applied_rainfall = current_rain.current_intensity_mm_per_hr
        else:
            applied_rainfall = float(rainfall_intensity_mm_hr)

        # Filter zones if subset requested
        if zone_ids:
            target_ids = {zid.lower() for zid in zone_ids}
            zones_to_eval = [z for z in all_zones if z.zone_id.lower() in target_ids]
        else:
            zones_to_eval = all_zones

        # Catchment elevation bounds for relative normalization
        elevations = [z.elevation_m for z in all_zones] or [10.0, 40.0]
        min_elev = min(elevations)
        max_elev = max(elevations)

        results: List[ZoneRunoffResult] = []
        total_discharge = 0.0
        high_risk_zones: List[str] = []

        for zone in zones_to_eval:
            res = self.calculate_zone_runoff(zone, applied_rainfall, min_elev, max_elev)
            results.append(res)
            total_discharge += res.peak_discharge_m3_s
            if res.runoff_tendency in [RunoffTendency.HIGH, RunoffTendency.SEVERE]:
                high_risk_zones.append(f"{res.name} ({res.zone_id})")

        return RunoffOverviewResponse(
            location=dataset.get("location", "Urban Catchment"),
            data_type=dataset.get("data_type", "DEMO-SIMULATED"),
            rainfall_intensity_used_mm_hr=applied_rainfall,
            total_discharge_m3_s=round(total_discharge, 4),
            highest_risk_zones=high_risk_zones,
            methodology="Rational Method: Q = (C * I * A) / 360",
            assumptions=self.ASSUMPTIONS,
            results=results,
            source_note="Synthetic runoff calculations for prototype demonstration. Not engineering hydraulic certification."
        )


# Global singleton instance
default_terrain_engine = TerrainEngine()
