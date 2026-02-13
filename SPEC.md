# chuk-mcp-maritime-archives Specification

Version 0.13.0

## Overview

chuk-mcp-maritime-archives is an MCP (Model Context Protocol) server that provides
structured access to historical maritime shipping records, vessel specifications,
crew muster rolls, cargo manifests, and shipwreck databases from the Age of Exploration
through the colonial era and beyond, 1497-2024. Covers Dutch (VOC), English (EIC), Portuguese
(Carreira da India), Spanish (Manila Galleon), Swedish (SOIC), UK Hydrographic Office (UKHO), and NOAA maritime archives.

- **30 tools** for searching, retrieving, analysing, and exporting maritime archival data
- **Cursor-based pagination** -- all 8 search tools support `cursor` / `next_cursor` / `has_more` for paging through large result sets
- **Dual output mode** -- all tools return JSON (default) or human-readable text via `output_mode` parameter
- **Async-first** -- tool entry points are async; sync HTTP I/O runs in thread pools
- **Pluggable storage** -- exported data stored via chuk-artifacts (memory, filesystem, S3)

## Supported Archives

| Archive ID | Name | Organisation | Records | Period | Data Types |
|-----------|------|-------------|---------|--------|------------|
| `das` | Dutch Asiatic Shipping | Huygens Institute | 8,194 voyages | 1595-1795 | voyages, vessels, incidents |
| `voc_crew` | VOC Opvarenden | Nationaal Archief | up to 774,200 records | 1633-1794 | crew muster rolls |
| `voc_cargo` | Boekhouder-Generaal Batavia | Huygens Institute | 200 curated records | 1700-1795 | cargo manifests |
| `maarer` | MAARER VOC Wrecks | Maritime Archaeological Research | 734 wrecks | 1595-1795 | wreck positions, incidents |
| `eic` | English East India Company | Curated from Hardy/Farrington | ~150 voyages, ~35 wrecks | 1600-1874 | voyages, wrecks |
| `carreira` | Portuguese Carreira da India | Curated + expanded from Guinote/Frutuoso/Lopes | ~500 voyages, ~100 wrecks | 1497-1835 | voyages, wrecks |
| `galleon` | Spanish Manila Galleon | Curated + expanded from Schurz | ~250 voyages, ~42 wrecks | 1565-1815 | voyages, wrecks |
| `soic` | Swedish East India Company | Curated + expanded from Koninckx | ~132 voyages, ~20 wrecks | 1731-1813 | voyages, wrecks |
| `ukho` | UK Hydrographic Office Global Wrecks | UK Hydrographic Office via EMODnet | 94,000+ wrecks | 1500-2024 | wrecks |
| `noaa` | NOAA Wrecks and Obstructions | NOAA Office of Coast Survey | 10,000+ wrecks | 1500-2024 | wrecks |

> **Note on data completeness:** The EIC, Carreira, Galleon, and SOIC archives are curated datasets compiled from published academic sources. Carreira, Galleon, and SOIC include programmatically expanded records covering the full historical period. VOC Crew data requires running `scripts/download_crew.py` to download from the Nationaal Archief (774K records, ~80 MB). Cargo and EIC have download scripts for future expansion from external sources.

### Archive Sources

| Archive | Base URL | Access Method |
|---------|----------|---------------|
| DAS | `https://resources.huygens.knaw.nl/das` | REST API via `download_das.py` |
| VOC Crew | `https://www.nationaalarchief.nl/onderzoeken/index/nt00444` | Bulk download via `download_crew.py` |
| BGB Cargo | `https://bgb.huygens.knaw.nl` | Curated local JSON + `download_cargo.py` |
| MAARER | `https://resources.huygens.knaw.nl/das` | Compiled data endpoint |
| EIC | Hardy/Farrington published sources | Local JSON via `generate_eic.py` + `download_eic.py` |
| Carreira | Guinote/Frutuoso/Lopes published sources | Local JSON via `generate_carreira.py` |
| Galleon | Schurz published sources | Local JSON via `generate_galleon.py` |
| SOIC | Koninckx published sources | Local JSON via `generate_soic.py` |
| UKHO | EMODnet Human Activities portal | Bulk download via `download_ukho.py` + `generate_ukho.py` fallback |
| NOAA | NOAA ENC Direct API | REST API via `download_noaa.py` + `generate_noaa.py` fallback |

All archives except DAS, UKHO, and NOAA work entirely offline with local JSON data. DAS data is
cached locally after first download. VOC Crew requires running `download_crew.py`
to fetch the 774K-record dataset. All scripts support `--force` for re-download.

---

## Tools

### Common Parameter

All tools accept the following optional parameter:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_mode` | `str` | `json` | Response format: `json` (structured) or `text` (human-readable) |

---

### Archive Discovery Tools

#### `maritime_list_archives`

List all available maritime archives with metadata.

**Parameters:** `output_mode` only

**Response:** `ArchiveListResponse`

| Field | Type | Description |
|-------|------|-------------|
| `archive_count` | `int` | Number of archives |
| `archives` | `ArchiveInfo[]` | Archive metadata entries |
| `message` | `str` | Result message |

---

#### `maritime_get_archive`

Get detailed metadata for a specific archive.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `archive_id` | `str` | *required* | Archive identifier: `das`, `voc_crew`, `voc_cargo`, `maarer`, `eic`, `carreira`, `galleon`, `soic`, `ukho`, `noaa` |

**Response:** `ArchiveDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `archive` | `ArchiveInfo` | Full archive metadata |
| `message` | `str` | Result message |

---

### Voyage Tools

#### `maritime_search_voyages`

Search voyage records across all archives with multiple filter criteria.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ship_name` | `str?` | `None` | Ship name (substring match, case-insensitive) |
| `captain` | `str?` | `None` | Captain name (substring match) |
| `date_range` | `str?` | `None` | Date range `YYYY/YYYY` or `YYYY-MM-DD/YYYY-MM-DD` |
| `departure_port` | `str?` | `None` | Departure port (substring match) |
| `destination_port` | `str?` | `None` | Destination port (substring match) |
| `route` | `str?` | `None` | Route keyword (matched against summary and ports) |
| `fate` | `str?` | `None` | Voyage outcome: `completed`, `wrecked`, `captured`, `scuttled`, `missing` |
| `archive` | `str?` | `None` | Limit to specific archive |
| `max_results` | `int` | `50` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `VoyageSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `voyage_count` | `int` | Number of voyages on this page |
| `voyages` | `VoyageInfo[]` | Voyage summaries |
| `archive` | `str?` | Archive filter applied |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

---

#### `maritime_get_voyage`

Get full details for a specific voyage by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str` | *required* | Voyage identifier (e.g., `das:7892`, `eic:0001`, `carreira:0001`, `galleon:0009`, `soic:0002`) |

**Response:** `VoyageDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `voyage` | `dict` | Full voyage record including vessel, incident, sources |
| `message` | `str` | Result message |

---

### Wreck Tools

#### `maritime_search_wrecks`

Search shipwreck and loss records across all archives.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ship_name` | `str?` | `None` | Ship name (substring match) |
| `date_range` | `str?` | `None` | Date range `YYYY/YYYY` or `YYYY-MM-DD/YYYY-MM-DD` |
| `region` | `str?` | `None` | Geographic region code (see Regions table) |
| `cause` | `str?` | `None` | Loss cause: `storm`, `reef`, `fire`, `battle`, `grounding`, `scuttled`, `collision`, `unknown` |
| `status` | `str?` | `None` | Wreck status: `found`, `unfound`, `approximate` |
| `min_depth_m` | `float?` | `None` | Minimum depth in metres |
| `max_depth_m` | `float?` | `None` | Maximum depth in metres |
| `min_cargo_value` | `float?` | `None` | Minimum cargo value in guilders |
| `flag` | `str?` | `None` | Vessel nationality/flag (substring match, UKHO data) |
| `vessel_type` | `str?` | `None` | Vessel type classification (substring match, UKHO data) |
| `gp_quality` | `str?` | `None` | Geographic position quality: `surveyed`, `approximate`, `reported` (NOAA data) |
| `archive` | `str?` | `None` | Limit to specific archive |
| `max_results` | `int` | `100` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `WreckSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `wreck_count` | `int` | Number of wrecks on this page |
| `wrecks` | `WreckInfo[]` | Wreck summaries with positions |
| `archive` | `str?` | Archive filter applied |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

---

#### `maritime_get_wreck`

Get full details for a specific wreck by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wreck_id` | `str` | *required* | Wreck identifier (e.g., `maarer:VOC-0789`, `eic_wreck:0010`, `carreira_wreck:0001`, `galleon_wreck:0001`, `soic_wreck:0001`, `ukho_wreck:00001`, `noaa_wreck:00001`) |

**Response:** `WreckDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `wreck` | `dict` | Full wreck record including position, depth, archaeological notes |
| `message` | `str` | Result message |

---

### Vessel Tools

#### `maritime_search_vessels`

Search VOC vessel records.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str?` | `None` | Vessel name (substring match) |
| `ship_type` | `str?` | `None` | Ship type: `retourschip`, `fluit`, `jacht`, `hooker`, `pinas`, `fregat` |
| `built_range` | `str?` | `None` | Build year range |
| `shipyard` | `str?` | `None` | Shipyard name |
| `chamber` | `str?` | `None` | VOC chamber: `Amsterdam`, `Zeeland`, `Delft`, `Rotterdam`, `Hoorn`, `Enkhuizen` |
| `min_tonnage` | `int?` | `None` | Minimum tonnage (lasten) |
| `max_tonnage` | `int?` | `None` | Maximum tonnage (lasten) |
| `archive` | `str?` | `None` | Limit to specific archive |
| `max_results` | `int` | `50` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `VesselSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `vessel_count` | `int` | Number of vessels on this page |
| `vessels` | `VesselInfo[]` | Vessel summaries |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

---

#### `maritime_get_vessel`

Get full specifications for a specific vessel by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vessel_id` | `str` | *required* | Vessel identifier (e.g., `das_vessel:1234`) |

**Response:** `VesselDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `vessel` | `dict` | Full vessel record including type, tonnage, shipyard, chamber |
| `message` | `str` | Result message |

---

#### `maritime_get_hull_profile`

Get hydrodynamic hull profile data for a ship type. Used for drift modelling
and wreck-site prediction.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ship_type` | `str` | *required* | Ship type code: `retourschip`, `fluit`, `jacht`, `hooker`, `pinas`, `fregat` |

**Response:** `HullProfileResponse`

| Field | Type | Description |
|-------|------|-------------|
| `profile` | `dict` | Full hull profile: dimensions, hydrodynamics, sinking characteristics, LLM guidance |
| `message` | `str` | Result message |

---

#### `maritime_list_hull_profiles`

List available ship types that have hull profile data.

**Parameters:** `output_mode` only

**Response:** `HullProfileListResponse`

| Field | Type | Description |
|-------|------|-------------|
| `ship_types` | `str[]` | Available ship type codes |
| `count` | `int` | Number of hull profiles |
| `message` | `str` | Result message |

---

### Crew Tools

#### `maritime_search_crew`

Search VOC crew muster roll records.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str?` | `None` | Person name (substring match) |
| `rank` | `str?` | `None` | Rank (e.g., `schipper`, `stuurman`, `bootsman`) |
| `ship_name` | `str?` | `None` | Ship name (substring match) |
| `voyage_id` | `str?` | `None` | Voyage identifier for cross-referencing |
| `origin` | `str?` | `None` | Place of origin (substring match) |
| `date_range` | `str?` | `None` | Date range |
| `fate` | `str?` | `None` | Service outcome: `survived`, `died_voyage`, `died_asia`, `deserted`, `discharged` |
| `archive` | `str` | `voc_crew` | Archive to query |
| `max_results` | `int` | `100` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `CrewSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `crew_count` | `int` | Number of crew records on this page |
| `crew` | `CrewInfo[]` | Crew record summaries |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

---

#### `maritime_get_crew_member`

Get full details for a specific crew member by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `crew_id` | `str` | *required* | Crew record identifier (e.g., `voc_crew:445892`) |

**Response:** `CrewDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `crew_member` | `dict` | Full crew record including rank, origin, pay, fate |
| `message` | `str` | Result message |

---

### Cargo Tools

#### `maritime_search_cargo`

Search cargo manifest records.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str?` | `None` | Filter by voyage |
| `commodity` | `str?` | `None` | Commodity name (substring match, e.g., `pepper`, `silver`) |
| `origin` | `str?` | `None` | Origin port/region (substring match) |
| `destination` | `str?` | `None` | Destination port (substring match) |
| `date_range` | `str?` | `None` | Date range |
| `min_value` | `float?` | `None` | Minimum value in guilders |
| `archive` | `str` | `voc_cargo` | Archive to query |
| `max_results` | `int` | `100` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `CargoSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `cargo_count` | `int` | Number of cargo entries on this page |
| `cargo` | `CargoInfo[]` | Cargo record summaries |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

---

#### `maritime_get_cargo_manifest`

Get the full cargo manifest for a specific voyage.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str` | *required* | Voyage identifier (e.g., `das:8123`) |

**Response:** `CargoDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `cargo_entries` | `dict[]` | All cargo entries for the voyage |
| `voyage_id` | `str` | Voyage identifier |
| `message` | `str` | Result message |

---

### Location Gazetteer Tools

#### `maritime_lookup_location`

Look up a historical place name in the VOC gazetteer. Returns coordinates, region
classification, and historical context. Handles aliases and historical spellings.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | *required* | Place name to look up (e.g., "Batavia", "Texel", "Kaap de Goede Hoop") |

**Response:** `LocationDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `location` | `LocationInfo` | Location with coordinates, region, type, aliases, notes |
| `message` | `str` | Result message |

---

#### `maritime_list_locations`

Search or browse the VOC historical gazetteer with optional filters.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str?` | `None` | Text search in names, aliases, and notes (case-insensitive substring) |
| `region` | `str?` | `None` | Filter by region code (see Regions table) |
| `location_type` | `str?` | `None` | Filter by type: `port`, `island`, `cape`, `anchorage`, `waterway`, `coast`, `channel`, `region` |
| `max_results` | `int` | `50` | Maximum results to return |

**Response:** `LocationSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `location_count` | `int` | Number of locations found |
| `locations` | `LocationInfo[]` | Location entries with coordinates |
| `message` | `str` | Result message |

---

### Route Tools

#### `maritime_list_routes`

List available VOC standard sailing routes. Optionally filter by direction or ports.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `direction` | `str?` | `None` | Route direction: `outward`, `return`, `intra_asian` |
| `departure_port` | `str?` | `None` | Filter routes containing this departure port (substring match) |
| `destination_port` | `str?` | `None` | Filter routes containing this destination (substring match) |

**Response:** `RouteListResponse`

| Field | Type | Description |
|-------|------|-------------|
| `route_count` | `int` | Number of routes found |
| `routes` | `RouteInfo[]` | Route summaries with direction, duration, waypoint count |
| `message` | `str` | Result message |

---

#### `maritime_get_route`

Get full details of a standard VOC sailing route including all waypoints.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `route_id` | `str` | *required* | Route identifier: `outward_outer`, `outward_inner`, `return`, `japan`, `spice_islands`, `ceylon`, `coromandel`, `malabar` |

**Response:** `RouteDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `route` | `dict` | Full route: name, description, direction, waypoints, hazards, season notes |
| `message` | `str` | Result message |

**Route Waypoint Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Waypoint name (e.g., "Cape of Good Hope") |
| `lat` | `float` | Latitude |
| `lon` | `float` | Longitude |
| `region` | `str` | Geographic region code |
| `cumulative_days` | `int` | Typical days elapsed from departure |
| `stop_days` | `int` | Typical days spent at this waypoint (0 = passing) |
| `notes` | `str` | Historical notes |

---

#### `maritime_estimate_position`

Estimate a ship's position on a specific date based on its route. Uses linear
interpolation between standard waypoints assuming typical sailing times.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `route_id` | `str` | *required* | Route identifier (from `maritime_list_routes`) |
| `departure_date` | `str` | *required* | Ship's departure date as `YYYY-MM-DD` |
| `target_date` | `str` | *required* | Date to estimate position for as `YYYY-MM-DD` |
| `use_speed_profiles` | `bool` | `false` | Enrich estimate with CLIWOC-derived speed statistics for the current segment |

**Response:** `PositionEstimateResponse`

| Field | Type | Description |
|-------|------|-------------|
| `estimate` | `dict` | Full estimate with position, segment, confidence, caveats |
| `message` | `str` | Result message |

**Estimate Output Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `route_id` | `str` | Route used for estimation |
| `departure_date` | `str` | Departure date |
| `target_date` | `str` | Target date |
| `elapsed_days` | `int` | Days elapsed since departure |
| `total_route_days` | `int` | Total typical days for this route |
| `voyage_progress` | `float` | 0.0-1.0 progress through the route |
| `estimated_position.lat` | `float` | Estimated latitude |
| `estimated_position.lon` | `float` | Estimated longitude |
| `estimated_position.region` | `str` | Geographic region at estimated position |
| `segment.from` | `str` | Previous waypoint name |
| `segment.to` | `str` | Next waypoint name |
| `segment.progress` | `float` | 0.0-1.0 progress through current segment |
| `confidence` | `str` | `high` (at port), `moderate` (between waypoints), `low` (past arrival) |
| `caveats` | `str[]` | Important caveats about estimate accuracy |
| `speed_profile` | `dict?` | Present when `use_speed_profiles=True` and data exists for the segment |

**Speed Profile Fields (when present):**

| Field | Type | Description |
|-------|------|-------------|
| `mean_km_day` | `float` | Mean historical speed for this segment (km/day) |
| `std_dev_km_day` | `float` | Standard deviation of historical speeds |
| `sample_count` | `int` | Number of CLIWOC observations used |
| `departure_month` | `int?` | Month-specific data (null = all-months aggregate) |

---

### Speed Profile Tools

#### `maritime_get_speed_profile`

Get historical sailing speed statistics per route segment, derived from CLIWOC 2.1
daily position data. Profiles give mean, median, standard deviation, and percentile
speeds (km/day) for each segment of a route, optionally broken down by departure month
for seasonal variation.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `route_id` | `str` | *required* | Route identifier (e.g., `"outward_outer"`, `"return"`) |
| `departure_month` | `int?` | `None` | Month (1-12) for seasonal data; omit for all-months aggregates |

**Response:** `SpeedProfileResponse`

| Field | Type | Description |
|-------|------|-------------|
| `route_id` | `str` | Route identifier |
| `departure_month` | `int?` | Month filter applied (null = all-months) |
| `segment_count` | `int` | Number of segments with data |
| `segments` | `SegmentSpeedInfo[]` | Per-segment speed statistics |
| `notes` | `str?` | Additional context |
| `message` | `str` | Result message |

**SegmentSpeedInfo fields:**

| Field | Type | Description |
|-------|------|-------------|
| `segment_from` | `str` | Origin waypoint name |
| `segment_to` | `str` | Destination waypoint name |
| `departure_month` | `int?` | Month-specific data (null = all-months aggregate) |
| `sample_count` | `int` | Number of CLIWOC observations |
| `mean_km_day` | `float` | Mean speed in km/day |
| `median_km_day` | `float` | Median speed in km/day |
| `std_dev_km_day` | `float` | Standard deviation of speed |
| `min_km_day` | `float?` | Minimum observed speed |
| `max_km_day` | `float?` | Maximum observed speed |
| `p25_km_day` | `float?` | 25th percentile speed |
| `p75_km_day` | `float?` | 75th percentile speed |

---

### Timeline Tools

#### `maritime_get_timeline`

Build a chronological timeline of events for a voyage from any archive, combining data
from the voyage database, route estimates, CLIWOC ship tracks, and wreck records. Useful
for understanding the full sequence of events in a voyage.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str` | *required* | Voyage identifier from any archive (e.g., `"das:0372.1"`, `"eic:0062"`, `"carreira:0001"`) |
| `include_positions` | `bool` | `false` | Include sampled CLIWOC daily positions as events |
| `max_positions` | `int` | `20` | Maximum CLIWOC positions to include (when `include_positions=True`) |

**Response:** `TimelineResponse`

| Field | Type | Description |
|-------|------|-------------|
| `voyage_id` | `str` | Voyage identifier |
| `ship_name` | `str?` | Ship name from voyage record |
| `event_count` | `int` | Total number of events |
| `events` | `TimelineEvent[]` | Chronological event list |
| `geojson` | `dict?` | GeoJSON LineString from positioned events |
| `data_sources` | `str[]` | Data sources used (e.g., `["das", "route_estimate", "cliwoc", "maarer"]`) |
| `message` | `str` | Result message |

**TimelineEvent fields:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | `str` | Event date (YYYY-MM-DD or partial) |
| `type` | `str` | Event type: `departure`, `waypoint_estimate`, `cliwoc_position`, `loss`, `arrival` |
| `title` | `str` | Human-readable event title |
| `details` | `dict` | Additional event-specific data |
| `position` | `dict?` | `{lat, lon}` if position is known |
| `source` | `str` | Data source: `das`, `route_estimate`, `cliwoc`, `maarer` |

---

### CLIWOC Ship Track Tools

#### `maritime_search_tracks`

Search historical ship tracks from the CLIWOC database (~261K daily logbook
positions from 1662-1855, 8 European maritime nations).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `nationality` | `str?` | `None` | Two-letter nationality code: NL, UK, ES, FR, SE, US, DE, DK |
| `year_start` | `int?` | `None` | Earliest year to include |
| `year_end` | `int?` | `None` | Latest year to include |
| `ship_name` | `str?` | `None` | Ship name or partial name (case-insensitive; requires CLIWOC 2.1 Full data) |
| `max_results` | `int` | `50` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |
| `output_mode` | `str` | `"json"` | `"json"` or `"text"` |

**Response: `TrackSearchResponse`**

| Field | Type | Description |
|-------|------|-------------|
| `track_count` | `int` | Number of tracks on this page |
| `tracks` | `TrackInfo[]` | Track summaries (no positions) |
| `total_count` | `int?` | Total matching tracks across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Human-readable summary |

**TrackInfo fields:**

| Field | Type | Description |
|-------|------|-------------|
| `voyage_id` | `int` | CLIWOC voyage identifier |
| `nationality` | `str?` | Two-letter nationality code |
| `start_date` | `str?` | First recorded position date |
| `end_date` | `str?` | Last recorded position date |
| `duration_days` | `int?` | Voyage duration in days |
| `year_start` | `int?` | Earliest year of positions |
| `year_end` | `int?` | Latest year of positions |
| `position_count` | `int` | Number of daily position records |

---

#### `maritime_get_track`

Get full position history for a CLIWOC voyage, including all dated lat/lon
positions from the ship's logbook.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `int` | required | CLIWOC voyage ID (from search results) |
| `output_mode` | `str` | `"json"` | `"json"` or `"text"` |

**Response: `TrackDetailResponse`**

| Field | Type | Description |
|-------|------|-------------|
| `track` | `dict` | Full track with metadata and positions |
| `message` | `str` | Human-readable summary |

Track includes all TrackInfo fields plus `positions` — a list of
`{date, lat, lon}` objects representing daily logbook readings.

---

#### `maritime_nearby_tracks`

Find ships near a given position on a given date. Searches all CLIWOC logbook
positions and returns tracks with positions within the search radius.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lat` | `float` | required | Latitude of search point (decimal degrees) |
| `lon` | `float` | required | Longitude of search point (decimal degrees) |
| `date` | `str` | required | Date to search (YYYY-MM-DD) |
| `radius_km` | `float` | `200.0` | Search radius in kilometres |
| `max_results` | `int` | `20` | Maximum results |
| `output_mode` | `str` | `"json"` | `"json"` or `"text"` |

**Response: `NearbyTracksResponse`**

| Field | Type | Description |
|-------|------|-------------|
| `search_point` | `dict` | `{lat, lon}` of search centre |
| `search_date` | `str` | Date searched |
| `radius_km` | `float` | Search radius used |
| `track_count` | `int` | Number of matches |
| `tracks` | `NearbyTrackInfo[]` | Matching tracks sorted by distance |
| `message` | `str` | Human-readable summary |

**NearbyTrackInfo fields:**

| Field | Type | Description |
|-------|------|-------------|
| `voyage_id` | `int` | CLIWOC voyage identifier |
| `nationality` | `str?` | Two-letter nationality code |
| `distance_km` | `float` | Distance from search point (km) |
| `matching_position` | `dict` | `{date, lat, lon}` of nearest position |
| `start_date` | `str?` | Voyage start date |
| `end_date` | `str?` | Voyage end date |
| `duration_days` | `int?` | Voyage duration |
| `position_count` | `int` | Total positions in track |

---

### Cross-Archive Linking Tools

#### `maritime_get_voyage_full`

Get a unified view of a voyage with all linked records: wreck, vessel,
hull profile, and CLIWOC track. This is the primary tool for cross-archive
investigation — it follows all links between voyage databases (DAS, EIC,
Carreira, Galleon, SOIC), wreck records, vessel registry, hull profiles,
and CLIWOC ship tracks automatically in a single call.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str` | required | Voyage identifier from any archive (e.g. `"das:0372.1"`, `"eic:0062"`, `"carreira:0001"`, `"galleon:0009"`, `"soic:0002"`) |
| `output_mode` | `str` | `"json"` | `"json"` or `"text"` |

**Response: `VoyageFullResponse`**

| Field | Type | Description |
|-------|------|-------------|
| `voyage` | `dict` | The voyage record (from any archive) |
| `wreck` | `dict?` | Linked wreck record (if ship was lost) |
| `vessel` | `dict?` | Linked vessel record (from DAS vessel registry, DAS voyages only) |
| `hull_profile` | `dict?` | Hull profile for the ship type |
| `cliwoc_track` | `dict?` | Linked CLIWOC track summary (without positions) |
| `links_found` | `str[]` | Names of linked records found (e.g. `["wreck", "vessel"]`) |
| `message` | `str` | Human-readable summary |

**Linking strategy:**

1. **Wreck**: Found by matching `voyage_id` in wreck records
2. **Vessel**: Found by reverse lookup in vessel `voyage_ids` arrays
3. **Hull profile**: Found by matching voyage `ship_type` to hull profile data
4. **CLIWOC track**: Found by DAS number (exact match), or ship name + nationality + date overlap (fuzzy match). Nationality mapped from archive: `das`/`eic`→NL/UK, `carreira`→PT, `galleon`→ES, `soic`→SE

---

### Position Assessment Tool

#### `maritime_assess_position`

Assess the quality and uncertainty of a historical position, accounting for the
navigation technology available at the time and the nature of the source.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str?` | `None` | Voyage to assess (looks up position from voyage record) |
| `wreck_id` | `str?` | `None` | Wreck to assess (looks up position from wreck record) |
| `position` | `dict?` | `None` | Manual position `{lat, lon}` to assess |
| `source_description` | `str?` | `None` | Description of how the position was determined |
| `date` | `str?` | `None` | Date for navigation era determination |

**Response:** `PositionAssessmentResponse`

| Field | Type | Description |
|-------|------|-------------|
| `assessment` | `dict` | Full assessment including quality score, uncertainty type/radius, factors, recommendations |
| `message` | `str` | Result message |

**Assessment Output Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `quality_score` | `float` | 0.0-1.0 quality score |
| `quality_label` | `str` | `good`, `moderate`, or `poor` |
| `uncertainty_type` | `str` | One of: `precise`, `triangulated`, `dead_reckoning`, `approximate`, `regional` |
| `uncertainty_radius_km` | `float` | Radius of uncertainty circle in kilometres |
| `confidence` | `float` | Confidence level (0.68 = 1-sigma) |
| `recommendations` | `dict` | Guidance for drift modelling and search planning |

---

### Export Tools

#### `maritime_export_geojson`

Export wreck positions as a GeoJSON FeatureCollection. Optionally stores the
result in the artifact store.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wreck_ids` | `str[]?` | `None` | Specific wreck IDs to export |
| `region` | `str?` | `None` | Filter by region |
| `status` | `str?` | `None` | Filter by wreck status |
| `archive` | `str?` | `None` | Filter by archive |
| `include_uncertainty` | `bool` | `true` | Include uncertainty radius in properties |
| `include_voyage_data` | `bool` | `true` | Include ship type, tonnage, loss cause |

**Response:** `GeoJSONExportResponse`

| Field | Type | Description |
|-------|------|-------------|
| `geojson` | `dict` | GeoJSON FeatureCollection |
| `feature_count` | `int` | Number of features exported |
| `artifact_ref` | `str?` | Artifact store reference (if stored) |
| `message` | `str` | Result message |

---

#### `maritime_get_statistics`

Get aggregate loss statistics across archives.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `archive` | `str?` | `None` | Limit to specific archive |
| `date_range` | `str?` | `None` | Date range filter |
| `group_by` | `str?` | `None` | Grouping dimension |

**Response:** `StatisticsResponse`

| Field | Type | Description |
|-------|------|-------------|
| `statistics` | `dict` | Aggregate statistics: totals, by region, by cause, by decade |
| `message` | `str` | Result message |

**Statistics Output Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `summary.total_losses` | `int` | Total number of ship losses |
| `summary.lives_lost_total` | `int` | Total lives lost |
| `summary.cargo_value_guilders_total` | `float` | Total cargo value lost |
| `losses_by_region` | `dict` | Loss count per geographic region |
| `losses_by_cause` | `dict` | Loss count per cause (storm, reef, fire, etc.) |
| `losses_by_status` | `dict` | Loss count per wreck status (found/unfound) |
| `losses_by_decade` | `dict` | Loss count per decade |

---

### Narrative Search Tool

#### `maritime_search_narratives`

Search free-text narrative content across all maritime archives. Searches voyage
`particulars`, wreck `particulars`, and wreck `loss_location` fields. All query
terms must be present (AND logic). Quoted phrases are matched exactly.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | Search text: keywords or quoted phrases (e.g. `"monsoon"`, `'"Cape of Good Hope"'`) |
| `record_type` | `str?` | `None` | Limit to `"voyage"` or `"wreck"` (default: both) |
| `archive` | `str?` | `None` | Restrict to a specific archive ID |
| `max_results` | `int` | `50` | Maximum results per page (max: 500) |
| `cursor` | `str?` | `None` | Pagination cursor from a previous result's `next_cursor` field |

**Response:** `NarrativeSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `result_count` | `int` | Number of results on this page |
| `results` | `NarrativeHit[]` | Matching narrative excerpts |
| `query` | `str` | Query used |
| `record_type` | `str?` | Record type filter applied |
| `archive` | `str?` | Archive filter applied |
| `total_count` | `int?` | Total matching records across all pages |
| `next_cursor` | `str?` | Cursor for next page (null if no more pages) |
| `has_more` | `bool` | Whether more pages are available |
| `message` | `str` | Result message |

**NarrativeHit fields:**

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `str` | Voyage ID or wreck ID |
| `record_type` | `str` | `"voyage"` or `"wreck"` |
| `archive` | `str` | Archive ID |
| `ship_name` | `str` | Ship name |
| `date` | `str?` | Departure date (voyages) or loss date (wrecks) |
| `field` | `str` | Field that matched (e.g. `"particulars"`, `"loss_location"`) |
| `snippet` | `str` | ~200-char text snippet with match context |
| `match_count` | `int` | Number of term occurrences in this record |

---

### Discovery Tool

#### `maritime_capabilities`

List full server capabilities for LLM workflow planning.

**Parameters:** `output_mode` only

**Response:** `CapabilitiesResponse`

| Field | Type | Description |
|-------|------|-------------|
| `server_name` | `str` | Server name |
| `version` | `str` | Server version |
| `archives` | `ArchiveInfo[]` | Available archives with metadata |
| `tools` | `ToolInfo[]` | All registered tools with categories and descriptions |
| `ship_types` | `str[]` | Available ship type codes |
| `regions` | `dict` | Geographic region codes and descriptions |
| `message` | `str` | Result message |

---

## Domain Reference Data

### VOC Ship Types

| Type | Description | Tonnage (lasten) |
|------|-------------|-----------------|
| `retourschip` | Large three-masted ship for Asia route | 600-1200 |
| `fluit` | Cargo vessel, economical crew requirements | 200-600 |
| `jacht` | Fast, light vessel for patrol and messenger duties | 50-200 |
| `hooker` | Small coastal trading vessel | 30-150 |
| `pinas` | Medium ship, versatile for trade and war | 200-500 |
| `fregat` | Fast warship, smaller than retourschip | 300-600 |

### Hull Profile Data

Each ship type includes full hydrodynamic profiles for drift modelling:

| Parameter | Units | Description |
|-----------|-------|-------------|
| `displacement_tonnes` | tonnes | Hull displacement {min, max, typical} |
| `block_coefficient` | dimensionless | Block coefficient Cb |
| `waterplane_area_m2` | m^2 | Waterplane area |
| `drag_coefficient_broadside` | dimensionless | Broadside drag |
| `drag_coefficient_longitudinal` | dimensionless | Longitudinal drag |
| `windage_area_m2` | m^2 | Above-waterline area |
| `windage_coefficient` | dimensionless | Wind drag coefficient |
| `terminal_velocity_ms` | m/s | Sinking terminal velocity |
| `orientation_weights` | probabilities | Sinking orientation likelihoods |

### Geographic Regions

| Region Code | Description |
|------------|-------------|
| `north_sea` | North Sea, English Channel |
| `english_channel` | English Channel approaches |
| `atlantic_europe` | Bay of Biscay to Canaries |
| `west_africa` | West African coast |
| `atlantic_crossing` | Mid-Atlantic |
| `south_atlantic` | South Atlantic Ocean |
| `cape` | Cape of Good Hope region |
| `mozambique_channel` | East African coast |
| `indian_ocean` | Open Indian Ocean |
| `arabian_sea` | Arabian Sea and Gulf of Aden |
| `malabar` | Indian west coast |
| `coromandel` | Indian east coast |
| `ceylon` | Sri Lanka waters |
| `bengal` | Bay of Bengal |
| `malacca` | Straits of Malacca |
| `indonesia` | Indonesian archipelago |
| `south_china_sea` | Vietnam, Philippines, South China |
| `south_china_coast` | South China coast |
| `philippine_sea` | Philippine Sea |
| `pacific` | Pacific Ocean |
| `japan` | Japanese waters |
| `caribbean` | Caribbean Sea |
| `gulf_of_mexico` | Gulf of Mexico |
| `great_lakes` | Great Lakes |
| `north_atlantic` | North Atlantic Ocean |
| `mediterranean` | Mediterranean Sea |
| `baltic` | Baltic Sea |
| `north_pacific` | North Pacific Ocean |
| `australia_nz` | Australia and New Zealand waters |

### Navigation Technology by Era

| Period | Technology | Typical Accuracy | Notes |
|--------|-----------|-----------------|-------|
| 1497-1595 | Dead reckoning with astrolabe | 35 km | Pre-VOC era. Portuguese and Spanish exploration. |
| 1595-1650 | Dead reckoning with cross-staff | 30 km | Early VOC era. No reliable longitude method. |
| 1650-1700 | Dead reckoning with backstaff | 25 km | Improved latitude measurements. |
| 1700-1760 | Dead reckoning with octant | 20 km | Hadley's octant from 1731. Better latitude. |
| 1760-1795 | Chronometer era | 10 km | Harrison's chronometer. Longitude measurable but instruments rare on VOC ships. |
| 1795-1840 | Chronometer widespread | 5 km | Marine chronometers standard equipment on major trading vessels. |
| 1840-1874 | Steam era navigation | 3 km | Steam power + chronometers. Late EIC period. |

### Position Uncertainty Types

| Type | Description | Typical Radius |
|------|-------------|---------------|
| `precise` | Modern GPS or well-surveyed wreck site | <100 m |
| `triangulated` | Multiple historical sources agree | <5 km |
| `dead_reckoning` | Calculated from course/speed | 10-100 km |
| `approximate` | General area described | 50-500 km |
| `regional` | Only broad region known | 100-1000 km |

### VOC Chambers

The six administrative divisions of the VOC that built and maintained ships:

`Amsterdam`, `Zeeland`, `Delft`, `Rotterdam`, `Hoorn`, `Enkhuizen`

### Loss Causes

`storm`, `reef`, `fire`, `battle`, `grounding`, `scuttled`, `collision`, `unknown`

### Voyage Fates

`completed`, `wrecked`, `captured`, `scuttled`, `missing`

### Crew Fates

`survived`, `died_voyage`, `died_asia`, `deserted`, `discharged`

---

## Caching Strategy

### LRU Caches

| Cache | Max Entries | Key Format | Populated By |
|-------|------------|-----------|-------------|
| Voyage cache | 500 | `das:7892` | `search_voyages`, `get_voyage` |
| Wreck cache | 500 | `maarer:VOC-0456` | `search_wrecks`, `get_wreck` |
| Vessel cache | unbounded | `das_vessel:1234` | `search_vessels`, `get_vessel` |

### Cache Behaviour

- **Search results populate caches**: every record from a search result is inserted
  into the relevant cache, enabling cache hits on follow-up detail requests
- **Cache-first lookups**: `get_voyage()`, `get_wreck()`, and `get_vessel()` check
  the cache before making an API call
- **LRU eviction**: when the cache exceeds its limit, the oldest (least recently
  used) entry is evicted via `OrderedDict.popitem(last=False)`
- **LRU touch on access**: both `_cache_put()` and `_cache_get()` call
  `move_to_end(key)` to refresh the entry's position

---

## Error Handling

All tools return `ErrorResponse` on failure:

```json
{
  "error": "Archive 'invalid' not found. Available: das, voc_crew, voc_cargo, maarer, eic, carreira, galleon, soic, ukho, noaa",
  "message": ""
}
```

### Common Error Scenarios

| Scenario | Error Message Template |
|----------|----------------------|
| Invalid archive ID | `"Archive '{}' not found. Available: {}"` |
| Voyage not found | `"Voyage '{}' not found"` |
| Wreck not found | `"Wreck '{}' not found"` |
| Vessel not found | `"Vessel '{}' not found"` |
| Crew not found | `"Crew record '{}' not found"` |
| Cargo not found | `"No cargo records for voyage '{}'"` |
| Invalid date range | `"Invalid date range format. Use YYYY/YYYY or YYYY-MM-DD/YYYY-MM-DD"` |
| Unknown region | `"Unknown region '{}'. Valid regions: {}"` |
| Unknown ship type | `"Unknown ship type '{}'. Valid types: {}"` |
| No results | `"No results found matching search criteria"` |
| Service unavailable | `"Archive '{}' temporarily unavailable"` |

---

## Artifact Storage

Exported GeoJSON data is stored via chuk-artifacts with metadata:

```json
{
  "type": "archive_export",
  "format": "application/geo+json",
  "feature_count": 5,
  "region": "cape",
  "include_uncertainty": true
}
```

### Storage Providers

| Provider | Env Variable | Value |
|----------|-------------|-------|
| Memory (default) | `CHUK_ARTIFACTS_PROVIDER` | `memory` |
| Filesystem | `CHUK_ARTIFACTS_PROVIDER` | `filesystem` |
| Amazon S3 | `CHUK_ARTIFACTS_PROVIDER` | `s3` |

Additional environment variables for S3: `BUCKET_NAME`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL_S3`.

---

## GeoJSON Export Format

Wreck positions are exported as standard GeoJSON FeatureCollection:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [113.79, -28.49]
      },
      "properties": {
        "wreck_id": "maarer:VOC-0789",
        "ship_name": "Batavia",
        "loss_date": "1629-06-04",
        "status": "found",
        "uncertainty_km": 0.1,
        "ship_type": "retourschip",
        "tonnage": 600,
        "loss_cause": "reef",
        "lives_lost": 125,
        "depth_m": 5
      }
    }
  ]
}
```

Optional property groups controlled by parameters:
- `include_uncertainty=true` adds `uncertainty_km`
- `include_voyage_data=true` adds `ship_type`, `tonnage`, `loss_cause`, `lives_lost`, `depth_m`
