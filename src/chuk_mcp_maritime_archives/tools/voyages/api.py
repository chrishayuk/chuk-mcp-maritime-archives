"""MCP tools for searching and retrieving VOC voyage records."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    VoyageDetailResponse,
    VoyageInfo,
    VoyageSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_voyage_tools(mcp: object, manager: object) -> None:
    """Register voyage tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_voyages(
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        route: str | None = None,
        fate: str | None = None,
        archive: str | None = None,
        max_results: int = 50,
        output_mode: str = "json",
    ) -> str:
        """
        Search for VOC voyages matching one or more criteria.

        Queries the Dutch Asiatic Shipping (DAS) database for voyages
        between the Netherlands and Asia, 1595-1795. All search parameters
        are optional and combined with AND logic.

        Args:
            ship_name: Ship name or partial name (case-insensitive)
            captain: Captain / skipper name or partial name
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            departure_port: Departure port name or partial name
            destination_port: Destination port name or partial name
            route: Route keyword (searches departure, destination, and summary)
            fate: Voyage outcome - completed, wrecked, captured, scuttled, missing
            archive: Restrict to a specific archive (default: all)
            max_results: Maximum results to return (default: 50)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching voyages

        Tips for LLMs:
            - Start broad (ship_name only) and narrow down with additional filters
            - Use date_range to focus on a specific century or decade
            - Set fate="wrecked" to find shipwreck voyages
            - Follow up with maritime_get_voyage for full voyage details
            - Combine with maritime_search_crew to find crew on a specific voyage
            - Combine with maritime_get_cargo_manifest for cargo carried
        """
        try:
            results = await manager.search_voyages(  # type: ignore[union-attr]
                ship_name=ship_name,
                captain=captain,
                date_range=date_range,
                departure_port=departure_port,
                destination_port=destination_port,
                route=route,
                fate=fate,
                archive=archive,
                max_results=max_results,
            )

            if not results:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            voyages = [
                VoyageInfo(
                    voyage_id=v.get("voyage_id", ""),
                    ship_name=v.get("ship_name", ""),
                    ship_type=v.get("ship_type"),
                    captain=v.get("captain"),
                    departure_port=v.get("departure_port"),
                    departure_date=v.get("departure_date"),
                    destination_port=v.get("destination_port"),
                    fate=v.get("fate"),
                    summary=v.get("summary"),
                )
                for v in results
            ]

            return format_response(
                VoyageSearchResponse(
                    voyage_count=len(voyages),
                    voyages=voyages,
                    archive=archive,
                    message=SuccessMessages.VOYAGES_FOUND.format(len(voyages)),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Voyage search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Voyage search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_voyage(
        voyage_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details for a specific voyage.

        Returns the complete voyage record including ship information,
        captain, route, dates, fate, and any incident details. The voyage
        must have been found by a prior maritime_search_voyages call or
        specified by its DAS voyage identifier.

        Args:
            voyage_id: Voyage identifier (from search results or DAS ID)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full voyage record

        Tips for LLMs:
            - Use maritime_search_voyages first to find the voyage_id
            - The response includes incident details if the voyage ended
              in shipwreck (loss date, position, cause)
            - Use the voyage_id with maritime_search_crew to find the crew
            - Use the voyage_id with maritime_get_cargo_manifest for cargo
            - Use with maritime_assess_position to evaluate wreck position quality
        """
        try:
            result = await manager.get_voyage(voyage_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.VOYAGE_NOT_FOUND.format(voyage_id),
                    ),
                    output_mode,
                )

            return format_response(
                VoyageDetailResponse(
                    voyage=result,
                    message=f"Voyage {voyage_id}: {result.get('ship_name', '?')}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get voyage '%s': %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get voyage"),
                output_mode,
            )
