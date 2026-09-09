"""WHAT-IF simulation engine comparing baseline flood conditions against modified rainfall and drainage scenarios."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.engines.flood_engine import FloodEngine, default_flood_engine
from backend.models.simulation_models import (
    SimulationImpact,
    SimulationResponse,
    SimulationSummary,
    ZoneSimulationComparison,
)


class SimulationEngine:
    """Executes dynamic hydraulic WHAT-IF simulations and computes baseline-to-scenario deltas."""

    def __init__(self, flood_engine: Optional[FloodEngine] = None):
        self.flood_engine = flood_engine or default_flood_engine

    @staticmethod
    def _classify_impact(depth_change_cm: float) -> SimulationImpact:
        """Categorizes flood depth difference into IMPROVED, UNCHANGED, or WORSENED."""
        if depth_change_cm < -0.05:
            return SimulationImpact.IMPROVED
        elif depth_change_cm > 0.05:
            return SimulationImpact.WORSENED
        else:
            return SimulationImpact.UNCHANGED

    @staticmethod
    def _generate_impact_summary(
        zone_name: str,
        baseline_depth: float,
        simulated_depth: float,
        depth_change: float,
        baseline_risk: str,
        simulated_risk: str,
        impact: SimulationImpact,
    ) -> str:
        """Synthesizes human-readable hydraulic impact explanation."""
        if impact == SimulationImpact.IMPROVED:
            return (
                f"{zone_name}: Inundation reduced by {abs(depth_change):.1f} cm "
                f"({baseline_depth:.1f} cm -> {simulated_depth:.1f} cm). "
                f"Risk category transitioned from {baseline_risk} to {simulated_risk}."
            )
        elif impact == SimulationImpact.WORSENED:
            return (
                f"{zone_name}: Inundation worsened by {depth_change:.1f} cm "
                f"({baseline_depth:.1f} cm -> {simulated_depth:.1f} cm). "
                f"Risk category shifted from {baseline_risk} to {simulated_risk}."
            )
        else:
            return (
                f"{zone_name}: Inundation depth remained unchanged at {simulated_depth:.1f} cm "
                f"with steady {simulated_risk} risk level."
            )

    def run_simulation(
        self,
        rainfall_mm_hr: Optional[float] = None,
        blockage_percent: Optional[float] = None,
        zone_id: Optional[str] = None,
    ) -> SimulationResponse:
        """
        Executes dynamic baseline vs simulated comparison across catchment zones.
        Reuses the actual multi-system flood and drainage computational pipelines.
        """
        # 1. Evaluate baseline flood condition using live default parameters
        baseline_resp = self.flood_engine.generate_flood_prediction(
            rainfall_override_mm_hr=None,
            blockage_override_percent=None,
            zone_id=zone_id,
        )

        if zone_id and not baseline_resp.zones:
            raise KeyError(f"Catchment zone '{zone_id}' not found in flood monitoring network")

        # 2. Evaluate simulated scenario with applied parameters
        simulated_resp = self.flood_engine.generate_flood_prediction(
            rainfall_override_mm_hr=rainfall_mm_hr,
            blockage_override_percent=blockage_percent,
            zone_id=zone_id,
        )

        # 3. Map zones and compute direct hydraulic differentials
        sim_map = {z.zone_id: z for z in simulated_resp.zones}
        comparisons: List[ZoneSimulationComparison] = []
        depth_changes: List[float] = []

        zones_improved = 0
        zones_unchanged = 0
        zones_worsened = 0

        for b_zone in baseline_resp.zones:
            s_zone = sim_map.get(b_zone.zone_id)
            if not s_zone:
                continue

            delta = round(s_zone.flood_depth_cm - b_zone.flood_depth_cm, 1)
            depth_changes.append(delta)

            impact = self._classify_impact(delta)
            if impact == SimulationImpact.IMPROVED:
                zones_improved += 1
            elif impact == SimulationImpact.WORSENED:
                zones_worsened += 1
            else:
                zones_unchanged += 1

            summary_text = self._generate_impact_summary(
                zone_name=b_zone.name,
                baseline_depth=b_zone.flood_depth_cm,
                simulated_depth=s_zone.flood_depth_cm,
                depth_change=delta,
                baseline_risk=b_zone.risk_level.value,
                simulated_risk=s_zone.risk_level.value,
                impact=impact,
            )

            comp = ZoneSimulationComparison(
                zone_id=b_zone.zone_id,
                name=b_zone.name,
                baseline_flood_depth_cm=b_zone.flood_depth_cm,
                simulated_flood_depth_cm=s_zone.flood_depth_cm,
                depth_change_cm=delta,
                baseline_risk_level=b_zone.risk_level,
                simulated_risk_level=s_zone.risk_level,
                baseline_rainfall_mm_hr=b_zone.rainfall_intensity_mm_hr,
                simulated_rainfall_mm_hr=s_zone.rainfall_intensity_mm_hr,
                baseline_drainage_utilization_percent=b_zone.drainage_utilization_percent,
                simulated_drainage_utilization_percent=s_zone.drainage_utilization_percent,
                baseline_blockage_percent=b_zone.blockage_percent,
                simulated_blockage_percent=s_zone.blockage_percent,
                baseline_excess_flow_m3s=b_zone.excess_flow_m3s,
                simulated_excess_flow_m3s=s_zone.excess_flow_m3s,
                impact=impact,
                impact_summary=summary_text,
            )
            comparisons.append(comp)

        # 4. Generate dynamic scenario metadata
        if rainfall_mm_hr is not None and blockage_percent is not None:
            scenario_name = f"Combined scenario: rainfall {rainfall_mm_hr:.1f} mm/hr and blockage {blockage_percent:.1f}%"
            scenario_desc = (
                f"Simulates concurrent meteorological and infrastructure change: "
                f"rainfall adjusted to {rainfall_mm_hr:.1f} mm/hr and drainage blockage set to {blockage_percent:.1f}%."
            )
        elif rainfall_mm_hr is not None:
            scenario_name = f"Increased rainfall scenario: {rainfall_mm_hr:.1f} mm/hr" if rainfall_mm_hr > 86.0 else f"Rainfall scenario: {rainfall_mm_hr:.1f} mm/hr"
            scenario_desc = (
                f"Simulates catchment hydrological response to modified precipitation intensity of {rainfall_mm_hr:.1f} mm/hr "
                f"with baseline drainage network configuration."
            )
        elif blockage_percent is not None:
            if blockage_percent == 0.0:
                scenario_name = "Drainage clearing scenario: 0.0% blockage"
                scenario_desc = (
                    "Simulates infrastructure maintenance scenario where all drainage conduits are completely "
                    "desilted and unblocked (0.0% blockage)."
                )
            else:
                scenario_name = f"Drainage blockage scenario: {blockage_percent:.1f}%"
                scenario_desc = (
                    f"Simulates hydraulic conveyance choking with conduit obstruction set to {blockage_percent:.1f}% "
                    f"under baseline rainfall."
                )
        else:
            scenario_name = "Nominal Baseline Simulation"
            scenario_desc = "Baseline operational simulation without parameter overrides."

        max_delta = max(depth_changes) if depth_changes else 0.0
        avg_delta = round(sum(depth_changes) / len(depth_changes), 1) if depth_changes else 0.0

        summary = SimulationSummary(
            total_zones_simulated=len(comparisons),
            zones_improved=zones_improved,
            zones_unchanged=zones_unchanged,
            zones_worsened=zones_worsened,
            max_depth_change_cm=max_delta,
            avg_depth_change_cm=avg_delta,
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        return SimulationResponse(
            scenario_name=scenario_name,
            scenario_description=scenario_desc,
            timestamp=now_iso,
            location=baseline_resp.location,
            parameters_applied={
                "rainfall_mm_hr": rainfall_mm_hr,
                "blockage_percent": blockage_percent,
                "zone_id": zone_id,
            },
            summary=summary,
            results=comparisons,
            data_provenance="SCENARIO SIMULATION USING MODEL-DERIVED FLOOD AND DEMO INPUTS",
            disclaimer=(
                "What-if simulation system for decision support. Results are model-derived from simulated inputs "
                "and not verified for real-world emergency deployment."
            ),
        )


# Global singleton instance
default_simulation_engine = SimulationEngine()
