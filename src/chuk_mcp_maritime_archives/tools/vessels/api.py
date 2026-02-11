"""MCP tools for searching vessels and querying hull profiles."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    HullProfileListResponse,
    HullProfileResponse,
    VesselDetailResponse,
    VesselInfo,
    VesselSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_vessel_tools(mcp: object, manager: object) -> None:
    """Register vessel and hull profile tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_vessels(
        name: str | None = None,
        ship_type: str | None = None,
        built_range: str | None = None,
        shipyard: str | None = None,
        chamber: str | None = None,
        min_tonnage: int | None = None,
        max_tonnage: int | None = None,
        archive: str | None = None,
        max_results: int = 50,
        cursor: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Search for VOC vessels by name, type, or construction details.

        Queries the DAS vessel registry for ships used by the VOC.
        All search parameters are optional and combined with AND logic.
        Supports cursor-based pagination.

        Args:
            name: Vessel name or partial name (case-insensitive)
            ship_type: Ship type filter. Options: retourschip, fluit, jacht,
                hooker, pinas, fregat
            built_range: Build year range as "YYYY/YYYY"
            shipyard: Shipyard name or partial name
            chamber: VOC chamber - Amsterdam, Zeeland, Delft, Rotterdam,
                Hoorn, Enkhuizen
            min_tonnage: Minimum tonnage in lasten
            max_tonnage: Maximum tonnage in lasten
            archive: Restrict to a specific archive (default: all)
            max_results: Maximum results per page (default: 50, max: 500)
            cursor: Pagination cursor from a previous result's next_cursor field
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching vessel records and pagination metadata

        Tips for LLMs:
            - Use ship_type to filter by vessel class (retourschip is the
              standard large Asia-route ship)
            - Chamber indicates which of the six VOC offices commissioned
              the vessel
            - If has_more is true, pass next_cursor as cursor to get the next page
            - Follow up with maritime_get_vessel for full construction details
            - Use maritime_get_hull_profile for hydrodynamic characteristics
              of a ship type (useful for drift modelling)
            - Combine with maritime_search_voyages to find voyages by this vessel
        """
        try:
            result = await manager.search_vessels(  # type: ignore[union-attr]
                name=name,
                ship_type=ship_type,
                built_range=built_range,
                shipyard=shipyard,
                chamber=chamber,
                min_tonnage=min_tonnage,
                max_tonnage=max_tonnage,
                archive=archive,
                max_results=max_results,
                cursor=cursor,
            )

            if not result.items:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            vessels = [
                VesselInfo(
                    vessel_id=v.get("vessel_id", ""),
                    name=v.get("name", ""),
                    type=v.get("type") or v.get("ship_type"),
                    tonnage=v.get("tonnage"),
                    built_year=v.get("built_year"),
                    chamber=v.get("chamber"),
                )
                for v in result.items
            ]

            return format_response(
                VesselSearchResponse(
                    vessel_count=len(vessels),
                    vessels=vessels,
                    message=SuccessMessages.VESSELS_FOUND.format(len(vessels)),
                    total_count=result.total_count,
                    next_cursor=result.next_cursor,
                    has_more=result.has_more,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Vessel search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Vessel search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_vessel(
        vessel_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details for a specific vessel.

        Returns the complete vessel record including name, type, tonnage,
        construction year, shipyard, VOC chamber, dimensions, and service
        history.

        Args:
            vessel_id: Vessel identifier (from search results)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full vessel record

        Tips for LLMs:
            - Use maritime_search_vessels first to find the vessel_id
            - Tonnage is measured in lasten (approximately 2 metric tonnes)
            - Use maritime_get_hull_profile with the ship type for
              hydrodynamic characteristics
            - Cross-reference with maritime_search_voyages using the
              vessel name to find its voyage history
        """
        try:
            result = await manager.get_vessel(vessel_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.VESSEL_NOT_FOUND.format(vessel_id),
                    ),
                    output_mode,
                )

            return format_response(
                VesselDetailResponse(
                    vessel=result,
                    message=f"Vessel {vessel_id}: {result.get('name', '?')}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get vessel '%s': %s", vessel_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get vessel"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_hull_profile(
        ship_type: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get hydrodynamic hull profile for a VOC ship type.

        Returns detailed hull characteristics including dimensions,
        displacement, drag coefficients, windage area, and drift
        modelling parameters. Used for calculating how a ship or
        wreckage would drift in ocean currents.

        Args:
            ship_type: Ship type identifier. Options: retourschip, fluit,
                jacht, hooker, pinas, fregat
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with hull profile data

        Tips for LLMs:
            - Use maritime_list_hull_profiles to see available types
            - Essential for drift modelling: provides drag coefficients,
              windage area, and sinking characteristics
            - The dimensions_typical field gives length, beam, and draught
              ranges for that ship type
            - The llm_guidance field contains domain-specific advice for
              using the profile in calculations
            - Retourschip is the most common VOC vessel type
        """
        try:
            available = manager.list_hull_profiles()  # type: ignore[union-attr]
            result = manager.get_hull_profile(ship_type)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.SHIP_TYPE_NOT_FOUND.format(
                            ship_type, ", ".join(available)
                        ),
                    ),
                    output_mode,
                )

            return format_response(
                HullProfileResponse(
                    profile=result,
                    message=f"Hull profile for {ship_type}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get hull profile '%s': %s", ship_type, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get hull profile"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_list_hull_profiles(
        output_mode: str = "json",
    ) -> str:
        """
        List all available ship types with hull profiles.

        Returns a list of VOC ship type identifiers for which
        hydrodynamic hull profile data is available.

        Args:
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text list of ship types

        Tips for LLMs:
            - Use this to discover which ship types have hull profiles
              before calling maritime_get_hull_profile
            - Common types: retourschip (large Asia trader), fluit (cargo),
              jacht (fast patrol)
        """
        try:
            ship_types = manager.list_hull_profiles()  # type: ignore[union-attr]

            return format_response(
                HullProfileListResponse(
                    ship_types=ship_types,
                    count=len(ship_types),
                    message=f"{len(ship_types)} hull profiles available",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to list hull profiles: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to list hull profiles"),
                output_mode,
            )
