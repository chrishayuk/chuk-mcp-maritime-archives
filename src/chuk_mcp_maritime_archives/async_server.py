"""
Async server setup for chuk-mcp-maritime-archives.

Creates the ChukMCPServer instance, instantiates the ArchiveManager,
and registers all tool groups.
"""

from chuk_mcp_server import ChukMCPServer

from .constants import ServerConfig
from .core.archive_manager import ArchiveManager
from .tools import (
    register_analytics_tools,
    register_archive_tools,
    register_cargo_tools,
    register_crew_tools,
    register_demographics_tools,
    register_discovery_tools,
    register_export_tools,
    register_linking_tools,
    register_location_tools,
    register_muster_tools,
    register_narrative_tools,
    register_position_tools,
    register_route_tools,
    register_speed_tools,
    register_timeline_tools,
    register_tracks_tools,
    register_vessel_tools,
    register_voyage_tools,
    register_wreck_tools,
)

mcp = ChukMCPServer(ServerConfig.NAME)
manager = ArchiveManager()

# Register all tool groups
register_archive_tools(mcp, manager)
register_voyage_tools(mcp, manager)
register_crew_tools(mcp, manager)
register_cargo_tools(mcp, manager)
register_wreck_tools(mcp, manager)
register_vessel_tools(mcp, manager)
register_position_tools(mcp, manager)
register_export_tools(mcp, manager)
register_location_tools(mcp, manager)
register_route_tools(mcp, manager)
register_tracks_tools(mcp, manager)
register_linking_tools(mcp, manager)
register_speed_tools(mcp, manager)
register_timeline_tools(mcp, manager)
register_muster_tools(mcp, manager)
register_narrative_tools(mcp, manager)
register_analytics_tools(mcp, manager)
register_demographics_tools(mcp, manager)
register_discovery_tools(mcp, manager)
