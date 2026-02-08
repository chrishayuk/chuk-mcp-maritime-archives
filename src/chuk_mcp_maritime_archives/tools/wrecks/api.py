"""MCP tools for searching and retrieving VOC shipwreck records."""

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
        archive: str | None = None,
        max_results: int = 100,
        output_mode: str = "json",
    ) -> str:
        """
        Search for VOC shipwreck records.

        Queries the MAARER wreck database for known and suspected wreck
        sites. All search parameters are optional and combined with AND logic.

        Args:
            ship_name: Ship name or partial name (case-insensitive)
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            region: Geographic region filter. Options: north_sea, atlantic_europe,
                atlantic_crossing, cape, mozambique_channel, indian_ocean,
                malabar, coromandel, ceylon, bengal, malacca, indonesia,
                south_china_sea, japan, caribbean
            cause: Loss cause filter - storm, reef, fire, battle, grounding,
                scuttled, unknown
            status: Wreck discovery status - found, unfound, approximate
            min_depth_m: Minimum estimated depth in metres
            max_depth_m: Maximum estimated depth in metres
            min_cargo_value: Minimum cargo value in guilders
            archive: Restrict to a specific archive (default: all)
            max_results: Maximum results to return (default: 100)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching wreck records

        Tips for LLMs:
            - Use region to focus on a geographic area (e.g., "cape" for
              Cape of Good Hope wrecks)
            - Set status="unfound" to find wrecks that have not been located
            - Combine cause="storm" with region to study weather-related losses
            - Follow up with maritime_get_wreck for full details including position
            - Use maritime_export_geojson to map wreck positions
            - Use maritime_assess_position to evaluate position certainty
        """
        try:
            results = await manager.search_wrecks(  # type: ignore[union-attr]
                ship_name=ship_name,
                date_range=date_range,
                region=region,
                cause=cause,
                status=status,
                min_depth_m=min_depth_m,
                max_depth_m=max_depth_m,
                min_cargo_value=min_cargo_value,
                archive=archive,
                max_results=max_results,
            )

            if not results:
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
                )
                for w in results
            ]

            return format_response(
                WreckSearchResponse(
                    wreck_count=len(wrecks),
                    wrecks=wrecks,
                    archive=archive,
                    message=SuccessMessages.WRECKS_FOUND.format(len(wrecks)),
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
