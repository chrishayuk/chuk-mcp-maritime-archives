"""MCP tools for track speed analytics — compute, aggregate, and compare."""

import logging

from ...constants import SuccessMessages
from ...core.cliwoc_tracks import (
    aggregate_track_speeds,
    compare_speed_groups,
    compute_track_speeds,
)
from ...models import (
    DailySpeed,
    ErrorResponse,
    SpeedAggregationGroup,
    SpeedComparisonResponse,
    TrackSpeedAggregationResponse,
    TrackSpeedsResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_analytics_tools(mcp: object, manager: object) -> None:
    """Register track analytics tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_compute_track_speeds(
        voyage_id: int,
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        output_mode: str = "json",
    ) -> str:
        """
        Compute daily sailing speeds for a single CLIWOC voyage.

        Calculates haversine distance between consecutive daily logbook
        positions and returns speed in km/day. Optionally filters by
        geographic bounding box and speed bounds.

        Args:
            voyage_id: CLIWOC voyage ID (from maritime_search_tracks)
            lat_min: Minimum latitude for position filtering
            lat_max: Maximum latitude for position filtering
            lon_min: Minimum longitude for position filtering
            lon_max: Maximum longitude for position filtering
            min_speed_km_day: Minimum speed to include (default: 5.0,
                filters out anchored/drifting)
            max_speed_km_day: Maximum speed to include (default: 400.0,
                filters out data errors)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with daily speed observations for the voyage

        Tips for LLMs:
            - Get voyage_id from maritime_search_tracks results
            - Use lat/lon bounds to focus on a specific ocean region
            - Speeds are in km/day (a sailing ship typically does 100-300 km/day)
            - Wind-driven: faster speeds indicate stronger winds
            - Use maritime_aggregate_track_speeds for bulk analysis across
              many voyages
        """
        try:
            result = compute_track_speeds(
                voyage_id=voyage_id,
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
            )

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=f"CLIWOC voyage {voyage_id} not found. "
                        "Use maritime_search_tracks to find valid voyage IDs."
                    ),
                    output_mode,
                )

            speeds = [
                DailySpeed(
                    date=s["date"],
                    lat=s["lat"],
                    lon=s["lon"],
                    km_day=s["km_day"],
                )
                for s in result["speeds"]
            ]

            return format_response(
                TrackSpeedsResponse(
                    voyage_id=result["voyage_id"],
                    ship_name=result.get("ship_name"),
                    nationality=result.get("nationality"),
                    observation_count=result["observation_count"],
                    mean_km_day=result["mean_km_day"],
                    speeds=speeds,
                    message=SuccessMessages.TRACK_SPEEDS_COMPUTED.format(
                        result["observation_count"], voyage_id
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Track speed computation failed for voyage %s: %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Track speed computation failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_aggregate_track_speeds(
        group_by: str = "decade",
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        nationality: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        direction: str | None = None,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        output_mode: str = "json",
    ) -> str:
        """
        Aggregate daily sailing speeds across all matching CLIWOC tracks.

        Computes haversine-based daily speeds from consecutive logbook
        positions, filters by geographic region, and aggregates by the
        requested dimension. Returns descriptive statistics per group.

        Args:
            group_by: Grouping dimension. Options:
                - "decade" — group by decade (e.g., 1750, 1760, ...)
                - "year" — group by individual year (e.g., 1783, 1784, ...)
                - "month" — group by month (1-12)
                - "direction" — group by eastbound/westbound
                - "nationality" — group by ship nationality (NL, UK, ES, ...)
            lat_min: Minimum latitude for position bounding box
            lat_max: Maximum latitude for position bounding box
            lon_min: Minimum longitude for position bounding box
            lon_max: Maximum longitude for position bounding box
            nationality: Filter tracks by nationality code (NL, UK, ES, FR, etc.)
            year_start: Filter tracks starting from this year
            year_end: Filter tracks ending at this year
            direction: Filter observations by "eastbound" or "westbound"
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with per-group statistics (n, mean, median, std,
            95% CI, percentiles)

        Tips for LLMs:
            - Use lat_min=-50, lat_max=-30 for the Roaring Forties wind belt
            - group_by="decade" shows speed trends over time
            - group_by="month" reveals seasonal wind patterns
            - group_by="direction" shows eastbound vs westbound asymmetry
              (confirms wind direction)
            - group_by="nationality" controls for shipbuilding differences
            - Combine direction="eastbound" with group_by="decade" for the
              clearest wind signal (ships running before the wind)
            - Use maritime_compare_speed_groups for statistical significance
              testing between time periods
        """
        try:
            result = aggregate_track_speeds(
                group_by=group_by,
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                nationality=nationality,
                year_start=year_start,
                year_end=year_end,
                direction=direction,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
            )

            groups = [
                SpeedAggregationGroup(
                    group_key=g["group_key"],
                    n=g["n"],
                    mean_km_day=g["mean_km_day"],
                    median_km_day=g["median_km_day"],
                    std_km_day=g["std_km_day"],
                    ci_lower=g["ci_lower"],
                    ci_upper=g["ci_upper"],
                    p25_km_day=g.get("p25_km_day"),
                    p75_km_day=g.get("p75_km_day"),
                )
                for g in result["groups"]
            ]

            return format_response(
                TrackSpeedAggregationResponse(
                    total_observations=result["total_observations"],
                    total_voyages=result["total_voyages"],
                    group_by=result["group_by"],
                    groups=groups,
                    latitude_band=result.get("latitude_band"),
                    longitude_band=result.get("longitude_band"),
                    direction_filter=result.get("direction_filter"),
                    nationality_filter=result.get("nationality_filter"),
                    message=SuccessMessages.SPEEDS_AGGREGATED.format(
                        result["total_observations"],
                        result["total_voyages"],
                        group_by,
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Track speed aggregation failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Track speed aggregation failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_compare_speed_groups(
        group1_years: str,
        group2_years: str,
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        nationality: str | None = None,
        direction: str | None = None,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        output_mode: str = "json",
    ) -> str:
        """
        Compare sailing speed distributions between two time periods.

        Computes daily speeds for each period, then runs a Mann-Whitney U
        test to determine if the difference is statistically significant.
        Also returns Cohen's d effect size.

        Args:
            group1_years: First period as "YYYY/YYYY" (e.g., "1750/1789")
            group2_years: Second period as "YYYY/YYYY" (e.g., "1820/1859")
            lat_min: Minimum latitude for position bounding box
            lat_max: Maximum latitude for position bounding box
            lon_min: Minimum longitude for position bounding box
            lon_max: Maximum longitude for position bounding box
            nationality: Filter tracks by nationality code
            direction: Filter by "eastbound" or "westbound"
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with group statistics, Mann-Whitney U, z-score,
            p-value, and Cohen's d effect size

        Tips for LLMs:
            - Compare "cold" vs "warm" periods to detect climate-driven
              wind changes (e.g., "1750/1789" vs "1820/1859")
            - p < 0.05 indicates statistically significant difference
            - Cohen's d > 0.8 indicates a large effect size
            - Use with direction="eastbound" for clearest wind signal
            - Combine with maritime_aggregate_track_speeds to understand
              the trend before testing significance
        """
        try:
            result = compare_speed_groups(
                group1_years=group1_years,
                group2_years=group2_years,
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                nationality=nationality,
                direction=direction,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
            )

            return format_response(
                SpeedComparisonResponse(
                    group1_label=result["group1_label"],
                    group1_n=result["group1_n"],
                    group1_mean=result["group1_mean"],
                    group1_std=result["group1_std"],
                    group2_label=result["group2_label"],
                    group2_n=result["group2_n"],
                    group2_mean=result["group2_mean"],
                    group2_std=result["group2_std"],
                    mann_whitney_u=result["mann_whitney_u"],
                    z_score=result["z_score"],
                    p_value=result["p_value"],
                    significant=result["significant"],
                    effect_size=result["effect_size"],
                    message=SuccessMessages.SPEED_GROUPS_COMPARED.format(
                        result["group1_n"],
                        result["group2_n"],
                        result["z_score"],
                        result["p_value"],
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Speed group comparison failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Speed group comparison failed"),
                output_mode,
            )
