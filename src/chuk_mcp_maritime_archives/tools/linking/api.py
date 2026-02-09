"""MCP tools for cross-archive linking of maritime records."""

import logging

from ...constants import ErrorMessages
from ...models import (
    ErrorResponse,
    VoyageFullResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_linking_tools(mcp: object, manager: object) -> None:
    """Register cross-archive linking tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_voyage_full(
        voyage_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get a unified view of a voyage with all linked records.

        Returns the voyage record enriched with related wreck, vessel,
        hull profile, and CLIWOC track data. This is the primary tool
        for cross-archive investigation — it follows all links between
        the DAS voyage database, wreck records, vessel registry, hull
        profiles, and CLIWOC ship tracks automatically.

        Args:
            voyage_id: DAS voyage identifier (e.g. "das:0372.1" or "0372.1")
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with unified voyage view including all linked records

        Tips for LLMs:
            - Start with maritime_search_voyages to find the voyage_id
            - This tool replaces the need to call get_voyage, get_wreck,
              get_vessel, and get_hull_profile separately
            - The links_found field shows which related records exist
            - Use this for comprehensive investigation of a single voyage
            - Cross-reference: a wreck's voyage_id links to the originating voyage
            - The cliwoc_track field shows logbook positions (requires CLIWOC
              2.1 Full data for ship name matching)
        """
        try:
            result = await manager.get_voyage_full(voyage_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.VOYAGE_NOT_FOUND_LINKING.format(voyage_id),
                    ),
                    output_mode,
                )

            links = result["links_found"]
            ship = result["voyage"].get("ship_name", "?")

            return format_response(
                VoyageFullResponse(
                    voyage=result["voyage"],
                    wreck=result.get("wreck"),
                    vessel=result.get("vessel"),
                    hull_profile=result.get("hull_profile"),
                    cliwoc_track=result.get("cliwoc_track"),
                    links_found=links,
                    message=(
                        f"Voyage {voyage_id}: {ship} "
                        f"({len(links)} linked record{'s' if len(links) != 1 else ''})"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get full voyage '%s': %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get full voyage"),
                output_mode,
            )
