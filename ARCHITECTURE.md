# Architecture

This document describes the design principles, module structure, and key patterns
used in chuk-mcp-maritime-archives.

## Design Principles

### 1. Async-First

All tool entry points are `async`. Synchronous HTTP I/O (urllib.request) is wrapped
in `asyncio.to_thread()` so the event loop is never blocked. The `BaseArchiveClient`
provides `_http_get()` and `_http_get_with_params()` helpers that handle this
transparently for all four archive clients.

### 2. Single Responsibility

Each module has one job. Tool functions validate inputs, call `ArchiveManager`, and
format responses. `ArchiveManager` orchestrates caching and client delegation.
Individual archive clients own HTTP communication and fallback logic. Models define
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

Each archive has a dedicated HTTP client that extends `BaseArchiveClient`:
- `DASClient` -- Dutch Asiatic Shipping voyages and vessels
- `CrewClient` -- VOC Opvarenden crew muster rolls
- `CargoClient` -- Boekhouder-Generaal Batavia cargo manifests
- `WreckClient` -- MAARER wreck database

`ArchiveManager` instantiates all four clients at startup and orchestrates lookups
across them.

### 6. LRU Caching

`ArchiveManager` maintains `OrderedDict`-based LRU caches for voyages (500 entries),
wrecks (500 entries), and vessels. On access, entries are moved to the end via
`move_to_end()`. When the cache exceeds its limit, the oldest (first) entry is evicted
via `popitem(last=False)`. Search results automatically populate caches so that
follow-up detail requests are instant.

### 7. Pluggable Storage via chuk-artifacts

Exported data (GeoJSON wreck positions) is stored through the `chuk-artifacts`
abstraction layer. Supported backends (memory, filesystem, S3) are selected via the
`CHUK_ARTIFACTS_PROVIDER` environment variable. The artifact store is initialised at
server startup in `server.py`, not at module import time.

### 8. Graceful Degradation

Every archive client attempts the remote API first. If the HTTP request fails (timeout,
network error, invalid JSON), the client falls back to curated sample data with a
warning logged. Errors in tool functions return structured JSON
(`{"error": "..."}`) -- never unhandled exceptions or stack traces.

### 9. Test Coverage -- 90%+ Target

Every module maintains at least 90% line coverage. Tests use `pytest-asyncio` and mock
at the client HTTP boundary (`_http_get`), not at the manager level, to exercise the
full data flow from tool to client.

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
                        |  position/ export/  |
                        |  discovery/         |
                        +---------------------+
                                    |
                                    | validate params, format response
                                    v
          +-----------+  +---------------------+
          | LRU Cache |--| ArchiveManager      |
          | (voyages, |  | (central            |
          |  wrecks,  |  |  orchestrator)      |
          |  vessels) |  +---------------------+
          +-----------+     |    |    |    |
                            |    |    |    |
                +-----------+    |    |    +----------+
                |                |    |               |
                v                v    v               v
         +-----------+   +--------+ +--------+  +-----------+
         | DASClient |   | Crew   | | Cargo  |  | Wreck     |
         | (voyages, |   | Client | | Client |  | Client    |
         |  vessels) |   +--------+ +--------+  +-----------+
         +-----------+       |          |             |
                |            |          |             |
                v            v          v             v
         +-----------+  +--------+  +--------+  +-----------+
         | DAS API   |  | NA API |  | BGB API|  | MAARER    |
         | Huygens   |  | Nat.   |  | Huygens|  | Data      |
         | Institute |  | Archief|  |        |  |           |
         +-----------+  +--------+  +--------+  +-----------+
```

---

## Module Dependency Graph

```
server.py                           # CLI entry point (sync)
  +-- async_server.py               # Async server setup, tool registration
  |     +-- tools/archives/api.py         # maritime_list_archives, maritime_get_archive
  |     +-- tools/voyages/api.py          # maritime_search_voyages, maritime_get_voyage
  |     +-- tools/crew/api.py             # maritime_search_crew, maritime_get_crew_member
  |     +-- tools/cargo/api.py            # maritime_search_cargo, maritime_get_cargo_manifest
  |     +-- tools/wrecks/api.py           # maritime_search_wrecks, maritime_get_wreck
  |     +-- tools/vessels/api.py          # maritime_search_vessels, maritime_get_vessel,
  |     |                                 #   maritime_get_hull_profile, maritime_list_hull_profiles
  |     +-- tools/position/api.py         # maritime_assess_position
  |     +-- tools/export/api.py           # maritime_export_geojson, maritime_get_statistics
  |     +-- tools/discovery/api.py        # maritime_capabilities
  |     +-- core/archive_manager.py       # Central orchestrator, LRU caches
  |           +-- core/clients/das_client.py     # DAS HTTP client
  |           +-- core/clients/crew_client.py    # VOC Crew HTTP client
  |           +-- core/clients/cargo_client.py   # BGB Cargo HTTP client
  |           +-- core/clients/wreck_client.py   # MAARER Wreck HTTP client
  |           +-- core/hull_profiles.py          # Static hydrodynamic reference data

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
|   +-- archive_manager.py   # Central orchestrator with LRU caches
|   +-- hull_profiles.py     # Static hydrodynamic reference data
|   +-- clients/
|       +-- __init__.py
|       +-- base.py           # BaseArchiveClient ABC
|       +-- das_client.py     # DAS (Dutch Asiatic Shipping) client
|       +-- crew_client.py    # VOC Opvarenden crew client
|       +-- cargo_client.py   # BGB cargo manifest client
|       +-- wreck_client.py   # MAARER wreck database client
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
    +-- position/      # maritime_assess_position
    +-- export/        # maritime_export_geojson, maritime_get_statistics
    +-- discovery/     # maritime_capabilities
```

---

## Component Responsibilities

### `server.py`

Synchronous entry point. Parses command-line arguments (`--mode`, `--port`), loads
`.env` via `python-dotenv`, configures the artifact store provider from environment
variables, and starts the MCP server. This is the only file that touches `sys.argv`
or `os.environ` directly.

### `async_server.py`

Creates the `ChukMCPServer` MCP instance, instantiates `ArchiveManager`, and registers
all nine tool groups. Each tool module receives the MCP instance and the shared
`ArchiveManager`.

### `core/archive_manager.py`

The central orchestrator. Manages:
- **Archive registry**: static metadata for all four archives
- **Data source clients**: DASClient, CrewClient, CargoClient, WreckClient
- **LRU caches**: OrderedDict caches for voyages, wrecks, and vessels
- **Hull profile lookups**: static reference data for 6 VOC ship types
- **Position assessment**: navigation era detection, uncertainty estimation
- **GeoJSON export**: wreck position FeatureCollection generation
- **Aggregate statistics**: loss statistics computed from wreck data

### `core/clients/base.py`

Abstract base class for all archive clients. Provides:
- `_http_get()`: async HTTP GET via `asyncio.to_thread(urllib.request.urlopen)`
- `_http_get_with_params()`: query parameter encoding
- `_filter_by_date_range()`: date range filtering for YYYY/YYYY format
- Abstract methods: `search()`, `get_by_id()`, `get_sample_data()`

### `core/clients/das_client.py`

HTTP client for the Dutch Asiatic Shipping database. Provides voyage search,
voyage detail retrieval, and vessel search. Falls back to 5 curated sample voyages
and 4 sample vessels when the Huygens Institute API is unavailable.

### `core/clients/crew_client.py`

HTTP client for the VOC Opvarenden crew database at the Nationaal Archief.
Provides crew search and detail retrieval. Falls back to 4 curated sample crew
records.

### `core/clients/cargo_client.py`

HTTP client for the Boekhouder-Generaal Batavia cargo database. Provides cargo
search and voyage manifest retrieval. Falls back to 4 curated sample cargo records.

### `core/clients/wreck_client.py`

Client for the MAARER compiled wreck database. Provides wreck search and detail
retrieval. Falls back to 5 curated sample wreck records spanning the Cape, Atlantic
Europe, and Indian Ocean regions.

### `core/hull_profiles.py`

Static reference data containing hydrodynamic hull profiles for 6 VOC ship types:
retourschip, fluit, jacht, hooker, pinas, and fregat. Each profile includes dimensions,
displacement, drag coefficients, windage, sinking characteristics, reference wrecks,
and LLM guidance notes.

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
- `VOYAGE_CACHE_MAX_ENTRIES`, `WRECK_CACHE_MAX_ENTRIES` -- cache limits
- `ErrorMessages`, `SuccessMessages` -- format-string message templates

---

## Data Flows

### Search -> Cache -> Detail

```
1. maritime_search_voyages(ship_name="Batavia", ...)
   +-- tool validates params
   +-- manager.search_voyages()
       +-- das_client.search(ship_name="Batavia")
       |   +-- _http_get_with_params(DAS_URL/searchVoyage, {ship: "Batavia"})
       |   +-- asyncio.to_thread(urllib.request.urlopen)
       |   +-- if API fails: get_sample_data() fallback
       |   +-- _apply_voyage_filters() client-side filtering
       +-- cache results: _cache_put(voyage_cache, id, data, 500)
   +-- tool formats VoyageSearchResponse

2. maritime_get_voyage(voyage_id="das:3456")
   +-- tool validates params
   +-- manager.get_voyage("das:3456")
       +-- _cache_get(voyage_cache, "das:3456")    <-- cache hit
       +-- if cache miss: das_client.get_by_id("das:3456")
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

### Graceful API Fallback

Every client follows the same pattern:
1. Build API query parameters from search kwargs
2. Call `_http_get_with_params()` against the remote API
3. If result is a list, use it directly
4. If result is a dict, try to unwrap from `results` or domain-specific key
5. If result is None or empty, call `get_sample_data()` with a warning log
6. Apply client-side filters to the returned dataset
7. Truncate to `max_results`

### Dual Output Mode

All tools accept an `output_mode` parameter (`"json"` or `"text"`). The
`format_response()` helper checks for a `to_text()` method on the response model.
In JSON mode, `model_dump_json(indent=2, exclude_none=True)` produces clean output.
In text mode, each response model's `to_text()` returns a human-readable summary.

### Client-Side Filtering

Because external APIs may not support all filter parameters, every client applies
filters locally after receiving results. This ensures consistent behaviour whether
data comes from the live API or from sample data fallback. Filters use
case-insensitive substring matching for text fields and exact matching for enumerated
fields.

### Navigation Era Detection

Position assessment uses `NAVIGATION_ERAS` from constants to determine the navigation
technology available in a given year. The era determines the baseline position
uncertainty (30km for 1595-1650 down to 10km for 1760-1795), which is then adjusted
based on the source description keywords.
