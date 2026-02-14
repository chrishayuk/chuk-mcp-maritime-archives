"""MCP tools for querying historical sailing routes."""

import logging

from ...constants import ErrorMessages
from ...core.voc_routes import (
    estimate_position,
    get_route,
    get_route_ids,
    list_routes,
    suggest_route,
)
from ...models import (
    ErrorResponse,
    PositionEstimateResponse,
    RouteDetailResponse,
    RouteInfo,
    RouteListResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_route_tools(mcp: object, manager: object) -> None:
    """Register route tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_list_routes(
        direction: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        List available historical sailing routes.

        Returns summaries of all known routes with typical durations.
        Covers VOC (Dutch), EIC (British), Carreira da India (Portuguese),
        Manila Galleon (Spanish), and SOIC (Swedish) routes.

        Args:
            direction: Filter by route direction — "outward" (Europe
                to Asia), "return" (Asia to Europe), "intra_asian"
                (between Asian ports), "pacific_westbound" (Acapulco
                to Manila), or "pacific_eastbound" (Manila to Acapulco)
            departure_port: Filter routes containing this departure port
                (substring match, e.g., "Texel", "Downs", "Lisbon")
            destination_port: Filter routes containing this destination
                (substring match, e.g., "Batavia", "Canton", "Manila")
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with list of available routes

        Tips for LLMs:
            - Use direction="outward" to see Europe-to-Asia routes for
              all nations (VOC, EIC, Carreira, SOIC)
            - Use departure_port and destination_port to find routes
              matching a specific voyage
            - Follow up with maritime_get_route for full waypoint details
            - Use maritime_estimate_position with a route_id to estimate
              where a ship was on a specific date
        """
        try:
            if direction or departure_port or destination_port:
                results = suggest_route(
                    departure_port=departure_port,
                    destination_port=destination_port,
                    direction=direction,
                )
            else:
                results = list_routes()

            if not results:
                return format_response(
                    ErrorResponse(
                        error="No routes found matching criteria. "
                        f"Available routes: {', '.join(get_route_ids())}",
                    ),
                    output_mode,
                )

            routes = [
                RouteInfo(
                    route_id=r["route_id"],
                    name=r["name"],
                    direction=r["direction"],
                    typical_duration_days=r["typical_duration_days"],
                    waypoint_count=r["waypoint_count"],
                )
                for r in results
            ]

            return format_response(
                RouteListResponse(
                    route_count=len(routes),
                    routes=routes,
                    message=f"Found {len(routes)} routes",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Route listing failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Route listing failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_route(
        route_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details of a historical sailing route.

        Returns all waypoints with coordinates, typical sailing times,
        stop durations, hazards, and seasonal notes for a specific route.

        Args:
            route_id: Route identifier. Options:
                VOC (Dutch): outward_outer, outward_inner, return,
                    japan, spice_islands, ceylon, coromandel, malabar
                EIC (British): eic_outward, eic_china, eic_return,
                    eic_country
                Carreira (Portuguese): carreira_outward, carreira_return
                Manila Galleon (Spanish): galleon_westbound,
                    galleon_eastbound
                SOIC (Swedish): soic_outward, soic_return
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with full route including waypoints, durations,
            hazards, and seasonal notes

        Tips for LLMs:
            - Each waypoint has cumulative_days (typical elapsed days from
              departure) and stop_days (typical port stay duration)
            - The outer route (south of Madagascar) was preferred from
              the 1660s for speed; the inner route used Mozambique Channel
            - Use the waypoints with maritime_lookup_location for details
              on each port
            - Use maritime_estimate_position with this route_id and a
              departure date to estimate a ship's position on any date
        """
        try:
            result = get_route(route_id)

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.ROUTE_NOT_FOUND.format(route_id),
                    ),
                    output_mode,
                )

            return format_response(
                RouteDetailResponse(
                    route=result,
                    message=f"Route: {result['name']}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get route '%s': %s", route_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get route"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_estimate_position(
        route_id: str,
        departure_date: str,
        target_date: str,
        use_speed_profiles: bool = False,
        output_mode: str = "json",
    ) -> str:
        """
        Estimate a ship's position on a specific date based on its route.

        Uses linear interpolation between historical route waypoints
        to estimate where a ship would have been on a given date,
        assuming typical sailing times. Works with all 18 routes
        across VOC, EIC, Carreira, Galleon, and SOIC. Essential for
        investigating wreck locations and lost voyages.

        Args:
            route_id: Route identifier (from maritime_list_routes or
                maritime_get_route). See maritime_get_route for full list.
            departure_date: Ship's departure date as YYYY-MM-DD
            target_date: Date to estimate position for as YYYY-MM-DD
                (e.g., last known date, or estimated loss date)
            use_speed_profiles: If True, enrich estimate with CLIWOC-derived
                speed statistics for the current route segment (default False)
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with estimated lat/lon, region, route segment,
            confidence level, and caveats

        Tips for LLMs:
            - Get the departure_date from maritime_get_voyage
            - Choose route_id based on the voyage's departure/destination
              ports (use maritime_list_routes to find matching routes)
            - The estimate is based on TYPICAL sailing times — actual
              positions varied due to weather, ship condition, and orders
            - Confidence is "high" at known ports, "moderate" between
              waypoints, "low" past the expected arrival date
            - Use maritime_lookup_location on the estimated region for
              more geographic context
            - Combine with maritime_assess_position for uncertainty analysis
        """
        try:
            result = estimate_position(
                route_id=route_id,
                departure_date=departure_date,
                target_date=target_date,
                use_speed_profiles=use_speed_profiles,
            )

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=f"Could not estimate position. Route '{route_id}' "
                        f"not found or dates invalid. "
                        f"Available routes: {', '.join(get_route_ids())}. "
                        "Dates must be YYYY-MM-DD format.",
                    ),
                    output_mode,
                )

            if "error" in result:
                return format_response(
                    ErrorResponse(error=result["error"]),
                    output_mode,
                )

            pos = result.get("estimated_position", {})
            return format_response(
                PositionEstimateResponse(
                    estimate=result,
                    message=(
                        f"Estimated position on {target_date}: "
                        f"{pos.get('lat', '?')}N, {pos.get('lon', '?')}E "
                        f"({pos.get('region', '?')})"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Position estimate failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Position estimate failed"),
                output_mode,
            )
