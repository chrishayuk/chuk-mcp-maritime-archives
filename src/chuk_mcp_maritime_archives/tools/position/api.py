"""MCP tools for assessing historical position quality and uncertainty."""

import logging

from ...constants import ErrorMessages
from ...models import (
    ErrorResponse,
    PositionAssessmentResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_position_tools(mcp: object, manager: object) -> None:
    """Register position assessment tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_assess_position(
        voyage_id: str | None = None,
        wreck_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        source_description: str | None = None,
        date: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Assess the quality and uncertainty of a historical position.

        Evaluates a position based on the navigation technology available
        at the time, the source quality, and known factors. Returns a
        quality score, uncertainty radius, and recommendations for
        drift modelling and search planning.

        Provide either a voyage_id, wreck_id, or explicit lat/lon coordinates.
        The assessment considers the era of navigation technology (cross-staff,
        backstaff, octant, chronometer) and the source description.

        Args:
            voyage_id: Voyage identifier to assess its incident position
            wreck_id: Wreck identifier to assess its recorded position
            latitude: Explicit latitude in decimal degrees (WGS84)
            longitude: Explicit longitude in decimal degrees (WGS84)
            source_description: Description of position source for quality
                scoring. Keywords that improve scoring: "GPS", "surveyed",
                "multiple sources", "triangulated". Keywords that lower
                scoring: "dead reckoning", "approximate", "regional"
            date: Date for navigation era lookup (YYYY or YYYY-MM-DD),
                used when no voyage_id or wreck_id is provided
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with position quality assessment

        Tips for LLMs:
            - Provide voyage_id or wreck_id to automatically look up
              the position and date from the archive
            - The quality_score ranges from 0 (unknown) to 1 (precise GPS)
            - uncertainty_radius_km defines the search area envelope
            - The recommendations field provides actionable guidance for
              drift modelling and search planning
            - For modern surveyed wrecks, include "GPS" or "surveyed" in
              source_description to get a precise assessment
            - For historical positions from ship logs, include "dead reckoning"
              to reflect the navigational limitations
            - Navigation accuracy improved over time: 1595-1650 (~30km),
              1650-1700 (~25km), 1700-1760 (~20km), 1760-1795 (~10km)
        """
        try:
            position = None
            if latitude is not None and longitude is not None:
                position = {"lat": latitude, "lon": longitude}

            result = await manager.assess_position(  # type: ignore[union-attr]
                voyage_id=voyage_id,
                wreck_id=wreck_id,
                position=position,
                source_description=source_description,
                date=date,
            )

            quality = result.get("assessment", {})
            quality_label = quality.get("quality_label", "unknown")
            uncertainty_km = quality.get("uncertainty_radius_km", "?")

            return format_response(
                PositionAssessmentResponse(
                    assessment=result,
                    message=(
                        f"Position quality: {quality_label} "
                        f"(+/-{uncertainty_km}km uncertainty)"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Position assessment failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Position assessment failed"),
                output_mode,
            )
