# chuk-mcp-maritime-archives Specification

Version 0.1.0

## Overview

chuk-mcp-maritime-archives is an MCP (Model Context Protocol) server that provides
structured access to historical maritime shipping records, vessel specifications,
crew muster rolls, cargo manifests, and shipwreck databases from the Dutch East India
Company (VOC) era, 1595-1795.

- **18 tools** for searching, retrieving, analysing, and exporting maritime archival data
- **Dual output mode** -- all tools return JSON (default) or human-readable text via `output_mode` parameter
- **Async-first** -- tool entry points are async; sync HTTP I/O runs in thread pools
- **Pluggable storage** -- exported data stored via chuk-artifacts (memory, filesystem, S3)

## Supported Archives

| Archive ID | Name | Organisation | Records | Period | Data Types |
|-----------|------|-------------|---------|--------|------------|
| `das` | Dutch Asiatic Shipping | Huygens Institute | 8,194 voyages | 1595-1795 | voyages, vessels, incidents |
| `voc_crew` | VOC Opvarenden | Nationaal Archief | 774,200 records | 1633-1794 | crew muster rolls |
| `voc_cargo` | Boekhouder-Generaal Batavia | Nationaal Archief | ~50,000 records | 1700-1795 | cargo manifests |
| `maarer` | MAARER VOC Wrecks | Maritime Archaeological Research | 734 wrecks | 1595-1795 | wreck positions, incidents |

### Archive Sources

| Archive | Base URL | Access Method |
|---------|----------|---------------|
| DAS | `https://resources.huygens.knaw.nl/das` | REST API |
| VOC Crew | `https://www.nationaalarchief.nl/onderzoeken/index/nt00444` | REST API |
| BGB Cargo | `https://bgb.huygens.knaw.nl` | REST API |
| MAARER | `https://resources.huygens.knaw.nl/das` | Compiled data endpoint |

All archives fall back to curated sample data when the remote API is unavailable.

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
| `archive_id` | `str` | *required* | Archive identifier: `das`, `voc_crew`, `voc_cargo`, `maarer` |

**Response:** `ArchiveDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `archive` | `ArchiveInfo` | Full archive metadata |
| `message` | `str` | Result message |

---

### Voyage Tools

#### `maritime_search_voyages`

Search VOC voyage records with multiple filter criteria.

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
| `max_results` | `int` | `50` | Maximum results to return |

**Response:** `VoyageSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `voyage_count` | `int` | Number of voyages found |
| `voyages` | `VoyageInfo[]` | Voyage summaries |
| `archive` | `str?` | Archive filter applied |
| `message` | `str` | Result message |

---

#### `maritime_get_voyage`

Get full details for a specific voyage by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voyage_id` | `str` | *required* | Voyage identifier (e.g., `das:7892`) |

**Response:** `VoyageDetailResponse`

| Field | Type | Description |
|-------|------|-------------|
| `voyage` | `dict` | Full voyage record including vessel, incident, sources |
| `message` | `str` | Result message |

---

### Wreck Tools

#### `maritime_search_wrecks`

Search shipwreck and loss records.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ship_name` | `str?` | `None` | Ship name (substring match) |
| `date_range` | `str?` | `None` | Date range `YYYY/YYYY` or `YYYY-MM-DD/YYYY-MM-DD` |
| `region` | `str?` | `None` | Geographic region code (see Regions table) |
| `cause` | `str?` | `None` | Loss cause: `storm`, `reef`, `fire`, `battle`, `grounding`, `scuttled`, `unknown` |
| `status` | `str?` | `None` | Wreck status: `found`, `unfound`, `approximate` |
| `min_depth_m` | `float?` | `None` | Minimum depth in metres |
| `max_depth_m` | `float?` | `None` | Maximum depth in metres |
| `min_cargo_value` | `float?` | `None` | Minimum cargo value in guilders |
| `archive` | `str?` | `None` | Limit to specific archive |
| `max_results` | `int` | `100` | Maximum results to return |

**Response:** `WreckSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `wreck_count` | `int` | Number of wrecks found |
| `wrecks` | `WreckInfo[]` | Wreck summaries with positions |
| `archive` | `str?` | Archive filter applied |
| `message` | `str` | Result message |

---

#### `maritime_get_wreck`

Get full details for a specific wreck by ID.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `wreck_id` | `str` | *required* | Wreck identifier (e.g., `maarer:VOC-0789`) |

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
| `max_results` | `int` | `50` | Maximum results to return |

**Response:** `VesselSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `vessel_count` | `int` | Number of vessels found |
| `vessels` | `VesselInfo[]` | Vessel summaries |
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
| `max_results` | `int` | `100` | Maximum results to return |

**Response:** `CrewSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `crew_count` | `int` | Number of crew records found |
| `crew` | `CrewInfo[]` | Crew record summaries |
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
| `max_results` | `int` | `100` | Maximum results to return |

**Response:** `CargoSearchResponse`

| Field | Type | Description |
|-------|------|-------------|
| `cargo_count` | `int` | Number of cargo entries found |
| `cargo` | `CargoInfo[]` | Cargo record summaries |
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
| `atlantic_europe` | Bay of Biscay to Canaries |
| `atlantic_crossing` | Mid-Atlantic |
| `cape` | Cape of Good Hope region |
| `mozambique_channel` | East African coast |
| `indian_ocean` | Open Indian Ocean |
| `malabar` | Indian west coast |
| `coromandel` | Indian east coast |
| `ceylon` | Sri Lanka waters |
| `bengal` | Bay of Bengal |
| `malacca` | Straits of Malacca |
| `indonesia` | Indonesian archipelago |
| `south_china_sea` | Vietnam, Philippines, South China |
| `japan` | Japanese waters |
| `caribbean` | Caribbean Sea |

### Navigation Technology by Era

| Period | Technology | Typical Accuracy | Notes |
|--------|-----------|-----------------|-------|
| 1595-1650 | Dead reckoning with cross-staff | 30 km | Early VOC era. No reliable longitude method. |
| 1650-1700 | Dead reckoning with backstaff | 25 km | Improved latitude measurements. |
| 1700-1760 | Dead reckoning with octant | 20 km | Hadley's octant from 1731. Better latitude. |
| 1760-1795 | Chronometer era | 10 km | Harrison's chronometer. Longitude measurable but instruments rare on VOC ships. |

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

`storm`, `reef`, `fire`, `battle`, `grounding`, `scuttled`, `unknown`

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
  "error": "Archive 'invalid' not found. Available: das, voc_crew, voc_cargo, maarer",
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
