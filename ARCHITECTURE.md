# Architecture

This document describes the design principles, module structure, and key patterns
used in chuk-mcp-maritime-archives.

## Design Principles

### 1. Async-First

All tool entry points are `async`. Archive clients extend `BaseArchiveClient` which
loads JSON data files from `data/` via `_load_json()` on first access, caching them
in memory. Reference data modules (gazetteer, routes, hull profiles, speed profiles,
CLIWOC tracks) also load from local JSON files on first access.

### 2. Single Responsibility

Each module has one job. Tool functions validate inputs, call `ArchiveManager`, and
format responses. `ArchiveManager` orchestrates caching and multi-archive dispatch.
Individual archive clients own data loading and search filtering. Models define
data shapes. Constants define identifiers and messages.

### 3. Pydantic v2 Native -- No Dict Goop

Domain models (vessels, positions, incidents, hull profiles) use
`model_config = ConfigDict(extra="allow")` so that additional fields from archival
sources are preserved when round-tripping through `model_validate` / `model_dump`.

Response envelopes use `model_config = ConfigDict(extra="forbid")` to catch stale or
mistyped fields at serialisation time. Every response model carries a `to_text()`
method for dual-mode output (JSON or human-readable).

### 4. No Magic Strings

Every repeated string lives in `constants.py` as an enum, class attribute, or
module-level constant. Archive IDs, ship types, region names, loss causes, crew fates,
uncertainty types, navigation eras, cache limits, error message templates, and success
message templates are all constants -- never inline strings.

### 5. Data Source Clients

Eleven archive clients extend `BaseArchiveClient`, each loading from local JSON:

**Core archives (Dutch):**
- `DASClient` -- Dutch Asiatic Shipping voyages and vessels (8,194 voyages)
- `CrewClient` -- VOC Opvarenden crew muster rolls (774K records, lazy-built indexes)
- `CargoClient` -- Boekhouder-Generaal Batavia cargo manifests (200 curated records)
- `WreckClient` -- MAARER wreck database (734 wrecks)

**Additional archives (multi-nation):**
- `EICClient` -- English East India Company voyages and wrecks (~150 voyages, ~35 wrecks)
- `CarreiraClient` -- Portuguese Carreira da India (~500 voyages, ~100 wrecks)
- `GalleonClient` -- Spanish Manila Galleon (~250 voyages, ~42 wrecks)
- `SOICClient` -- Swedish East India Company (~132 voyages, ~20 wrecks)
- `UKHOClient` -- UK Hydrographic Office global wrecks (94,000+ wrecks, wrecks-only)
- `NOAAClient` -- NOAA Automated Wreck and Obstruction Information System (AWOIS) wrecks (wrecks-only)
- `DSSClient` -- Dutch Ships and Sailors musters + crew (~70 GZMVOC musters, ~101 MDB crew records)

Each multi-nation client handles both voyages and wrecks in a single class, with
`search()`, `get_by_id()`, `search_wrecks()`, and `get_wreck_by_id()` methods.
`UKHOClient` and `NOAAClient` are wrecks-only -- `search()` and `get_by_id()` delegate to wreck methods.
`DSSClient` handles musters and crew in a single class, with `search_musters()`, `get_muster_by_id()`,
`search_crews()`, and `get_crew_by_id()` methods. The abstract `search()` and `get_by_id()` delegate to crew methods.

Reference data modules load from JSON files in `data/`:
- `voc_gazetteer` -- ~160 historical place names from `data/gazetteer.json`
- `voc_routes` -- 8 standard sailing routes from `data/routes.json`
- `hull_profiles` -- 6 ship type profiles from `data/hull_profiles.json`
- `speed_profiles` -- 215 speed profiles across 6 routes from `data/speed_profiles.json`

`ArchiveManager` instantiates all 11 clients at startup and uses `_voyage_clients`,
`_wreck_clients`, and `_crew_clients` dispatch dicts to route queries by archive ID.

### 6. LRU Caching

`ArchiveManager` maintains `OrderedDict`-based LRU caches for voyages (500 entries),
wrecks (500 entries), and vessels. On access, entries are moved to the end via
`move_to_end()`. When the cache exceeds its limit, the oldest (first) entry is evicted
via `popitem(last=False)`. Search results automatically populate caches so that
follow-up detail requests are instant.

### 7. Pluggable Storage via chuk-artifacts

Exported data (GeoJSON wreck positions, timeline tracks) is stored through the
`chuk-artifacts` abstraction layer. Supported backends (memory, filesystem, S3) are
selected via the `CHUK_ARTIFACTS_PROVIDER` environment variable. The artifact store is
initialised at server startup in `server.py`, not at module import time.

GeoJSON exports and timeline GeoJSON are stored with `scope="sandbox"` so they are
accessible across sessions. If the artifact store is unavailable (e.g., memory provider
with no S3 configured), tools degrade gracefully -- `artifact_ref` is `None` but all
data is still returned in the response.

Reference data (~35 MB across 18 JSON files) can optionally be preloaded from the artifact
store at server startup. Set `MARITIME_REFERENCE_MANIFEST` to a manifest artifact ID
(produced by `scripts/upload_reference_data.py`) and the server will download any missing
data files before importing the data loaders. This eliminates the need to run download
scripts on each new server deployment.

### 8. Local-First Data

All archive clients read from local JSON data files produced by download/generate scripts.
If a data file is missing (e.g. crew.json not yet downloaded), the client returns empty
results gracefully. Tool functions catch these cases and return structured JSON
(`{"error": "..."}`) -- never unhandled exceptions or stack traces.

The `CrewClient` is notable for its lazy-built in-memory indexes: `_voyage_index`
(dict[str, list[dict]]) for O(1) voyage-based lookups and `_id_index` (dict[str, dict])
for instant crew member retrieval across 774K records.

### 9. Multi-Archive Dispatch

`ArchiveManager` routes queries to the correct client via dispatch dicts:
- `_voyage_clients`: maps archive IDs (das, eic, carreira, galleon, soic) to voyage clients
- `_wreck_clients`: maps archive IDs (maarer, eic, carreira, galleon, soic, ukho, noaa) to wreck clients

When `archive` is specified, the query goes to a single client. When omitted, all clients
are queried and results are aggregated. Prefixed IDs (e.g. `eic:0062`) are parsed to route
`get_by_id()` calls to the correct client. Wreck IDs use compound prefixes routed via a
prefix list: `("eic_wreck:", self._eic_client)`, `("carreira_wreck:", self._carreira_client)`,
`("galleon_wreck:", self._galleon_client)`, `("soic_wreck:", self._soic_client)`,
`("ukho_wreck:", self._ukho_client)`, `("noaa_wreck:", self._noaa_client)`. CLIWOC nationality
cross-referencing maps archive IDs to nationality codes (das→NL, eic→UK, carreira→PT,
galleon→ES, soic→SE).

### 10. Reproducible Data Pipeline

All data files in `data/` are produced by scripts in `scripts/`:
- Download scripts (`download_das.py`, `download_cliwoc.py`, `download_crew.py`,
  `download_cargo.py`, `download_eic.py`, `download_ukho.py`) fetch data from external sources
- Generate scripts (`generate_eic.py`, `generate_carreira.py`, `generate_galleon.py`,
  `generate_soic.py`, `generate_ukho.py`, `generate_cargo.py`, `generate_reference.py`,
  `generate_speed_profiles.py`) produce curated or computed datasets
- All scripts support `--force` to regenerate and use a cache-check-download pattern
  via shared utilities in `scripts/download_utils.py`
- `scripts/download_all.py` orchestrates all scripts with `--force` passthrough

### 11. Test Coverage -- 96%+

All modules maintain 96%+ branch coverage (923 tests across 14 test modules). Tests use
`pytest-asyncio` and mock at the client data boundary (`_load_json`), not at the manager
level, to exercise the full data flow from tool to client.

---

## Architecture Diagram

```
                          MCP Client (Claude, mcp-cli, etc.)
                                    |
                                    | MCP protocol (stdio / HTTP)
                                    v
                        +---------------------+
                        |   Tool Functions    |
                        |  archives/ voyages/ |
                        |  crew/ cargo/       |
                        |  wrecks/ vessels/   |
                        |  location/ routes/  |
                        |  tracks/ linking/   |
                        |  speed/ timeline/   |
                        |  position/ export/  |
                        |  narratives/        |
                        |  analytics/         |
                        |  discovery/         |
                        +---------------------+
                                    |
                                    | validate params, format response
                                    v
          +-----------+  +---------------------+
          | LRU Cache |--| ArchiveManager      |
          | (voyages, |  | (multi-archive      |
          |  wrecks,  |  |  dispatch +         |
          |  vessels) |  |  orchestration)     |
          +-----------+  +---------------------+
                             |            |
            _voyage_clients  |            | _wreck_clients
            +----------------+            +----------------+
            |    |    |    |    |         |    |    |    |
            v    v    v    v    v         v    v    v    v
         +-----+ +---+ +---+ +---+ +---+ +------+ (+ EIC, Carreira,
         | DAS | |EIC| |Car| |Gal| |SOI| |Wreck |  Galleon, SOIC
         +-----+ +---+ +---+ +---+ +---+ |Client|  also serve
            |      |     |     |     |    +------+  wrecks)
            v      v     v     v     v       v
         +------+ +------+ +------+ +------+ +------+
         | Local JSON data files in data/            |
         | voyages.json, vessels.json, wrecks.json,  |
         | eic_voyages.json, eic_wrecks.json,        |
         | carreira_voyages.json, galleon_voyages.json|
         | soic_voyages.json, noaa_wrecks.json,       |
         | crew.json, cargo.json                      |
         +-------------------------------------------+

         +------+ +------+ +------+ +------+ +------+
         | Crew | | Cargo|   Reference Data Modules
         |Client| |Client|   gazetteer, routes, hull
         +------+ +------+   profiles, speed profiles,
            |        |       cliwoc_tracks
            v        v
         crew.json  cargo.json
```

---

## Module Dependency Graph

```
server.py                           # CLI entry point (sync)
  +-- core/reference_preload.py     # Preload reference data from artifact store
  +-- async_server.py               # Async server setup, tool registration
  |     +-- tools/archives/api.py         # maritime_list_archives, maritime_get_archive
  |     +-- tools/voyages/api.py          # maritime_search_voyages, maritime_get_voyage
  |     +-- tools/crew/api.py             # maritime_search_crew, maritime_get_crew_member
  |     +-- tools/cargo/api.py            # maritime_search_cargo, maritime_get_cargo_manifest
  |     +-- tools/wrecks/api.py           # maritime_search_wrecks, maritime_get_wreck
  |     +-- tools/vessels/api.py          # maritime_search_vessels, maritime_get_vessel,
  |     |                                 #   maritime_get_hull_profile, maritime_list_hull_profiles
  |     +-- tools/location/api.py         # maritime_lookup_location, maritime_list_locations
  |     +-- tools/routes/api.py           # maritime_list_routes, maritime_get_route,
  |     |                                 #   maritime_estimate_position
  |     +-- tools/tracks/api.py           # maritime_search_tracks, maritime_get_track,
  |     |                                 #   maritime_nearby_tracks
  |     +-- tools/linking/api.py          # maritime_get_voyage_full
  |     +-- tools/speed/api.py            # maritime_get_speed_profile
  |     +-- tools/timeline/api.py         # maritime_get_timeline
  |     +-- tools/position/api.py         # maritime_assess_position
  |     +-- tools/export/api.py           # maritime_export_geojson, maritime_get_statistics
  |     +-- tools/musters/api.py          # maritime_search_musters, maritime_get_muster,
  |     |                                #   maritime_compare_wages
  |     +-- tools/narratives/api.py       # maritime_search_narratives
  |     +-- tools/analytics/api.py       # maritime_compute_track_speeds,
  |     |                                #   maritime_aggregate_track_speeds,
  |     |                                #   maritime_compare_speed_groups
  |     +-- tools/discovery/api.py        # maritime_capabilities
  |     +-- core/archive_manager.py       # Central orchestrator, multi-archive dispatch
  |           +-- core/clients/das_client.py       # DAS voyages + vessels (local JSON)
  |           +-- core/clients/crew_client.py      # VOC Crew (local JSON, indexed)
  |           +-- core/clients/cargo_client.py     # BGB Cargo (local JSON)
  |           +-- core/clients/wreck_client.py     # MAARER wrecks (local JSON)
  |           +-- core/clients/eic_client.py       # EIC voyages + wrecks (local JSON)
  |           +-- core/clients/carreira_client.py  # Carreira voyages + wrecks (local JSON)
  |           +-- core/clients/galleon_client.py   # Galleon voyages + wrecks (local JSON)
  |           +-- core/clients/soic_client.py      # SOIC voyages + wrecks (local JSON)
  |           +-- core/clients/ukho_client.py      # UKHO global wrecks (local JSON)
  |           +-- core/clients/noaa_client.py      # NOAA AWOIS wrecks (local JSON)
  |           +-- core/clients/dss_client.py       # DSS musters + crew (local JSON)
  |           +-- core/hull_profiles.py            # Hull profiles (data/hull_profiles.json)
  |           +-- core/voc_gazetteer.py            # VOC gazetteer (data/gazetteer.json)
  |           +-- core/voc_routes.py               # VOC routes (data/routes.json)
  |           +-- core/speed_profiles.py           # Speed profiles (data/speed_profiles.json)
  |           +-- core/entity_resolution.py         # Fuzzy ship name matching (Levenshtein, Soundex)
  |           +-- core/cliwoc_tracks.py            # CLIWOC tracks (data/cliwoc_tracks.json)

models/maritime.py              # Domain models (extra="allow")
models/responses.py             # Response envelopes (extra="forbid")
constants.py                    # Enums, constants, messages
```

---

## Module Structure

```
src/chuk_mcp_maritime_archives/
+-- __init__.py
+-- server.py          # Sync entry point (CLI, artifact store init)
+-- async_server.py    # Async setup (ChukMCPServer, tool registration)
+-- constants.py       # Enums, constants, messages
+-- core/
|   +-- __init__.py
|   +-- archive_manager.py     # Central orchestrator, multi-archive dispatch, LRU caches
|   +-- reference_preload.py   # Preload reference data from artifact store
|   +-- hull_profiles.py       # Hull profiles (loaded from data/hull_profiles.json)
|   +-- voc_gazetteer.py       # VOC gazetteer (loaded from data/gazetteer.json)
|   +-- voc_routes.py          # VOC routes (loaded from data/routes.json)
|   +-- speed_profiles.py      # Speed profiles (loaded from data/speed_profiles.json)
|   +-- entity_resolution.py   # Fuzzy ship name matching (Levenshtein, Soundex, ShipNameIndex)
|   +-- cliwoc_tracks.py       # CLIWOC tracks (loaded from data/cliwoc_tracks.json)
|   +-- clients/
|       +-- __init__.py
|       +-- base.py              # BaseArchiveClient ABC
|       +-- das_client.py        # DAS voyages + vessels (local JSON)
|       +-- crew_client.py       # VOC Crew (local JSON, indexed lookups)
|       +-- cargo_client.py      # BGB Cargo (local JSON)
|       +-- wreck_client.py      # MAARER wrecks (local JSON)
|       +-- eic_client.py        # EIC voyages + wrecks (local JSON)
|       +-- carreira_client.py   # Carreira voyages + wrecks (local JSON)
|       +-- galleon_client.py    # Galleon voyages + wrecks (local JSON)
|       +-- soic_client.py       # SOIC voyages + wrecks (local JSON)
|       +-- ukho_client.py       # UKHO global wrecks (local JSON)
|       +-- noaa_client.py       # NOAA AWOIS wrecks (local JSON)
|       +-- dss_client.py        # DSS musters + crew (local JSON)
+-- models/
|   +-- __init__.py
|   +-- maritime.py    # Domain models (extra="allow")
|   +-- responses.py   # Response envelopes (extra="forbid")
+-- tools/
    +-- __init__.py
    +-- archives/      # maritime_list_archives, maritime_get_archive
    +-- voyages/       # maritime_search_voyages, maritime_get_voyage
    +-- crew/          # maritime_search_crew, maritime_get_crew_member
    +-- cargo/         # maritime_search_cargo, maritime_get_cargo_manifest
    +-- wrecks/        # maritime_search_wrecks, maritime_get_wreck
    +-- vessels/       # maritime_search_vessels, maritime_get_vessel, hull profiles
    +-- location/      # maritime_lookup_location, maritime_list_locations
    +-- routes/        # maritime_list_routes, maritime_get_route, maritime_estimate_position
    +-- tracks/        # maritime_search_tracks, maritime_get_track, maritime_nearby_tracks
    +-- linking/       # maritime_get_voyage_full
    +-- speed/         # maritime_get_speed_profile
    +-- timeline/      # maritime_get_timeline
    +-- position/      # maritime_assess_position
    +-- export/        # maritime_export_geojson, maritime_get_statistics
    +-- musters/       # maritime_search_musters, maritime_get_muster, maritime_compare_wages
    +-- narratives/    # maritime_search_narratives
    +-- analytics/     # maritime_compute_track_speeds, aggregate, compare
    +-- discovery/     # maritime_capabilities
```

---

## Component Responsibilities

### `server.py`

Synchronous entry point. Parses command-line arguments (`--mode`, `--port`), loads
`.env` via `python-dotenv`, configures the artifact store provider from environment
variables, and starts the MCP server. This is the only file that touches `sys.argv`
or `os.environ` directly.

The `main()` function follows a strict initialization order:
1. Initialize artifact store (`_init_artifact_store()`)
2. Preload reference data from artifacts (if `MARITIME_REFERENCE_MANIFEST` is set)
3. Import `async_server` (triggers module-level data loaders)

Step 3 is a lazy import inside `main()` rather than a module-level import. This is
critical because the data loaders (`_load_tracks()`, `_load_routes()`, etc.) run at
import time, and the preload step must complete before they execute.

### `core/reference_preload.py`

Optional reference data preloader. When `MARITIME_REFERENCE_MANIFEST` is set, downloads
data files from the artifact store to the local `data/` directory. The manifest is a
JSON artifact mapping filenames to artifact IDs. Skips files that already exist locally.
Falls back silently if the store is unavailable or any download fails.

### `async_server.py`

Creates the `ChukMCPServer` MCP instance, instantiates `ArchiveManager`, and registers
all tool groups (19 categories, 37 tools). Each tool module receives the MCP instance
and the shared `ArchiveManager`.

### `core/archive_manager.py`

The central orchestrator. Manages:
- **Archive registry**: static metadata for all 10 archives
- **Data source clients**: 10 clients (DAS, Crew, Cargo, Wreck, EIC, Carreira, Galleon, SOIC, UKHO, NOAA)
- **Multi-archive dispatch**: `_voyage_clients` and `_wreck_clients` dicts route by archive ID
- **LRU caches**: OrderedDict caches for voyages, wrecks, and vessels
- **Hull profile lookups**: static reference data for 6 VOC ship types
- **Cross-archive linking**: unified voyage view with wreck, vessel, hull profile, CLIWOC track, crew records, and confidence scores
- **Entity resolution**: fuzzy ship name matching via `ShipNameIndex` (Levenshtein + Soundex + date proximity)
- **Link auditing**: precision/recall metrics for cross-archive links against known ground truth
- **Timeline assembly**: chronological events from voyages, route estimates, CLIWOC tracks, and wrecks
- **Position assessment**: navigation era detection, uncertainty estimation
- **GeoJSON export**: wreck position FeatureCollection generation
- **Aggregate statistics**: loss statistics computed from wreck data
- **Narrative search**: full-text search across all free-text fields with snippet extraction

### `core/clients/base.py`

Abstract base class for all archive clients. Provides:
- `_load_json()`: loads a JSON data file from `data/`, caching in memory
- `_filter_by_date_range()`: date range filtering for YYYY/YYYY format
- `_contains()`: case-insensitive substring matching
- Abstract methods: `search()`, `get_by_id()`

### `core/clients/das_client.py`

Client for the Dutch Asiatic Shipping database. Loads voyages and vessels from
`data/voyages.json` and `data/vessels.json`. Provides voyage search with ship name,
date range, and fate filters, plus vessel search.

### `core/clients/crew_client.py`

Client for the VOC Opvarenden crew database (774K records from `data/crew.json`,
downloaded via `scripts/download_crew.py`). Builds lazy in-memory indexes on first
access: `_voyage_index` (dict[str, list[dict]]) for O(1) voyage-based lookups and
`_id_index` (dict[str, dict]) for instant crew member retrieval.

### `core/clients/cargo_client.py`

Client for the Boekhouder-Generaal Batavia cargo database. Loads 200 curated records
from `data/cargo.json`. Provides cargo search by voyage, commodity, origin, destination.

### `core/clients/wreck_client.py`

Client for the MAARER compiled wreck database. Loads 734 wrecks from `data/wrecks.json`.
Provides wreck search with region, cause, status, depth, and cargo value filters.

### `core/clients/eic_client.py`

Client for the English East India Company (~150 voyages, ~35 wrecks). Loads from
`data/eic_voyages.json` and `data/eic_wrecks.json`. Handles both voyages and wrecks
in a single class with lazy-built ID indexes for fast lookups.

### `core/clients/carreira_client.py`

Client for the Portuguese Carreira da India (~500 voyages, ~100 wrecks). Loads from
`data/carreira_voyages.json` and `data/carreira_wrecks.json`. Curated from
Guinote/Frutuoso/Lopes with era-based fleet expansion.

### `core/clients/galleon_client.py`

Client for the Spanish Manila Galleon (~250 voyages, ~42 wrecks). Loads from
`data/galleon_voyages.json` and `data/galleon_wrecks.json`. Pacific crossing
routes between Acapulco and Manila.

### `core/clients/soic_client.py`

Client for the Swedish East India Company (~132 voyages, ~20 wrecks). Loads from
`data/soic_voyages.json` and `data/soic_wrecks.json`. Gothenburg-Canton route
via the Cape of Good Hope.

### `core/clients/ukho_client.py`

Client for the UK Hydrographic Office global wrecks database (94,000+ wrecks from
`data/ukho_wrecks.json`, downloaded via `scripts/download_ukho.py` or generated
via `scripts/generate_ukho.py`). Wrecks-only archive — no voyage data. `search()`
and `get_by_id()` delegate to `search_wrecks()` and `get_wreck_by_id()`. Supports
additional filter parameters `flag` (nationality) and `vessel_type`. Uses lazy-built
`_wreck_index` for O(1) lookups across 94K records.

### `core/clients/noaa_client.py`

Client for the NOAA Automated Wreck and Obstruction Information System (AWOIS)
(`data/noaa_wrecks.json`). Wrecks-only archive -- no voyage data. `search()`
and `get_by_id()` delegate to `search_wrecks()` and `get_wreck_by_id()`. Uses
lazy-built `_wreck_index` for O(1) lookups.

### `core/hull_profiles.py`

Hydrodynamic hull profiles for 6 VOC ship types, loaded from `data/hull_profiles.json`:
retourschip, fluit, jacht, hooker, pinas, and fregat. Each profile includes dimensions,
displacement, drag coefficients, windage, sinking characteristics, reference wrecks,
and LLM guidance notes.

### `core/voc_gazetteer.py`

Historical place-name gazetteer loaded from `data/gazetteer.json`. Contains ~160 VOC-era
place names with modern coordinates, region classification, location type, aliases
(historical spellings and modern equivalents), and historical notes. Provides exact match,
alias match, and substring match lookups plus filtered search.

### `core/voc_routes.py`

Standard VOC sailing routes loaded from `data/routes.json`. Defines 8 routes (outward
outer/inner, return, Japan, Spice Islands, Ceylon, Coromandel, Malabar) as sequences
of waypoints with cumulative sailing days, stop durations, hazards, and season notes.
Key feature: `estimate_position()` interpolates a ship's position on any date via linear
interpolation between waypoints, optionally enriched with CLIWOC-derived speed profiles.

### `core/speed_profiles.py`

Historical sailing speed statistics loaded from `data/speed_profiles.json` (generated by
`scripts/generate_speed_profiles.py` from CLIWOC 2.1 daily positions). Contains 215
profiles across 6 routes with mean, median, standard deviation, and percentile speeds
(km/day) per route segment. Provides: `get_speed_profile()` for all segments of a route
with optional departure-month filtering, `get_segment_speed()` for single-segment lookup
with month-to-all-months fallback, and `list_profiled_routes()` for available route IDs.

### `core/entity_resolution.py`

Pure-Python entity resolution for historical maritime ship names. Provides fuzzy
matching, phonetic encoding, and confidence scoring for linking records across
archives where ship names vary in spelling, casing, and use of articles. No
external dependencies. Key components: `normalize_ship_name()` strips articles
(De, Het, 'T, HMS, VOC) while preserving saints (San, Santa, Sao);
`levenshtein_distance()` / `levenshtein_similarity()` for edit-distance scoring;
`soundex()` for phonetic encoding; `score_ship_match()` for composite confidence
with weights: name=0.50, date=0.30, nationality=0.10, phonetic=0.10;
`ShipNameIndex` for fast three-level lookup (exact normalized -> Soundex ->
Levenshtein fallback with length-based early rejection).

### `core/cliwoc_tracks.py`

CLIWOC ship track data loaded from `data/cliwoc_tracks.json` (produced by
`scripts/download_cliwoc.py`). Contains ~261K daily logbook positions from 1,981 voyages
across 8 European maritime nations (1662-1855). Uses CLIWOC 2.1 Full data (182 columns)
with ship names, company, DAS numbers, and ship types. Provides: `search_tracks()` with
nationality/year/ship name filters, `get_track()` for full position history,
`nearby_tracks()` for proximity search using haversine distance,
`get_track_by_das_number()` and `find_track_for_voyage()` for cross-archive linking.
Also provides track analytics: `compute_track_speeds()` for single-voyage haversine-based
daily speeds, `aggregate_track_speeds()` for bulk speed computation with grouping by
decade/year/month/direction/nationality and descriptive statistics, and
`compare_speed_groups()` for Mann-Whitney U significance testing between time periods.
Useful for finding contextual ship traffic around wreck sites and incidents, and for
climate proxy research using ship speed as a wind strength indicator.

### `models/maritime.py`

Pydantic v2 domain models for the maritime world. All use `extra="allow"` so
additional archival fields pass through without validation errors. Includes:
`Position`, `PositionUncertainty`, `Waypoint`, `Vessel`, `VesselDimensions`,
`PersonnelSummary`, `CargoSummary`, `Incident`, `SourceReference`, `HullProfile`,
`HullHydrodynamics`, `SinkingCharacteristics`.

### `models/responses.py`

Pydantic v2 response models for every tool. All use `extra="forbid"` to catch
serialisation errors early. Each model carries a `to_text()` method for
human-readable output. Includes: `ArchiveListResponse`, `VoyageSearchResponse`,
`WreckDetailResponse`, `HullProfileResponse`, `PositionAssessmentResponse`,
`GeoJSONExportResponse`, `CapabilitiesResponse`, and others.

### `constants.py`

All magic strings, identifiers, and configuration values. Includes:
- `ServerConfig`, `StorageProvider`, `SessionProvider` -- server configuration enums
- `ArchiveId`, `ARCHIVE_METADATA` -- archive identifiers and metadata
- `REGIONS`, `SHIP_TYPES`, `LOSS_CAUSES`, `WRECK_STATUSES` -- domain constants
- `VOYAGE_FATES`, `CREW_FATES` -- outcome constants
- `UNCERTAINTY_TYPES`, `NAVIGATION_ERAS` -- position assessment reference data
- `VOC_CHAMBERS` -- VOC administrative divisions
- `ErrorMessages`, `SuccessMessages` -- format-string message templates

---

## Data Flows

### Search -> Cache -> Detail

```
1. maritime_search_voyages(ship_name="Batavia", ...)
   +-- tool validates params
   +-- manager.search_voyages()
       +-- resolve archive -> _voyage_clients["das"]
       +-- das_client.search(ship_name="Batavia")
       |   +-- _load_json("voyages.json")   <-- cached in memory after first load
       |   +-- filter: ship_name substring match
       |   +-- filter: date_range, fate, etc.
       |   +-- truncate to max_results
       +-- cache results: _cache_put(voyage_cache, id, data, 500)
   +-- tool formats VoyageSearchResponse

2. maritime_search_voyages(ship_name="Trade", archive="eic")
   +-- resolve archive -> _voyage_clients["eic"]
   +-- eic_client.search(ship_name="Trade")
   +-- (only EIC voyages searched)

3. maritime_search_voyages(ship_name="Batavia")  [no archive filter]
   +-- queries ALL _voyage_clients (das, eic, carreira, galleon, soic)
   +-- aggregates results across archives

4. maritime_get_voyage(voyage_id="das:3456")
   +-- tool validates params
   +-- manager.get_voyage("das:3456")
       +-- _cache_get(voyage_cache, "das:3456")    <-- cache hit
       +-- if cache miss: parse prefix "das" -> _voyage_clients["das"]
       +-- das_client.get_by_id("das:3456")
       +-- _cache_put(voyage_cache, ..., 500)
   +-- tool formats VoyageDetailResponse
```

### Position Assessment

```
maritime_assess_position(wreck_id="maarer:VOC-0789", source_description="GPS surveyed")
  +-- manager.assess_position()
      +-- get_wreck("maarer:VOC-0789")      <-- fetch/cache wreck record
      +-- extract year from loss_date        <-- 1629
      +-- _get_navigation_era(1629)          <-- "dead_reckoning_with_cross_staff"
      +-- evaluate source_description        <-- "GPS" -> precise
      +-- compute quality_score, uncertainty_km, recommendations
  +-- tool formats PositionAssessmentResponse
```

### GeoJSON Export

```
maritime_export_geojson(region="cape", include_uncertainty=True)
  +-- manager.export_geojson()
      +-- search_wrecks(region="cape")       <-- fetch all Cape wrecks
      +-- for each wreck:
      |   +-- extract lat/lon from position
      |   +-- build GeoJSON Feature with properties
      +-- return FeatureCollection
  +-- optionally store via chuk-artifacts
  +-- tool formats GeoJSONExportResponse
```

---

## Key Patterns

### LRU Cache with OrderedDict

`ArchiveManager` uses `collections.OrderedDict` for LRU caching. The `_cache_put()`
method calls `move_to_end(key)` for existing entries and `popitem(last=False)` to
evict the oldest entry when the cache exceeds its limit. `_cache_get()` moves accessed
entries to the end to maintain LRU order.

### Local JSON Client Pattern

Every client follows the same pattern:
1. Call `_load_json(filename)` to load data (cached in memory after first call)
2. If data file is missing, return `[]` (graceful degradation)
3. Apply keyword filters via `_contains()` (case-insensitive substring matching)
4. Apply date range filters via `_filter_by_date_range()`
5. Truncate to `max_results`

Multi-nation clients (EIC, Carreira, Galleon, SOIC) extend this with:
- Separate voyage and wreck JSON files
- Lazy-built ID indexes for O(1) detail lookups
- `search_wrecks()` and `get_wreck_by_id()` alongside voyage methods

### Dual Output Mode

All tools accept an `output_mode` parameter (`"json"` or `"text"`). The
`format_response()` helper checks for a `to_text()` method on the response model.
In JSON mode, `model_dump_json(indent=2, exclude_none=True)` produces clean output.
In text mode, each response model's `to_text()` returns a human-readable summary.

### Client-Side Filtering

All data is local, so filtering is always client-side. Filters use case-insensitive
substring matching for text fields (via `_contains()`) and exact matching for
enumerated fields (fate, cause, status, region).

### JSON Data Loading

Reference data modules (gazetteer, routes, hull profiles) follow a consistent pattern:
1. Module-level dict is initially empty
2. A `_load_*()` function checks if the dict is populated; if not, loads from JSON
3. `_load_*()` is called at module import time (`_load_routes()` at bottom of file)
4. All public functions call `_load_*()` defensively before accessing data
5. JSON files in `data/` are the source of truth; `scripts/generate_reference.py`
   validates and reformats them

This pattern ensures data is available immediately on import while keeping the source
of truth in version-controlled JSON files that can be regenerated or edited directly.

### Navigation Era Detection

Position assessment uses `NAVIGATION_ERAS` from constants to determine the navigation
technology available in a given year. Six eras span 1595-1880, covering the full range
of all 10 archives. The era determines the baseline position uncertainty (30km for
1595-1650 down to 2km for 1840-1880), which is then adjusted based on the source
description keywords.
