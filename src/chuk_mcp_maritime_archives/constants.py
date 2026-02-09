"""
Constants and configuration for chuk-mcp-maritime-archives.

All magic strings live here as enums or module-level constants.
"""

from enum import Enum
from typing import Literal


# --- Server Configuration -------------------------------------------------


class ServerConfig(str, Enum):
    NAME = "chuk-mcp-maritime-archives"
    VERSION = "0.5.0"
    DESCRIPTION = "Historical Maritime Archives"


# --- Storage / Session Providers -------------------------------------------


class StorageProvider(str, Enum):
    MEMORY = "memory"
    S3 = "s3"
    FILESYSTEM = "filesystem"


class SessionProvider(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"


# --- Environment Variable Names --------------------------------------------


class EnvVar:
    """Environment variable names used throughout the application."""

    ARTIFACTS_PROVIDER = "CHUK_ARTIFACTS_PROVIDER"
    BUCKET_NAME = "BUCKET_NAME"
    REDIS_URL = "REDIS_URL"
    ARTIFACTS_PATH = "CHUK_ARTIFACTS_PATH"
    AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
    AWS_ENDPOINT_URL_S3 = "AWS_ENDPOINT_URL_S3"
    MCP_STDIO = "MCP_STDIO"


# --- Archive Definitions ---------------------------------------------------


class ArchiveId(str, Enum):
    """Identifiers for supported maritime archives."""

    DAS = "das"
    VOC_CREW = "voc_crew"
    VOC_CARGO = "voc_cargo"
    MAARER = "maarer"


ARCHIVE_METADATA: dict[str, dict] = {
    "das": {
        "name": "Dutch Asiatic Shipping",
        "organisation": "Huygens Institute",
        "coverage_start": "1595",
        "coverage_end": "1795",
        "record_types": ["voyages", "vessels", "incidents"],
        "total_voyages": 8194,
        "total_losses": 734,
        "access_method": "api",
        "documentation_url": "https://resources.huygens.knaw.nl/das",
        "description": (
            "Comprehensive database of all VOC voyages between the Netherlands "
            "and Asia, 1595-1795. Based on J.R. Bruijn, F.S. Gaastra and "
            "I. Schoffer, Dutch-Asiatic Shipping in the 17th and 18th "
            "Centuries (1987)."
        ),
        "citation": (
            "Bruijn, J.R., F.S. Gaastra and I. Schoffer. Dutch-Asiatic "
            "Shipping in the 17th and 18th Centuries. 3 vols. The Hague, 1987."
        ),
        "license": "Open access for research",
    },
    "voc_crew": {
        "name": "VOC Opvarenden",
        "organisation": "Nationaal Archief",
        "coverage_start": "1633",
        "coverage_end": "1794",
        "record_types": ["crew"],
        "total_records": 774200,
        "access_method": "api",
        "documentation_url": "https://www.nationaalarchief.nl/onderzoeken/index/nt00444",
        "description": (
            "Crew muster rolls for VOC vessels. Contains personnel records "
            "including name, origin, rank, pay, and fate for 774,200 individuals."
        ),
        "license": "Open access for research",
    },
    "voc_cargo": {
        "name": "Boekhouder-Generaal Batavia",
        "organisation": "Nationaal Archief",
        "coverage_start": "1700",
        "coverage_end": "1795",
        "record_types": ["cargo"],
        "total_records": 50000,
        "access_method": "api",
        "documentation_url": "https://bgb.huygens.knaw.nl/",
        "description": (
            "Cargo manifests from the VOC bookkeeper-general in Batavia. "
            "Records of goods shipped between Asia and the Netherlands."
        ),
        "license": "Open access for research",
    },
    "maarer": {
        "name": "MAARER VOC Wrecks",
        "organisation": "Maritime Archaeological Research",
        "coverage_start": "1595",
        "coverage_end": "1795",
        "record_types": ["wrecks", "incidents"],
        "total_wrecks": 734,
        "access_method": "compiled",
        "description": (
            "Compiled database of VOC wreck positions and loss circumstances. "
            "Combines data from DAS, archaeological surveys, and historical sources."
        ),
        "license": "Open access for research",
    },
}


# --- Geographic Regions ----------------------------------------------------


REGIONS: dict[str, str] = {
    "north_sea": "North Sea, English Channel",
    "atlantic_europe": "Bay of Biscay to Canaries",
    "atlantic_crossing": "Mid-Atlantic",
    "cape": "Cape of Good Hope region",
    "mozambique_channel": "East African coast",
    "indian_ocean": "Open Indian Ocean",
    "malabar": "Indian west coast",
    "coromandel": "Indian east coast",
    "ceylon": "Sri Lanka waters",
    "bengal": "Bay of Bengal",
    "malacca": "Straits of Malacca",
    "indonesia": "Indonesian archipelago",
    "south_china_sea": "Vietnam, Philippines, South China",
    "japan": "Japanese waters",
    "caribbean": "Caribbean Sea",
}


# --- VOC Ship Types --------------------------------------------------------


SHIP_TYPES: dict[str, str] = {
    "retourschip": "Large three-masted ship for Asia route (600-1200 lasten)",
    "fluit": "Cargo vessel, economical crew requirements",
    "jacht": "Fast, light vessel for patrol and messenger duties",
    "hooker": "Small coastal trading vessel",
    "pinas": "Medium ship, versatile for trade and war",
    "fregat": "Fast warship, smaller than retourschip",
}


# --- Loss Causes -----------------------------------------------------------


LOSS_CAUSES: list[str] = [
    "storm",
    "reef",
    "fire",
    "battle",
    "grounding",
    "scuttled",
    "unknown",
]


# --- Wreck Status ----------------------------------------------------------


WRECK_STATUSES: list[str] = ["found", "unfound", "approximate"]


# --- Voyage Fates ----------------------------------------------------------


VOYAGE_FATES: list[str] = ["completed", "wrecked", "captured", "scuttled", "missing"]


# --- Crew Fates ------------------------------------------------------------


CREW_FATES: list[str] = [
    "survived",
    "died_voyage",
    "died_asia",
    "deserted",
    "discharged",
]


# --- Position Uncertainty Types --------------------------------------------


UNCERTAINTY_TYPES: dict[str, str] = {
    "precise": "Modern GPS or well-surveyed wreck site (<100m)",
    "triangulated": "Multiple historical sources agree (<5km)",
    "dead_reckoning": "Calculated from course/speed (10-100km)",
    "approximate": "General area described (50-500km)",
    "regional": "Only broad region known (100-1000km)",
}


# --- Navigation Technology by Era ------------------------------------------


NAVIGATION_ERAS: dict[str, dict] = {
    "1595-1650": {
        "technology": "dead_reckoning_with_cross_staff",
        "typical_accuracy_km": 30,
        "notes": "Early VOC era. No reliable longitude method.",
    },
    "1650-1700": {
        "technology": "dead_reckoning_with_backstaff",
        "typical_accuracy_km": 25,
        "notes": "Improved latitude measurements. Longitude still by dead reckoning.",
    },
    "1700-1760": {
        "technology": "dead_reckoning_with_octant",
        "typical_accuracy_km": 20,
        "notes": "Hadley's octant from 1731. Better latitude precision.",
    },
    "1760-1795": {
        "technology": "chronometer_era",
        "typical_accuracy_km": 10,
        "notes": "Harrison's chronometer. Longitude measurable but instruments rare on VOC ships.",
    },
}


# --- VOC Chambers ----------------------------------------------------------


VOC_CHAMBERS: list[str] = [
    "Amsterdam",
    "Zeeland",
    "Delft",
    "Rotterdam",
    "Hoorn",
    "Enkhuizen",
]


# --- Defaults --------------------------------------------------------------


MAX_RESULTS: int = 50
DEFAULT_ARCHIVE: str = "das"


# --- Type Literals ---------------------------------------------------------


ArchiveName = Literal["das", "voc_crew", "voc_cargo", "maarer"]
RegionName = Literal[
    "north_sea",
    "atlantic_europe",
    "atlantic_crossing",
    "cape",
    "mozambique_channel",
    "indian_ocean",
    "malabar",
    "coromandel",
    "ceylon",
    "bengal",
    "malacca",
    "indonesia",
    "south_china_sea",
    "japan",
    "caribbean",
]


# --- Artifact Types --------------------------------------------------------


class ArtifactType(str, Enum):
    """Type identifiers for artifacts stored in chuk-artifacts."""

    ARCHIVE_EXPORT = "archive_export"


# --- MIME Types ------------------------------------------------------------


class MimeType:
    """MIME type constants for artifact storage."""

    GEOJSON = "application/geo+json"
    JSON = "application/json"


# --- Messages --------------------------------------------------------------


class ErrorMessages:
    ARCHIVE_NOT_FOUND = "Archive '{}' not found. Available: {}"
    VOYAGE_NOT_FOUND = "Voyage '{}' not found"
    WRECK_NOT_FOUND = "Wreck '{}' not found"
    VESSEL_NOT_FOUND = "Vessel '{}' not found"
    CREW_NOT_FOUND = "Crew record '{}' not found"
    CARGO_NOT_FOUND = "No cargo records for voyage '{}'"
    INVALID_DATE_RANGE = "Invalid date range format. Use YYYY/YYYY or YYYY-MM-DD/YYYY-MM-DD"
    REGION_NOT_FOUND = "Unknown region '{}'. Valid regions: {}"
    SHIP_TYPE_NOT_FOUND = "Unknown ship type '{}'. Valid types: {}"
    NO_RESULTS = "No results found matching search criteria"
    LOCATION_NOT_FOUND = "Location '{}' not found in VOC gazetteer. Try maritime_list_locations to browse available places."
    ROUTE_NOT_FOUND = "Route '{}' not found. Use maritime_list_routes to see available routes."
    CLIWOC_VOYAGE_NOT_FOUND = (
        "CLIWOC voyage {} not found. Use maritime_search_tracks to find valid voyage IDs."
    )
    VOYAGE_NOT_FOUND_LINKING = (
        "Voyage not found: {}. Use maritime_search_voyages to find valid voyage IDs."
    )
    SERVICE_ERROR = "Archive '{}' temporarily unavailable"
    SPEED_PROFILE_NOT_FOUND = "No speed profile data for route '{}'. Available: {}"
    TIMELINE_VOYAGE_NOT_FOUND = (
        "Voyage '{}' not found. Use maritime_search_voyages to find valid voyage IDs."
    )
    TIMELINE_NO_EVENTS = "No dated events found for voyage '{}'"


class SuccessMessages:
    ARCHIVES_LISTED = "{} maritime archives available"
    VOYAGES_FOUND = "Found {} voyages matching criteria"
    WRECKS_FOUND = "Found {} wrecks matching criteria"
    VESSELS_FOUND = "Found {} vessels matching criteria"
    CREW_FOUND = "Found {} crew records"
    CARGO_FOUND = "Found {} cargo entries"
    LOCATIONS_FOUND = "Found {} locations"
    EXPORT_COMPLETE = "Exported {} wreck positions to GeoJSON"
    STATISTICS_COMPLETE = "Statistics for {} losses across {} years"
