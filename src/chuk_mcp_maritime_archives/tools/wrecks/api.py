"""MCP tools for searching and retrieving maritime shipwreck records."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    WreckDetailResponse,
    WreckInfo,
    WreckSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_wreck_tools(mcp: object, manager: object) -> None:
    """Register wreck tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_wrecks(
        ship_name: str | None = None,
        date_range: str | None = None,
        region: str | None = None,
        cause: str | None = None,
        status: str | None = None,
        min_depth_m: float | None = None,
        max_depth_m: float | None = None,
        min_cargo_value: float | None = None,
        flag: str | None = None,
        vessel_type: str | None = None,
        archive: str | None = None,
        max_results: int = 100,
        cursor: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Search for maritime shipwreck records across all archives.

        Queries wreck databases for known and suspected wreck sites.
        All search parameters are optional and combined with AND logic.
        Supports cursor-based pagination.

        Archives with wreck data:
            - maarer: MAARER VOC Wrecks, 1595-1795
            - eic: English East India Company wrecks, 1600-1874
            - carreira: Portuguese Carreira da India wrecks, 1497-1835
            - galleon: Spanish Manila Galleon wrecks, 1565-1815
            - soic: Swedish East India Company wrecks, 1731-1813
            - ukho: UK Hydrographic Office Global Wrecks, 1500-2024

        Args:
            ship_name: Ship name or partial name (case-insensitive)
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            region: Geographic region filter (e.g., cape, pacific, indian_ocean)
            cause: Loss cause filter - storm, reef, fire, battle, grounding,
                scuttled, collision, unknown
            status: Wreck discovery status - found, unfound, approximate
            min_depth_m: Minimum estimated depth in metres
            max_depth_m: Maximum estimated depth in metres
            min_cargo_value: Minimum cargo value in guilders
            flag: Vessel nationality/flag (substring match, e.g. "UK", "NL")
            vessel_type: Vessel type classification (substring match, e.g. "liner", "warship")
            archive: Restrict to specific archive - maarer, eic, carreira, galleon, soic, ukho (default: all)
            max_results: Maximum results per page (default: 100, max: 500)
            cursor: Pagination cursor from a previous result's next_cursor field
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching wreck records and pagination metadata

        Tips for LLMs:
            - Use region to focus on a geographic area (e.g., "cape", "pacific")
            - Set status="unfound" to find wrecks that have not been located
            - If has_more is true, pass next_cursor as cursor to get the next page
            - Follow up with maritime_get_wreck for full details including position
            - Use maritime_export_geojson to map wreck positions
            - Use flag to filter by nationality (e.g. "UK", "NL", "US")
            - Use vessel_type to filter by ship classification (e.g. "liner", "warship")
        """
        try:
            result = await manager.search_wrecks(  # type: ignore[union-attr]
                ship_name=ship_name,
                date_range=date_range,
                region=region,
                cause=cause,
                status=status,
                min_depth_m=min_depth_m,
                max_depth_m=max_depth_m,
                min_cargo_value=min_cargo_value,
                flag=flag,
                vessel_type=vessel_type,
                archive=archive,
                max_results=max_results,
                cursor=cursor,
            )

            if not result.items:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            wrecks = [
                WreckInfo(
                    wreck_id=w.get("wreck_id", ""),
                    ship_name=w.get("ship_name", ""),
                    loss_date=w.get("loss_date"),
                    loss_cause=w.get("loss_cause"),
                    region=w.get("region"),
                    status=w.get("status"),
                    position=w.get("position"),
                    archive=w.get("archive"),
                    flag=w.get("flag"),
                    vessel_type=w.get("vessel_type"),
                    depth_estimate_m=w.get("depth_estimate_m"),
                )
                for w in result.items
            ]

            return format_response(
                WreckSearchResponse(
                    wreck_count=len(wrecks),
                    wrecks=wrecks,
                    archive=archive,
                    message=SuccessMessages.WRECKS_FOUND.format(len(wrecks)),
                    total_count=result.total_count,
                    next_cursor=result.next_cursor,
                    has_more=result.has_more,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Wreck search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Wreck search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_wreck(
        wreck_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details for a specific wreck record.

        Returns the complete wreck record including ship information,
        loss date, cause, position with uncertainty, depth estimate,
        discovery status, and archaeological notes.

        Args:
            wreck_id: Wreck identifier (from search results)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full wreck record

        Tips for LLMs:
            - Use maritime_search_wrecks first to find the wreck_id
            - The position field includes lat, lon, and uncertainty_km
            - Use maritime_assess_position with this wreck_id to get a
              detailed position quality assessment
            - Use maritime_export_geojson with wreck_ids to map the location
            - Cross-reference with maritime_get_voyage using the linked voyage_id
        """
        try:
            result = await manager.get_wreck(wreck_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.WRECK_NOT_FOUND.format(wreck_id),
                    ),
                    output_mode,
                )

            return format_response(
                WreckDetailResponse(
                    wreck=result,
                    message=f"Wreck {wreck_id}: {result.get('ship_name', '?')}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get wreck '%s': %s", wreck_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get wreck"),
                output_mode,
            )
