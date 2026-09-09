"""Rainfall calculation and forecast processing engine."""
from typing import List, Optional
from backend.models.rainfall_models import (
    CurrentRainfallResponse,
    DataSourceType,
    ForecastResponse,
    RainfallPoint,
)
from backend.services.rainfall_service import (
    InvalidRainfallDataFormatError,
    RainfallService,
    default_rainfall_service,
)


class RainfallEngine:
    """Core engine for processing rainfall observations and generating 0-3 hour nowcasts."""

    def __init__(self, service: Optional[RainfallService] = None):
        self.service = service or default_rainfall_service

    def get_validated_series(self) -> List[RainfallPoint]:
        """Loads and validates all rainfall points in chronological order."""
        data = self.service.load_dataset()
        raw_series = data.get("series", [])
        if not raw_series:
            raise InvalidRainfallDataFormatError("Rainfall series cannot be empty")

        points: List[RainfallPoint] = []
        for item in raw_series:
            if not isinstance(item, dict):
                raise InvalidRainfallDataFormatError(f"Series element must be a dictionary, got: {type(item)}")
            # Pydantic model validation handles range checks
            point = RainfallPoint(
                offset_minutes=item.get("offset_minutes", 0),
                intensity_mm_per_hr=float(item.get("intensity_mm_per_hr", 0.0)),
                timestamp=item.get("timestamp")
            )
            points.append(point)

        # Sort strictly by offset_minutes ascending
        points.sort(key=lambda p: p.offset_minutes)
        return points

    def determine_trend(self, points: List[RainfallPoint]) -> str:
        """Determines the short-term trend (increasing, decreasing, peak, stable)."""
        if len(points) < 2:
            return "stable"

        first = points[0].intensity_mm_per_hr
        second = points[1].intensity_mm_per_hr

        # Check if current is already highest
        max_intensity = max(p.intensity_mm_per_hr for p in points)
        if first == max_intensity:
            return "peak"
        elif second > first:
            return "increasing"
        elif second < first:
            return "decreasing"
        return "stable"

    def get_current_rainfall(self) -> CurrentRainfallResponse:
        """Calculates current rainfall status and recent observations."""
        data = self.service.load_dataset()
        points = self.get_validated_series()

        current_pt = points[0]
        peak_intensity = max(p.intensity_mm_per_hr for p in points)
        trend = self.determine_trend(points)

        return CurrentRainfallResponse(
            location=data.get("location", "Urban Catchment"),
            unit=data.get("unit", "mm/hr"),
            data_type=data.get("data_type", DataSourceType.DEMO_SIMULATED.value),
            generated_at=data.get("generated_at", "2026-09-09T00:00:00Z"),
            current_intensity_mm_per_hr=current_pt.intensity_mm_per_hr,
            peak_intensity_mm_per_hr=peak_intensity,
            trend=trend,
            recent_observations=points,
            source_note="Demo simulated data for prototyping; not a live radar observation."
        )

    def get_forecast(self, horizon_minutes: int = 180) -> ForecastResponse:
        """Generates 0-3 hour rainfall forecast series up to specified horizon."""
        data = self.service.load_dataset()
        points = self.get_validated_series()

        # Slice series within forecast horizon
        forecast_points = [p for p in points if p.offset_minutes <= horizon_minutes]
        if not forecast_points:
            raise InvalidRainfallDataFormatError(f"No forecast points within horizon of {horizon_minutes} minutes")

        # Determine step size
        if len(forecast_points) > 1:
            time_step = forecast_points[1].offset_minutes - forecast_points[0].offset_minutes
        else:
            time_step = 30

        # Find peak forecast point
        peak_point = max(forecast_points, key=lambda p: p.intensity_mm_per_hr)

        return ForecastResponse(
            location=data.get("location", "Urban Catchment"),
            unit=data.get("unit", "mm/hr"),
            data_type=data.get("data_type", DataSourceType.DEMO_SIMULATED.value),
            generated_at=data.get("generated_at", "2026-09-09T00:00:00Z"),
            forecast_horizon_minutes=horizon_minutes,
            time_step_minutes=time_step,
            forecast_series=forecast_points,
            peak_forecast_intensity_mm_per_hr=peak_point.intensity_mm_per_hr,
            peak_forecast_offset_minutes=peak_point.offset_minutes,
            source_note="Demo simulated nowcast curve for prototyping; not live meteorological radar output."
        )

    def interpolate_intensity(self, offset_minutes: int) -> float:
        """Interpolates rainfall intensity at an arbitrary time offset (useful for physics engines)."""
        points = self.get_validated_series()
        if not points:
            return 0.0

        if offset_minutes <= points[0].offset_minutes:
            return points[0].intensity_mm_per_hr
        if offset_minutes >= points[-1].offset_minutes:
            return points[-1].intensity_mm_per_hr

        # Linear interpolation between adjacent bounding points
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            if p1.offset_minutes <= offset_minutes <= p2.offset_minutes:
                delta_t = p2.offset_minutes - p1.offset_minutes
                if delta_t == 0:
                    return p1.intensity_mm_per_hr
                fraction = (offset_minutes - p1.offset_minutes) / delta_t
                return p1.intensity_mm_per_hr + fraction * (p2.intensity_mm_per_hr - p1.intensity_mm_per_hr)

        return points[-1].intensity_mm_per_hr


# Global singleton instance
default_rainfall_engine = RainfallEngine()
