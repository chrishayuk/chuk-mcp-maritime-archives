"""MCP tools for server discovery and capability listing."""

import logging

from ...constants import REGIONS, SHIP_TYPES, ServerConfig
from ...models import (
    ArchiveInfo,
    CapabilitiesResponse,
    ErrorResponse,
    ToolInfo,
    format_response,
)

logger = logging.getLogger(__name__)


def register_discovery_tools(mcp: object, manager: object) -> None:
    """Register discovery tools with the MCP server."""

    @mcp.tool  # type: ignore[union-attr]
    async def maritime_capabilities(
        output_mode: str = "json",
    ) -> str:
        """
        List full server capabilities: archives, tools, and reference data.

        Returns a comprehensive overview of this maritime archives server
        including all available archives, registered tools, supported ship
        types, and geographic regions. Call this first to understand what
        the server can do.

        Args:
            output_mode: Response format - "json" (default) or "text"

        Returns:
            JSON or text with server capabilities

        Tips for LLMs:
            - Call this FIRST to plan a research workflow
            - The archives list shows available data sources and their
              coverage periods
            - The tools list shows every registered tool with its category
              and description
            - ship_types lists valid values for vessel type filters
            - regions lists valid values for geographic region filters
            - Typical workflow: maritime_capabilities -> maritime_search_voyages
              or maritime_search_wrecks -> detail tools -> export/analysis
        """
        try:
            # Build archive info list
            archive_dicts = manager.list_archives()  # type: ignore[union-attr]
            archives = [
                ArchiveInfo(
                    archive_id=a.get("id", ""),
                    name=a.get("name", ""),
                    organisation=a.get("organisation"),
                    coverage_start=a.get("coverage_start"),
                    coverage_end=a.get("coverage_end"),
                    record_types=a.get("record_types", []),
                    total_records=a.get("total_voyages")
                    or a.get("total_records")
                    or a.get("total_wrecks"),
                    description=a.get("description"),
                )
                for a in archive_dicts
            ]

            # Build tool info list
            tools = [
                ToolInfo(
                    name="maritime_list_archives",
                    category="archives",
                    description="List all available maritime archives",
                ),
                ToolInfo(
                    name="maritime_get_archive",
                    category="archives",
                    description="Get detailed metadata for a specific archive",
                ),
                ToolInfo(
                    name="maritime_search_voyages",
                    category="voyages",
                    description="Search for VOC voyages by ship, captain, date, port, or fate",
                ),
                ToolInfo(
                    name="maritime_get_voyage",
                    category="voyages",
                    description="Get full details for a specific voyage",
                ),
                ToolInfo(
                    name="maritime_search_wrecks",
                    category="wrecks",
                    description="Search for VOC shipwrecks by name, region, cause, or status",
                ),
                ToolInfo(
                    name="maritime_get_wreck",
                    category="wrecks",
                    description="Get full details for a specific wreck record",
                ),
                ToolInfo(
                    name="maritime_search_vessels",
                    category="vessels",
                    description="Search for VOC vessels by name, type, or construction details",
                ),
                ToolInfo(
                    name="maritime_get_vessel",
                    category="vessels",
                    description="Get full vessel specification",
                ),
                ToolInfo(
                    name="maritime_get_hull_profile",
                    category="vessels",
                    description="Get hydrodynamic hull profile for a ship type",
                ),
                ToolInfo(
                    name="maritime_list_hull_profiles",
                    category="vessels",
                    description="List ship types with available hull profiles",
                ),
                ToolInfo(
                    name="maritime_search_crew",
                    category="crew",
                    description="Search VOC crew muster records",
                ),
                ToolInfo(
                    name="maritime_get_crew_member",
                    category="crew",
                    description="Get full crew member record",
                ),
                ToolInfo(
                    name="maritime_search_cargo",
                    category="cargo",
                    description="Search VOC cargo records",
                ),
                ToolInfo(
                    name="maritime_get_cargo_manifest",
                    category="cargo",
                    description="Get full cargo manifest for a voyage",
                ),
                ToolInfo(
                    name="maritime_lookup_location",
                    category="location",
                    description="Look up a historical place name in the VOC gazetteer",
                ),
                ToolInfo(
                    name="maritime_list_locations",
                    category="location",
                    description="Search or browse VOC places by region, type, or text",
                ),
                ToolInfo(
                    name="maritime_list_routes",
                    category="routes",
                    description="List standard VOC sailing routes",
                ),
                ToolInfo(
                    name="maritime_get_route",
                    category="routes",
                    description="Get full route with waypoints, hazards, and season notes",
                ),
                ToolInfo(
                    name="maritime_estimate_position",
                    category="routes",
                    description="Estimate ship position on a date from route and departure",
                ),
                ToolInfo(
                    name="maritime_search_tracks",
                    category="tracks",
                    description="Search CLIWOC historical ship tracks by nationality and date",
                ),
                ToolInfo(
                    name="maritime_get_track",
                    category="tracks",
                    description="Get full position history for a CLIWOC voyage",
                ),
                ToolInfo(
                    name="maritime_nearby_tracks",
                    category="tracks",
                    description="Find ships near a position on a given date",
                ),
                ToolInfo(
                    name="maritime_get_voyage_full",
                    category="linking",
                    description="Get unified view of a voyage with all linked records",
                ),
                ToolInfo(
                    name="maritime_get_timeline",
                    category="linking",
                    description="Build chronological timeline of events for a voyage",
                ),
                ToolInfo(
                    name="maritime_get_speed_profile",
                    category="routes",
                    description="Get historical sailing speed statistics for a route",
                ),
                ToolInfo(
                    name="maritime_assess_position",
                    category="position",
                    description="Assess quality and uncertainty of a historical position",
                ),
                ToolInfo(
                    name="maritime_export_geojson",
                    category="export",
                    description="Export wreck positions as GeoJSON FeatureCollection",
                ),
                ToolInfo(
                    name="maritime_get_statistics",
                    category="export",
                    description="Get aggregate statistics across archives",
                ),
                ToolInfo(
                    name="maritime_search_narratives",
                    category="narratives",
                    description="Search narrative text across all archives",
                ),
                ToolInfo(
                    name="maritime_compute_track_speeds",
                    category="analytics",
                    description="Compute daily sailing speeds for a single voyage",
                ),
                ToolInfo(
                    name="maritime_aggregate_track_speeds",
                    category="analytics",
                    description="Aggregate track speeds by decade, month, direction, or nationality",
                ),
                ToolInfo(
                    name="maritime_compare_speed_groups",
                    category="analytics",
                    description="Compare speed distributions between two time periods (Mann-Whitney U)",
                ),
                ToolInfo(
                    name="maritime_capabilities",
                    category="discovery",
                    description="List full server capabilities",
                ),
            ]

            return format_response(
                CapabilitiesResponse(
                    server_name=ServerConfig.NAME,
                    version=ServerConfig.VERSION,
                    archives=archives,
                    tools=tools,
                    ship_types=list(SHIP_TYPES.keys()),
                    regions=dict(REGIONS),
                    message=(
                        f"{ServerConfig.NAME} v{ServerConfig.VERSION}: "
                        f"{len(archives)} archives, {len(tools)} tools"
                    ),
                ),
                output_mode,
            )
        except Exception as e:
            logger.error("Failed to get capabilities: %s", e)
            return format_response(
                ErrorResponse(error=str(e), message="Failed to get capabilities"),
                output_mode,
            )
