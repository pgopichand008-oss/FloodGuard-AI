"""WHY-FLOOD Explainability Engine providing transparent, rule-based attribution of urban flood risks."""
from typing import Any, Dict, List, Optional, Tuple

from backend.models.explain_models import (
    ContributingFactor,
    ContributionLevel,
    FactorSeverity,
    ZoneExplanation,
)
from backend.models.flood_models import FloodRiskLevel


class ExplainEngine:
    """Transparent engineering explainability engine calculating factor contributions and primary flood causes."""

    # Benchmarks and engineering thresholds
    RAINFALL_THRESHOLD_CRITICAL_MM_HR: float = 80.0
    RAINFALL_THRESHOLD_HIGH_MM_HR: float = 50.0
    RAINFALL_THRESHOLD_MODERATE_MM_HR: float = 25.0

    UTILIZATION_THRESHOLD_CRITICAL_PCT: float = 100.0
    UTILIZATION_THRESHOLD_HIGH_PCT: float = 80.0
    UTILIZATION_THRESHOLD_MODERATE_PCT: float = 60.0

    BLOCKAGE_THRESHOLD_CRITICAL_PCT: float = 35.0
    BLOCKAGE_THRESHOLD_HIGH_PCT: float = 20.0
    BLOCKAGE_THRESHOLD_MODERATE_PCT: float = 10.0

    EXCESS_FLOW_THRESHOLD_CRITICAL_M3S: float = 0.50
    EXCESS_FLOW_THRESHOLD_HIGH_M3S: float = 0.10

    LOW_ELEVATION_THRESHOLD_M: float = 16.0
    FLAT_SLOPE_THRESHOLD_PCT: float = 1.0

    @staticmethod
    def _map_score_to_contribution(score: float) -> Tuple[FactorSeverity, ContributionLevel]:
        """Maps continuous 0.0-1.0 attribution score to severity and contribution categories."""
        if score >= 0.75:
            return FactorSeverity.CRITICAL, ContributionLevel.CRITICAL
        elif score >= 0.50:
            return FactorSeverity.HIGH, ContributionLevel.HIGH
        elif score >= 0.25:
            return FactorSeverity.MODERATE, ContributionLevel.MODERATE
        else:
            return FactorSeverity.NEGLIGIBLE, ContributionLevel.LOW

    def evaluate_rainfall_factor(self, rainfall_mm_hr: float) -> ContributingFactor:
        """Evaluates precipitation intensity driver."""
        if rainfall_mm_hr <= 0.0:
            score = 0.0
            explanation = "No rainfall observed; zero precipitation contribution."
        elif rainfall_mm_hr >= self.RAINFALL_THRESHOLD_CRITICAL_MM_HR:
            score = min(1.0, 0.80 + 0.20 * ((rainfall_mm_hr - self.RAINFALL_THRESHOLD_CRITICAL_MM_HR) / 50.0))
            explanation = f"Torrential rainfall rate of {rainfall_mm_hr:.1f} mm/hr severely overwhelms local drainage and surface retention."
        elif rainfall_mm_hr >= self.RAINFALL_THRESHOLD_HIGH_MM_HR:
            score = 0.55 + 0.25 * ((rainfall_mm_hr - self.RAINFALL_THRESHOLD_HIGH_MM_HR) / 30.0)
            explanation = f"Heavy rainfall rate of {rainfall_mm_hr:.1f} mm/hr exceeds ordinary urban infiltration rates."
        elif rainfall_mm_hr >= self.RAINFALL_THRESHOLD_MODERATE_MM_HR:
            score = 0.30 + 0.25 * ((rainfall_mm_hr - self.RAINFALL_THRESHOLD_MODERATE_MM_HR) / 25.0)
            explanation = f"Moderate rainfall rate of {rainfall_mm_hr:.1f} mm/hr generates steady surface runoff."
        else:
            score = 0.10 + 0.20 * (rainfall_mm_hr / self.RAINFALL_THRESHOLD_MODERATE_MM_HR)
            explanation = f"Light rainfall of {rainfall_mm_hr:.1f} mm/hr is within normal urban tolerance."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Rainfall Intensity",
            severity=severity,
            value=round(rainfall_mm_hr, 1),
            unit="mm/hr",
            threshold=self.RAINFALL_THRESHOLD_HIGH_MM_HR,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def evaluate_drainage_utilization_factor(self, utilization_pct: float) -> ContributingFactor:
        """Evaluates conduit hydraulic utilization driver."""
        if utilization_pct <= 0.0:
            score = 0.0
            explanation = "Drainage conduits are idle with ample available conveyance capacity."
        elif utilization_pct >= self.UTILIZATION_THRESHOLD_CRITICAL_PCT:
            score = min(1.0, 0.85 + 0.15 * min(1.0, (utilization_pct - 100.0) / 50.0))
            explanation = f"Drainage capacity is fully exhausted at {utilization_pct:.1f}% utilization, causing complete hydraulic choking."
        elif utilization_pct >= self.UTILIZATION_THRESHOLD_HIGH_PCT:
            score = 0.60 + 0.25 * ((utilization_pct - self.UTILIZATION_THRESHOLD_HIGH_PCT) / 20.0)
            explanation = f"Drainage system operates under severe stress at {utilization_pct:.1f}% capacity."
        elif utilization_pct >= self.UTILIZATION_THRESHOLD_MODERATE_PCT:
            score = 0.30 + 0.30 * ((utilization_pct - self.UTILIZATION_THRESHOLD_MODERATE_PCT) / 20.0)
            explanation = f"Drainage utilization is elevated at {utilization_pct:.1f}%, approaching capacity limits."
        else:
            score = 0.10 + 0.20 * (utilization_pct / self.UTILIZATION_THRESHOLD_MODERATE_PCT)
            explanation = f"Drainage utilization at {utilization_pct:.1f}% is comfortably within design limits."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Drainage Utilization",
            severity=severity,
            value=round(utilization_pct, 1),
            unit="%",
            threshold=self.UTILIZATION_THRESHOLD_HIGH_PCT,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def evaluate_surcharge_factor(self, excess_flow_m3s: float, is_surcharged: bool) -> ContributingFactor:
        """Evaluates uncontained conduit surcharge overflow driver."""
        if not is_surcharged or excess_flow_m3s <= 0.0:
            score = 0.0
            explanation = "No conduit surcharge observed; storm flows remain fully contained within pipes."
        elif excess_flow_m3s >= self.EXCESS_FLOW_THRESHOLD_CRITICAL_M3S:
            score = min(1.0, 0.85 + 0.15 * min(1.0, (excess_flow_m3s - 0.50) / 1.0))
            explanation = f"Severe pipe surcharge releasing {excess_flow_m3s:.2f} m³/s of pressurized overflow directly onto streets."
        elif excess_flow_m3s >= self.EXCESS_FLOW_THRESHOLD_HIGH_M3S:
            score = 0.60 + 0.25 * ((excess_flow_m3s - self.EXCESS_FLOW_THRESHOLD_HIGH_M3S) / 0.40)
            explanation = f"Active conduit surcharge discharging {excess_flow_m3s:.2f} m³/s above pipe capacity."
        else:
            score = 0.40 + 0.20 * (excess_flow_m3s / self.EXCESS_FLOW_THRESHOLD_HIGH_M3S)
            explanation = f"Minor pipe surcharge of {excess_flow_m3s:.2f} m³/s overflowing drainage inlets."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Drainage Surcharge",
            severity=severity,
            value=round(excess_flow_m3s, 2),
            unit="m3/s",
            threshold=self.EXCESS_FLOW_THRESHOLD_HIGH_M3S,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def evaluate_blockage_factor(self, blockage_pct: float) -> ContributingFactor:
        """Evaluates conduit physical siltation and obstruction driver."""
        if blockage_pct <= 0.0:
            score = 0.0
            explanation = "Drainage conduits are clear of significant physical obstructions."
        elif blockage_pct >= self.BLOCKAGE_THRESHOLD_CRITICAL_PCT:
            score = min(1.0, 0.80 + 0.20 * min(1.0, (blockage_pct - 35.0) / 30.0))
            explanation = f"Critical pipe blockage of {blockage_pct:.1f}% severely throttles cross-sectional discharge capacity."
        elif blockage_pct >= self.BLOCKAGE_THRESHOLD_HIGH_PCT:
            score = 0.55 + 0.25 * ((blockage_pct - self.BLOCKAGE_THRESHOLD_HIGH_PCT) / 15.0)
            explanation = f"Substantial pipe blockage of {blockage_pct:.1f}% noticeably constricts stormwater throughput."
        elif blockage_pct >= self.BLOCKAGE_THRESHOLD_MODERATE_PCT:
            score = 0.30 + 0.25 * ((blockage_pct - self.BLOCKAGE_THRESHOLD_MODERATE_PCT) / 10.0)
            explanation = f"Moderate sediment accumulation ({blockage_pct:.1f}% blockage) partially impedes flow."
        else:
            score = 0.05 + 0.20 * (blockage_pct / self.BLOCKAGE_THRESHOLD_MODERATE_PCT)
            explanation = f"Low debris accumulation ({blockage_pct:.1f}% blockage) has negligible conveyance impact."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Drainage Blockage",
            severity=severity,
            value=round(blockage_pct, 1),
            unit="%",
            threshold=self.BLOCKAGE_THRESHOLD_HIGH_PCT,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def evaluate_terrain_factor(self, elevation_m: float, slope_pct: float, is_low_lying: bool) -> ContributingFactor:
        """Evaluates topographical vulnerability and depression retention driver."""
        # Topographical vulnerability increases with lower elevation and flatter slope
        elev_component = max(0.0, min(1.0, (35.0 - elevation_m) / 25.0))
        slope_component = max(0.0, min(1.0, (3.0 - slope_pct) / 2.5))
        base_score = 0.60 * elev_component + 0.40 * slope_component

        if is_low_lying:
            score = min(1.0, max(0.65, base_score + 0.20))
            explanation = f"Low-lying depression topography ({elevation_m:.1f} m elevation, {slope_pct:.1f}% slope) naturally collects and retains runoff."
        elif elevation_m < self.LOW_ELEVATION_THRESHOLD_M:
            score = min(1.0, max(0.50, base_score))
            explanation = f"Low elevation ({elevation_m:.1f} m) creates a vulnerable collecting zone with sluggish gravity drainage."
        elif slope_pct > 3.0:
            score = max(0.05, min(0.25, 0.30 - (slope_pct / 20.0)))
            explanation = f"Elevated terrain ({elevation_m:.1f} m) with steep {slope_pct:.1f}% slope promotes rapid natural runoff shedding."
        else:
            score = max(0.15, min(0.45, base_score))
            explanation = f"Moderate terrain elevation ({elevation_m:.1f} m) and slope ({slope_pct:.1f}%) exhibit standard drainage characteristics."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Terrain Elevation & Slope",
            severity=severity,
            value=round(elevation_m, 1),
            unit="m",
            threshold=self.LOW_ELEVATION_THRESHOLD_M,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def evaluate_runoff_factor(self, runoff_m3s: float) -> ContributingFactor:
        """Evaluates surface runoff generation volume driver."""
        if runoff_m3s <= 0.0:
            score = 0.0
            explanation = "Zero surface runoff generated across catchment."
        elif runoff_m3s >= 0.70:
            score = min(1.0, 0.75 + 0.25 * min(1.0, (runoff_m3s - 0.70) / 0.50))
            explanation = f"Heavy surface runoff discharge of {runoff_m3s:.2f} m³/s generated by impermeable urban coverage."
        elif runoff_m3s >= 0.40:
            score = 0.50 + 0.25 * ((runoff_m3s - 0.40) / 0.30)
            explanation = f"Substantial surface runoff rate of {runoff_m3s:.2f} m³/s flowing toward drainage inlets."
        elif runoff_m3s >= 0.20:
            score = 0.25 + 0.25 * ((runoff_m3s - 0.20) / 0.20)
            explanation = f"Moderate runoff discharge of {runoff_m3s:.2f} m³/s."
        else:
            score = 0.05 + 0.20 * (runoff_m3s / 0.20)
            explanation = f"Low runoff discharge of {runoff_m3s:.2f} m³/s."

        severity, contribution = self._map_score_to_contribution(score)
        return ContributingFactor(
            factor="Surface Runoff Volume",
            severity=severity,
            value=round(runoff_m3s, 2),
            unit="m3/s",
            threshold=0.40,
            contribution_score=round(score, 3),
            contribution=contribution,
            explanation=explanation,
        )

    def determine_primary_cause(
        self,
        factors: List[ContributingFactor],
        depth_cm: float,
        risk_level: FloodRiskLevel,
    ) -> Tuple[str, Optional[str]]:
        """
        Derives the primary and secondary contributing causes based on scored factors and hydraulic state.
        Never hardcoded; strictly determined from attribution score rankings and physical triggers.
        """
        f_map = {f.factor: f for f in factors}
        rain_f = f_map.get("Rainfall Intensity")

        if depth_cm <= 0.0 or (rain_f and rain_f.value <= 0.0):
            return "Nominal Conditions / Zero Inundation", None

        if depth_cm <= 2.0 or risk_level == FloodRiskLevel.LOW:
            top_elev = f_map.get("Terrain Elevation & Slope")
            if top_elev and top_elev.value > 30.0:
                return "Elevated Terrain Runoff Shedding", None
            return "Nominal Drainage / Minimal Inundation", None

        # Sorted factors by contribution score descending
        sorted_factors = sorted(factors, key=lambda f: f.contribution_score, reverse=True)
        top = sorted_factors[0]
        second = sorted_factors[1] if len(sorted_factors) > 1 else None

        f_map = {f.factor: f for f in factors}
        surcharge = f_map.get("Drainage Surcharge")
        utilization = f_map.get("Drainage Utilization")
        blockage = f_map.get("Drainage Blockage")
        terrain = f_map.get("Terrain Elevation & Slope")
        rainfall = f_map.get("Rainfall Intensity")

        # 1. Drainage Surcharge is a critical, direct flood catalyst
        if surcharge and surcharge.value > 0.10:
            if blockage and blockage.value >= 25.0:
                primary = "Drainage Surcharge Induced by Conduit Blockage"
            elif utilization and utilization.value >= 100.0:
                primary = "Drainage Surcharge from Pipe Overload"
            else:
                primary = "Drainage Surcharge Overflow"
            secondary = top.factor if top.factor != "Drainage Surcharge" else (second.factor if second else None)
            return primary, secondary

        # 2. Pipe utilization overload without active surcharge yet
        if utilization and utilization.value >= 90.0:
            if blockage and blockage.value >= 25.0:
                primary = "Drainage Capacity Choked by Conduit Blockage"
            elif rainfall and rainfall.value >= 70.0:
                primary = "Combined Heavy Rainfall and Drainage Overload"
            else:
                primary = "Drainage Capacity Overload"
            secondary = top.factor if top.factor != "Drainage Utilization" else (second.factor if second else None)
            return primary, secondary

        # 3. Severe conduit blockage
        if blockage and blockage.value >= 30.0 and blockage.contribution_score >= 0.60:
            primary = "Drainage Conduit Blockage"
            secondary = top.factor if top.factor != "Drainage Blockage" else (second.factor if second else None)
            return primary, secondary

        # 4. Low-lying terrain accumulation
        if terrain and terrain.contribution_score >= 0.70 and top.factor == "Terrain Elevation & Slope":
            if rainfall and rainfall.value >= 60.0:
                primary = "Ponding in Low-Lying Depression Under Heavy Rain"
            else:
                primary = "Low-Lying Topographical Retention"
            secondary = second.factor if second else None
            return primary, secondary

        # 5. Extreme rainfall rate
        if rainfall and rainfall.value >= 75.0 and top.factor == "Rainfall Intensity":
            primary = "Torrential Rainfall Intensity"
            secondary = second.factor if second else None
            return primary, secondary

        # Default to highest scored factor's name
        primary = top.factor
        secondary = second.factor if second else None
        return primary, secondary

    def synthesize_summary_explanation(
        self,
        zone_name: str,
        zone_id: str,
        risk_level: FloodRiskLevel,
        depth_cm: float,
        primary_cause: str,
        factors: List[ContributingFactor],
    ) -> str:
        """Synthesizes human-readable operational briefing text from actual hydraulic indicators."""
        f_map = {f.factor: f for f in factors}
        rain_val = f_map.get("Rainfall Intensity").value if "Rainfall Intensity" in f_map else 0.0
        util_val = f_map.get("Drainage Utilization").value if "Drainage Utilization" in f_map else 0.0
        sur_val = f_map.get("Drainage Surcharge").value if "Drainage Surcharge" in f_map else 0.0
        block_val = f_map.get("Drainage Blockage").value if "Drainage Blockage" in f_map else 0.0
        elev_val = f_map.get("Terrain Elevation & Slope").value if "Terrain Elevation & Slope" in f_map else 0.0

        if depth_cm <= 2.0 or risk_level == FloodRiskLevel.LOW:
            return (
                f"Zone {zone_id} ({zone_name}) is at LOW flood risk with nominal surface water depth ({depth_cm:.1f} cm). "
                f"Topographical elevation ({elev_val:.1f} m) and adequate drainage capacity (utilization {util_val:.1f}%) "
                f"allow rainfall ({rain_val:.1f} mm/hr) to discharge without surface surcharge."
            )

        # High or Moderate risk text synthesis
        narrative = (
            f"Zone {zone_id} ({zone_name}) is at {risk_level.value} flood risk with an estimated surface depth of {depth_cm:.1f} cm. "
            f"The primary contributing factor is {primary_cause}."
        )

        supporting_details = []
        if sur_val > 0.0:
            supporting_details.append(f"uncontained drainage surcharge of {sur_val:.2f} m³/s")
        if util_val >= 80.0:
            supporting_details.append(f"exhausted pipe capacity ({util_val:.1f}% utilization)")
        if block_val >= 15.0:
            supporting_details.append(f"{block_val:.1f}% conduit blockage")
        if elev_val < 15.0:
            supporting_details.append(f"low-lying elevation ({elev_val:.1f} m)")
        if rain_val >= 50.0:
            supporting_details.append(f"sustained heavy rainfall of {rain_val:.1f} mm/hr")

        if supporting_details:
            narrative += f" Key drivers include {', '.join(supporting_details)}."

        return narrative

    def explain_zone(
        self,
        zone_data: Dict[str, Any],
        ml_prediction: Optional[Dict[str, Any]] = None,
    ) -> ZoneExplanation:
        """
        Analyzes a single zone's complete hydraulic and ML state and generates a structured ZoneExplanation.
        """
        zone_id = str(zone_data.get("zone_id", ""))
        name = str(zone_data.get("name", ""))
        raw_risk = zone_data.get("risk_level", FloodRiskLevel.LOW)
        risk_level = FloodRiskLevel(raw_risk) if isinstance(raw_risk, str) else raw_risk
        depth_cm = float(zone_data.get("flood_depth_cm", 0.0))

        # Evaluate individual drivers
        factors: List[ContributingFactor] = [
            self.evaluate_rainfall_factor(float(zone_data.get("rainfall_intensity_mm_hr", 0.0))),
            self.evaluate_drainage_utilization_factor(float(zone_data.get("drainage_utilization_percent", 0.0))),
            self.evaluate_surcharge_factor(
                float(zone_data.get("excess_flow_m3s", 0.0)),
                bool(zone_data.get("is_surcharged", False)),
            ),
            self.evaluate_blockage_factor(float(zone_data.get("blockage_percent", 0.0))),
            self.evaluate_terrain_factor(
                float(zone_data.get("elevation_m", 25.0)),
                float(zone_data.get("slope_percent", 2.0)),
                bool(zone_data.get("is_low_lying", False)),
            ),
            self.evaluate_runoff_factor(float(zone_data.get("runoff_discharge_m3s", 0.0))),
        ]

        # Sort factors by contribution score descending
        factors.sort(key=lambda f: f.contribution_score, reverse=True)

        primary_cause, secondary_cause = self.determine_primary_cause(factors, depth_cm, risk_level)
        summary_exp = self.synthesize_summary_explanation(
            zone_name=name,
            zone_id=zone_id,
            risk_level=risk_level,
            depth_cm=depth_cm,
            primary_cause=primary_cause,
            factors=factors,
        )

        evidence = {
            "rainfall_intensity_mm_hr": zone_data.get("rainfall_intensity_mm_hr"),
            "elevation_m": zone_data.get("elevation_m"),
            "slope_percent": zone_data.get("slope_percent"),
            "is_low_lying": zone_data.get("is_low_lying"),
            "runoff_discharge_m3s": zone_data.get("runoff_discharge_m3s"),
            "drainage_capacity_m3s": zone_data.get("drainage_capacity_m3s"),
            "drainage_effective_capacity_m3s": zone_data.get("drainage_effective_capacity_m3s"),
            "drainage_utilization_percent": zone_data.get("drainage_utilization_percent"),
            "blockage_percent": zone_data.get("blockage_percent"),
            "excess_flow_m3s": zone_data.get("excess_flow_m3s"),
            "is_surcharged": zone_data.get("is_surcharged"),
            "flood_depth_cm": depth_cm,
            "risk_level": risk_level.value,
        }

        ml_insights = None
        if ml_prediction:
            ml_depth = ml_prediction.get("predicted_flood_depth_cm", 0.0)
            delta = round(ml_depth - depth_cm, 1)
            ml_insights = {
                "ml_predicted_depth_cm": ml_depth,
                "ml_predicted_risk": ml_prediction.get("predicted_risk_level"),
                "ml_flood_probability": ml_prediction.get("flood_probability"),
                "ml_confidence": ml_prediction.get("model_confidence"),
                "physics_agreement": "STRONG" if abs(delta) <= 5.0 else ("MODERATE" if abs(delta) <= 15.0 else "DIVERGENT"),
                "depth_delta_cm": delta,
            }

        return ZoneExplanation(
            zone_id=zone_id,
            name=name,
            risk_level=risk_level,
            flood_depth_cm=depth_cm,
            primary_cause=primary_cause,
            secondary_cause=secondary_cause,
            summary_explanation=summary_exp,
            contributing_factors=factors,
            evidence=evidence,
            ml_insights=ml_insights,
            data_provenance="RULE-BASED EXPLANATION FROM MODEL-DERIVED AND DEMO-SIMULATED INPUTS",
            methodology_note="Transparent multi-factor engineering attribution scoring. Does not claim formal empirical causal proof.",
        )


# Global singleton instance
default_explain_engine = ExplainEngine()
