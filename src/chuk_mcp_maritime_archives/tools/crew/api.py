"""MCP tools for searching and retrieving VOC crew muster records."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    CrewDetailResponse,
    CrewInfo,
    CrewSearchResponse,
    ErrorResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_crew_tools(mcp: object, manager: object) -> None:
    """Register crew tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_crew(
        name: str | None = None,
        rank: str | None = None,
        ship_name: str | None = None,
        voyage_id: str | None = None,
        origin: str | None = None,
        date_range: str | None = None,
        fate: str | None = None,
        archive: str | None = None,
        max_results: int = 100,
        output_mode: str = "json",
    ) -> str:
        """
        Search for VOC crew members in muster roll records.

        Queries the VOC Opvarenden database containing 774,200 personnel
        records from 1633-1794. All search parameters are optional and
        combined with AND logic.

        Args:
            name: Crew member name or partial name (case-insensitive)
            rank: Rank or role (e.g., schipper, stuurman, matroos, soldaat)
            ship_name: Ship name or partial name
            voyage_id: Specific voyage identifier to list all crew
            origin: Place of origin or partial name
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            fate: Crew fate - survived, died_voyage, died_asia, deserted,
                discharged
            archive: Restrict to a specific archive (default: voc_crew)
            max_results: Maximum results to return (default: 100)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching crew records

        Tips for LLMs:
            - Use voyage_id to list the complete crew of a specific voyage
            - Set fate="died_voyage" to find crew lost at sea
            - Names are in historical Dutch spelling; try partial matches
            - Follow up with maritime_get_crew_member for full details
              including pay and embarkation date
            - Combine with maritime_search_voyages to cross-reference
              ship and voyage information
        """
        try:
            results = await manager.search_crew(  # type: ignore[union-attr]
                name=name,
                rank=rank,
                ship_name=ship_name,
                voyage_id=voyage_id,
                origin=origin,
                date_range=date_range,
                fate=fate,
                archive=archive or "voc_crew",
                max_results=max_results,
            )

            if not results:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            crew = [
                CrewInfo(
                    crew_id=c.get("crew_id", ""),
                    name=c.get("name", ""),
                    rank=c.get("rank"),
                    rank_english=c.get("rank_english"),
                    ship_name=c.get("ship_name"),
                    voyage_id=c.get("voyage_id"),
                )
                for c in results
            ]

            return format_response(
                CrewSearchResponse(
                    crew_count=len(crew),
                    crew=crew,
                    message=SuccessMessages.CREW_FOUND.format(len(crew)),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Crew search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Crew search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_crew_member(
        crew_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details for a specific crew member.

        Returns the complete crew record including name, rank, origin,
        ship name, voyage, monthly pay, embarkation date, and fate.

        Args:
            crew_id: Crew member identifier (from search results)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full crew member record

        Tips for LLMs:
            - Use maritime_search_crew first to find the crew_id
            - Pay is in guilders per month; compare with rank averages
            - The fate field indicates what happened to the crew member
              (survived, died_voyage, died_asia, deserted, discharged)
            - Cross-reference with maritime_get_voyage using the voyage_id
              for full voyage context
        """
        try:
            result = await manager.get_crew_member(crew_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.CREW_NOT_FOUND.format(crew_id),
                    ),
                    output_mode,
                )

            return format_response(
                CrewDetailResponse(
                    crew_member=result,
                    message=f"Crew: {result.get('name', '?')} ({result.get('rank_english', result.get('rank', '?'))})",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get crew member '%s': %s", crew_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get crew member"),
                output_mode,
            )
