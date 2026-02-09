"""MCP tools for building chronological voyage timelines."""

import json
import logging

from ...constants import ArtifactScope, ErrorMessages, MimeType
from ...models import (
    ErrorResponse,
    TimelineEvent,
    TimelineResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_timeline_tools(mcp: object, manager: object) -> None:
    """Register timeline tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_timeline(
        voyage_id: str,
        include_positions: bool = False,
        max_positions: int = 20,
        output_mode: str = "json",
    ) -> str:
        """
        Build a chronological timeline of events for a voyage.

        Combines data from multiple archives — DAS voyages, MAARER wrecks,
        CLIWOC ship tracks, and route estimates — into a single chronological
        sequence of events. Optionally includes CLIWOC position data.

        Args:
            voyage_id: DAS voyage identifier (e.g., "5999.1")
            include_positions: Include CLIWOC track positions as events
                (default False, can add many events)
            max_positions: Maximum CLIWOC positions to include (default 20)
            output_mode: Response format — "json" (default) or "text"

        Returns:
            JSON or text with chronological event list, optional GeoJSON
            track, and list of data sources consulted

        Tips for LLMs:
            - Start with include_positions=False to see major events
            - Set include_positions=True for detailed track reconstruction
            - Events from different sources may have conflicting dates
            - The geojson field contains a LineString of all positioned events
            - Use maritime_get_voyage_full for non-chronological linked data
        """
        try:
            result = await manager.build_timeline(  # type: ignore[union-attr]
                voyage_id=voyage_id,
                include_positions=include_positions,
                max_positions=max_positions,
            )

            if result is None:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.TIMELINE_VOYAGE_NOT_FOUND.format(voyage_id),
                    ),
                    output_mode,
                )

            events_data = result.get("events", [])
            if not events_data:
                return format_response(
                    ErrorResponse(
                        error=ErrorMessages.TIMELINE_NO_EVENTS.format(voyage_id),
                    ),
                    output_mode,
                )

            events = [
                TimelineEvent(
                    date=e["date"],
                    type=e["type"],
                    title=e["title"],
                    details=e.get("details", {}),
                    position=e.get("position"),
                    source=e["source"],
                )
                for e in events_data
            ]

            # Store timeline GeoJSON to artifact store if available
            artifact_ref = None
            geojson_data = result.get("geojson")
            if geojson_data:
                try:
                    from chuk_mcp_server import get_artifact_store

                    store = get_artifact_store()
                    if store is not None:
                        geojson_bytes = json.dumps(geojson_data).encode("utf-8")
                        artifact_ref = await store.store(
                            data=geojson_bytes,
                            mime=MimeType.GEOJSON,
                            summary=f"Timeline GeoJSON for voyage {voyage_id}",
                            meta={"voyage_id": voyage_id},
                            filename=f"timeline_{voyage_id}.geojson",
                            scope=ArtifactScope.SANDBOX,
                        )
                except Exception:
                    logger.debug("Artifact store unavailable for timeline GeoJSON")

            return format_response(
                TimelineResponse(
                    voyage_id=voyage_id,
                    ship_name=result.get("ship_name"),
                    event_count=len(events),
                    events=events,
                    geojson=geojson_data,
                    artifact_ref=artifact_ref,
                    data_sources=result.get("data_sources", []),
                    message=(
                        f"Timeline for voyage {voyage_id}: "
                        f"{len(events)} events from "
                        f"{', '.join(result.get('data_sources', []))}"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Timeline build failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Timeline build failed"),
                output_mode,
            )
