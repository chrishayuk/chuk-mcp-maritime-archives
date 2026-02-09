# Chuk MCP Maritime Archives

**Historical Maritime Archives MCP Server** -- A comprehensive Model Context Protocol (MCP) server for querying historical maritime shipping records, vessel specifications, crew muster rolls, cargo manifests, shipwreck databases, historical place names, and sailing routes spanning 1595-1855.

> This is a demonstration project provided as-is for learning and testing purposes.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

This MCP server provides structured access to historical maritime archives and reference data through twenty-three tools.

**All tools return fully-typed Pydantic v2 models** for type safety, validation, and excellent IDE support. All tools support `output_mode="text"` for human-readable output alongside the default JSON.

### 1. Archive Discovery (`maritime_list_archives`, `maritime_get_archive`)
Browse available maritime archives:
- Dutch Asiatic Shipping (DAS) -- 8,194 voyages
- VOC Opvarenden -- 774,200 crew records
- Boekhouder-Generaal Batavia -- ~50,000 cargo records
- MAARER Wreck Database -- 734 wreck positions

### 2. Voyage Search (`maritime_search_voyages`, `maritime_get_voyage`)
Search VOC voyage records:
- Filter by ship name, captain, ports, date range, fate
- Route keyword matching across summaries
- Full voyage detail including incident narratives and vessel data

### 3. Wreck Search (`maritime_search_wrecks`, `maritime_get_wreck`)
Search shipwreck and loss records:
- Filter by region, cause, depth, cargo value, status
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
Search VOC crew muster rolls:
- Filter by name, rank, ship, origin, fate
- Personnel records: rank, pay, embarkation/service dates
- Cross-reference with voyage records

### 7. Cargo Search (`maritime_search_cargo`, `maritime_get_cargo_manifest`)
Search cargo manifests:
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

### 11. Export & Statistics (`maritime_export_geojson`, `maritime_get_statistics`)
Export and analyse wreck data:
- GeoJSON FeatureCollection export with optional uncertainty
- Aggregate loss statistics by region, cause, decade
- Artifact store integration for persistent export

### 12. Server Discovery (`maritime_capabilities`)
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
- "What crew served on the Ridderschap van Holland?"
- "Search for wrecks with cargo worth over 1 million guilders"
- "What cargo was the Slot ter Hooge carrying when it sank?"
- "Get the hull profile for a retourschip -- I need drag coefficients for drift modelling"
- "Where are the coordinates for Batavia?" (gazetteer lookup)
- "Show me all the ports in Indonesia" (location search)
- "What route would a ship take from Texel to Batavia?"
- "If a ship left Texel on 1629-10-28, where would it be on 1630-02-15?"
- "Assess the position quality for wreck VOC-0456"
- "Export all Cape wrecks as GeoJSON"
- "Show me loss statistics by decade for the entire VOC period"

### Running the Examples

The `examples/` directory contains runnable demo scripts that call all 23 MCP tools directly:

```bash
cd examples

# Quick start (no network required)
python capabilities_demo.py        # server capabilities, ship types, regions
python hull_profiles_demo.py       # hydrodynamic data for all 6 ship types
python location_lookup_demo.py     # VOC gazetteer: place names to coordinates
python route_explorer_demo.py      # sailing routes + position estimation

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
| `voyage_search_demo.py` | Yes | `maritime_search_voyages`, `maritime_get_voyage` |
| `wreck_investigation_demo.py` | Yes | `maritime_search_wrecks`, `maritime_get_wreck`, `maritime_assess_position`, `maritime_export_geojson` |
| `vessel_search_demo.py` | Yes | `maritime_search_vessels`, `maritime_get_vessel`, `maritime_get_hull_profile` |
| `crew_muster_demo.py` | Yes | `maritime_search_crew`, `maritime_get_crew_member` |
| `cargo_trade_demo.py` | Yes | `maritime_search_cargo`, `maritime_get_cargo_manifest` |
| `geojson_export_demo.py` | Yes | `maritime_export_geojson`, `maritime_search_wrecks` |
| `statistics_demo.py` | Yes | `maritime_get_statistics`, `maritime_search_wrecks` |
| `batavia_case_study_demo.py` | Yes | All 12 tool categories chained together |

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
  "target_date": "1630-02-15"                    # date to estimate position
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

### `.env` File

The server loads environment variables from a `.env` file via `python-dotenv`:

```bash
CHUK_ARTIFACTS_PROVIDER=filesystem
CHUK_ARTIFACTS_PATH=/tmp/maritime-artifacts
```

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
- **Dual Output**: All 23 tools support `output_mode="text"` for human-readable responses
- **Domain Reference Data**: ~160 place gazetteer, 8 routes, 6 hull profiles, 15 regions, 4 navigation eras
- **349+ Tests**: Across 7 test modules with 97%+ branch coverage

### Supported Archives

| Archive | Records | Period | URL |
|---------|---------|--------|-----|
| Dutch Asiatic Shipping (DAS) | 8,194 voyages | 1595-1795 | resources.huygens.knaw.nl/das |
| VOC Opvarenden | 774,200 crew | 1633-1794 | nationaalarchief.nl |
| Boekhouder-Generaal Batavia | ~50,000 cargo | 1700-1795 | bgb.huygens.knaw.nl |
| MAARER Wrecks | 734 wrecks | 1595-1795 | Compiled dataset |
| CLIWOC Ship Tracks | ~261,000 positions | 1662-1855 | figshare.com (CLIWOC Slim) |

### Reference Data

| Dataset | Records | Source |
|---------|---------|--------|
| VOC Gazetteer | ~160 place names | Curated from historical sources |
| VOC Routes | 8 sailing routes | Bruijn, Gaastra & Schoffer (1987) |
| Hull Profiles | 6 ship types | Archaeological measurements |

See [ARCHITECTURE.md](ARCHITECTURE.md) for design principles and data flow diagrams.
See [SPEC.md](SPEC.md) for the full tool specification with parameter tables.

## Roadmap

### Completed (v0.1.0)

- 18 MCP tools across 10 categories (voyages, wrecks, vessels, crew, cargo, position, export, discovery, archives, hull profiles)
- 4 archive clients: DAS, VOC Crew, BGB Cargo, MAARER Wrecks
- Pydantic v2 response models with dual output (JSON + text)
- LRU caching for voyages, wrecks, and vessels
- Position quality assessment with navigation-era detection
- GeoJSON export with artifact store integration
- Hull hydrodynamic profiles for drift modelling

### Completed (v0.2.0)

- **23 MCP tools** across 12 categories (added location gazetteer and sailing routes)
- **VOC Gazetteer**: ~160 historical place names with coordinates, aliases, and region classification
- **Sailing routes**: 8 standard VOC routes with waypoints, durations, hazards, and season notes
- **Position estimation**: interpolate ship position on any date from departure and route
- **CLIWOC ship tracks**: download script for ~261K logbook positions (1662-1855, all nationalities)
- **Reproducible data pipeline**: download scripts for DAS and CLIWOC; JSON reference data for gazetteer, routes, and hull profiles
- 349 tests, 97%+ branch coverage

### Planned

- **CLIWOC MCP tools**: search and browse actual historical ship tracks from the CLIWOC database
- **Cross-archive linking**: automatic correlation between voyage, crew, and cargo records for the same ship/date
- **Streaming search**: paginated search results for large result sets
- **Timeline view**: chronological event tool combining voyage waypoints, crew changes, and incidents
- **Wreck probability model**: Bayesian position estimation combining navigation era, drift models, and historical accounts
- **Additional archives**: English East India Company (EIC), Portuguese Estado da India, Spanish Manila Galleon records
- **WebSocket transport**: real-time subscription to search refinements

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
