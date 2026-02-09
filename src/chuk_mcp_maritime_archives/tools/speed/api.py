"""MCP tools for querying historical sailing speed profiles."""

import logging

from ...constants import ErrorMessages
from ...core.speed_profiles import get_speed_profile, list_profiled_routes
from ...models import (
    ErrorResponse,
    SegmentSpeedInfo,
    SpeedProfileResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_speed_tools(mcp: object, manager: object) -> None:
    """Register speed profile tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_speed_profile(
        route_id: str,
        departure_month: int | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Get historical sailing speed statistics for a route.

        Returns per-segment speed profiles derived from CLIWOC ship track
        data, including mean, median, and standard deviation of daily
        distances (km/day). Optionally filtered by departure month for
        seasonal variation.

        Args:
            route_id: Route identifier (e.g., "outward_outer", "return").
                Use maritime_list_routes to see available routes.
            departure_month: Optional month (1-12) for seasonal speed data.
                If not provided, returns all-months aggregate.
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with per-segment speed statistics

        Tips for LLMs:
            - Compare different months to see seasonal wind patterns
              (e.g., monsoon effects on Indian Ocean segments)
            - Use with maritime_estimate_position for more informed
              position estimation
            - High std_dev indicates variable conditions on a segment
            - Low sample_count means less reliable statistics
            - The mean_km_day can help assess whether a voyage was
              running ahead or behind schedule
        """
        try:
            profiles = get_speed_profile(route_id, departure_month)

            if not profiles:
                available = list_profiled_routes()
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.SPEED_PROFILE_NOT_FOUND.format(
                            route_id, ", ".join(available) or "none"
                        ),
                    ),
                    output_mode,
                )

            segments = [
                SegmentSpeedInfo(
                    segment_from=p["segment_from"],
                    segment_to=p["segment_to"],
                    departure_month=p.get("departure_month"),
                    sample_count=p["sample_count"],
                    mean_km_day=p["mean_km_day"],
                    median_km_day=p["median_km_day"],
                    std_dev_km_day=p["std_dev_km_day"],
                    min_km_day=p.get("min_km_day"),
                    max_km_day=p.get("max_km_day"),
                    p25_km_day=p.get("p25_km_day"),
                    p75_km_day=p.get("p75_km_day"),
                )
                for p in profiles
            ]

            month_str = f" (month {departure_month})" if departure_month else ""
            return format_response(
                SpeedProfileResponse(
                    route_id=route_id,
                    departure_month=departure_month,
                    segment_count=len(segments),
                    segments=segments,
                    notes=(
                        "Speed profiles derived from CLIWOC 2.1 ship track data. "
                        "Actual speeds varied with wind, currents, and ship condition."
                    ),
                    message=f"Speed profile for {route_id}{month_str}: {len(segments)} segments",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Speed profile lookup failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Speed profile lookup failed"),
                output_mode,
            )
