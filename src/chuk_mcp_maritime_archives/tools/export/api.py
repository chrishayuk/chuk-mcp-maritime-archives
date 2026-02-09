"""MCP tools for exporting wreck data as GeoJSON and computing statistics."""

import json
import logging

from ...constants import ArtifactScope, MimeType, SuccessMessages
from ...models import (
    ErrorResponse,
    GeoJSONExportResponse,
    StatisticsResponse,
    format_response,
)

logger = logging.getLogger(__name__)


def register_export_tools(mcp: object, manager: object) -> None:
    """Register export and statistics tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_export_geojson(
        wreck_ids: list[str] | None = None,
        region: str | None = None,
        status: str | None = None,
        archive: str | None = None,
        include_uncertainty: bool = True,
        include_voyage_data: bool = True,
        output_mode: str = "json",
    ) -> str:
        """
        Export wreck positions as a GeoJSON FeatureCollection.

        Creates a GeoJSON document with Point features for each wreck
        site. Can export specific wrecks by ID or all wrecks matching
        filter criteria. Suitable for mapping and GIS analysis.

        Args:
            wreck_ids: Specific wreck IDs to export (overrides other filters)
            region: Region filter. Options: north_sea, atlantic_europe,
                atlantic_crossing, cape, mozambique_channel, indian_ocean,
                malabar, coromandel, ceylon, bengal, malacca, indonesia,
                south_china_sea, japan, caribbean
            status: Wreck status filter - found, unfound, approximate
            archive: Restrict to a specific archive
            include_uncertainty: Include position uncertainty radius in
                properties (default: true)
            include_voyage_data: Include ship type, tonnage, loss cause,
                lives lost, and depth in properties (default: true)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON with GeoJSON FeatureCollection and feature count

        Tips for LLMs:
            - Provide wreck_ids for a targeted export of specific sites
            - Use region and status filters for geographic or discovery
              status based exports
            - The GeoJSON uses WGS84 coordinates (EPSG:4326)
            - Include_uncertainty adds uncertainty_km to each feature's
              properties (useful for drawing search area buffers)
            - Include_voyage_data enriches features with vessel and loss
              context (useful for thematic mapping)
            - Use the output for mapping, spatial analysis, or as input
              to drift modelling tools
        """
        try:
            result = await manager.export_geojson(  # type: ignore[union-attr]
                wreck_ids=wreck_ids,
                region=region,
                status=status,
                archive=archive,
                include_uncertainty=include_uncertainty,
                include_voyage_data=include_voyage_data,
            )

            features = result.get("features", [])

            # Store to artifact store if available
            artifact_ref = None
            try:
                from chuk_mcp_server import get_artifact_store

                store = get_artifact_store()
                if store is not None:
                    geojson_bytes = json.dumps(result).encode("utf-8")
                    artifact_ref = await store.store(
                        data=geojson_bytes,
                        mime=MimeType.GEOJSON,
                        summary=f"GeoJSON export: {len(features)} wreck positions",
                        meta={"feature_count": len(features)},
                        filename="wreck_export.geojson",
                        scope=ArtifactScope.SANDBOX,
                    )
            except Exception:
                logger.debug("Artifact store unavailable for GeoJSON export")

            return format_response(
                GeoJSONExportResponse(
                    geojson=result,
                    feature_count=len(features),
                    artifact_ref=artifact_ref,
                    message=SuccessMessages.EXPORT_COMPLETE.format(len(features)),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("GeoJSON export failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="GeoJSON export failed"),
                output_mode,
            )

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_get_statistics(
        archive: str | None = None,
        date_range: str | None = None,
        group_by: str | None = None,
        output_mode: str = "json",
    ) -> str:
        """
        Get aggregate statistics across maritime archives.

        Computes summary statistics for VOC shipping losses including
        total losses, lives lost, cargo value, and breakdowns by region,
        cause, status, and decade.

        Args:
            archive: Restrict to a specific archive (default: all)
            date_range: Date range as "YYYY/YYYY" (default: 1595-1795)
            group_by: Grouping dimension (reserved for future use)
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with aggregate statistics

        Tips for LLMs:
            - Use date_range to focus statistics on a specific period
              (e.g., "1700/1750" for the early 18th century)
            - The response includes losses_by_region, losses_by_cause,
              losses_by_status, and losses_by_decade breakdowns
            - Total cargo_value_guilders_total gives the aggregate value
              of goods lost in all matched wrecks
            - Compare decades to identify trends in shipping safety
            - Compare regions to identify the most dangerous routes
        """
        try:
            result = await manager.get_statistics(  # type: ignore[union-attr]
                archive=archive,
                date_range=date_range,
                group_by=group_by,
            )

            summary = result.get("summary", {})
            total_losses = summary.get("total_losses", 0)
            date_str = result.get("date_range", "1595-1795")

            return format_response(
                StatisticsResponse(
                    statistics=result,
                    message=SuccessMessages.STATISTICS_COMPLETE.format(total_losses, date_str),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Statistics failed: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Statistics computation failed"),
                output_mode,
            )
