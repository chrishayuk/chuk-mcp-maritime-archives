# Roadmap

Development roadmap for chuk-mcp-maritime-archives.

---

## Completed

### v0.1.0 -- Foundation

Core MCP server with 18 tools across 10 categories.

- **4 archive clients**: DAS voyages/vessels, VOC Crew muster rolls, BGB cargo manifests, MAARER wrecks
- **Pydantic v2 response models** with dual output (JSON + text) for all tools
- **LRU caching** for voyages (500), wrecks (500), and vessels
- **Position quality assessment** with navigation-era detection (4 technology periods, 1595-1795)
- **GeoJSON export** with artifact store integration (memory, filesystem, S3)
- **Hull hydrodynamic profiles** for 6 VOC ship types (retourschip, fluit, jacht, hooker, pinas, fregat)
- **256 tests**, 98%+ branch coverage

### v0.2.0 -- Reference Data & Routes

Expanded to 23 tools across 12 categories. Reproducible data pipeline.

**New tools:**
- `maritime_lookup_location` -- resolve historical place names to coordinates
- `maritime_list_locations` -- search/browse ~160 VOC-era locations by region or type
- `maritime_list_routes` -- list 8 standard VOC sailing routes
- `maritime_get_route` -- full route with waypoints, hazards, season notes
- `maritime_estimate_position` -- interpolate ship position on any date from route

**Data pipeline:**
- `scripts/download_das.py` -- downloads 8,194 voyages from DAS CSV endpoints, extracts vessels and wrecks
- `scripts/download_cliwoc.py` -- downloads ~261K ship logbook positions from CLIWOC (Figshare), all nationalities (1662-1855)
- `scripts/generate_reference.py` -- validates and reformats reference JSON files
- `scripts/download_all.py` -- orchestrates all download scripts
- All reference data (gazetteer, routes, hull profiles) stored as JSON in `data/`, loaded at runtime

**Reference data:**
- VOC Gazetteer: ~160 historical place names with coordinates, aliases, region classification
- VOC Routes: 8 sailing routes with waypoints, cumulative days, stop durations, hazards, season notes
- Hull Profiles: 6 ship type profiles with dimensions, hydrodynamics, sinking characteristics

**Quality:**
- 349 tests across 7 test modules, 97%+ branch coverage
- 13 example scripts (4 offline, 9 network-dependent)

### v0.3.0 -- CLIWOC Ship Tracks

Expanded to 26 tools across 13 categories. CLIWOC logbook data searchable via MCP.

**New tools:**
- `maritime_search_tracks` -- search historical ship tracks by nationality, date range
- `maritime_get_track` -- get full position history for a specific voyage
- `maritime_nearby_tracks` -- find ships near a given position on a given date

**Features:**
- Filter by nationality (NL, UK, ES, FR, SE, US, DE, DK) and year range (1662-1855)
- 1,973 voyages with 260,631 daily logbook positions
- Nearby ship search with haversine distance calculation
- Useful for context: "what other ships were in this area when the wreck occurred?"

**Quality:**
- 396 tests across 8 test modules, 97%+ branch coverage
- 14 example scripts (5 offline, 9 network-dependent)

### v0.4.0 -- Cross-Archive Linking & CLIWOC 2.1 Full

Expanded to 27 tools across 14 categories. Unified cross-archive queries and richer CLIWOC data.

**New tools:**
- `maritime_get_voyage_full` -- single call returning voyage + wreck + vessel + hull profile + CLIWOC track

**CLIWOC 2.1 Full upgrade:**
- Upgraded from CLIWOC Slim (7 columns) to CLIWOC 2.1 Full (182 columns, 282K records)
- Ship names, company (VOC, EIC, RN, etc.), DAS number, ship type, voyage from/to
- `maritime_search_tracks` now supports `ship_name` parameter
- DASnumber field directly links CLIWOC logbook records to DAS voyages
- 1,981 voyages with 260,639 positions; 1,981 with ship names, 48 with DAS numbers

**Cross-archive linking:**
- `WreckClient.get_by_voyage_id()` -- find wreck linked to a voyage
- `DASClient.get_vessel_for_voyage()` -- find vessel via reverse voyage_ids index
- `get_track_by_das_number()` -- CLIWOC↔DAS direct linking via DAS number
- `find_track_for_voyage()` -- fuzzy match CLIWOC tracks by ship name + date overlap
- `ArchiveManager.get_voyage_full()` -- orchestrates all linking in one call

**Quality:**
- 430 tests across 9 test modules, 97%+ branch coverage
- 15 example scripts (6 offline, 9 network-dependent)

### v0.5.0 -- Enhanced Position Estimation & Timeline View

Expanded to 29 tools across 16 categories. CLIWOC-based speed profiles and chronological timeline.

**New tools:**
- `maritime_get_speed_profile` -- per-segment sailing speed statistics derived from CLIWOC track data
- `maritime_get_timeline` -- chronological event view combining all data sources for a voyage

**Speed profiles (Enhanced Position Estimation):**
- Pre-computed speed statistics per route segment from CLIWOC 2.1 daily positions
- 215 profiles across 6 routes (outward_outer, return, ceylon, coromandel, japan, malabar)
- Mean, median, std dev, and percentile speeds (km/day) per segment
- Seasonal variation: month-specific profiles where sample counts permit
- `maritime_estimate_position` now accepts `use_speed_profiles=True` to enrich estimates with historical speed data
- Generation script `scripts/generate_speed_profiles.py` for reproducible computation from CLIWOC data

**Timeline view:**
- `maritime_get_timeline` assembles chronological events for any DAS voyage
- Combines: departure, route waypoint estimates, CLIWOC track positions, wreck/loss, arrival
- Optional `include_positions=True` to sample CLIWOC daily positions into the timeline
- GeoJSON LineString output from positioned events
- Event types: `departure`, `waypoint_estimate`, `cliwoc_position`, `loss`, `arrival`

**Quality:**
- 483 tests across 11 test modules, 97%+ branch coverage
- 16 example scripts (8 offline, 8 network-dependent)

### v0.6.0 -- Artifact Store Integration

Wired up chuk-artifacts for GeoJSON storage and S3-backed reference data preloading.

**Artifact-stored exports:**
- `maritime_export_geojson` stores GeoJSON to artifact store with `scope="sandbox"`
- `maritime_get_timeline` stores timeline GeoJSON to artifact store
- `artifact_ref` field populated in `GeoJSONExportResponse` and `TimelineResponse`
- Graceful degradation: if store is unavailable, `artifact_ref` is `None` but all data is still returned

**S3-backed reference data preloading:**
- `scripts/upload_reference_data.py` uploads all 8 data files to artifact store, produces manifest
- Set `MARITIME_REFERENCE_MANIFEST=<id>` in `.env` for automatic preloading at startup
- Server downloads missing files from artifacts before importing data loaders
- Eliminates need to run download scripts on each new server deployment

**Configuration:**
- `.env.example` template documenting all environment variables
- Restructured `server.py` startup: init store -> preload reference data -> import async_server

**Quality:**
- 499 tests across 12 test modules, 97%+ branch coverage

### v0.7.0 -- Additional Archives (EIC, Carreira, Galleon, SOIC)

Expanded from 4 Dutch archives to 8 multi-nation archives. Multi-archive dispatch via existing tools.

**New archives:**
- **English East India Company (EIC)** -- ~150 voyages, ~35 wrecks (1600-1874). Curated from Hardy's Register of Ships and Farrington's Catalogue.
- **Portuguese Carreira da India** -- ~120 voyages, ~40 wrecks (1497-1835). Curated from Guinote/Frutuoso/Lopes "As Armadas da India".
- **Spanish Manila Galleon** -- ~100 voyages, ~25 wrecks (1565-1815). Curated from Schurz "The Manila Galleon".
- **Swedish East India Company (SOIC)** -- ~80 voyages, ~12 wrecks (1731-1813). Curated from Koninckx "First and Second Charters of the SEIC".

**Architecture:**
- Multi-archive dispatch in `ArchiveManager` -- `_voyage_clients` and `_wreck_clients` dicts route queries by archive ID or ID prefix
- `search_voyages(archive="eic")` queries a single archive; no archive filter queries all 5
- `get_voyage("eic:0001")` routes by prefix to the correct client
- 4 new client classes (`EICClient`, `CarreiraClient`, `GalleonClient`, `SOICClient`) following `BaseArchiveClient` pattern
- Each client handles both voyages and wrecks in a single class
- CLIWOC nationality cross-referencing: `eic`→UK, `carreira`→PT, `galleon`→ES, `soic`→SE
- `archive` field added to `VoyageInfo` and `WreckInfo` response models

**Data pipeline:**
- `scripts/generate_eic.py`, `scripts/generate_carreira.py`, `scripts/generate_galleon.py`, `scripts/generate_soic.py`
- Each script contains embedded curated data from published academic sources
- `scripts/download_all.py` updated to run all 4 generation scripts

**Quality:**
- 585 tests across 13 test modules, 97%+ branch coverage

### v0.8.0 -- Expanded Archives & Download Infrastructure

Full-coverage data pipeline with cache-check-download pattern and expanded curated archives.

**Download infrastructure:**
- `scripts/download_utils.py` -- shared utilities: `parse_args()` with `--force`, `is_cached()`, `download_file()`, `save_json()`
- All 10 download/generate scripts retrofitted with `--force` flag and cache-check pattern
- `scripts/download_all.py` rewritten to orchestrate all scripts with `--force` passthrough

**New download scripts:**
- `scripts/download_crew.py` -- downloads 774K VOC crew records from Nationaal Archief bulk CSV
- `scripts/download_cargo.py` -- downloads BGB cargo data from Zenodo RDF dataset
- `scripts/download_eic.py` -- downloads EIC data from ThreeDecks (falls back to curated generator)

**Expanded curated archives:**
- **Carreira da India**: 120 → ~500 voyages, 40 → ~100 wrecks. Programmatic fleet-filling with era-appropriate ship name, captain, and tonnage pools covering 1497-1835.
- **Manila Galleon**: 100 → ~250 voyages, 25 → ~42 wrecks. Expanded with eastbound/westbound pairs and era-specific cargo details covering 1565-1815.
- **SOIC**: 80 → ~132 voyages, 12 → ~20 wrecks. Added 8 wreck entries along the Gothenburg-Canton route.

**Crew client indexed lookups:**
- `CrewClient` rewritten with lazy-built in-memory indexes for O(1) voyage_id and crew_id lookups
- `_voyage_index`: dict[str, list[dict]] for fast filtered search across 774K records
- `_id_index`: dict[str, dict] for instant crew member retrieval

**Cargo data model fix:**
- `CargoInfo.quantity` changed from `float | None` to `str | float | None` to support descriptive quantities (e.g. "450 balen")

**Other:**
- `scripts/upload_reference_data.py` updated with new data files
- `.gitignore` updated: `data/cache/`, `data/crew.json`
- `constants.py` record counts updated for all expanded archives
- Version bumped to 0.8.0

### v0.9.0 -- Cursor-Based Pagination

Cursor-based pagination for all 6 search tools. Enables browsing large result sets page by page.

**Pagination infrastructure:**
- `encode_cursor()` / `decode_cursor()` utilities (base64-encoded offset)
- `PaginatedResult` dataclass returned by all `ArchiveManager.search_*()` methods
- `_paginate()` static method centralises offset/limit slicing across all search methods
- `MAX_PAGE_SIZE = 500` clamp prevents oversized pages

**Updated search tools (6 tools):**
- `maritime_search_voyages` -- `cursor` parameter, `total_count` / `next_cursor` / `has_more` in response
- `maritime_search_wrecks` -- same pattern
- `maritime_search_crew` -- same pattern (enables paging through 774K records)
- `maritime_search_cargo` -- same pattern
- `maritime_search_vessels` -- same pattern
- `maritime_search_tracks` -- same pattern (tool-level pagination for CLIWOC module function)

**Response model changes:**
- 6 search response models (`VoyageSearchResponse`, `WreckSearchResponse`, `CrewSearchResponse`, `CargoSearchResponse`, `VesselSearchResponse`, `TrackSearchResponse`) gained `total_count`, `next_cursor`, `has_more` fields
- `to_text()` output includes pagination footer when `has_more` is true
- Backward compatible: all new fields have safe defaults (`None` / `False`)

**Multi-archive pagination:**
- Deterministic sort order for multi-archive results (by date + ID) ensures stable pagination
- Fetch all matching records from all clients, sort, then paginate the combined result

**Quality:**
- 597 tests across 13 test modules, 97%+ branch coverage

---

## Planned

### WebSocket Transport

Real-time updates for interactive exploration.

- Subscribe to search refinements
- Progressive result loading
- Live position tracking during route estimation

---

## Related Servers (Ecosystem)

### chuk-mcp-ocean-drift (v0.1.0, 10 tools, 235 tests)

Drift modelling server that consumes hull profiles and position data from this server.

- Forward and backtrack drift computation from wreck site or sinking point
- Monte Carlo simulations for probability distributions
- Uses hull hydrodynamic profiles (drag coefficients, windage, sinking characteristics)
- Accounts for wind/current patterns
- Output: probability map of wreck location as GeoJSON

### Composable Ecosystem

This server is the data layer in a composable stack of MCP servers:

| Server | Tools | Tests | Role |
|--------|-------|-------|------|
| chuk-mcp-maritime-archives | 29 | 597 | Voyage, wreck, vessel, crew, cargo records |
| chuk-mcp-ocean-drift | 10 | 235 | Forward/backtrack/Monte Carlo drift |
| chuk-mcp-dem | 4 | 711 | Bathymetry and elevation data |
| chuk-mcp-stac | 5 | 382 | Satellite imagery via STAC catalogues |
| chuk-mcp-celestial | 8 | 254 | Tidal forces, sun/moon positions |
| chuk-mcp-tides | 8 | 717 | Tidal current data |
| chuk-mcp-physics | 66 | 240 | Fluid dynamics computations |
| chuk-mcp-open-meteo | 6 | 22 | Weather and wind data |
| **Total** | **136** | **3,158** | |

All servers follow the same patterns: Pydantic v2 models, dual output mode, chuk-artifacts storage.

**Example wreck investigation pipeline:**
1. `maritime_search_wrecks` → find wreck, get position + uncertainty
2. `maritime_get_hull_profile` → drag coefficients, sinking characteristics
3. `maritime_assess_position` → quantify position reliability
4. `ocean_drift_backtrack` → reverse-compute from wreck site to sinking point
5. `dem_get_elevation` → confirm depth at candidate locations
6. `tides_get_currents` → tidal influence at the site
7. `stac_search` → satellite/sonar imagery of search area

---

## Data Sources

Current and potential data sources for the project.

### Active

| Source | Records | Script | Status |
|--------|---------|--------|--------|
| [DAS](https://resources.huygens.knaw.nl/das) | 8,194 voyages | `download_das.py` | Working |
| [CLIWOC 2.1 Full](https://historicalclimatology.com/cliwoc.html) | 282K records, 182 columns | `download_cliwoc.py` | Working |
| [VOC Opvarenden](https://www.nationaalarchief.nl/) | 774,200 crew records | `download_crew.py` | Working (bulk CSV download) |
| [BGB Cargo](https://bgb.huygens.knaw.nl/) | 200 curated + expandable | `download_cargo.py` / `generate_cargo.py` | Working (Zenodo RDF + curated fallback) |
| VOC Gazetteer | ~160 places | `data/gazetteer.json` | Curated |
| VOC Routes | 8 routes | `data/routes.json` | Curated |
| Hull Profiles | 6 types | `data/hull_profiles.json` | Curated |
| Speed Profiles | 215 profiles, 6 routes | `data/speed_profiles.json` | Generated from CLIWOC |
| EIC Archives | ~150 voyages, ~35 wrecks | `generate_eic.py` / `download_eic.py` | Curated from Hardy/Farrington + ThreeDecks download |
| Carreira da India | ~500 voyages, ~100 wrecks | `generate_carreira.py` | Curated + expanded from Guinote/Frutuoso/Lopes |
| Manila Galleon | ~250 voyages, ~42 wrecks | `generate_galleon.py` | Curated + expanded from Schurz |
| SOIC Archives | ~132 voyages, ~20 wrecks | `generate_soic.py` | Curated + expanded from Koninckx |

> **Note:** All download and generate scripts support `--force` to regenerate data. Run `python scripts/download_all.py` to fetch/generate all datasets. Core reference data is ~35 MB; with crew data downloaded, total is ~115 MB.

### Potential

| Source | Description | Format | Notes |
|--------|-------------|--------|-------|
| [Dutch Ships and Sailors](https://datasets.iisg.amsterdam/dataverse/dss) | Linked data on Dutch maritime | RDF/SPARQL | Crew, ships, voyages -- needs SPARQL client |
| [Nationaal Archief OAI](https://www.nationaalarchief.nl/) | Archival metadata | OAI-PMH | Broader than just VOC |

---

## Contributing

See [README.md](README.md#contributing) for contribution guidelines. Key areas where help is welcome:

- **EIC expansion** -- expanding the 150-voyage EIC dataset using Hardy's Register and ThreeDecks data
- **Gazetteer expansion** -- adding more historical place names with coordinates (especially for non-Dutch ports)
- **Route accuracy** -- improving waypoint positions and sailing time estimates
- **Additional sailing routes** -- EIC, Carreira, Galleon, and SOIC standard routes
- **Test coverage** -- edge cases in position estimation, date handling, and multi-archive dispatch
- **Cargo enrichment** -- expanding the 200-record curated cargo dataset using Glamann's "Dutch-Asiatic Trade" tables
