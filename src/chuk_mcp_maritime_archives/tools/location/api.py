"""MCP tools for looking up historical VOC place names."""

import logging

from ...constants import ErrorMessages
from ...core.voc_gazetteer import (
    lookup_location,
    search_locations,
)
from ...models import (
    ErrorResponse,
    LocationDetailResponse,
    LocationInfo,
    LocationSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_location_tools(mcp: object, manager: object) -> None:
    """Register location gazetteer tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_lookup_location(
        name: str,
        output_mode: str = "json",
    ) -> str:
        """
        Look up a historical place name in the VOC gazetteer.

        Returns coordinates (lat/lon), region classification, and historical
        context for a place name mentioned in voyage or wreck records.
        Handles historical spellings and aliases automatically.

        Args:
            name: Place name to look up (e.g., "Batavia", "Texel",
                "Abrolhos", "Kaap de Goede Hoop"). Supports historical
                Dutch spellings and modern equivalents.
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with coordinates, region, and historical notes

        Tips for LLMs:
            - Use this after reading a voyage's 'particulars' field to
              geocode places mentioned in the text
            - Handles common VOC-era place names and their modern equivalents
              (e.g., "Batavia" -> Jakarta, "Formosa" -> Taiwan)
            - The 'region' field matches the regions used by
              maritime_search_wrecks and maritime_get_statistics
            - Coordinates are approximate centres for historical locations
            - Use maritime_list_locations to browse available places by
              region or type
            - Combine with maritime_assess_position to evaluate position
              accuracy for a given location and time period
        """
        try:
            result = lookup_location(name)

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=f"Location '{name}' not found in VOC gazetteer. "
                        "Try maritime_list_locations to browse available places.",
                    ),
                    output_mode,
                )

            location = LocationInfo(
                name=result["name"],
                lat=result["lat"],
                lon=result["lon"],
                region=result["region"],
                type=result["type"],
                aliases=result.get("aliases", []),
                notes=result.get("notes"),
            )

            return format_response(
                LocationDetailResponse(
                    location=location,
                    message=f"Location: {result['name']} ({result['region']})",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Location lookup failed for '%s': %s", name, e)
            return format_response(
                ErrorResponse(error=str(e), message="Location lookup failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_list_locations(
        query: str | None = None,
        region: str | None = None,
        location_type: str | None = None,
        max_results: int = 50,
        output_mode: str = "json",
    ) -> str:
        """
        Search or browse the VOC historical gazetteer.

        Returns a list of known VOC-era locations with coordinates
        and region classifications. Use filters to narrow results.

        Args:
            query: Text to search in place names, aliases, and notes
                (case-insensitive substring match)
            region: Filter by region. Options: north_sea, atlantic_europe,
                atlantic_crossing, cape, mozambique_channel, indian_ocean,
                malabar, coromandel, ceylon, bengal, malacca, indonesia,
                south_china_sea, japan, caribbean
            location_type: Filter by type. Options: port, island, cape,
                anchorage, waterway, coast, channel, region
            max_results: Maximum results (default: 50)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching locations

        Tips for LLMs:
            - Call without filters to see all available locations
            - Use region filter to find all ports/islands in a specific area
            - Use location_type="port" to find VOC trading posts
            - Use query to search by historical or modern name
            - The 'region' values match those used in maritime_search_wrecks
            - Follow up with maritime_lookup_location for full details
              on a specific place
        """
        try:
            results = search_locations(
                query=query,
                region=region,
                location_type=location_type,
                max_results=max_results,
            )

            if not results:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            locations = [
                LocationInfo(
                    name=r["name"],
                    lat=r["lat"],
                    lon=r["lon"],
                    region=r["region"],
                    type=r["type"],
                    aliases=r.get("aliases", []),
                    notes=r.get("notes"),
                )
                for r in results
            ]

            return format_response(
                LocationSearchResponse(
                    location_count=len(locations),
                    locations=locations,
                    message=f"Found {len(locations)} locations",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Location search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Location search failed"),
                output_mode,
            )
