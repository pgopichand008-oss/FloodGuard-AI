"""Action Priority and Decision Engine ranking urban flood zones for municipal intervention."""
from typing import Any, Dict, List, Optional, Tuple

from backend.models.flood_models import FloodRiskLevel
from backend.models.priority_models import PriorityLevel, ZonePriority


class PriorityEngine:
    """Calculates multi-criteria action priority scores, assigns intervention urgency, and recommends field actions."""

    # Transparent engineering weights summing to 100.0 points
    WEIGHT_FLOOD_DEPTH: float = 40.0
    WEIGHT_DRAINAGE_OVERLOAD: float = 25.0
    WEIGHT_BLOCKAGE: float = 15.0
    WEIGHT_ML_HAZARD: float = 10.0
    WEIGHT_TOPOGRAPHY: float = 10.0

    # Deterministic priority classification thresholds
    THRESHOLD_CRITICAL: float = 75.0
    THRESHOLD_HIGH: float = 50.0
    THRESHOLD_MEDIUM: float = 25.0

    @classmethod
    def classify_priority_level(cls, score: float) -> PriorityLevel:
        """Maps continuous 0.0-100.0 priority score into categorical intervention level."""
        if score >= cls.THRESHOLD_CRITICAL:
            return PriorityLevel.CRITICAL
        elif score >= cls.THRESHOLD_HIGH:
            return PriorityLevel.HIGH
        elif score >= cls.THRESHOLD_MEDIUM:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW

    def calculate_depth_component(self, depth_cm: float, risk_level: FloodRiskLevel) -> float:
        """Calculates flood depth severity sub-score (0.0 to 40.0 points)."""
        if depth_cm <= 0.0:
            return 0.0

        base_score = self.WEIGHT_FLOOD_DEPTH * min(1.0, depth_cm / 50.0)
        return round(min(self.WEIGHT_FLOOD_DEPTH, base_score), 2)

    def calculate_drainage_component(
        self, utilization_pct: float, excess_flow_m3s: float, is_surcharged: bool
    ) -> Tuple[float, float, float]:
        """Calculates drainage stress and surcharge sub-score (0.0 to 25.0 points)."""
        # 1. Surcharge portion (15.0 points max)
        if excess_flow_m3s > 0.0:
            surcharge_pts = 15.0 * min(1.0, 0.40 + 0.60 * (excess_flow_m3s / 1.0))
        elif is_surcharged:
            surcharge_pts = 6.0
        else:
            surcharge_pts = 0.0

        # 2. Utilization portion (10.0 points max)
        if utilization_pct >= 100.0:
            util_pts = 10.0
        elif utilization_pct >= 50.0:
            util_pts = 10.0 * ((utilization_pct - 50.0) / 50.0)
        else:
            util_pts = 10.0 * 0.10 * (utilization_pct / 50.0)

        total_pts = round(min(self.WEIGHT_DRAINAGE_OVERLOAD, surcharge_pts + util_pts), 2)
        return total_pts, round(surcharge_pts, 2), round(util_pts, 2)

    def calculate_blockage_component(self, blockage_pct: float) -> float:
        """Calculates infrastructure blockage sub-score (0.0 to 15.0 points)."""
        clamped_blockage = max(0.0, min(100.0, blockage_pct))
        pts = self.WEIGHT_BLOCKAGE * (clamped_blockage / 100.0)
        return round(pts, 2)

    def calculate_ml_hazard_component(
        self, ml_prob: Optional[float], depth_cm: float, peak_depth_cm: float
    ) -> float:
        """Calculates storm progression and ML hazard consensus sub-score (0.0 to 10.0 points)."""
        if ml_prob is not None:
            pts = self.WEIGHT_ML_HAZARD * max(0.0, min(1.0, ml_prob))
        elif peak_depth_cm > depth_cm and depth_cm > 0.0:
            growth_ratio = (peak_depth_cm - depth_cm) / max(5.0, depth_cm)
            pts = self.WEIGHT_ML_HAZARD * min(1.0, growth_ratio)
        else:
            pts = 0.0

        return round(pts, 2)

    def calculate_topography_component(
        self, is_low_lying: bool, elevation_m: float, slope_pct: float
    ) -> float:
        """Calculates natural topographical retention vulnerability sub-score (0.0 to 10.0 points)."""
        pts = 6.0 if is_low_lying else 1.0

        if elevation_m < 15.0:
            pts += 2.5
        elif elevation_m < 25.0:
            pts += 1.0

        if slope_pct < 1.0:
            pts += 1.5
        elif slope_pct > 3.5:
            pts = max(0.5, pts - 1.5)

        return round(min(self.WEIGHT_TOPOGRAPHY, pts), 2)

    @staticmethod
    def recommend_action(
        depth_cm: float,
        blockage_pct: float,
        excess_flow_m3s: float,
        is_surcharged: bool,
        utilization_pct: float,
        priority_level: PriorityLevel,
    ) -> str:
        """Generates context-specific, condition-driven operational field action recommendations."""
        if (is_surcharged or excess_flow_m3s > 0.25) and blockage_pct >= 20.0:
            return (
                "Deploy emergency jetting and vactor units to clear conduit blockage and "
                "relieve pressurized surcharge overflow."
            )
        elif is_surcharged or excess_flow_m3s > 0.20:
            return (
                "Deploy high-capacity mobile bypass pumping units and establish surface channels "
                "to relieve saturated trunk drainage."
            )
        elif blockage_pct >= 25.0:
            return (
                "Dispatch municipal maintenance crew to desilt and unclog stormwater inlets "
                "and culverts before next storm pulse."
            )
        elif depth_cm >= 30.0:
            return (
                "Erect temporary flood barriers, divert vehicular traffic away from inundated corridor, "
                "and stage rapid dewatering pumps."
            )
        elif depth_cm >= 15.0:
            return (
                "Deploy flood hazard warning signs, monitor vulnerable low-lying access points, "
                "and stage rapid-response drainage teams."
            )
        elif utilization_pct >= 80.0:
            return (
                "Inspect storm grates, monitor conduit capacity saturation, and prepare standby bypass operations."
            )
        elif priority_level == PriorityLevel.MEDIUM:
            return "Increase localized patrol frequency and inspect inlet grates for debris accumulation."
        else:
            return "Continue routine sensor monitoring; no immediate field intervention required."

    @staticmethod
    def generate_priority_reason(
        zone_name: str,
        score: float,
        level: PriorityLevel,
        depth_cm: float,
        excess_m3s: float,
        util_pct: float,
        blockage_pct: float,
        is_low_lying: bool,
    ) -> str:
        """Synthesizes human-readable engineering rationale justifying the assigned priority."""
        if depth_cm <= 1.0 and excess_m3s <= 0.0 and util_pct < 30.0:
            return (
                f"{zone_name}: Assigned {level.value} priority (score {score:.1f}/100) due to nominal surface depth ({depth_cm:.1f} cm), "
                f"ample available drainage capacity ({util_pct:.1f}% utilization), and zero pipe surcharge."
            )

        drivers = []
        if depth_cm >= 15.0:
            drivers.append(f"hazardous flood depth of {depth_cm:.1f} cm")
        elif depth_cm > 2.0:
            drivers.append(f"surface water depth of {depth_cm:.1f} cm")

        if excess_m3s > 0.0:
            drivers.append(f"{excess_m3s:.2f} m³/s of pressurized drainage surcharge")
        elif util_pct >= 80.0:
            drivers.append(f"high drainage utilization ({util_pct:.1f}%)")

        if blockage_pct >= 15.0:
            drivers.append(f"{blockage_pct:.1f}% conduit blockage")

        if is_low_lying:
            drivers.append("vulnerable low-lying terrain depression")

        driver_text = ", ".join(drivers) if drivers else "elevated local hydrological indicators"
        return f"{zone_name}: Assigned {level.value} priority (score {score:.1f}/100) driven by {driver_text}."

    def evaluate_zone_priority(
        self,
        zone_dict: Dict[str, Any],
        ml_prediction: Optional[Dict[str, Any]] = None,
        rank: int = 1,
    ) -> ZonePriority:
        """Evaluates multi-criteria priority score and packages ZonePriority profile."""
        zone_id = str(zone_dict.get("zone_id", ""))
        name = str(zone_dict.get("name", ""))
        depth_cm = float(zone_dict.get("flood_depth_cm", 0.0))
        raw_risk = zone_dict.get("risk_level", FloodRiskLevel.LOW)
        risk_level = FloodRiskLevel(raw_risk) if isinstance(raw_risk, str) else raw_risk

        util_pct = float(zone_dict.get("drainage_utilization_percent", 0.0))
        blockage_pct = float(zone_dict.get("blockage_percent", 0.0))
        excess_m3s = float(zone_dict.get("excess_flow_m3s", 0.0))
        is_surcharged = bool(zone_dict.get("is_surcharged", False))
        is_low_lying = bool(zone_dict.get("is_low_lying", False))
        elevation_m = float(zone_dict.get("elevation_m", 25.0))
        slope_pct = float(zone_dict.get("slope_percent", 2.0))
        peak_depth = float(zone_dict.get("peak_depth_cm", depth_cm))
        rain_mm_hr = float(zone_dict.get("rainfall_intensity_mm_hr", 0.0))

        ml_prob = None
        if ml_prediction:
            ml_prob = ml_prediction.get("flood_probability")

        # Zero guard
        if depth_cm <= 0.0 and rain_mm_hr <= 0.0 and excess_m3s <= 0.0 and not is_surcharged:
            return ZonePriority(
                zone_id=zone_id,
                zone_name=name,
                rank=rank,
                priority_score=0.0,
                priority_level=PriorityLevel.LOW,
                flood_depth_cm=0.0,
                risk_level=FloodRiskLevel.LOW,
                drainage_utilization_percent=util_pct,
                blockage_percent=blockage_pct,
                excess_flow_m3s=0.0,
                is_surcharged=False,
                recommended_action="Continue routine sensor monitoring; no immediate field intervention required.",
                reason="Assigned LOW priority (score 0.0/100): Zero precipitation and zero inundation observed.",
                score_breakdown={
                    "flood_depth": 0.0,
                    "drainage_overload": 0.0,
                    "blockage": 0.0,
                    "ml_hazard": 0.0,
                    "topography": 0.0,
                },
                data_provenance="DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS",
            )

        # 1. Depth score
        s_depth = self.calculate_depth_component(depth_cm, risk_level)

        # 2. Drainage score
        s_drainage, s_surcharge, s_util = self.calculate_drainage_component(
            util_pct, excess_m3s, is_surcharged
        )

        # 3. Blockage score
        s_blockage = self.calculate_blockage_component(blockage_pct)

        # 4. ML / Storm progression score
        s_ml = self.calculate_ml_hazard_component(ml_prob, depth_cm, peak_depth)

        # 5. Topography score
        s_topo = self.calculate_topography_component(is_low_lying, elevation_m, slope_pct)

        total_score = round(min(100.0, max(0.0, s_depth + s_drainage + s_blockage + s_ml + s_topo)), 1)
        priority_level = self.classify_priority_level(total_score)

        rec_action = self.recommend_action(
            depth_cm=depth_cm,
            blockage_pct=blockage_pct,
            excess_flow_m3s=excess_m3s,
            is_surcharged=is_surcharged,
            utilization_pct=util_pct,
            priority_level=priority_level,
        )

        reason_text = self.generate_priority_reason(
            zone_name=name,
            score=total_score,
            level=priority_level,
            depth_cm=depth_cm,
            excess_m3s=excess_m3s,
            util_pct=util_pct,
            blockage_pct=blockage_pct,
            is_low_lying=is_low_lying,
        )

        return ZonePriority(
            zone_id=zone_id,
            zone_name=name,
            rank=rank,
            priority_score=total_score,
            priority_level=priority_level,
            flood_depth_cm=depth_cm,
            risk_level=risk_level,
            drainage_utilization_percent=util_pct,
            blockage_percent=blockage_pct,
            excess_flow_m3s=excess_m3s,
            is_surcharged=is_surcharged,
            recommended_action=rec_action,
            reason=reason_text,
            score_breakdown={
                "flood_depth": s_depth,
                "drainage_overload": s_drainage,
                "blockage": s_blockage,
                "ml_hazard": s_ml,
                "topography": s_topo,
            },
            data_provenance="DECISION PRIORITY DERIVED FROM MODEL-DERIVED FLOOD, DRAINAGE AND DEMO INPUTS",
        )


# Global singleton instance
default_priority_engine = PriorityEngine()
