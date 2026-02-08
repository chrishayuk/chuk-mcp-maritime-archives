"""
Async server setup for chuk-mcp-maritime-archives.

Creates the ChukMCPServer instance, instantiates the ArchiveManager,
and registers all tool groups.
"""

from chuk_mcp_server import ChukMCPServer

from .constants import ServerConfig
from .core.archive_manager import ArchiveManager
from .tools import (
    register_archive_tools,
    register_cargo_tools,
    register_crew_tools,
    register_discovery_tools,
    register_export_tools,
    register_position_tools,
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
register_discovery_tools(mcp, manager)
