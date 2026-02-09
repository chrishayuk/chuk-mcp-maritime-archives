"""MCP tools for querying standard VOC sailing routes."""

import logging

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
        List available VOC standard sailing routes.

        Returns summaries of all known VOC routes with typical durations.
        Optionally filter by direction or by departure/destination port.

        Args:
            direction: Filter by route direction — "outward" (Netherlands
                to Asia), "return" (Asia to Netherlands), or "intra_asian"
                (between Asian ports)
            departure_port: Filter routes containing this departure port
                (substring match, e.g., "Texel", "Batavia")
            destination_port: Filter routes containing this destination
                (substring match, e.g., "Batavia", "Deshima")
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with list of available routes

        Tips for LLMs:
            - Use direction="outward" to see the main Netherlands-to-Asia
              routes (outer and inner variants)
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
        Get full details of a standard VOC sailing route.

        Returns all waypoints with coordinates, typical sailing times,
        stop durations, hazards, and seasonal notes for a specific route.

        Args:
            route_id: Route identifier. Options:
                - outward_outer: Netherlands to Batavia (south of Madagascar)
                - outward_inner: Netherlands to Batavia (Mozambique Channel)
                - return: Batavia to Netherlands
                - japan: Batavia to Deshima (Nagasaki)
                - spice_islands: Batavia to Ambon and Banda
                - ceylon: Batavia to Galle and Colombo
                - coromandel: Batavia to Indian east coast
                - malabar: Batavia to Indian west coast (Cochin)
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
                        error=f"Route '{route_id}' not found. "
                        f"Available: {', '.join(get_route_ids())}",
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
        output_mode: str = "json",
    ) -> str:
        """
        Estimate a ship's position on a specific date based on its route.

        Uses linear interpolation between standard VOC route waypoints
        to estimate where a ship would have been on a given date,
        assuming typical sailing times. Essential for investigating
        wreck locations and lost voyages.

        Args:
            route_id: Route identifier (from maritime_list_routes or
                maritime_get_route)
            departure_date: Ship's departure date as YYYY-MM-DD
            target_date: Date to estimate position for as YYYY-MM-DD
                (e.g., last known date, or estimated loss date)
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
