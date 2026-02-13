"""MCP tools for cross-archive linking of maritime records."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    LinkAuditResponse,
    VoyageFullResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_linking_tools(mcp: object, manager: object) -> None:
    """Register cross-archive linking tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_voyage_full(
        voyage_id: str,
        include_crew: bool = False,
        output_mode: str = "json",
    ) -> str:
        """
        Get a unified view of a voyage with all linked records.

        Returns the voyage record enriched with related wreck, vessel,
        hull profile, CLIWOC track, and optionally crew data. Each link
        includes a confidence score (0.0-1.0) indicating match quality.

        Args:
            voyage_id: Voyage identifier (e.g. "das:0372.1", "eic:0042")
            include_crew: If true, also find crew records linked to this voyage
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with unified voyage view including all linked records

        Tips for LLMs:
            - Start with maritime_search_voyages to find the voyage_id
            - This tool replaces the need to call get_voyage, get_wreck,
              get_vessel, and get_hull_profile separately
            - The links_found field shows which related records exist
            - The link_confidence field shows match quality (1.0 = exact ID match,
              lower values indicate fuzzy name+date matching)
            - Use include_crew=true to find crew/muster records for a voyage
            - Cross-reference: a wreck's voyage_id links to the originating voyage
            - The cliwoc_track field shows logbook positions (requires CLIWOC
              2.1 Full data for ship name matching)
        """
        try:
            result = await manager.get_voyage_full(  # type: ignore[union-attr]
                voyage_id, include_crew=include_crew
            )

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
                    crew=result.get("crew"),
                    links_found=links,
                    link_confidence=result.get("link_confidence", {}),
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

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_audit_links(
        output_mode: str = "json",
    ) -> str:
        """
        Audit cross-archive link quality against known ground truth.

        Evaluates the precision and recall of entity resolution across
        all archive linking strategies. Uses known DAS-CLIWOC direct links
        (tracks with DAS numbers) and wreck records (with voyage_id fields)
        as ground truth.

        Args:
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with precision/recall metrics and confidence
            distributions for wreck, CLIWOC track, and crew links

        Tips for LLMs:
            - Run this to check linking quality after data updates
            - The confidence distribution shows how many links are high
              quality vs marginal
            - Target: 200+ CLIWOC fuzzy matches with mean confidence > 0.7
            - Wreck links use exact voyage_id matching (precision = 1.0)
            - CLIWOC links use fuzzy ship name + date matching
        """
        try:
            result = await manager.audit_links()  # type: ignore[union-attr]

            wl = result["wreck_links"]
            cl = result["cliwoc_links"]

            return format_response(
                LinkAuditResponse(
                    wreck_links=result["wreck_links"],
                    cliwoc_links=result["cliwoc_links"],
                    crew_links=result["crew_links"],
                    total_links_evaluated=result["total_links_evaluated"],
                    confidence_distribution=result.get("confidence_distribution", {}),
                    message=SuccessMessages.LINKS_AUDITED.format(
                        result["total_links_evaluated"],
                        wl.get("ground_truth_count", 0),
                        cl.get("direct_links", 0) + cl.get("fuzzy_matches", 0),
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to audit links: %s", e)
            return format_response(
                ErrorResponse(
                    error=ErrorMessages.AUDIT_FAILED.format(str(e)),
                    message="Link audit failed",
                ),
                output_mode,
            )
