"""MCP tool registration for chuk-mcp-maritime-archives."""

from .archives.api import register_archive_tools
from .cargo.api import register_cargo_tools
from .crew.api import register_crew_tools
from .discovery.api import register_discovery_tools
from .export.api import register_export_tools
from .location.api import register_location_tools
from .position.api import register_position_tools
from .routes.api import register_route_tools
from .tracks.api import register_tracks_tools
from .vessels.api import register_vessel_tools
from .voyages.api import register_voyage_tools
from .wrecks.api import register_wreck_tools

__all__ = [
    "register_archive_tools",
    "register_cargo_tools",
    "register_crew_tools",
    "register_discovery_tools",
    "register_export_tools",
    "register_location_tools",
    "register_position_tools",
    "register_route_tools",
    "register_tracks_tools",
    "register_vessel_tools",
    "register_voyage_tools",
    "register_wreck_tools",
]
