"""MCP tool for full-text narrative search across all maritime archives."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    NarrativeHit,
    NarrativeSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_narrative_tools(mcp: object, manager: object) -> None:
    """Register narrative search tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_narratives(
        query: str,
        record_type: str | None = None,
        archive: str | None = None,
        max_results: int = 50,
        cursor: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Search free-text narrative content across all maritime archives.

        Performs full-text search across voyage particulars, wreck particulars,
        and loss location descriptions.  All query terms must be present in a
        record for it to match (AND logic).  Use quoted phrases for exact
        multi-word matching (e.g. "Cape of Good Hope").

        Narrative fields searched:
            - Voyage ``particulars``: DAS, EIC, Carreira, Galleon, SOIC
            - Wreck ``particulars``: MAARER, EIC, Carreira, Galleon
            - Wreck ``loss_location``: all wreck archives

        Args:
            query: Search text — keywords or quoted phrases (e.g. "monsoon",
                '"Cape of Good Hope"', "storm cannon")
            record_type: Limit to "voyage" or "wreck" (default: both)
            archive: Restrict to a specific archive ID (e.g. "eic", "carreira")
            max_results: Maximum results per page (default: 50, max: 500)
            cursor: Pagination cursor from a previous result's next_cursor
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with matching narrative excerpts, snippets, and
            pagination metadata

        Tips for LLMs:
            - Use this tool for research questions like "find mentions of
              monsoon across all archives"
            - Quoted phrases match exactly: '"East India"' finds only that
              phrase, not "East" and "India" separately
            - Multiple unquoted words use AND logic: "storm cape" finds records
              containing both "storm" AND "cape"
            - Results are ranked by relevance (number of term occurrences)
            - Use record_type="voyage" or "wreck" to narrow results
            - Use archive to limit to one archive (e.g. archive="carreira")
            - Follow up with maritime_get_voyage or maritime_get_wreck for full
              record details
            - If has_more is true, pass next_cursor as cursor to get the next page
        """
        try:
            result = await manager.search_narratives(  # type: ignore[union-attr]
                query=query,
                record_type=record_type,
                archive=archive,
                max_results=max_results,
                cursor=cursor,
            )

            if not result.items:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            hits = [
                NarrativeHit(
                    record_id=h["record_id"],
                    record_type=h["record_type"],
                    archive=h["archive"],
                    ship_name=h["ship_name"],
                    date=h.get("date"),
                    field=h["field"],
                    snippet=h["snippet"],
                    match_count=h["match_count"],
                )
                for h in result.items
            ]

            return format_response(
                NarrativeSearchResponse(
                    result_count=len(hits),
                    results=hits,
                    query=query,
                    record_type=record_type,
                    archive=archive,
                    message=SuccessMessages.NARRATIVES_FOUND.format(result.total_count, query),
                    total_count=result.total_count,
                    next_cursor=result.next_cursor,
                    has_more=result.has_more,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Narrative search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Narrative search failed"),
                output_mode,
            )
