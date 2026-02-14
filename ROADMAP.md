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
- `maritime_list_locations` -- search/browse ~170 VOC-era locations by region or type
- `maritime_list_routes` -- list historical sailing routes (18 routes, 5 nations)
- `maritime_get_route` -- full route with waypoints, hazards, season notes
- `maritime_estimate_position` -- interpolate ship position on any date from route

**Data pipeline:**
- `scripts/download_das.py` -- downloads 8,194 voyages from DAS CSV endpoints, extracts vessels and wrecks
- `scripts/download_cliwoc.py` -- downloads ~261K ship logbook positions from CLIWOC (Figshare), all nationalities (1662-1855)
- `scripts/generate_reference.py` -- validates and reformats reference JSON files
- `scripts/download_all.py` -- orchestrates all download scripts
- All reference data (gazetteer, routes, hull profiles) stored as JSON in `data/`, loaded at runtime

**Reference data:**
- VOC Gazetteer: ~170 historical place names with coordinates, aliases, region classification
- Historical Routes: 18 sailing routes (5 nations) with waypoints, cumulative days, stop durations, hazards, season notes
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
- `get_track_by_das_number()` -- CLIWOC-DAS direct linking via DAS number
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
- CLIWOC nationality cross-referencing: `eic`->UK, `carreira`->PT, `galleon`->ES, `soic`->SE
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
- **Carreira da India**: 120 -> ~500 voyages, 40 -> ~100 wrecks
- **Manila Galleon**: 100 -> ~250 voyages, 25 -> ~42 wrecks
- **SOIC**: 80 -> ~132 voyages, 12 -> ~20 wrecks

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
- `maritime_search_voyages`, `maritime_search_wrecks`, `maritime_search_crew`, `maritime_search_cargo`, `maritime_search_vessels`, `maritime_search_tracks`
- `total_count` / `next_cursor` / `has_more` in all search responses

**Response model changes:**
- 6 search response models (`VoyageSearchResponse`, `WreckSearchResponse`, `CrewSearchResponse`, `CargoSearchResponse`, `VesselSearchResponse`, `TrackSearchResponse`) gained `total_count`, `next_cursor`, `has_more` fields
- `to_text()` output includes pagination footer when `has_more` is true
- Backward compatible: all new fields have safe defaults (`None` / `False`)

**Multi-archive pagination:**
- Deterministic sort order for multi-archive results (by date + ID) ensures stable pagination
- Fetch all matching records from all clients, sort, then paginate the combined result

**Quality:**
- 597 tests across 13 test modules, 97%+ branch coverage

### v0.11.0 -- UKHO Global Wrecks

Integrated the UK Hydrographic Office wrecks and obstructions dataset -- 94,000+ records worldwide, available under Open Government Licence v3.0.

**New archive:**
- **`UKHOClient`** -- wrecks-only client following `BaseArchiveClient` pattern with lazy-indexed lookups for 94K records
- `scripts/download_ukho.py` -- downloads from EMODnet WFS service with paginated requests
- `scripts/generate_ukho.py` -- curated fallback of 50 representative wrecks (ships with repo)
- Multi-archive dispatch: `search_wrecks(archive="ukho")` or cross-archive search
- 9 archives across 6 nations; total wreck records expanded from ~930 to ~95,000

**New search filters:**
- `flag` -- filter wrecks by vessel nationality (UKHO-specific)
- `vessel_type` -- filter by ship type classification (UKHO-specific)

**Expanded geographic coverage:**
- 5 new global regions: `north_atlantic`, `mediterranean`, `baltic`, `north_pacific`, `australia_nz`
- `classify_region()` bounding-box classifier maps global UKHO positions to region codes
- `"collision"` added to `LOSS_CAUSES` for UKHO data

**Quality:**
- 616 tests across 13 test modules, 97%+ branch coverage

### v0.12.0 -- NOAA Wrecks & Obstructions (US Waters)

Integrated NOAA's Automated Wreck and Obstruction Information System (AWOIS) -- ~13,000 wrecks in US coastal waters, public domain.

**New archive:**
- **`NOAAClient`** -- wrecks-only client following `UKHOClient` pattern with GP quality filtering
- `scripts/download_noaa.py` -- downloads from NOAA ArcGIS REST API with paginated requests
- `scripts/generate_noaa.py` -- curated fallback of 50 representative US wrecks (ships with repo)
- Multi-archive dispatch: `search_wrecks(archive="noaa")` or cross-archive search
- 10 archives across 6 nations; 7 wreck archives total

**New search filter:**
- `gp_quality` -- NOAA position accuracy code (1=High, 2=Medium, 3=Low, 4=Poor)

**Expanded geographic coverage:**
- 2 new US regions: `gulf_of_mexico`, `great_lakes`
- `classify_region()` maps US waters to region codes

**Quality:**
- 636 tests across 13 test modules, 97%+ branch coverage

### v0.13.0 -- Full-Text Narrative Search

Full-text search across all free-text narrative content in all 10 archives.

**New tool:**
- `maritime_search_narratives` -- search voyage `particulars`, wreck `particulars`, and wreck `loss_location` fields across all archives
- Simple keyword and quoted phrase matching with AND logic
- Relevance-ranked results (by term frequency) with ~200-char text snippets
- Filter by `record_type` (voyage/wreck) and `archive`
- Cursor-based pagination

**Architecture:**
- `ArchiveManager.search_narratives()` scans all voyage and wreck clients, extracts narrative fields, matches against query terms, builds result dicts with snippet extraction
- `_parse_query_terms()` supports quoted phrases and bare keywords
- `_extract_snippet()` centres a ~200-char snippet around the first match
- In-memory substring search (no external search engine) -- consistent with local-first pattern
- `NarrativeHit` and `NarrativeSearchResponse` Pydantic v2 response models
- `tools/narratives/api.py` with `register_narrative_tools()`

**Narrative fields searched:**
- Voyage `particulars`: DAS, EIC, Carreira, Galleon, SOIC
- Wreck `particulars`: MAARER, EIC, Carreira, Galleon
- Wreck `loss_location`: all 7 wreck archives

**Quality:**
- 727 tests across 13 test modules, 96%+ branch coverage

### v0.14.0 -- Track Analytics

Expanded to 33 tools across 17 categories. Server-side speed computation, aggregation, and statistical testing on CLIWOC track data.

**New tools:**
- `maritime_compute_track_speeds` -- compute daily sailing speeds (haversine) for a single CLIWOC voyage
- `maritime_aggregate_track_speeds` -- aggregate daily speeds across all matching tracks by decade, year, month, direction, or nationality
- `maritime_compare_speed_groups` -- Mann-Whitney U test comparing speed distributions between two time periods

**Enhanced tools:**
- `maritime_search_tracks` -- added `lat_min`, `lat_max`, `lon_min`, `lon_max` optional params for geographic bounding box filtering

**Architecture:**
- `_compute_daily_speeds()` computes haversine distances between consecutive logbook positions, filters by lat/lon band and speed bounds
- `aggregate_track_speeds()` bulk-computes speeds across all matching tracks, groups by dimension, returns n/mean/median/std/95% CI/percentiles per group
- `compare_speed_groups()` implements Mann-Whitney U with large-sample normal approximation (no scipy dependency) + Cohen's d effect size
- `_infer_direction()` determines eastbound/westbound from longitude change (handles 180° wrap)
- New response models: `DailySpeed`, `TrackSpeedsResponse`, `SpeedAggregationGroup`, `TrackSpeedAggregationResponse`, `SpeedComparisonResponse`
- `tools/analytics/api.py` with `register_analytics_tools()`

**Enables:**
- "Find all tracks passing through the Roaring Forties" (lat/lon bounding box search)
- "Compute decadal speed trends in the Southern Ocean" (server-side aggregation)
- "Is the speed difference between 1750s and 1850s statistically significant?" (Mann-Whitney U)
- Full climate proxy analysis workflow via mcp-cli without pre-computed data

**Example demos:**
- `climate_proxy_demo.py` -- full climate proxy analysis using live analytics tools (decadal, monthly, directional, nationality trends + Mann-Whitney U tests)
- `volcanic_signal_demo.py` -- four novel research analyses: Laki 1783 volcanic signal detection, E/W speed ratio as wind vs technology decomposition, seasonal amplitude evolution, western vs eastern Indian Ocean spatial variation

**Quality:**
- 762 tests across 13 test modules, 96%+ branch coverage

### v0.15.0 -- Dutch Ships and Sailors (Linked Data)

Expanded to 36 tools across 19 categories. Integrated the DSS Linked Data Cloud with GZMVOC ship muster records and MDB individual crew records.

**New tools:**
- `maritime_search_musters` -- search GZMVOC ship-level muster records from Asian waters (1691-1791)
- `maritime_get_muster` -- get full muster record details (crew composition, wages, ranks)
- `maritime_compare_wages` -- compare crew wage distributions between two time periods

**Enhanced tools:**
- `maritime_search_crew` -- extended with `archive="dss"` for MDB individual crew records (1803-1837)
- `maritime_get_crew_member` -- extended to route `dss:` prefixed IDs to DSSClient

**New archive:**
- **Dutch Ships and Sailors (DSS)** -- CLARIN-IV project combining multiple Dutch maritime datasets
- **GZMVOC (Generale Zeemonsterrollen VOC)**: Ship-level crew composition and muster records from Asian waters (1691-1791). Crew counts, wages, rank summaries per ship.
- **MDB (Noordelijke Monsterrollen)**: Individual crew records from four northern Dutch provinces (Groningen, Friesland, Drenthe, Overijssel), 1803-1837. ~77,043 records.
- Cross-links to DAS voyages via `das_voyage_id` field

**Architecture:**
- `DSSClient` -- new client following multi-data-file pattern (musters + crews), with lazy indexes for muster, crew, and voyage-muster lookups
- `_crew_clients` dispatch dict in `ArchiveManager` (like `_voyage_clients` / `_wreck_clients`) for multi-archive crew search
- `compare_wages()` method with mean/median statistics and percentage difference
- Response models: `MusterInfo`, `MusterSearchResponse`, `MusterDetailResponse`, `WageComparisonResponse`
- `tools/musters/api.py` with `register_muster_tools()`

**Data pipeline:**
- `scripts/generate_dss.py` -- curated fallback data generator (70 musters, 101 crew records)
- `scripts/download_dss.py` -- .ttl download from DANS Data Station with Turtle parser (SPARQL endpoints offline)

**Quality:**
- 810 tests across 13 test modules, 97%+ branch coverage

### v0.16.0 -- Improved Cross-Archive Entity Resolution

Expanded to 37 tools across 19 categories. Added pure-Python fuzzy entity resolution for historical ship name matching, confidence scoring for all cross-archive links, a link audit tool, and crew-voyage linking.

**New tool:**
- `maritime_audit_links` -- audit cross-archive link quality with precision/recall metrics and confidence distribution

**Enhanced tools:**
- `maritime_get_voyage_full` -- gains `link_confidence` dict (0.0-1.0 per link), optional `include_crew` parameter for crew record linking

**Entity resolution module** (`core/entity_resolution.py`):
- Ship name normalization: strips articles (De, Het, 'T, HMS, VOC), preserves saints (San, Santa, Sao)
- Levenshtein distance (two-row DP) for edit-distance similarity
- American Soundex for phonetic matching across historical spelling variants
- Composite scoring: name similarity (0.50), date proximity (0.30), nationality (0.10), phonetic (0.10)
- `ShipNameIndex` -- three-level pre-built index (exact -> Soundex -> Levenshtein fallback)

**Results:**
- 45 direct DAS-CLIWOC links + 118 fuzzy matches (163 total, up from 48 direct-only)
- Mean fuzzy match confidence: 0.661
- 83 high-confidence (0.7-0.9), 35 moderate (0.5-0.7) fuzzy matches

**Data quality:**
- `is_curated` field on all EIC, Carreira, Galleon, and SOIC records: `true` for hand-curated entries from historical sources, `false` for programmatically expanded fleet records

**Example demos:**
- `entity_resolution_demo.py` -- ship name normalization, fuzzy matching, composite scoring, index lookup, link_confidence display, audit metrics

**Quality:**
- 923 tests across 14 test modules, 96%+ branch coverage

### v0.17.0 -- Additional Sailing Routes

Extended the route library from 8 VOC routes to 18 routes across all 5 archive nations. Expanded gazetteer with 10 new ports. Position estimation now works for all nations.

**New routes (10):**
- **EIC (British)**: `eic_outward` (Downs->Madras, 180d), `eic_china` (Downs->Canton, 210d), `eic_return` (Madras->Downs, 180d), `eic_country` (Madras->Calcutta, 30d intra-Asian)
- **Carreira da India (Portuguese)**: `carreira_outward` (Lisbon->Goa, 180d), `carreira_return` (Goa->Lisbon, 180d)
- **Manila Galleon (Spanish)**: `galleon_westbound` (Acapulco->Manila, 90d), `galleon_eastbound` (Manila->Acapulco, 130d)
- **SOIC (Swedish)**: `soic_outward` (Gothenburg->Canton, 240d), `soic_return` (Canton->Gothenburg, 210d)

**New direction values:**
- `pacific_westbound` and `pacific_eastbound` for Manila Galleon Pacific crossings

**Gazetteer expansion (10 new entries):**
- London, The Downs, Lisbon, Gothenburg, Acapulco, Guam, Cape Mendocino, Azores, San Bernardino Strait, Masulipatnam
- Mozambique entry updated with aliases (Ilha de Mocambique, Mozambique Island)

**Speed profile classification:**
- `generate_speed_profiles.py` updated with port sets and classification rules for EIC, Carreira, Galleon, and SOIC routes
- UK track catch-all split into specific EIC routes (eic_outward, eic_china) with narrowed VOC fallback

**Quality:**
- 968+ tests across 14 test modules, 96%+ branch coverage

### v0.18.0 -- Crew Demographics & Network Analysis

Analytical tools built on the 774K crew records cross-referenced with voyage data.

- `maritime_crew_demographics` -- aggregate statistics by rank, origin, fate, decade, or ship with sub-distributions
- `maritime_crew_career` -- reconstruct individual careers across multiple voyages (name + origin matching, rank progression)
- `maritime_crew_survival_analysis` -- survival, mortality, and desertion rates by dimension
- `CrewClient.all_records()` for bulk analytics across the full 774K record dataset
- 7 new Pydantic response models: `DemographicsGroup`, `CrewDemographicsResponse`, `CareerVoyage`, `CareerRecord`, `CrewCareerResponse`, `SurvivalGroup`, `CrewSurvivalResponse`
- `examples/crew_demographics_demo.py` -- 8-section demo: rank distribution, origin distribution, decade trends, fate breakdown, career reconstruction, survival by rank, survival by decade, text mode

**Quality:**
- 1033+ tests across 14 test modules, 96%+ branch coverage

### v0.18.1 -- Bugfixes (Prefix Normalisation & Date-Line Crossing)

Two bugfixes discovered during GPT-5.2 testing and architecture review.

**Bug 1: Voyage ID prefix normalisation**
- `_find_wreck_for_voyage("0372.1")` would default prefix to `"das"` correctly, but then pass the raw `"0372.1"` to `wreck_client.get_by_voyage_id()`, which did an exact match against stored `"das:0372.1"` — returning `None`. Same issue affected `get_vessel_for_voyage()`.
- **Fixes**: `ArchiveManager._find_wreck_for_voyage()` normalises to prefixed form; `WreckClient.get_by_voyage_id()` and `DASClient.get_vessel_for_voyage()` try `das:` prefix fallback.

**Bug 2: Date-line crossing in position estimation**
- `estimate_position()` used naive linear interpolation for longitude. On the Manila Galleon westbound route, interpolating between Mid-Pacific (lon=-170) and Guam (lon=+144.79) produced lon=31.47 (Africa) instead of lon=161.07 (western Pacific).
- **Fix**: detect >180° longitude difference and wrap the shorter way around ±180°, then normalise result to [-180, 180].

**ARCHITECTURE.md audit**: fixed 8 discrepancies — removed stale LRU cache documentation (never implemented), corrected archive count (10→11), category count (20→19), test module count (14→15), added missing tool directories (demographics/, musters/) to architecture diagram, added demographics/career/survival to ArchiveManager component description, added missing scripts to pipeline list.

**Quality:**
- 1042+ tests across 15 test modules, 96%+ branch coverage

### v0.19.0 -- Seasonal Climate Filters

Seasonal month filtering for track analytics tools, driven by GPT-5.2 Laki volcanic signal analysis.

**Context:** A GPT-5.2 session autonomously discovered a statistically significant Laki 1783 volcanic signal — UK eastbound speeds in the Roaring Forties increased +56 km/day (+31%) post-Laki with p≈0 and effect size d=0.64, while westbound speeds were flat. The model identified that `month_start`/`month_end` filtering would unlock the most diagnostic seasonal test for volcanic aerosol forcing.

**Enhanced tools:**
- `maritime_aggregate_track_speeds` -- added `month_start` / `month_end` params (1-12) with wrap-around support (e.g., 11-2 = Nov-Feb)
- `maritime_compare_speed_groups` -- added `month_start` / `month_end` params for seasonal decomposition of Mann-Whitney U tests

**Enables:**
- Austral winter (Jun-Aug) vs summer (Dec-Feb) decomposition for volcanic signal isolation
- Seasonal amplitude evolution analysis across decades
- Month-restricted statistical testing for climate proxy research

**Quality:**
- 1055+ tests across 15 test modules, 96%+ branch coverage

---

## Planned

### v1.0.0 -- Stability & API Freeze

Stable release with frozen tool signatures and response models.

- Semantic versioning commitment: no breaking changes within v1.x
- Published JSON Schema for all 33+ tool input/output models
- OpenAPI-compatible specification for HTTP mode
- Comprehensive migration guide from v0.x
- Performance benchmarks for all search tools across full dataset sizes
- Documentation: expanded ARCHITECTURE.md with data flow diagrams for all linking strategies

---

## Future Considerations

These are ideas being tracked but not yet committed to a specific version.

### EMODnet Shipwrecks (European)

The European Marine Observation and Data Network aggregates wreck data from SHOM (France), Historic England, Ireland's National Monument Service, and the Oxford Roman Economy Project. Would extend European coverage significantly, including archaeological wrecks dating back millennia.

### Lloyd's List & War Losses

Lloyd's List (1740-present) covers global shipping movements and casualties. Lloyd's War Losses (1914-1945) covers WWI/WWII vessel losses. Both would massively expand temporal coverage but access is restricted and would require licensing agreements.

### WebSocket Transport

Real-time updates for interactive exploration.

- Subscribe to search refinements
- Progressive result loading
- Live position tracking during route estimation

### Wreck Probability Surfaces

Systematic position correction for all unfound wrecks using the full pipeline.

- For each of ~680 unfound VOC wrecks: classify position uncertainty -> estimate drift from hull profile -> generate probability surface
- Requires chuk-mcp-ocean-drift integration for drift computation
- Output: GeoJSON probability maps per wreck, scored and ranked by search feasibility
- The 54 found wrecks serve as ground truth for calibrating drift models

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
| chuk-mcp-maritime-archives | 40 | 1042+ | Voyage, wreck, vessel, crew, cargo, musters, demographics, analytics |
| chuk-mcp-ocean-drift | 10 | 235 | Forward/backtrack/Monte Carlo drift |
| chuk-mcp-dem | 4 | 711 | Bathymetry and elevation data |
| chuk-mcp-stac | 5 | 382 | Satellite imagery via STAC catalogues |
| chuk-mcp-celestial | 8 | 254 | Tidal forces, sun/moon positions |
| chuk-mcp-tides | 8 | 717 | Tidal current data |
| chuk-mcp-physics | 66 | 240 | Fluid dynamics computations |
| chuk-mcp-open-meteo | 6 | 22 | Weather and wind data |
| **Total** | **145** | **3,479+** | |

All servers follow the same patterns: Pydantic v2 models, dual output mode, chuk-artifacts storage.

**Example wreck investigation pipeline:**
1. `maritime_search_wrecks` -> find wreck, get position + uncertainty
2. `maritime_get_hull_profile` -> drag coefficients, sinking characteristics
3. `maritime_assess_position` -> quantify position reliability
4. `ocean_drift_backtrack` -> reverse-compute from wreck site to sinking point
5. `dem_get_elevation` -> confirm depth at candidate locations
6. `tides_get_currents` -> tidal influence at the site
7. `stac_search` -> satellite/sonar imagery of search area

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
| VOC Gazetteer | ~170 places | `data/gazetteer.json` | Curated |
| Historical Routes | 18 routes (5 nations) | `data/routes.json` | Curated |
| Hull Profiles | 6 types | `data/hull_profiles.json` | Curated |
| Speed Profiles | 215 profiles, 6 routes | `data/speed_profiles.json` | Generated from CLIWOC |
| EIC Archives | ~150 voyages, ~35 wrecks | `generate_eic.py` / `download_eic.py` | Curated from Hardy/Farrington + ThreeDecks download |
| Carreira da India | ~500 voyages, ~100 wrecks | `generate_carreira.py` | Curated + expanded from Guinote/Frutuoso/Lopes |
| Manila Galleon | ~250 voyages, ~42 wrecks | `generate_galleon.py` | Curated + expanded from Schurz |
| SOIC Archives | ~132 voyages, ~20 wrecks | `generate_soic.py` | Curated + expanded from Koninckx |
| [UKHO Wrecks](https://www.admiralty.co.uk/access-data/marine-data) | 94,000+ wrecks worldwide | `download_ukho.py` / `generate_ukho.py` | Working (EMODnet WFS download + curated fallback) |
| [NOAA AWOIS](https://nauticalcharts.noaa.gov/) | ~13,000 US wrecks | `download_noaa.py` / `generate_noaa.py` | Working (ArcGIS REST download + curated fallback) |
| [Dutch Ships and Sailors](https://datasets.iisg.amsterdam/dataverse/dss) | ~70 musters, ~101 crew (curated) | `generate_dss.py` / `download_dss.py` | Working (curated + .ttl download fallback) |

> **Note:** All download and generate scripts support `--force` to regenerate data. Run `python scripts/download_all.py` to fetch/generate all datasets. Core reference data is ~35 MB; with crew data downloaded, total is ~115 MB.

### Potential

| Source | Description | Format | Notes |
|--------|-------------|--------|-------|
| [EMODnet Shipwrecks](https://emodnet.ec.europa.eu/) | European wreck aggregation (SHOM, Historic England, Ireland, Oxford Roman Economy) | WFS/CSV | Multi-source, includes archaeological wrecks dating back millennia |
| [Nationaal Archief OAI](https://www.nationaalarchief.nl/) | Archival metadata | OAI-PMH | Broader than just VOC |
| Lloyd's List | Global shipping movements and casualties (1740-present) | Restricted | Would require licensing |
| Lloyd's War Losses | WWI/WWII vessel losses (1914-1945) | Restricted | Would require licensing |

---

## Contributing

See [README.md](README.md#contributing) for contribution guidelines. Key areas where help is welcome:

- **EIC expansion** -- expanding the 150-voyage EIC dataset using Hardy's Register and ThreeDecks data
- **Gazetteer expansion** -- adding more historical place names with coordinates (especially for non-Dutch ports)
- **Route accuracy** -- improving waypoint positions and sailing time estimates
- **Route accuracy** -- improving waypoint positions and sailing time estimates for all 18 routes
- **Test coverage** -- edge cases in position estimation, date handling, and multi-archive dispatch
- **Cargo enrichment** -- expanding the 200-record curated cargo dataset using Glamann's "Dutch-Asiatic Trade" tables
- **Entity resolution** -- improving fuzzy matching between CLIWOC ship names and DAS voyage records
- **Narrative search expansion** -- improving relevance ranking and adding boolean operators to `maritime_search_narratives`
