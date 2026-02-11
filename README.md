# Chuk MCP Maritime Archives

**Historical Maritime Archives MCP Server** -- A comprehensive Model Context Protocol (MCP) server for querying historical maritime shipping records, vessel specifications, crew muster rolls, cargo manifests, shipwreck databases, historical place names, and sailing routes spanning 1497-1874. Covers Dutch (VOC), English (EIC), Portuguese (Carreira da India), Spanish (Manila Galleon), and Swedish (SOIC) maritime archives.

> This is a demonstration project provided as-is for learning and testing purposes.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

This MCP server provides structured access to historical maritime archives and reference data through 29 tools across 8 archives and 5 nations.

**All tools return fully-typed Pydantic v2 models** for type safety, validation, and excellent IDE support. All tools support `output_mode="text"` for human-readable output alongside the default JSON.

### 1. Archive Discovery (`maritime_list_archives`, `maritime_get_archive`)
Browse 8 maritime archives across 5 nations:
- Dutch Asiatic Shipping (DAS) -- 8,194 voyages (1595-1795)
- VOC Opvarenden -- 774,200 crew records (1633-1794) *(stub client, requires network)*
- Boekhouder-Generaal Batavia -- ~50,000 cargo records (1700-1795) *(stub client, requires network)*
- MAARER Wreck Database -- 734 wreck positions (1595-1795)
- English East India Company (EIC) -- ~150 curated voyages, ~35 wrecks (1600-1874)
- Portuguese Carreira da India -- ~120 curated voyages, ~40 wrecks (1497-1835)
- Spanish Manila Galleon -- ~100 curated voyages, ~25 wrecks (1565-1815)
- Swedish East India Company (SOIC) -- ~80 curated voyages, ~12 wrecks (1731-1813)

> **Note:** The EIC, Carreira, Galleon, and SOIC archives are curated seed datasets of notable voyages and famous wrecks compiled from published academic sources -- not exhaustive inventories. The EIC alone conducted thousands of voyages; our ~150 represent a selection of historically significant records. The VOC Crew and Cargo clients are stub implementations that depend on external APIs which may be unavailable.

### 2. Voyage Search (`maritime_search_voyages`, `maritime_get_voyage`)
Search voyage records across all 5 voyage archives (DAS, EIC, Carreira, Galleon, SOIC):
- Filter by ship name, captain, ports, date range, fate, archive
- Multi-archive search: query all archives at once or filter by specific archive
- Full voyage detail including incident narratives and vessel data

### 3. Wreck Search (`maritime_search_wrecks`, `maritime_get_wreck`)
Search shipwreck and loss records across all 5 wreck archives (MAARER, EIC, Carreira, Galleon, SOIC):
- Filter by region, cause, depth, cargo value, status, archive
- Multi-archive wreck search or single-archive filtering
- Position data with uncertainty estimates
- Archaeological status and notes

### 4. Vessel Search (`maritime_search_vessels`, `maritime_get_vessel`)
Search VOC vessel records:
- Filter by ship type, tonnage, chamber, shipyard
- 6 ship types: retourschip, fluit, jacht, hooker, pinas, fregat
- Construction and service history

### 5. Hull Profiles (`maritime_get_hull_profile`, `maritime_list_hull_profiles`)
Hydrodynamic hull data for drift modelling:
- Dimensions, displacement, drag coefficients
- Windage area and coefficients
- Sinking characteristics and orientation weights
- Reference wrecks and LLM guidance notes

### 6. Crew Search (`maritime_search_crew`, `maritime_get_crew_member`)
Search VOC crew muster rolls *(stub client -- depends on Nationaal Archief API availability)*:
- Filter by name, rank, ship, origin, fate
- Personnel records: rank, pay, embarkation/service dates
- Cross-reference with voyage records

### 7. Cargo Search (`maritime_search_cargo`, `maritime_get_cargo_manifest`)
Search cargo manifests *(stub client -- depends on BGB Huygens API availability)*:
- Filter by commodity, origin, destination, value
- Full voyage manifests with quantities and values
- Dutch and English commodity names

### 8. Position Assessment (`maritime_assess_position`)
Evaluate historical position quality:
- Navigation era detection (4 technology periods)
- 5 uncertainty levels from precise to regional
- Recommendations for drift modelling and search planning

### 9. Location Gazetteer (`maritime_lookup_location`, `maritime_list_locations`)
Historical place-name resolution:
- ~160 VOC-era place names with modern coordinates
- Alias resolution (e.g., "Batavia" -> Jakarta, "Formosa" -> Taiwan)
- Region classification matching wreck and route data
- Filter by region, location type, or text search

### 10. Sailing Routes (`maritime_list_routes`, `maritime_get_route`, `maritime_estimate_position`)
Standard VOC sailing routes with position estimation:
- 8 routes: outward (outer/inner), return, Japan, Spice Islands, Ceylon, Coromandel, Malabar
- Waypoints with coordinates, typical sailing days, stop durations
- Hazards and seasonal navigation notes
- **Position estimation**: interpolate a ship's likely position on any date
- **Speed profile enrichment**: `use_speed_profiles=True` adds CLIWOC-derived speed statistics

### 11. Speed Profiles (`maritime_get_speed_profile`)
Historical sailing speed statistics derived from CLIWOC 2.1 daily positions:
- 215 profiles across 6 routes (outward_outer, return, ceylon, coromandel, japan, malabar)
- Mean, median, std dev, and percentile speeds (km/day) per route segment
- Seasonal variation: filter by departure month for month-specific data
- Generated from ~61K daily observations matched to standard routes

### 12. Ship Tracks (`maritime_search_tracks`, `maritime_get_track`, `maritime_nearby_tracks`)
Historical ship track data from CLIWOC 2.1 Full logbooks (1662-1855):
- ~261K daily position observations from 8 European maritime nations
- Search by nationality (NL, UK, ES, FR, SE, US, DE, DK), year range, and ship name
- Full position histories for individual voyages with ship names, company, and DAS numbers
- **Nearby ship search**: find what other ships were near a position on a given date
- Useful for wreck investigation context and route reconstruction

### 13. Cross-Archive Linking (`maritime_get_voyage_full`)
Unified voyage view with all linked records in a single call, across all archives:
- Works with DAS, EIC, Carreira, Galleon, and SOIC voyages
- Wreck record (linked via voyage_id, across all wreck archives)
- Vessel record (linked via voyage_ids array, DAS voyages)
- Hull profile (linked via ship_type)
- CLIWOC track (linked via DAS number or ship name + nationality matching)
- Replaces the need to call get_voyage, get_wreck, get_vessel, and get_hull_profile separately

### 14. Timeline (`maritime_get_timeline`)
Chronological event view combining all data sources for a voyage:
- Assembles events from DAS voyages, route estimates, CLIWOC tracks, and wreck records
- Event types: departure, waypoint estimates, CLIWOC positions, loss/wreck, arrival
- Optional `include_positions=True` to sample CLIWOC daily positions into the timeline
- GeoJSON LineString output from positioned events

### 15. Export & Statistics (`maritime_export_geojson`, `maritime_get_statistics`)
Export and analyse wreck data:
- GeoJSON FeatureCollection export with optional uncertainty
- Aggregate loss statistics by region, cause, decade
- Artifact store integration for persistent export

### 16. Server Discovery (`maritime_capabilities`)
List full server capabilities for LLM workflow planning:
- Available archives with metadata
- All registered tools with descriptions
- Ship types and geographic regions

## Installation

### Using uvx (Recommended -- No Installation Required!)

```bash
uvx chuk-mcp-maritime-archives
```

### Using uv (Recommended for Development)

```bash
# Install from PyPI
uv pip install chuk-mcp-maritime-archives

# Or clone and install from source
git clone <repository-url>
cd chuk-mcp-maritime-archives
uv sync --dev
```

### Using pip (Traditional)

```bash
pip install chuk-mcp-maritime-archives
```

## Usage

### With Claude Desktop

#### Option 1: Run Locally with uvx

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "maritime": {
      "command": "uvx",
      "args": ["chuk-mcp-maritime-archives"]
    }
  }
}
```

#### Option 2: Run Locally with pip

```json
{
  "mcpServers": {
    "maritime": {
      "command": "chuk-mcp-maritime-archives"
    }
  }
}
```

### Standalone

Run the server directly:

```bash
# With uvx (recommended -- always latest version)
uvx chuk-mcp-maritime-archives

# With uvx in HTTP mode
uvx chuk-mcp-maritime-archives --mode http

# Or if installed locally
chuk-mcp-maritime-archives
chuk-mcp-maritime-archives --mode http
```

Or with uv/Python:

```bash
# STDIO mode (default, for MCP clients)
uv run chuk-mcp-maritime-archives
# or: python -m chuk_mcp_maritime_archives.server

# HTTP mode (for web access)
uv run chuk-mcp-maritime-archives --mode http
# or: python -m chuk_mcp_maritime_archives.server --mode http
```

**STDIO mode** is for MCP clients like Claude Desktop and mcp-cli.
**HTTP mode** runs a web server on http://localhost:8005 for HTTP-based MCP clients.

## Example Usage

Once configured, you can ask Claude questions like:

- "List the available maritime archives"
- "Search for VOC voyages that were wrecked near the Cape of Good Hope"
- "Show me the full record for the Batavia voyage"
- "Search for EIC voyages involving the Earl of Abergavenny"
- "Find Portuguese Carreira voyages commanded by Vasco da Gama"
- "Show me Manila Galleon wrecks in the Pacific"
- "Search for Swedish East India Company voyages of the Gotheborg"
- "What crew served on the Ridderschap van Holland?"
- "Search for wrecks with cargo worth over 1 million guilders"
- "Get the hull profile for a retourschip -- I need drag coefficients for drift modelling"
- "Where are the coordinates for Batavia?" (gazetteer lookup)
- "What route would a ship take from Texel to Batavia?"
- "If a ship left Texel on 1629-10-28, where would it be on 1630-02-15?"
- "Search for Dutch ship tracks from the 1780s"
- "What other ships were near the Batavia wreck site on 1629-06-04?"
- "What were the typical sailing speeds on the outward route via the Roaring Forties?"
- "Show me the timeline of the Batavia's final voyage"
- "Assess the position quality for wreck VOC-0456"
- "Export all Cape wrecks as GeoJSON"
- "Show me loss statistics by decade across all archives"

### Running the Examples

The `examples/` directory contains runnable demo scripts that call MCP tools directly:

```bash
cd examples

# Quick start (no network required)
python capabilities_demo.py        # server capabilities, ship types, regions
python hull_profiles_demo.py       # hydrodynamic data for all 6 ship types
python location_lookup_demo.py     # VOC gazetteer: place names to coordinates
python route_explorer_demo.py      # sailing routes + position estimation
python track_explorer_demo.py      # CLIWOC ship tracks + nearby search
python cross_archive_demo.py      # unified voyage view across 5 archives
python speed_profile_demo.py       # CLIWOC-derived speed statistics per segment
python climate_proxy_demo.py       # ship speeds as climate proxies (wind & monsoon)
python timeline_demo.py            # chronological voyage timeline from all sources

# Core tool demos (network required)
python voyage_search_demo.py       # search + detail workflow
python wreck_investigation_demo.py # search, assess, export workflow
python vessel_search_demo.py       # vessel search + ship type comparison
python crew_muster_demo.py         # crew search + detail retrieval
python cargo_trade_demo.py         # cargo search + commodity analysis
python geojson_export_demo.py      # GeoJSON export + filtering
python statistics_demo.py          # aggregate loss statistics

# Full case study (network required)
python batavia_case_study_demo.py  # 12-tool chain investigating the Batavia wreck
```

| Script | Network | Tools Demonstrated |
|--------|---------|-------------------|
| `capabilities_demo.py` | No | `maritime_capabilities`, `maritime_list_archives`, `maritime_list_hull_profiles` |
| `hull_profiles_demo.py` | No | `maritime_list_hull_profiles`, `maritime_get_hull_profile` |
| `location_lookup_demo.py` | No | `maritime_lookup_location`, `maritime_list_locations` |
| `route_explorer_demo.py` | No | `maritime_list_routes`, `maritime_get_route`, `maritime_estimate_position` |
| `track_explorer_demo.py` | No | `maritime_search_tracks`, `maritime_get_track`, `maritime_nearby_tracks` |
| `cross_archive_demo.py` | Partial | `maritime_search_voyages`, `maritime_get_voyage_full` (EIC/Carreira/Galleon/SOIC offline, DAS needs network) |
| `speed_profile_demo.py` | No | `maritime_get_speed_profile`, `maritime_estimate_position` |
| `climate_proxy_demo.py` | No | `maritime_get_speed_profile`, `maritime_get_route`, `maritime_search_tracks`, `maritime_get_track` |
| `timeline_demo.py` | No | `maritime_get_timeline`, `maritime_search_voyages` |
| `voyage_search_demo.py` | Partial | `maritime_search_voyages`, `maritime_get_voyage` (DAS needs network, EIC/Carreira/Galleon/SOIC offline) |
| `wreck_investigation_demo.py` | Partial | `maritime_search_wrecks`, `maritime_get_wreck`, `maritime_assess_position`, `maritime_export_geojson` (multi-archive, mostly offline) |
| `vessel_search_demo.py` | Yes | `maritime_search_vessels`, `maritime_get_vessel`, `maritime_get_hull_profile` |
| `crew_muster_demo.py` | Yes | `maritime_search_crew`, `maritime_get_crew_member` |
| `cargo_trade_demo.py` | Yes | `maritime_search_cargo`, `maritime_get_cargo_manifest` |
| `geojson_export_demo.py` | Yes | `maritime_export_geojson`, `maritime_search_wrecks` |
| `statistics_demo.py` | Partial | `maritime_get_statistics`, `maritime_search_wrecks` (multi-archive, mostly offline) |
| `batavia_case_study_demo.py` | Yes | All tool categories chained together |

## Tool Reference

All tools accept an optional `output_mode` parameter (`"json"` default, or `"text"` for human-readable output).

| Tool | Category | Description |
|------|----------|-------------|
| `maritime_list_archives` | Archives | List all available maritime archives |
| `maritime_get_archive` | Archives | Get archive detail by ID |
| `maritime_search_voyages` | Voyages | Search voyages with filters |
| `maritime_get_voyage` | Voyages | Get voyage detail by ID |
| `maritime_search_wrecks` | Wrecks | Search wreck records |
| `maritime_get_wreck` | Wrecks | Get wreck detail by ID |
| `maritime_search_vessels` | Vessels | Search vessel records |
| `maritime_get_vessel` | Vessels | Get vessel detail by ID |
| `maritime_get_hull_profile` | Vessels | Hydrodynamic profile for ship type |
| `maritime_list_hull_profiles` | Vessels | Available ship types |
| `maritime_search_crew` | Crew | Search crew muster rolls |
| `maritime_get_crew_member` | Crew | Get crew member detail |
| `maritime_search_cargo` | Cargo | Search cargo manifests |
| `maritime_get_cargo_manifest` | Cargo | Full cargo manifest for a voyage |
| `maritime_lookup_location` | Location | Look up historical place name in VOC gazetteer |
| `maritime_list_locations` | Location | Search/browse gazetteer by region, type, or text |
| `maritime_list_routes` | Routes | List standard VOC sailing routes |
| `maritime_get_route` | Routes | Full route with waypoints, hazards, season notes |
| `maritime_estimate_position` | Routes | Estimate ship position on a date from route |
| `maritime_search_tracks` | Tracks | Search CLIWOC ship tracks by nationality and date |
| `maritime_get_track` | Tracks | Get full position history for a CLIWOC voyage |
| `maritime_nearby_tracks` | Tracks | Find ships near a position on a given date |
| `maritime_get_speed_profile` | Speed | Historical sailing speed statistics per segment |
| `maritime_get_voyage_full` | Linking | Unified voyage view with all linked records |
| `maritime_get_timeline` | Timeline | Chronological event view for a voyage |
| `maritime_assess_position` | Position | Position quality and uncertainty assessment |
| `maritime_export_geojson` | Export | GeoJSON wreck position export |
| `maritime_get_statistics` | Export | Aggregate loss statistics |
| `maritime_capabilities` | Discovery | Server capabilities and reference data |

### maritime_search_voyages

```python
{
  "ship_name": "Batavia",                       # optional, substring match
  "captain": "Jacobsz",                         # optional
  "date_range": "1620/1640",                     # optional, YYYY/YYYY
  "departure_port": "Texel",                     # optional
  "fate": "wrecked",                             # optional
  "max_results": 10                              # optional, default 50
}
```

### maritime_search_wrecks

```python
{
  "region": "cape",                              # optional, region code
  "cause": "storm",                              # optional
  "status": "unfound",                           # optional
  "min_depth_m": 100,                            # optional
  "min_cargo_value": 100000,                     # optional, guilders
  "max_results": 50                              # optional, default 100
}
```

### maritime_search_crew

```python
{
  "ship_name": "Ridderschap van Holland",        # optional
  "rank": "schipper",                            # optional
  "fate": "died_voyage",                         # optional
  "max_results": 50                              # optional, default 100
}
```

### maritime_search_cargo

```python
{
  "commodity": "pepper",                         # optional, substring match
  "origin": "Malabar",                           # optional
  "min_value": 100000,                           # optional, guilders
  "max_results": 50                              # optional, default 100
}
```

### maritime_assess_position

```python
{
  "wreck_id": "maarer:VOC-0789",                 # assess wreck position
  "source_description": "GPS surveyed site"      # position source info
}
```

### maritime_export_geojson

```python
{
  "region": "cape",                              # optional filter
  "status": "found",                             # optional filter
  "include_uncertainty": true,                   # include uncertainty radius
  "include_voyage_data": true                    # include ship/cargo data
}
```

### maritime_lookup_location

```python
{
  "name": "Batavia"                              # place name or alias
}
```

### maritime_list_locations

```python
{
  "query": "spice",                              # optional, text search
  "region": "indonesia",                         # optional, region code
  "location_type": "port",                       # optional: port, island, cape, etc.
  "max_results": 50                              # optional, default 50
}
```

### maritime_list_routes

```python
{
  "direction": "outward",                        # optional: outward, return, intra_asian
  "departure_port": "Texel",                     # optional, substring match
  "destination_port": "Batavia"                  # optional, substring match
}
```

### maritime_get_route

```python
{
  "route_id": "outward_outer"                    # route identifier
}
```

### maritime_estimate_position

```python
{
  "route_id": "outward_outer",                   # route identifier
  "departure_date": "1629-10-28",                # YYYY-MM-DD
  "target_date": "1630-02-15",                   # date to estimate position
  "use_speed_profiles": true                     # optional: enrich with CLIWOC speed data
}
```

### maritime_get_speed_profile

```python
{
  "route_id": "outward_outer",                   # route identifier
  "departure_month": 10                          # optional: month (1-12) for seasonal data
}
```

### maritime_get_timeline

```python
{
  "voyage_id": "das:0372.1",                     # voyage ID from any archive
  "include_positions": true,                     # optional: include CLIWOC daily positions
  "max_positions": 20                            # optional: max CLIWOC positions to sample
}
```

### maritime_get_voyage_full

```python
{
  "voyage_id": "eic:0062"                          # voyage ID from any archive (das, eic, carreira, galleon, soic)
}
```

### maritime_search_tracks

```python
{
  "nationality": "NL",                            # optional: NL, UK, ES, FR, SE, US, DE, DK
  "year_start": 1780,                             # optional, earliest year
  "year_end": 1800,                               # optional, latest year
  "ship_name": "BATAVIA",                         # optional, substring match (CLIWOC 2.1 Full)
  "max_results": 50                               # optional, default 50
}
```

### maritime_get_track

```python
{
  "voyage_id": 118                                # CLIWOC voyage ID (integer)
}
```

### maritime_nearby_tracks

```python
{
  "lat": -28.49,                                  # latitude of search point
  "lon": 113.79,                                  # longitude of search point
  "date": "1629-06-04",                           # date to search (YYYY-MM-DD)
  "radius_km": 200,                               # optional, default 200km
  "max_results": 20                               # optional, default 20
}
```

### maritime_get_hull_profile

```python
{
  "ship_type": "retourschip"                     # ship type code
}
```

## Development

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd chuk-mcp-maritime-archives

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=src/chuk_mcp_maritime_archives --cov-report=term-missing

# Run a specific test file
pytest tests/test_archive_manager.py -v
```

### Code Quality

```bash
# Run all checks (lint, typecheck, security, test)
make check

# Lint and format with ruff
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/ -x tests/
```

### Building

```bash
# Build package
python -m build

# Or with uv
uv build
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUK_ARTIFACTS_PROVIDER` | `memory` | Storage backend: `memory`, `filesystem`, `s3` |
| `CHUK_ARTIFACTS_PATH` | - | Filesystem storage path |
| `BUCKET_NAME` | - | S3 bucket name |
| `AWS_ACCESS_KEY_ID` | - | AWS access key for S3 |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key for S3 |
| `AWS_ENDPOINT_URL_S3` | - | Custom S3 endpoint (MinIO, etc.) |
| `MCP_STDIO` | - | Set to any value to force stdio mode |
| `REDIS_URL` | - | Redis URL for session management |
| `MARITIME_REFERENCE_MANIFEST` | - | Artifact ID of reference data manifest (see below) |

### `.env` File

The server loads environment variables from a `.env` file via `python-dotenv`.
Copy `.env.example` for a documented template:

```bash
cp .env.example .env
```

Minimal local development (no S3):
```bash
CHUK_ARTIFACTS_PROVIDER=memory
```

With filesystem storage:
```bash
CHUK_ARTIFACTS_PROVIDER=filesystem
CHUK_ARTIFACTS_PATH=/tmp/maritime-artifacts
```

### S3-Backed Reference Data

For multi-server deployments, reference data (~34 MB across 16 JSON files) can be
stored in S3 and preloaded at startup, eliminating the need to run download scripts
on each server.

1. Configure S3 credentials in `.env`:
   ```bash
   CHUK_ARTIFACTS_PROVIDER=s3
   BUCKET_NAME=your-maritime-bucket
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   ```

2. Upload reference data to the artifact store:
   ```bash
   python scripts/upload_reference_data.py
   ```

3. Set the manifest ID printed by the script:
   ```bash
   MARITIME_REFERENCE_MANIFEST=<manifest-artifact-id>
   ```

4. New servers will automatically download missing data files from S3 at startup.

## Docker

### Build

```bash
docker build -t chuk-mcp-maritime-archives .
```

### Run

```bash
# HTTP mode (default in container)
docker run -p 8005:8005 chuk-mcp-maritime-archives

# With S3 storage
docker run -p 8005:8005 \
  -e CHUK_ARTIFACTS_PROVIDER=s3 \
  -e BUCKET_NAME=my-bucket \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  chuk-mcp-maritime-archives
```

## Architecture

Built on top of chuk-mcp-server, this server uses:

- **Async-First**: Native async/await with sync HTTP wrapped in `asyncio.to_thread()`
- **Type-Safe**: Pydantic v2 models with `extra="forbid"` for all responses, `extra="allow"` for domain models
- **LRU Caching**: OrderedDict-based caches for voyages (500), wrecks (500), and vessels
- **Reproducible Data**: Download scripts fetch real data from DAS and CLIWOC; reference data stored as JSON
- **Pluggable Storage**: Artifact storage via chuk-artifacts (memory, filesystem, S3)
- **No External HTTP Deps**: Uses stdlib `urllib.request` -- no requests/httpx dependency
- **Cross-Archive Linking**: Unified voyage view with wreck, vessel, hull profile, and CLIWOC track linking
- **Multi-Archive Dispatch**: 8 archives across 5 nations (Dutch, English, Portuguese, Spanish, Swedish) with unified query interface
- **Dual Output**: All 29 tools support `output_mode="text"` for human-readable responses
- **Domain Reference Data**: ~160 place gazetteer, 8 routes, 6 hull profiles, 215 speed profiles, ~261K ship positions, 22 regions, 7 navigation eras
- **585 Tests**: Across 13 test modules with 97%+ branch coverage

### Supported Archives

| Archive | Records | Period | Source |
|---------|---------|--------|--------|
| Dutch Asiatic Shipping (DAS) | 8,194 voyages | 1595-1795 | resources.huygens.knaw.nl/das |
| VOC Opvarenden | 774,200 crew | 1633-1794 | nationaalarchief.nl |
| Boekhouder-Generaal Batavia | ~50,000 cargo | 1700-1795 | bgb.huygens.knaw.nl |
| MAARER Wrecks | 734 wrecks | 1595-1795 | Compiled dataset |
| CLIWOC Ship Tracks | ~261,000 positions | 1662-1855 | historicalclimatology.com (CLIWOC 2.1 Full) |
| English East India Company (EIC) | ~150 voyages, ~35 wrecks | 1600-1874 | Hardy/Farrington (curated) |
| Portuguese Carreira da India | ~120 voyages, ~40 wrecks | 1497-1835 | Guinote/Frutuoso/Lopes (curated) |
| Spanish Manila Galleon | ~100 voyages, ~25 wrecks | 1565-1815 | Schurz (curated) |
| Swedish East India Company (SOIC) | ~80 voyages, ~12 wrecks | 1731-1813 | Koninckx (curated) |

### Reference Data

| Dataset | Records | Source |
|---------|---------|--------|
| VOC Gazetteer | ~160 place names | Curated from historical sources |
| VOC Routes | 8 sailing routes | Bruijn, Gaastra & Schoffer (1987) |
| Speed Profiles | 215 profiles, 6 routes | Generated from CLIWOC 2.1 daily positions |
| Hull Profiles | 6 ship types | Archaeological measurements |
| EIC Archives | ~150 voyages, ~35 wrecks | Hardy's Register of Ships (1835), Farrington (1999) |
| Carreira Archives | ~120 voyages, ~40 wrecks | Guinote/Frutuoso/Lopes "As Armadas da India" |
| Galleon Archives | ~100 voyages, ~25 wrecks | Schurz "The Manila Galleon" (1939) |
| SOIC Archives | ~80 voyages, ~12 wrecks | Koninckx "First and Second Charters of the SEIC" (1980) |

See [ARCHITECTURE.md](ARCHITECTURE.md) for design principles and data flow diagrams.
See [SPEC.md](SPEC.md) for the full tool specification with parameter tables.
See [ROADMAP.md](ROADMAP.md) for the development roadmap and planned features.

## Roadmap

### Completed (v0.1.0 - v0.3.0)

- 26 MCP tools across 13 categories (voyages, wrecks, vessels, crew, cargo, position, export, discovery, archives, hull profiles, location, routes, tracks)
- 4 archive clients: DAS, VOC Crew, BGB Cargo, MAARER Wrecks
- CLIWOC ship tracks: ~261K logbook positions (1662-1855, 8 nationalities)
- VOC Gazetteer, sailing routes, position estimation, hull profiles
- Reproducible data pipeline: download scripts for DAS and CLIWOC

### Completed (v0.4.0)

- **27 MCP tools** across 14 categories (added cross-archive linking)
- **Cross-archive linking**: `maritime_get_voyage_full` returns unified voyage view with wreck, vessel, hull profile, and CLIWOC track
- **CLIWOC 2.1 Full upgrade**: ship names, company, DAS numbers for direct cross-archive linking
- **Ship name search**: `maritime_search_tracks` now supports ship name filtering
- 430 tests, 97%+ branch coverage

### Completed (v0.5.0)

- **29 MCP tools** across 16 categories (added speed profiles and timeline)
- **Speed profiles**: `maritime_get_speed_profile` returns CLIWOC-derived speed statistics per route segment with seasonal variation
- **Timeline view**: `maritime_get_timeline` assembles chronological events from all data sources for a voyage
- **Enhanced position estimation**: `maritime_estimate_position` now supports `use_speed_profiles=True` for CLIWOC-enriched estimates
- 483 tests, 97%+ branch coverage

### Completed (v0.6.0)

- **Artifact store integration**: GeoJSON exports and timeline tracks stored to chuk-artifacts with `scope="sandbox"`
- **S3-backed reference data**: `scripts/upload_reference_data.py` + `MARITIME_REFERENCE_MANIFEST` for automatic preloading
- **`.env.example`** configuration template documenting all environment variables
- 499 tests, 97%+ branch coverage

### Completed (v0.7.0)

- **8 archives across 5 nations**: English East India Company (EIC), Portuguese Carreira da India, Spanish Manila Galleon, Swedish East India Company (SOIC)
- **Multi-archive dispatch**: `search_voyages(archive="eic")` queries one archive; no filter queries all
- **~450 new voyage records, ~112 new wrecks** from curated academic sources
- **Coverage expanded**: 1497-1874 (from 1595-1795)
- 585 tests, 97%+ branch coverage

### Planned

- **Streaming search**: paginated search results for large result sets
- **WebSocket transport**: real-time subscription to search refinements
- **Drift modelling**: available as chuk-mcp-ocean-drift (10 tools, v0.1.0) — forward/backtrack/Monte Carlo drift computation using hull profiles and position data from this server

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Apache License 2.0 -- See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Huygens Institute](https://resources.huygens.knaw.nl/) for the Dutch Asiatic Shipping database
- [Nationaal Archief](https://www.nationaalarchief.nl/) for VOC crew and cargo records
- [CLIWOC](https://www.historicalclimatology.com/cliwoc.html) for the Climatological Database for World's Oceans
- [Dani Arribas-Bel](https://figshare.com/articles/dataset/CLIWOC_Slim_and_Routes/11941224) for the CLIWOC Slim and Routes dataset
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [Anthropic](https://www.anthropic.com/) for Claude and MCP support
- J.R. Bruijn, F.S. Gaastra, and I. Schoffer for _Dutch-Asiatic Shipping in the 17th and 18th Centuries_ (1987)
- C.R. Hardy for _A Register of Ships Employed in the Service of the East India Company_ (1835)
- A. Farrington for _Catalogue of East India Company Ships' Journals and Logs_ (1999)
- P. Guinote, E. Frutuoso, and A. Lopes for _As Armadas da India 1497-1835_
- W.L. Schurz for _The Manila Galleon_ (1939)
- C. Koninckx for _The First and Second Charters of the Swedish East India Company_ (1980)
