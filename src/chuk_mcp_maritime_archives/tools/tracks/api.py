"""MCP tools for searching CLIWOC historical ship tracks."""

import logging

from ...constants import ErrorMessages
from ...core.cliwoc_tracks import (
    get_track,
    nearby_tracks,
    search_tracks,
)
from ...models import (
    ErrorResponse,
    NearbyTrackInfo,
    NearbyTracksResponse,
    TrackDetailResponse,
    TrackInfo,
    TrackSearchResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_tracks_tools(mcp: object, manager: object) -> None:
    """Register CLIWOC ship track tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_search_tracks(
        nationality: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        max_results: int = 50,
        output_mode: str = "json",
    ) -> str:
        """
        Search historical ship tracks from the CLIWOC database (1662-1855).

        Returns voyage track summaries from ~261K daily logbook observations
        recorded by 8 European maritime nations. Each track represents one
        voyage with dated lat/lon positions from the ship's logbook.

        Args:
            nationality: Two-letter nationality code to filter by.
                Options: NL (Dutch), UK (British), ES (Spanish), FR (French),
                SE (Swedish), US (American), DE (German), DK (Danish)
            year_start: Earliest year to include (e.g., 1700)
            year_end: Latest year to include (e.g., 1750)
            max_results: Maximum results (default: 50)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with matching track summaries

        Tips for LLMs:
            - Use nationality filter to find ships of a specific nation
            - Combine year_start/year_end to narrow to a specific period
            - Results show track summaries (start/end dates, position count)
            - Follow up with maritime_get_track to get full position data
            - Use maritime_nearby_tracks to find ships near a wreck site
            - CLIWOC covers 1662-1855 with most data from 1750-1850
            - Nationality breakdown: UK (732), NL (677), ES (472), FR (85)
        """
        try:
            results = search_tracks(
                nationality=nationality,
                year_start=year_start,
                year_end=year_end,
                max_results=max_results,
            )

            if not results:
                return format_response(
                    ErrorResponse(error=ErrorMessages.NO_RESULTS),
                    output_mode,
                )

            tracks = [
                TrackInfo(
                    voyage_id=r["voyage_id"],
                    nationality=r.get("nationality"),
                    start_date=r.get("start_date"),
                    end_date=r.get("end_date"),
                    duration_days=r.get("duration_days"),
                    year_start=r.get("year_start"),
                    year_end=r.get("year_end"),
                    position_count=r.get("position_count", 0),
                )
                for r in results
            ]

            return format_response(
                TrackSearchResponse(
                    track_count=len(tracks),
                    tracks=tracks,
                    message=f"Found {len(tracks)} CLIWOC tracks",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Track search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Track search failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_track(
        voyage_id: int,
        output_mode: str = "json",
    ) -> str:
        """
        Get full position history for a CLIWOC voyage.

        Returns the complete track including all dated lat/lon positions
        from the ship's logbook. Positions are daily observations
        recorded by the ship's navigator.

        Args:
            voyage_id: CLIWOC voyage ID (integer, from search results)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with full track including positions

        Tips for LLMs:
            - Get voyage_id from maritime_search_tracks results
            - Positions are daily logbook readings, not continuous
            - Gaps in dates indicate missing logbook entries
            - Use positions to reconstruct the ship's route on a map
            - Combine with maritime_export_geojson for mapping
            - Position accuracy varies: typically ±20-50km for this era
        """
        try:
            track = get_track(voyage_id)

            if track is None:
                return format_response(
                    ErrorResponse(
                        error=f"CLIWOC voyage {voyage_id} not found. "
                        "Use maritime_search_tracks to find valid voyage IDs.",
                    ),
                    output_mode,
                )

            return format_response(
                TrackDetailResponse(
                    track=track,
                    message=f"CLIWOC voyage {voyage_id}: "
                    f"{track.get('position_count', 0)} positions",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Track lookup failed for voyage %s: %s", voyage_id, e)
            return format_response(
                ErrorResponse(error=str(e), message="Track lookup failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_nearby_tracks(
        lat: float,
        lon: float,
        date: str,
        radius_km: float = 200.0,
        max_results: int = 20,
        output_mode: str = "json",
    ) -> str:
        """
        Find ships near a given position on a given date.

        Searches all CLIWOC logbook positions for the specified date
        and returns tracks with positions within the search radius.
        Useful for finding what other ships were in an area when
        a wreck or incident occurred.

        Args:
            lat: Latitude of search point (decimal degrees)
            lon: Longitude of search point (decimal degrees)
            date: Date to search (YYYY-MM-DD format)
            radius_km: Search radius in kilometres (default: 200)
            max_results: Maximum results (default: 20)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with nearby tracks sorted by distance

        Tips for LLMs:
            - Use with wreck positions to find potential witness ships
            - Increase radius_km if no results (ships were sparse)
            - Date must be exact YYYY-MM-DD — logbook entries are daily
            - Try adjacent dates if exact date yields no results
            - Results include distance_km and matching position
            - CLIWOC covers 1662-1855; earlier dates have fewer records
            - Combine with maritime_assess_position for uncertainty context
        """
        try:
            results = nearby_tracks(
                lat=lat,
                lon=lon,
                date=date,
                radius_km=radius_km,
                max_results=max_results,
            )

            if not results:
                return format_response(
                    ErrorResponse(
                        error=f"No CLIWOC tracks found within {radius_km}km of "
                        f"({lat}, {lon}) on {date}. Try a larger radius or "
                        "adjacent dates.",
                    ),
                    output_mode,
                )

            tracks = [
                NearbyTrackInfo(
                    voyage_id=r["voyage_id"],
                    nationality=r.get("nationality"),
                    start_date=r.get("start_date"),
                    end_date=r.get("end_date"),
                    duration_days=r.get("duration_days"),
                    position_count=r.get("position_count", 0),
                    distance_km=r["distance_km"],
                    matching_position=r["matching_position"],
                )
                for r in results
            ]

            return format_response(
                NearbyTracksResponse(
                    search_point={"lat": lat, "lon": lon},
                    search_date=date,
                    radius_km=radius_km,
                    track_count=len(tracks),
                    tracks=tracks,
                    message=f"Found {len(tracks)} tracks within {radius_km}km on {date}",
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Nearby tracks search failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Nearby tracks search failed"),
                output_mode,
            )
