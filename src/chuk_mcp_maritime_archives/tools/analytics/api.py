"""MCP tools for track speed analytics — compute, aggregate, and compare."""

import logging

from ...constants import SuccessMessages
from ...core.cliwoc_tracks import (
    aggregate_track_speeds,
    aggregate_track_tortuosity,
    compare_speed_groups,
    compute_track_speeds,
    compute_track_tortuosity,
    did_speed_test,
    wind_rose,
)
from ...models import (
    BeaufortCount,
    DailySpeed,
    DiDSpeedTestResponse,
    ErrorResponse,
    SpeedAggregationGroup,
    SpeedComparisonResponse,
    TortuosityAggregationGroup,
    TortuosityAggregationResponse,
    TortuosityComparisonResult,
    TrackSpeedAggregationResponse,
    TrackSpeedsResponse,
    TrackTortuosityResponse,
    WindRoseResponse,
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
        month_start: int | None = None,
        month_end: int | None = None,
        aggregate_by: str = "observation",
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        wind_force_min: int | None = None,
        wind_force_max: int | None = None,
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
                - "beaufort" — group by Beaufort wind force (0-12)
            lat_min: Minimum latitude for position bounding box
            lat_max: Maximum latitude for position bounding box
            lon_min: Minimum longitude for position bounding box
            lon_max: Maximum longitude for position bounding box
            nationality: Filter tracks by nationality code (NL, UK, ES, FR, etc.)
            year_start: Filter tracks starting from this year
            year_end: Filter tracks ending at this year
            direction: Filter observations by "eastbound" or "westbound"
            month_start: Filter by start month (1-12). Supports wrap-around
                with month_end (e.g., month_start=11, month_end=2 = Nov-Feb)
            month_end: Filter by end month (1-12). Used with month_start
            aggregate_by: Unit of analysis — "observation" (default, each
                daily speed is a data point) or "voyage" (one mean speed
                per voyage, statistically independent samples)
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            wind_force_min: Minimum Beaufort force (0-12). Requires wind data
            wind_force_max: Maximum Beaufort force (0-12). Requires wind data
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with per-group statistics (n, mean, median, std,
            95% CI, percentiles)

        Tips for LLMs:
            - Use lat_min=-50, lat_max=-30 for the Roaring Forties wind belt
            - group_by="decade" shows speed trends over time
            - group_by="direction" shows eastbound vs westbound asymmetry
            - group_by="beaufort" shows speed profiles by wind force
            - Use aggregate_by="voyage" for statistically independent samples
            - Use wind_force_min/max to condition on wind strength
            - Use maritime_compare_speed_groups for significance testing
            - Use maritime_did_speed_test for direction x period interaction
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
                month_start=month_start,
                month_end=month_end,
                aggregate_by=aggregate_by,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
                wind_force_min=wind_force_min,
                wind_force_max=wind_force_max,
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
                    aggregate_by=result.get("aggregate_by", "observation"),
                    groups=groups,
                    latitude_band=result.get("latitude_band"),
                    longitude_band=result.get("longitude_band"),
                    direction_filter=result.get("direction_filter"),
                    nationality_filter=result.get("nationality_filter"),
                    month_start_filter=result.get("month_start_filter"),
                    month_end_filter=result.get("month_end_filter"),
                    wind_force_min_filter=result.get("wind_force_min_filter"),
                    wind_force_max_filter=result.get("wind_force_max_filter"),
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
        month_start: int | None = None,
        month_end: int | None = None,
        aggregate_by: str = "observation",
        include_samples: bool = False,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        wind_force_min: int | None = None,
        wind_force_max: int | None = None,
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
            month_start: Filter by start month (1-12). Supports wrap-around
            month_end: Filter by end month (1-12). Used with month_start
            aggregate_by: Unit of analysis — "observation" (default) or
                "voyage" (one mean per voyage, statistically independent)
            include_samples: If True, include raw speed arrays in response
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            wind_force_min: Minimum Beaufort force (0-12). Requires wind data
            wind_force_max: Maximum Beaufort force (0-12). Requires wind data
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with group statistics, Mann-Whitney U, z-score,
            p-value, and Cohen's d effect size

        Tips for LLMs:
            - Use aggregate_by="voyage" for statistically independent samples
            - Use wind_force_min/max to condition on Beaufort force
            - Use maritime_did_speed_test for formal direction x period interaction
            - p < 0.05 indicates statistically significant difference
            - Cohen's d > 0.8 indicates a large effect size
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
                month_start=month_start,
                month_end=month_end,
                aggregate_by=aggregate_by,
                include_samples=include_samples,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
                wind_force_min=wind_force_min,
                wind_force_max=wind_force_max,
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
                    aggregate_by=result.get("aggregate_by", "observation"),
                    group1_samples=result.get("group1_samples"),
                    group2_samples=result.get("group2_samples"),
                    month_start_filter=result.get("month_start_filter"),
                    month_end_filter=result.get("month_end_filter"),
                    wind_force_min_filter=result.get("wind_force_min_filter"),
                    wind_force_max_filter=result.get("wind_force_max_filter"),
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

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_did_speed_test(
        period1_years: str,
        period2_years: str,
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        nationality: str | None = None,
        month_start: int | None = None,
        month_end: int | None = None,
        aggregate_by: str = "voyage",
        n_bootstrap: int = 10000,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        wind_force_min: int | None = None,
        wind_force_max: int | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Formal 2x2 Difference-in-Differences test: direction x period.

        Tests whether the difference between eastbound and westbound speeds
        changed significantly between two time periods. A significant DiD
        means one direction gained more than the other — isolating wind
        changes from symmetric technology improvements.

        DiD = (period2_east - period1_east) - (period2_west - period1_west)

        Uses bootstrap resampling for confidence intervals and p-values.
        Defaults to voyage-level aggregation for statistically independent
        samples (daily observations within a voyage are autocorrelated).

        Args:
            period1_years: First period as "YYYY/YYYY" (e.g., "1750/1783")
            period2_years: Second period as "YYYY/YYYY" (e.g., "1784/1810")
            lat_min: Minimum latitude for position bounding box
            lat_max: Maximum latitude for position bounding box
            lon_min: Minimum longitude for position bounding box
            lon_max: Maximum longitude for position bounding box
            nationality: Filter tracks by nationality code
            month_start: Filter by start month (1-12). Supports wrap-around
            month_end: Filter by end month (1-12). Used with month_start
            aggregate_by: "voyage" (default, independent samples) or
                "observation" (more data but autocorrelated)
            n_bootstrap: Bootstrap iterations (default: 10000)
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            wind_force_min: Minimum Beaufort force (0-12). Requires wind data
            wind_force_max: Maximum Beaufort force (0-12). Requires wind data
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with 4-cell summary, marginal diffs, DiD estimate,
            bootstrap 95% CI, and p-value

        Tips for LLMs:
            - Always splits by direction (eastbound vs westbound)
            - Use lat_min=-50, lat_max=-30 for the Roaring Forties
            - Positive DiD = eastbound gained more = wind strengthened
            - Use wind_force_min/max for Beaufort-stratified DiD
            - Default aggregate_by="voyage" gives correct p-values
            - If DiD scales with Beaufort, that is genuine wind change
        """
        try:
            result = did_speed_test(
                period1_years=period1_years,
                period2_years=period2_years,
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                nationality=nationality,
                month_start=month_start,
                month_end=month_end,
                aggregate_by=aggregate_by,
                n_bootstrap=n_bootstrap,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
                wind_force_min=wind_force_min,
                wind_force_max=wind_force_max,
            )

            return format_response(
                DiDSpeedTestResponse(
                    period1_label=result["period1_label"],
                    period2_label=result["period2_label"],
                    aggregate_by=result["aggregate_by"],
                    n_bootstrap=result["n_bootstrap"],
                    period1_eastbound_n=result["period1_eastbound_n"],
                    period1_eastbound_mean=result["period1_eastbound_mean"],
                    period1_westbound_n=result["period1_westbound_n"],
                    period1_westbound_mean=result["period1_westbound_mean"],
                    period2_eastbound_n=result["period2_eastbound_n"],
                    period2_eastbound_mean=result["period2_eastbound_mean"],
                    period2_westbound_n=result["period2_westbound_n"],
                    period2_westbound_mean=result["period2_westbound_mean"],
                    eastbound_diff=result["eastbound_diff"],
                    westbound_diff=result["westbound_diff"],
                    did_estimate=result["did_estimate"],
                    did_ci_lower=result["did_ci_lower"],
                    did_ci_upper=result["did_ci_upper"],
                    did_p_value=result["did_p_value"],
                    significant=result["significant"],
                    latitude_band=result.get("latitude_band"),
                    longitude_band=result.get("longitude_band"),
                    nationality_filter=result.get("nationality_filter"),
                    month_start_filter=result.get("month_start_filter"),
                    month_end_filter=result.get("month_end_filter"),
                    wind_force_min_filter=result.get("wind_force_min_filter"),
                    wind_force_max_filter=result.get("wind_force_max_filter"),
                    message=SuccessMessages.DID_TEST_COMPLETE.format(
                        result["did_estimate"],
                        result["period1_eastbound_n"] + result["period1_westbound_n"],
                        result["period2_eastbound_n"] + result["period2_westbound_n"],
                        result["n_bootstrap"],
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("DiD speed test failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="DiD speed test failed"),
                output_mode,
            )

    # ------------------------------------------------------------------
    # Tortuosity tools
    # ------------------------------------------------------------------

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_track_tortuosity(
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
        Compute route tortuosity for a single CLIWOC voyage.

        Tortuosity = path_km / net_km. A value of 1.0 means perfectly
        direct; higher values indicate meandering. Compares actual sailed
        distance (sum of position-to-position haversine legs) to
        great-circle distance (first to last position in bbox).

        Args:
            voyage_id: CLIWOC voyage ID (from maritime_search_tracks)
            lat_min: Minimum latitude for bounding box
            lat_max: Maximum latitude for bounding box
            lon_min: Minimum longitude for bounding box
            lon_max: Maximum longitude for bounding box
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with path_km, net_km, tortuosity_r,
            inferred_direction, n_in_box

        Tips for LLMs:
            - Use lat_min=-50, lat_max=-30 for the Roaring Forties
            - Tortuosity ~1.0-1.1 = direct sailing, >1.3 = detours
            - Compare pre/post-chronometer voyages to test navigation
            - Use maritime_aggregate_track_tortuosity for bulk analysis
        """
        try:
            result = compute_track_tortuosity(
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
                        error=f"CLIWOC voyage {voyage_id} not found or insufficient "
                        "positions in bounding box."
                    ),
                    output_mode,
                )

            return format_response(
                TrackTortuosityResponse(
                    voyage_id=result["voyage_id"],
                    ship_name=result.get("ship_name"),
                    nationality=result.get("nationality"),
                    path_km=result["path_km"],
                    net_km=result["net_km"],
                    tortuosity_r=result["tortuosity_r"],
                    inferred_direction=result["inferred_direction"],
                    n_in_box=result["n_in_box"],
                    message=SuccessMessages.TRACK_TORTUOSITY_COMPUTED.format(
                        result["voyage_id"], result["tortuosity_r"]
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Tortuosity computation failed for voyage %s: %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Tortuosity computation failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_aggregate_track_tortuosity(
        group_by: str = "decade",
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        nationality: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        direction: str | None = None,
        month_start: int | None = None,
        month_end: int | None = None,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        min_positions: int = 5,
        period1_years: str | None = None,
        period2_years: str | None = None,
        n_bootstrap: int = 10000,
        output_mode: str = "json",
    ) -> str:
        """
        Aggregate route tortuosity across CLIWOC tracks with optional comparison.

        Tests the chronometer hypothesis: if marine chronometers improved
        navigation, tortuosity should decrease over time. If tortuosity stays
        constant while speed DiD shows asymmetric gains, that confirms wind
        change rather than better routing.

        Args:
            group_by: "decade", "year", "direction", "nationality"
            lat_min/lat_max/lon_min/lon_max: Bounding box
            nationality: Filter by nationality code
            year_start/year_end: Filter by year range
            direction: Filter by "eastbound" or "westbound"
            month_start/month_end: Month filter (supports wrap-around)
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            min_positions: Minimum positions in bbox (default: 5)
            period1_years: First period as "YYYY/YYYY" for comparison
            period2_years: Second period as "YYYY/YYYY" for comparison
            n_bootstrap: Bootstrap iterations (default: 10000)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with per-group tortuosity stats, optional comparison

        Tips for LLMs:
            - group_by="decade" to see tortuosity trends over time
            - Use direction="eastbound" vs "westbound" separately
            - period1_years/period2_years for formal comparison with CI
            - Combine with maritime_did_speed_test for complete decomposition
            - min_positions=5 filters out short transits
        """
        try:
            result = aggregate_track_tortuosity(
                group_by=group_by,
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                nationality=nationality,
                year_start=year_start,
                year_end=year_end,
                direction=direction,
                month_start=month_start,
                month_end=month_end,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
                min_positions=min_positions,
                period1_years=period1_years,
                period2_years=period2_years,
                n_bootstrap=n_bootstrap,
            )

            groups = [
                TortuosityAggregationGroup(
                    group_key=g["group_key"],
                    n=g["n"],
                    mean_tortuosity=g["mean_tortuosity"],
                    median_tortuosity=g["median_tortuosity"],
                    std_tortuosity=g["std_tortuosity"],
                    ci_lower=g["ci_lower"],
                    ci_upper=g["ci_upper"],
                    p25_tortuosity=g.get("p25_tortuosity"),
                    p75_tortuosity=g.get("p75_tortuosity"),
                )
                for g in result["groups"]
            ]

            comparison = None
            if result.get("comparison"):
                c = result["comparison"]
                comparison = TortuosityComparisonResult(
                    period1_label=c["period1_label"],
                    period1_n=c["period1_n"],
                    period1_mean=c["period1_mean"],
                    period2_label=c["period2_label"],
                    period2_n=c["period2_n"],
                    period2_mean=c["period2_mean"],
                    diff=c["diff"],
                    ci_lower=c["ci_lower"],
                    ci_upper=c["ci_upper"],
                    p_value=c["p_value"],
                    significant=c["significant"],
                )

            return format_response(
                TortuosityAggregationResponse(
                    total_voyages=result["total_voyages"],
                    min_positions_required=result["min_positions_required"],
                    group_by=result["group_by"],
                    groups=groups,
                    comparison=comparison,
                    latitude_band=result.get("latitude_band"),
                    longitude_band=result.get("longitude_band"),
                    direction_filter=result.get("direction_filter"),
                    nationality_filter=result.get("nationality_filter"),
                    month_start_filter=result.get("month_start_filter"),
                    month_end_filter=result.get("month_end_filter"),
                    message=SuccessMessages.TORTUOSITY_AGGREGATED.format(
                        result["total_voyages"], min_positions
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Tortuosity aggregation failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Tortuosity aggregation failed"),
                output_mode,
            )

    # ------------------------------------------------------------------
    # Wind rose tool
    # ------------------------------------------------------------------

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_wind_rose(
        lat_min: float | None = None,
        lat_max: float | None = None,
        lon_min: float | None = None,
        lon_max: float | None = None,
        nationality: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        direction: str | None = None,
        month_start: int | None = None,
        month_end: int | None = None,
        period1_years: str | None = None,
        period2_years: str | None = None,
        min_speed_km_day: float = 5.0,
        max_speed_km_day: float = 400.0,
        output_mode: str = "json",
    ) -> str:
        """
        Beaufort wind force distributions from CLIWOC logbook observations.

        Counts observations by Beaufort force (0-12) with mean speed at each
        force level. Optionally compares distributions between two periods.

        Key tool for the Kelly and O Grada approach: if recorded Beaufort
        distributions shift between periods, that indicates genuine wind
        change. If distributions are stable while speeds increase, that
        indicates technology improvement (hull, sails, routing).

        Requires CLIWOC 2.1 Full with wind data. Returns has_wind_data=false
        with a helpful message if wind data is not available.

        Args:
            lat_min/lat_max/lon_min/lon_max: Bounding box
            nationality: Filter by nationality code
            year_start/year_end: Filter by year range
            direction: Filter by "eastbound" or "westbound"
            month_start/month_end: Month filter (supports wrap-around)
            period1_years: First period as "YYYY/YYYY" for comparison
            period2_years: Second period as "YYYY/YYYY" for comparison
            min_speed_km_day: Minimum speed filter (default: 5.0)
            max_speed_km_day: Maximum speed filter (default: 400.0)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with Beaufort distribution, optional period split

        Tips for LLMs:
            - Use period1_years/period2_years to compare distributions
            - Combine with group_by="beaufort" on aggregate tool for
              speed profiles at each wind force
            - Requires re-running download script for wind data
        """
        try:
            result = wind_rose(
                lat_min=lat_min,
                lat_max=lat_max,
                lon_min=lon_min,
                lon_max=lon_max,
                nationality=nationality,
                year_start=year_start,
                year_end=year_end,
                direction=direction,
                month_start=month_start,
                month_end=month_end,
                period1_years=period1_years,
                period2_years=period2_years,
                min_speed=min_speed_km_day,
                max_speed=max_speed_km_day,
            )

            if not result["has_wind_data"]:
                msg = SuccessMessages.WIND_ROSE_NO_DATA
            else:
                msg = SuccessMessages.WIND_ROSE_COMPUTED.format(
                    result["total_with_wind"], result["total_voyages"]
                )

            beaufort_counts = [
                BeaufortCount(
                    force=bc["force"],
                    count=bc["count"],
                    percent=bc["percent"],
                    mean_speed_km_day=bc.get("mean_speed_km_day"),
                )
                for bc in result["beaufort_counts"]
            ]

            p1_counts = None
            p2_counts = None
            if result.get("period1_counts"):
                p1_counts = [
                    BeaufortCount(
                        force=bc["force"],
                        count=bc["count"],
                        percent=bc["percent"],
                        mean_speed_km_day=bc.get("mean_speed_km_day"),
                    )
                    for bc in result["period1_counts"]
                ]
            if result.get("period2_counts"):
                p2_counts = [
                    BeaufortCount(
                        force=bc["force"],
                        count=bc["count"],
                        percent=bc["percent"],
                        mean_speed_km_day=bc.get("mean_speed_km_day"),
                    )
                    for bc in result["period2_counts"]
                ]

            return format_response(
                WindRoseResponse(
                    total_with_wind=result["total_with_wind"],
                    total_without_wind=result["total_without_wind"],
                    total_voyages=result["total_voyages"],
                    has_wind_data=result["has_wind_data"],
                    beaufort_counts=beaufort_counts,
                    period1_label=result.get("period1_label"),
                    period1_counts=p1_counts,
                    period2_label=result.get("period2_label"),
                    period2_counts=p2_counts,
                    latitude_band=result.get("latitude_band"),
                    longitude_band=result.get("longitude_band"),
                    direction_filter=result.get("direction_filter"),
                    nationality_filter=result.get("nationality_filter"),
                    month_start_filter=result.get("month_start_filter"),
                    month_end_filter=result.get("month_end_filter"),
                    message=msg,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Wind rose computation failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Wind rose computation failed"),
                output_mode,
            )
