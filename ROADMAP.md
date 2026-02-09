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

---

## Planned

### Streaming Search

Paginated search results for large result sets.

- Cursor-based pagination for voyage, crew, and cargo searches
- `next_cursor` field in search responses
- Efficient for browsing the full 8,194-voyage or 774,200-crew datasets

### Additional Archives

Expand beyond Dutch maritime records.

- **English East India Company (EIC)** -- British Library digitised records
- **Portuguese Estado da India** -- Arquivo Nacional da Torre do Tombo
- **Spanish Manila Galleon** -- Archivo General de Indias
- **Swedish East India Company** -- Gothenburg city archives
- Each archive gets its own download script and client

### WebSocket Transport

Real-time updates for interactive exploration.

- Subscribe to search refinements
- Progressive result loading
- Live position tracking during route estimation

---

## Separate Projects

### Drift Modelling (chuk-mcp-drift-modelling)

Drift modelling will be implemented as a dedicated MCP server that consumes hull profiles and position data from this server.

- Estimate where debris/hull drifted given wreck date, position, and ship type
- Use hull hydrodynamic profiles (drag coefficients, windage, sinking characteristics)
- Account for seasonal wind/current patterns
- Output: probability map of wreck location as GeoJSON

---

## Data Sources

Current and potential data sources for the project.

### Active

| Source | Records | Script | Status |
|--------|---------|--------|--------|
| [DAS](https://resources.huygens.knaw.nl/das) | 8,194 voyages | `download_das.py` | Working |
| [CLIWOC 2.1 Full](https://historicalclimatology.com/cliwoc.html) | 282K records, 182 columns | `download_cliwoc.py` | Working |
| VOC Gazetteer | ~160 places | `data/gazetteer.json` | Curated |
| VOC Routes | 8 routes | `data/routes.json` | Curated |
| Hull Profiles | 6 types | `data/hull_profiles.json` | Curated |
| Speed Profiles | 215 profiles, 6 routes | `data/speed_profiles.json` | Generated from CLIWOC |

### Potential

| Source | Description | Format | Notes |
|--------|-------------|--------|-------|
| [Dutch Ships and Sailors](https://datasets.iisg.amsterdam/dataverse/dss) | Linked data on Dutch maritime | RDF/SPARQL | Crew, ships, voyages -- needs SPARQL client |
| [VOC Opvarenden](https://www.nationaalarchief.nl/) | 774,200 crew records | REST API | Currently stub client |
| [BGB Cargo](https://bgb.huygens.knaw.nl/) | ~50,000 cargo records | REST API | Currently stub client |
| [Nationaal Archief OAI](https://www.nationaalarchief.nl/) | Archival metadata | OAI-PMH | Broader than just VOC |

---

## Contributing

See [README.md](README.md#contributing) for contribution guidelines. Key areas where help is welcome:

- **New archive download scripts** -- especially for EIC, Portuguese, and Spanish records
- **Gazetteer expansion** -- adding more historical place names with coordinates
- **Route accuracy** -- improving waypoint positions and sailing time estimates
- **CLIWOC analysis** -- statistical speed profiles from actual ship track data
- **Test coverage** -- edge cases in position estimation and date handling
