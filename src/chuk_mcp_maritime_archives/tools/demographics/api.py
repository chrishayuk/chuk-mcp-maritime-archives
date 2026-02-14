"""MCP tools for crew demographics, career reconstruction, and survival analysis."""

import logging

from ...models import (
    CareerRecord,
    CareerVoyage,
    CrewCareerResponse,
    CrewDemographicsResponse,
    CrewSurvivalResponse,
    DemographicsGroup,
    ErrorResponse,
    SurvivalGroup,
    format_response,
)

logger = logging.getLogger(__name__)


def register_demographics_tools(mcp: object, manager: object) -> None:
    """Register crew demographics tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_crew_demographics(
        group_by: str = "rank",
        date_range: str | None = None,
        rank: str | None = None,
        origin: str | None = None,
        fate: str | None = None,
        ship_name: str | None = None,
        top_n: int = 25,
        output_mode: str = "json",
    ) -> str:
        """
        Aggregate crew demographics by rank, origin, fate, decade, or ship.

        Analyses the VOC Opvarenden dataset (774K crew records) to show
        distributions and patterns in crew composition.

        Args:
            group_by: Dimension to group by — "rank", "origin", "fate",
                      "decade", or "ship_name"
            date_range: Filter by embarkation date (e.g. "1700/1750")
            rank: Filter by rank substring (e.g. "matroos")
            origin: Filter by origin substring (e.g. "Amsterdam")
            fate: Filter by exact fate (e.g. "deserted")
            ship_name: Filter by ship name substring
            top_n: Number of top groups to return (default 25)
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with demographic breakdown

        Tips for LLMs:
            - Use group_by="origin" to study labour migration patterns
            - Use group_by="decade" to track workforce trends over time
            - Use group_by="rank" for crew composition analysis
            - Use group_by="fate" to see overall outcome distribution
            - Combine filters: rank="matroos" + group_by="decade" shows
              sailor recruitment trends
            - Each group includes a fate sub-distribution for deeper analysis
        """
        try:
            result = manager.crew_demographics(  # type: ignore[union-attr]
                group_by=group_by,
                date_range=date_range,
                rank=rank,
                origin=origin,
                fate=fate,
                ship_name=ship_name,
                top_n=top_n,
            )
            groups = [DemographicsGroup(**g) for g in result["groups"]]
            return format_response(
                CrewDemographicsResponse(
                    total_records=result["total_records"],
                    total_filtered=result["total_filtered"],
                    group_by=result["group_by"],
                    group_count=result["group_count"],
                    groups=groups,
                    other_count=result.get("other_count", 0),
                    filters_applied=result.get("filters_applied", {}),
                    message=(
                        f"Crew demographics by {group_by}: "
                        f"{result['group_count']} groups from "
                        f"{result['total_filtered']} records"
                    ),
                ),
                output_mode,
            )
        except ValueError as e:
            return format_response(
                ErrorResponse(error=str(e), message="Invalid demographics request"),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get crew demographics: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get crew demographics"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_crew_career(
        name: str,
        origin: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Reconstruct career history for crew members matching a name.

        Searches the VOC Opvarenden dataset for all records matching the
        given name, groups them by individual (using name + origin), and
        reconstructs each person's career chronologically.

        Args:
            name: Name to search for (substring, case-insensitive)
            origin: Optional origin city to disambiguate (exact match)
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with career reconstruction(s)

        Tips for LLMs:
            - Common names may match multiple individuals; use origin
              to disambiguate
            - Look at ranks_held to see career progression
              (e.g. matroos -> stuurman -> schipper)
            - career_span_years shows how long someone served the VOC
            - final_fate shows how their career ended
            - Each voyage includes ship_name, rank, and embarkation_date
        """
        try:
            result = manager.crew_career(  # type: ignore[union-attr]
                name=name,
                origin=origin,
            )
            individuals = [
                CareerRecord(
                    name=ind["name"],
                    origin=ind.get("origin"),
                    voyage_count=ind["voyage_count"],
                    first_date=ind.get("first_date"),
                    last_date=ind.get("last_date"),
                    career_span_years=ind.get("career_span_years"),
                    distinct_ships=ind.get("distinct_ships", []),
                    ranks_held=ind.get("ranks_held", []),
                    final_fate=ind.get("final_fate"),
                    voyages=[CareerVoyage(**v) for v in ind.get("voyages", [])],
                )
                for ind in result["individuals"]
            ]
            return format_response(
                CrewCareerResponse(
                    query_name=result["query_name"],
                    query_origin=result.get("query_origin"),
                    individual_count=result["individual_count"],
                    total_matches=result["total_matches"],
                    individuals=individuals,
                    message=(
                        f"Found {result['individual_count']} individual(s) "
                        f"matching '{name}' ({result['total_matches']} total records)"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get crew career: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get crew career"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_crew_survival_analysis(
        group_by: str = "rank",
        date_range: str | None = None,
        rank: str | None = None,
        origin: str | None = None,
        top_n: int = 25,
        output_mode: str = "json",
    ) -> str:
        """
        Analyse survival, mortality, and desertion rates for VOC crews.

        Computes rates from the service_end_reason field across the VOC
        Opvarenden dataset, grouped by the chosen dimension.

        Args:
            group_by: Dimension to group by — "rank", "origin", "fate",
                      "decade", or "ship_name"
            date_range: Filter by embarkation date (e.g. "1700/1750")
            rank: Filter by rank substring (e.g. "soldaat")
            origin: Filter by origin substring (e.g. "Rotterdam")
            top_n: Number of top groups to return (default 25)
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with survival analysis

        Tips for LLMs:
            - group_by="rank" reveals which ranks had highest mortality
            - group_by="decade" shows how mortality changed over the VOC era
            - group_by="origin" shows whether origin city affected survival
            - survival_rate = percentage who returned home
            - mortality_rate = percentage who died (voyage + Asia combined)
            - desertion_rate = percentage who deserted
            - Rates are per 100 crew with known fate
        """
        try:
            result = manager.crew_survival(  # type: ignore[union-attr]
                group_by=group_by,
                date_range=date_range,
                rank=rank,
                origin=origin,
                top_n=top_n,
            )
            groups = [SurvivalGroup(**g) for g in result["groups"]]
            return format_response(
                CrewSurvivalResponse(
                    total_records=result["total_records"],
                    total_with_known_fate=result["total_with_known_fate"],
                    group_by=result["group_by"],
                    group_count=result["group_count"],
                    groups=groups,
                    filters_applied=result.get("filters_applied", {}),
                    message=(
                        f"Survival analysis by {group_by}: "
                        f"{result['group_count']} groups from "
                        f"{result['total_with_known_fate']} records with known fate"
                    ),
                ),
                output_mode,
            )
        except ValueError as e:
            return format_response(
                ErrorResponse(error=str(e), message="Invalid survival analysis request"),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get survival analysis: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get survival analysis"),
                output_mode,
            )
