"""MCP tools for searching cargo records and retrieving manifests."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    CargoDetailResponse,
    CargoInfo,
    CargoSearchResponse,
    ErrorResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_cargo_tools(mcp: object, manager: object) -> None:
    """Register cargo tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_cargo(
        voyage_id: str | None = None,
        commodity: str | None = None,
        origin: str | None = None,
        destination: str | None = None,
        date_range: str | None = None,
        min_value: float | None = None,
        archive: str | None = None,
        max_results: int = 100,
        cursor: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Search for VOC cargo records.

        Queries the Boekhouder-Generaal Batavia (BGB) cargo database for
        trade goods shipped between Asia and the Netherlands, 1700-1795.
        All search parameters are optional and combined with AND logic.
        Supports cursor-based pagination.

        Args:
            voyage_id: Filter by specific voyage
            commodity: Commodity name or partial name (e.g., pepper, cloves,
                textiles, silver, porcelain)
            origin: Origin port or region
            destination: Destination port or region
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            min_value: Minimum cargo value in guilders
            archive: Restrict to a specific archive (default: voc_cargo)
            max_results: Maximum results per page (default: 100, max: 500)
            cursor: Pagination cursor from a previous result's next_cursor field
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching cargo records and pagination metadata

        Tips for LLMs:
            - Use commodity to search for specific trade goods
            - Use voyage_id to see all cargo on a specific voyage;
              alternatively use maritime_get_cargo_manifest for the full list
            - Common VOC commodities: pepper, cloves, nutmeg, mace, cinnamon,
              textiles, porcelain, silver, copper, tea, coffee, sugar
            - Values are in contemporary Dutch guilders
            - If has_more is true, pass next_cursor as cursor to get the next page
            - Combine with maritime_search_voyages to find the voyage context
        """
        try:
            result = await manager.search_cargo(  # type: ignore[union-attr]
                voyage_id=voyage_id,
                commodity=commodity,
                origin=origin,
                destination=destination,
                date_range=date_range,
                min_value=min_value,
                archive=archive or "voc_cargo",
                max_results=max_results,
                cursor=cursor,
            )

            if not result.items:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            cargo = [
                CargoInfo(
                    cargo_id=c.get("cargo_id", ""),
                    voyage_id=c.get("voyage_id"),
                    ship_name=c.get("ship_name"),
                    commodity=c.get("commodity", ""),
                    quantity=c.get("quantity"),
                    unit=c.get("unit"),
                    value_guilders=c.get("value_guilders"),
                )
                for c in result.items
            ]

            return format_response(
                CargoSearchResponse(
                    cargo_count=len(cargo),
                    cargo=cargo,
                    message=SuccessMessages.CARGO_FOUND.format(len(cargo)),
                    total_count=result.total_count,
                    next_cursor=result.next_cursor,
                    has_more=result.has_more,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Cargo search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Cargo search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_cargo_manifest(
        voyage_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get the full cargo manifest for a specific voyage.

        Returns all cargo entries recorded for the voyage, including
        commodity, quantity, unit, and value in guilders.

        Args:
            voyage_id: Voyage identifier (from search results or DAS ID)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with all cargo entries for the voyage

        Tips for LLMs:
            - Use maritime_search_voyages first to find the voyage_id
            - The manifest lists all goods loaded on the ship
            - Values are in contemporary Dutch guilders
            - Useful for estimating the total value of cargo lost in a
              shipwreck — combine with maritime_get_wreck
            - Not all voyages have cargo records; the BGB archive covers
              1700-1795 while DAS voyages start from 1595
        """
        try:
            results = await manager.get_cargo_manifest(voyage_id)  # type: ignore[union-attr]

            if not results:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.CARGO_NOT_FOUND.format(voyage_id),
                    ),
                    output_mode,
                )

            return format_response(
                CargoDetailResponse(
                    cargo_entries=results,
                    voyage_id=voyage_id,
                    message=f"Manifest for voyage {voyage_id}: {len(results)} entries",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get cargo manifest for '%s': %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get cargo manifest"),
                output_mode,
            )
