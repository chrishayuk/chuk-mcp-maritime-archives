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

---

## Planned

### Cross-Archive Linking

Automatic correlation between voyage, crew, cargo, and wreck records.

- Link DAS voyage IDs to crew muster rolls (same ship + date)
- Link voyages to cargo manifests
- Link wreck records to their originating voyage
- CLIWOC `DASnumber` field links logbook records to DAS voyages
- `maritime_get_voyage_full` -- single call returning voyage + crew + cargo + wreck data

### Drift Modelling Tools

Combine hull profiles, routes, and position data for wreck search planning.

- `maritime_estimate_drift` -- given wreck date, position, and ship type, estimate where debris/hull drifted
- Use hull hydrodynamic profiles (drag coefficients, windage, sinking characteristics)
- Account for seasonal wind/current patterns from CLIWOC data
- Output: probability map of wreck location as GeoJSON

### Enhanced Position Estimation

Improve position estimation beyond linear interpolation.

- Use CLIWOC actual track data to build statistical speed profiles per route segment
- Seasonal variation: monsoon-dependent speeds for Asian routes
- Wind/current adjustment based on month of travel
- Confidence intervals based on historical variance

### Timeline View

Chronological event tool combining all data sources.

- `maritime_get_timeline` -- all events for a ship/voyage in chronological order
- Combines: departure, waypoints, crew changes, cargo loading, incidents, arrival
- Visualisable as GeoJSON LineString with temporal properties

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

## Data Sources

Current and potential data sources for the project.

### Active

| Source | Records | Script | Status |
|--------|---------|--------|--------|
| [DAS](https://resources.huygens.knaw.nl/das) | 8,194 voyages | `download_das.py` | Working |
| [CLIWOC Slim](https://figshare.com/articles/dataset/11941224) | ~261K positions | `download_cliwoc.py` | Working |
| VOC Gazetteer | ~160 places | `data/gazetteer.json` | Curated |
| VOC Routes | 8 routes | `data/routes.json` | Curated |
| Hull Profiles | 6 types | `data/hull_profiles.json` | Curated |

### Potential

| Source | Description | Format | Notes |
|--------|-------------|--------|-------|
| [CLIWOC 2.1 Full](https://historicalclimatology.com/cliwoc.html) | 287K records, 182 columns | GeoPackage (190 MB) | Ship names, company (VOC/WIC), crew, cargo, weather |
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
