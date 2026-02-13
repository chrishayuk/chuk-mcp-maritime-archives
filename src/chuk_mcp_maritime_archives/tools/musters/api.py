"""MCP tools for searching GZMVOC ship muster records and comparing wages."""

import logging

from ...constants import ErrorMessages, SuccessMessages
from ...models import (
    ErrorResponse,
    MusterDetailResponse,
    MusterInfo,
    MusterSearchResponse,
    WageComparisonResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_muster_tools(mcp: object, manager: object) -> None:
    """Register muster tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_musters(
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        location: str | None = None,
        das_voyage_id: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        max_results: int = 50,
        cursor: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Search GZMVOC ship-level muster records from Asian waters.

        Queries the Generale Zeemonsterrollen VOC database containing
        ship crew composition, wages, and staffing data from VOC ships
        stationed in Asia, 1691-1791. Complements VOC Opvarenden which
        records departures from the Netherlands.

        Args:
            ship_name: Ship name or partial name (case-insensitive)
            captain: Captain name or partial name
            date_range: Date range as "YYYY/YYYY" or "YYYY-MM-DD/YYYY-MM-DD"
            location: Muster location (e.g., Batavia, Makassar, Ceylon)
            das_voyage_id: Link to a specific DAS voyage identifier
            year_start: Filter musters from this year onward
            year_end: Filter musters up to this year
            max_results: Maximum results per page (default: 50, max: 500)
            cursor: Pagination cursor from a previous result's next_cursor field
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching muster records and pagination metadata

        Tips for LLMs:
            - Musters record crew composition at Asian ports, not departures
            - Use location to filter by port (Batavia, Makassar, Colombo, etc.)
            - Use year_start/year_end for temporal queries within 1691-1791
            - Cross-link to DAS voyages using das_voyage_id field
            - Follow up with maritime_get_muster for full crew breakdown
            - Use maritime_compare_wages to analyze wage trends over time
        """
        try:
            result = await manager.search_musters(  # type: ignore[union-attr]
                ship_name=ship_name,
                captain=captain,
                date_range=date_range,
                location=location,
                das_voyage_id=das_voyage_id,
                year_start=year_start,
                year_end=year_end,
                max_results=max_results,
                cursor=cursor,
            )

            if not result.items:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            musters = [
                MusterInfo(
                    muster_id=m.get("muster_id", ""),
                    ship_name=m.get("ship_name", ""),
                    captain=m.get("captain"),
                    muster_date=m.get("muster_date"),
                    muster_location=m.get("muster_location"),
                    total_crew=m.get("total_crew"),
                    das_voyage_id=m.get("das_voyage_id"),
                    archive=m.get("archive"),
                )
                for m in result.items
            ]

            return format_response(
                MusterSearchResponse(
                    muster_count=len(musters),
                    musters=musters,
                    message=SuccessMessages.MUSTERS_FOUND.format(len(musters)),
                    total_count=result.total_count,
                    next_cursor=result.next_cursor,
                    has_more=result.has_more,
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Muster search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Muster search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_muster(
        muster_id: str,
        output_mode: str = "json",
    ) -> str:
        """
        Get full details for a specific ship muster record.

        Returns the complete GZMVOC muster record including ship name,
        captain, crew composition by rank, total European and Asian crew,
        aggregate wages, and linked DAS voyage ID.

        Args:
            muster_id: Muster record identifier (e.g., "dss_muster:0001")
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full muster record details

        Tips for LLMs:
            - Use maritime_search_musters first to find the muster_id
            - ranks_summary shows crew counts per rank (Dutch names)
            - total_european + total_asian = total_crew
            - mean_wage_guilders is the average monthly wage across all crew
            - If das_voyage_id is set, use maritime_get_voyage to get voyage context
            - Compare with maritime_search_crew archive="dss" for individual
              MDB crew records from the post-VOC era (1803-1837)
        """
        try:
            result = await manager.get_muster(muster_id)  # type: ignore[union-attr]

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.MUSTER_NOT_FOUND.format(muster_id),
                    ),
                    output_mode,
                )

            return format_response(
                MusterDetailResponse(
                    muster=result,
                    message=f"Muster: {result.get('ship_name', '?')} at {result.get('muster_location', '?')} ({result.get('muster_date', '?')})",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get muster '%s': %s", muster_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get muster record"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_compare_wages(
        group1_start: int,
        group1_end: int,
        group2_start: int,
        group2_end: int,
        rank: str | None = None,
        origin: str | None = None,
        source: str = "musters",
        output_mode: str = "json",
    ) -> str:
        """
        Compare crew wage distributions between two time periods.

        Calculates mean and median wages for two year ranges and reports
        the percentage difference. Can use GZMVOC aggregate muster data
        (1691-1791) or MDB individual crew records (1803-1837).

        Args:
            group1_start: Start year for first comparison group
            group1_end: End year for first comparison group
            group2_start: Start year for second comparison group
            group2_end: End year for second comparison group
            rank: Optional rank filter (e.g., matroos, stuurman)
            origin: Optional place of origin filter (MDB crews only)
            source: Data source - "musters" for GZMVOC aggregate data,
                "crews" for MDB individual records
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with wage comparison statistics

        Tips for LLMs:
            - Use source="musters" for VOC Asian muster data (1691-1791)
            - Use source="crews" for post-VOC individual records (1803-1837)
            - The difference_pct shows group2 relative to group1
            - Combine with rank filter to compare wages for specific roles
            - origin filter only works with source="crews" (MDB records)
            - Consider inflation: guilder purchasing power changed over time
        """
        try:
            result = await manager.compare_wages(  # type: ignore[union-attr]
                group1_start=group1_start,
                group1_end=group1_end,
                group2_start=group2_start,
                group2_end=group2_end,
                rank=rank,
                origin=origin,
                source=source,
            )

            return format_response(
                WageComparisonResponse(
                    group1_label=result["group1_label"],
                    group1_n=result["group1_n"],
                    group1_mean_wage=result["group1_mean_wage"],
                    group1_median_wage=result["group1_median_wage"],
                    group2_label=result["group2_label"],
                    group2_n=result["group2_n"],
                    group2_mean_wage=result["group2_mean_wage"],
                    group2_median_wage=result["group2_median_wage"],
                    difference_pct=result["difference_pct"],
                    message=SuccessMessages.WAGES_COMPARED.format(
                        result["group1_label"],
                        result["group1_n"],
                        result["group2_label"],
                        result["group2_n"],
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Wage comparison failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Wage comparison failed"),
                output_mode,
            )
