"""
Archive Manager — central orchestrator for maritime archive data.

Manages:
- Archive registry and metadata
- Data source clients for each archive (DAS, EIC, Carreira, Galleon, SOIC, etc.)
- Hull profile lookups
- Position uncertainty assessment
- GeoJSON export
- Aggregate statistics
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..constants import (
    ARCHIVE_METADATA,
    NAVIGATION_ERAS,
)
from .clients import (
    CargoClient,
    CarreiraClient,
    CrewClient,
    DASClient,
    EICClient,
    GalleonClient,
    SOICClient,
    WreckClient,
)
from .cliwoc_tracks import (
    find_track_for_voyage,
    get_track,
    get_track_by_das_number,
)
from .hull_profiles import HULL_PROFILES
from .voc_routes import estimate_position, get_route as get_route_detail, suggest_route

logger = logging.getLogger(__name__)

# Default data directory relative to the project root
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Map archive IDs to CLIWOC nationality codes
_ARCHIVE_NATIONALITY = {
    "das": "NL",
    "eic": "UK",
    "carreira": "PT",
    "galleon": "ES",
    "soic": "SE",
}


class ArchiveManager:
    """
    Central orchestrator for maritime archive data access.

    Delegates data access to archive-specific clients that read from
    local JSON data files produced by the download scripts.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._archives = dict(ARCHIVE_METADATA)
        self._hull_profiles = dict(HULL_PROFILES)

        data_path = data_dir or _DEFAULT_DATA_DIR

        # Data source clients
        self._das_client = DASClient(data_dir=data_path)
        self._crew_client = CrewClient(data_dir=data_path)
        self._cargo_client = CargoClient(data_dir=data_path)
        self._wreck_client = WreckClient(data_dir=data_path)

        # Additional archive clients
        self._eic_client = EICClient(data_dir=data_path)
        self._carreira_client = CarreiraClient(data_dir=data_path)
        self._galleon_client = GalleonClient(data_dir=data_path)
        self._soic_client = SOICClient(data_dir=data_path)

        # Multi-archive dispatch: archive ID -> voyage client
        self._voyage_clients: dict[str, Any] = {
            "das": self._das_client,
            "eic": self._eic_client,
            "carreira": self._carreira_client,
            "galleon": self._galleon_client,
            "soic": self._soic_client,
        }

        # Multi-archive dispatch: archive ID -> wreck client
        self._wreck_clients: dict[str, Any] = {
            "maarer": self._wreck_client,
            "eic": self._eic_client,
            "carreira": self._carreira_client,
            "galleon": self._galleon_client,
            "soic": self._soic_client,
        }

    # --- Archive Registry ---------------------------------------------------

    def list_archives(self) -> list[dict]:
        """Return metadata for all available archives."""
        results = []
        for archive_id, meta in self._archives.items():
            results.append({"id": archive_id, **meta})
        return results

    def get_archive(self, archive_id: str) -> dict | None:
        """Return detailed metadata for a specific archive."""
        meta = self._archives.get(archive_id)
        if meta is None:
            return None
        return {"archive_id": archive_id, **meta}

    def get_available_archive_ids(self) -> list[str]:
        """Return list of available archive identifiers."""
        return list(self._archives.keys())

    # --- Voyage Operations --------------------------------------------------

    async def search_voyages(
        self,
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        route: str | None = None,
        fate: str | None = None,
        archive: str | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Search for voyages across all archives or a specific one."""
        search_kwargs = dict(
            ship_name=ship_name,
            captain=captain,
            date_range=date_range,
            departure_port=departure_port,
            destination_port=destination_port,
            route=route,
            fate=fate,
            max_results=max_results,
        )

        if archive and archive in self._voyage_clients:
            results = await self._voyage_clients[archive].search(**search_kwargs)
        elif archive:
            return []
        else:
            # Query all voyage archives and merge results
            all_results: list[dict] = []
            for client in self._voyage_clients.values():
                all_results.extend(await client.search(**search_kwargs))
            results = all_results

        return results[:max_results]

    async def get_voyage(self, voyage_id: str) -> dict | None:
        """Get full voyage details, routing to the correct archive client."""
        prefix = voyage_id.split(":")[0] if ":" in voyage_id else "das"
        client = self._voyage_clients.get(prefix, self._das_client)
        return await client.get_by_id(voyage_id)

    # --- Cross-Archive Linking ----------------------------------------------

    async def get_voyage_full(self, voyage_id: str) -> dict | None:
        """
        Get unified view of a voyage with all linked records.

        Returns the voyage record enriched with related wreck, vessel,
        hull profile, and CLIWOC track data (where available).
        """
        voyage = await self.get_voyage(voyage_id)
        if not voyage:
            return None

        # Find linked wreck record (via voyage_id) -- check all wreck clients
        wreck = await self._find_wreck_for_voyage(voyage_id)

        # Find linked vessel record (via voyage_ids array, DAS only)
        vessel = self._das_client.get_vessel_for_voyage(voyage_id)

        # Find hull profile for ship type
        ship_type = voyage.get("ship_type")
        hull_profile = self.get_hull_profile(ship_type) if ship_type else None

        # Find linked CLIWOC track
        cliwoc_track = self._find_cliwoc_track_for_voyage(voyage)

        links_found = [
            k
            for k, v in {
                "wreck": wreck,
                "vessel": vessel,
                "hull_profile": hull_profile,
                "cliwoc_track": cliwoc_track,
            }.items()
            if v
        ]

        return {
            "voyage": voyage,
            "wreck": wreck,
            "vessel": vessel,
            "hull_profile": hull_profile,
            "cliwoc_track": cliwoc_track,
            "links_found": links_found,
        }

    def _find_cliwoc_track_for_voyage(self, voyage: dict) -> dict | None:
        """Try to find a CLIWOC track linked to this voyage."""
        # Try DASnumber first (from CLIWOC 2.1 Full data, DAS only)
        voyage_number = voyage.get("voyage_number")
        if voyage_number:
            track = get_track_by_das_number(voyage_number)
            if track:
                # Return summary without full positions
                return {k: v for k, v in track.items() if k != "positions"}

        # Fall back to ship name + date + nationality matching
        ship_name = voyage.get("ship_name")
        archive = voyage.get("archive", "das")
        nationality = _ARCHIVE_NATIONALITY.get(archive, "NL")
        if ship_name:
            return find_track_for_voyage(
                ship_name=ship_name,
                departure_date=voyage.get("departure_date"),
                nationality=nationality,
            )

        return None

    async def _find_wreck_for_voyage(self, voyage_id: str) -> dict | None:
        """Find a wreck record linked to a voyage, checking the appropriate client."""
        prefix = voyage_id.split(":")[0] if ":" in voyage_id else "das"

        # For DAS voyages, check the MAARER wreck client
        if prefix == "das":
            return await self._wreck_client.get_by_voyage_id(voyage_id)

        # For other archives, the archive client handles its own wrecks
        client = self._voyage_clients.get(prefix)
        if client and hasattr(client, "get_wreck_by_voyage_id"):
            return await client.get_wreck_by_voyage_id(voyage_id)

        return None

    # --- Timeline -----------------------------------------------------------

    async def build_timeline(
        self,
        voyage_id: str,
        include_positions: bool = False,
        max_positions: int = 20,
    ) -> dict | None:
        """
        Build a chronological timeline of events for a voyage.

        Assembles events from multiple archives:
        - DAS voyage: departure, arrival
        - Route estimates: waypoint positions
        - CLIWOC tracks: observed ship positions
        - MAARER wrecks: loss event
        """
        voyage = await self.get_voyage(voyage_id)
        if not voyage:
            return None

        events: list[dict] = []
        data_sources: list[str] = []
        ship_name = voyage.get("ship_name")

        # --- Departure event ---
        dep_date = voyage.get("departure_date")
        dep_port = voyage.get("departure_port", "Unknown")
        if dep_date:
            data_sources.append("das")
            events.append(
                {
                    "date": dep_date,
                    "type": "departure",
                    "title": f"Departed {dep_port}",
                    "details": {
                        "port": dep_port,
                        "ship_name": ship_name,
                        "captain": voyage.get("captain"),
                    },
                    "position": None,
                    "source": "das",
                }
            )

        # --- Route waypoint estimates ---
        if dep_date:
            route_matches = suggest_route(
                departure_port=voyage.get("departure_port"),
                destination_port=voyage.get("destination_port"),
            )
            if route_matches:
                route_id = route_matches[0]["route_id"]
                route_data = get_route_detail(route_id)
                if route_data:
                    if "route_estimate" not in data_sources:
                        data_sources.append("route_estimate")
                    for wp in route_data.get("waypoints", [])[1:]:  # skip departure
                        try:
                            dep_dt = datetime.strptime(dep_date, "%Y-%m-%d")
                        except ValueError:
                            break
                        wp_date = dep_dt + timedelta(days=wp["cumulative_days"])
                        wp_date_str = wp_date.strftime("%Y-%m-%d")

                        est = estimate_position(
                            route_id=route_id,
                            departure_date=dep_date,
                            target_date=wp_date_str,
                        )
                        pos = None
                        if est and "estimated_position" in est:
                            ep = est["estimated_position"]
                            pos = {"lat": ep["lat"], "lon": ep["lon"]}

                        events.append(
                            {
                                "date": wp_date_str,
                                "type": "waypoint_estimate",
                                "title": f"Estimated at {wp['name']}",
                                "details": {
                                    "waypoint": wp["name"],
                                    "region": wp.get("region", ""),
                                    "cumulative_days": wp["cumulative_days"],
                                },
                                "position": pos,
                                "source": "route_estimate",
                            }
                        )

        # --- CLIWOC track positions ---
        cliwoc_track_info = self._find_cliwoc_track_for_voyage(voyage)
        if cliwoc_track_info and include_positions:
            cliwoc_voyage_id = cliwoc_track_info.get("voyage_id")
            if cliwoc_voyage_id is not None:
                full_track = get_track(cliwoc_voyage_id)
                if full_track:
                    if "cliwoc" not in data_sources:
                        data_sources.append("cliwoc")
                    positions = full_track.get("positions", [])
                    # Sample positions if there are too many
                    if len(positions) > max_positions and max_positions > 0:
                        step = max(1, len(positions) // max_positions)
                        positions = positions[::step][:max_positions]
                    for p in positions:
                        if p.get("date") and p.get("lat") is not None:
                            events.append(
                                {
                                    "date": p["date"],
                                    "type": "cliwoc_position",
                                    "title": f"CLIWOC position ({p.get('lat', '?')}N, {p.get('lon', '?')}E)",
                                    "details": {
                                        "nationality": full_track.get("nationality"),
                                    },
                                    "position": {"lat": p["lat"], "lon": p["lon"]},
                                    "source": "cliwoc",
                                }
                            )
        elif cliwoc_track_info:
            if "cliwoc" not in data_sources:
                data_sources.append("cliwoc")

        # --- Wreck / loss event ---
        wreck = await self._find_wreck_for_voyage(voyage_id)
        if wreck:
            if "maarer" not in data_sources:
                data_sources.append("maarer")
            loss_date = wreck.get("loss_date")
            if loss_date:
                pos = None
                wreck_pos = wreck.get("position")
                if wreck_pos and wreck_pos.get("lat") is not None:
                    pos = {"lat": wreck_pos["lat"], "lon": wreck_pos["lon"]}
                events.append(
                    {
                        "date": loss_date,
                        "type": "loss",
                        "title": f"Lost: {wreck.get('loss_cause', 'unknown cause')}",
                        "details": {
                            "wreck_id": wreck.get("wreck_id"),
                            "loss_cause": wreck.get("loss_cause"),
                            "loss_location": wreck.get("loss_location"),
                            "region": wreck.get("region"),
                        },
                        "position": pos,
                        "source": "maarer",
                    }
                )

        # --- Arrival event ---
        arrival_date = voyage.get("arrival_date")
        dest_port = voyage.get("destination_port", "Unknown")
        if arrival_date and voyage.get("fate") != "wrecked":
            events.append(
                {
                    "date": arrival_date,
                    "type": "arrival",
                    "title": f"Arrived {dest_port}",
                    "details": {
                        "port": dest_port,
                    },
                    "position": None,
                    "source": "das",
                }
            )

        # Sort events chronologically
        events.sort(key=lambda e: e["date"])

        # Build GeoJSON LineString from positioned events
        geojson = None
        positioned = [
            e for e in events if e.get("position") and e["position"].get("lat") is not None
        ]
        if len(positioned) >= 2:
            coords = [[e["position"]["lon"], e["position"]["lat"]] for e in positioned]
            geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
                "properties": {
                    "voyage_id": voyage_id,
                    "ship_name": ship_name,
                    "point_count": len(coords),
                },
            }

        return {
            "voyage_id": voyage_id,
            "ship_name": ship_name,
            "events": events,
            "data_sources": data_sources,
            "geojson": geojson,
        }

    # --- Wreck Operations ---------------------------------------------------

    async def search_wrecks(
        self,
        ship_name: str | None = None,
        date_range: str | None = None,
        region: str | None = None,
        cause: str | None = None,
        status: str | None = None,
        min_depth_m: float | None = None,
        max_depth_m: float | None = None,
        min_cargo_value: float | None = None,
        archive: str | None = None,
        max_results: int = 100,
    ) -> list[dict]:
        """Search wreck records across all archives or a specific one."""
        search_kwargs = dict(
            ship_name=ship_name,
            date_range=date_range,
            region=region,
            cause=cause,
            status=status,
            min_depth_m=min_depth_m,
            max_depth_m=max_depth_m,
            min_cargo_value=min_cargo_value,
            max_results=max_results,
        )

        if archive and archive in self._wreck_clients:
            client = self._wreck_clients[archive]
            if hasattr(client, "search_wrecks"):
                results = await client.search_wrecks(**search_kwargs)
            else:
                results = await client.search(**search_kwargs)
        elif archive:
            return []
        else:
            # Query all wreck archives and merge results
            all_results: list[dict] = []
            for client in self._wreck_clients.values():
                if hasattr(client, "search_wrecks"):
                    all_results.extend(await client.search_wrecks(**search_kwargs))
                else:
                    all_results.extend(await client.search(**search_kwargs))
            results = all_results

        return results[:max_results]

    async def get_wreck(self, wreck_id: str) -> dict | None:
        """Get full wreck record, routing to the correct archive client."""
        # Determine which client handles this wreck ID
        if wreck_id.startswith("maarer:"):
            return await self._wreck_client.get_by_id(wreck_id)

        # Check compound prefixes: eic_wreck:, carreira_wreck:, etc.
        for prefix, client in [
            ("eic_wreck:", self._eic_client),
            ("carreira_wreck:", self._carreira_client),
            ("galleon_wreck:", self._galleon_client),
            ("soic_wreck:", self._soic_client),
        ]:
            if wreck_id.startswith(prefix):
                return await client.get_wreck_by_id(wreck_id)

        # Default to MAARER
        return await self._wreck_client.get_by_id(wreck_id)

    # --- Vessel Operations --------------------------------------------------

    async def search_vessels(
        self,
        name: str | None = None,
        ship_type: str | None = None,
        built_range: str | None = None,
        shipyard: str | None = None,
        chamber: str | None = None,
        min_tonnage: int | None = None,
        max_tonnage: int | None = None,
        archive: str | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Search vessel records from local DAS data."""
        return await self._das_client.search_vessels(
            name=name,
            ship_type=ship_type,
            chamber=chamber,
            min_tonnage=min_tonnage,
            max_tonnage=max_tonnage,
            max_results=max_results,
        )

    async def get_vessel(self, vessel_id: str) -> dict | None:
        """Get full vessel specification."""
        return await self._das_client.get_vessel_by_id(vessel_id)

    # --- Crew Operations ----------------------------------------------------

    async def search_crew(
        self,
        name: str | None = None,
        rank: str | None = None,
        ship_name: str | None = None,
        voyage_id: str | None = None,
        origin: str | None = None,
        date_range: str | None = None,
        fate: str | None = None,
        archive: str = "voc_crew",
        max_results: int = 100,
    ) -> list[dict]:
        """Search crew muster records."""
        return await self._crew_client.search(
            name=name,
            rank=rank,
            ship_name=ship_name,
            voyage_id=voyage_id,
            origin=origin,
            fate=fate,
            max_results=max_results,
        )

    async def get_crew_member(self, crew_id: str) -> dict | None:
        """Get full crew member record."""
        return await self._crew_client.get_by_id(crew_id)

    # --- Cargo Operations ---------------------------------------------------

    async def search_cargo(
        self,
        voyage_id: str | None = None,
        commodity: str | None = None,
        origin: str | None = None,
        destination: str | None = None,
        date_range: str | None = None,
        min_value: float | None = None,
        archive: str = "voc_cargo",
        max_results: int = 100,
    ) -> list[dict]:
        """Search cargo manifests."""
        return await self._cargo_client.search(
            voyage_id=voyage_id,
            commodity=commodity,
            origin=origin,
            destination=destination,
            min_value=min_value,
            max_results=max_results,
        )

    async def get_cargo_manifest(self, voyage_id: str) -> list[dict]:
        """Get full cargo manifest for a voyage."""
        return await self._cargo_client.search(voyage_id=voyage_id, max_results=1000)

    # --- Hull Profiles ------------------------------------------------------

    def get_hull_profile(self, ship_type: str) -> dict | None:
        """Return hydrodynamic hull profile for a ship type."""
        return self._hull_profiles.get(ship_type)

    def list_hull_profiles(self) -> list[str]:
        """Return available ship types with hull profiles."""
        return list(self._hull_profiles.keys())

    # --- Position Assessment ------------------------------------------------

    async def assess_position(
        self,
        voyage_id: str | None = None,
        wreck_id: str | None = None,
        position: dict | None = None,
        source_description: str | None = None,
        date: str | None = None,
    ) -> dict:
        """Assess quality and uncertainty of a historical position."""
        year = None
        pos = position or {}

        if voyage_id:
            voyage = await self.get_voyage(voyage_id)
            if voyage:
                loss_date = voyage.get("loss_date") or voyage.get("departure_date", "")
                if loss_date and len(loss_date) >= 4:
                    try:
                        year = int(loss_date[:4])
                    except ValueError:
                        pass
                if voyage.get("incident") and voyage["incident"].get("position"):
                    pos = voyage["incident"]["position"]
        elif wreck_id:
            wreck = await self.get_wreck(wreck_id)
            if wreck:
                if wreck.get("loss_date") and len(wreck["loss_date"]) >= 4:
                    year = int(wreck["loss_date"][:4])
                if wreck.get("position"):
                    pos = wreck["position"]
        elif date and len(date) >= 4:
            year = int(date[:4])

        nav_era = self._get_navigation_era(year)

        quality_score = 0.5
        uncertainty_km = nav_era.get("typical_accuracy_km", 50) if nav_era else 50
        uncertainty_type = "approximate"

        if source_description:
            desc_lower = source_description.lower()
            if "gps" in desc_lower or "surveyed" in desc_lower:
                quality_score = 0.95
                uncertainty_km = 0.1
                uncertainty_type = "precise"
            elif "multiple" in desc_lower or "triangulat" in desc_lower:
                quality_score = 0.7
                uncertainty_km = 5
                uncertainty_type = "triangulated"
            elif "dead reckoning" in desc_lower:
                quality_score = 0.4
                uncertainty_km = max(uncertainty_km, 30)
                uncertainty_type = "dead_reckoning"
            elif "approximate" in desc_lower or "general" in desc_lower:
                quality_score = 0.3
                uncertainty_km = 100
                uncertainty_type = "approximate"
            elif "regional" in desc_lower or "straits" in desc_lower:
                quality_score = 0.15
                uncertainty_km = 500
                uncertainty_type = "regional"

        quality_label = (
            "good" if quality_score > 0.7 else ("moderate" if quality_score > 0.4 else "poor")
        )

        return {
            "voyage_id": voyage_id,
            "wreck_id": wreck_id,
            "position": pos,
            "assessment": {
                "quality_score": round(quality_score, 2),
                "quality_label": quality_label,
                "uncertainty_type": uncertainty_type,
                "uncertainty_radius_km": uncertainty_km,
                "confidence": 0.68,
            },
            "factors": {
                "navigation_era": {
                    "year": year,
                    **(nav_era or {}),
                },
                "position_source": {
                    "type": "reconstructed" if not source_description else "described",
                    "description": source_description,
                },
            },
            "recommendations": {
                "for_drift_modelling": (
                    f"Use uncertainty envelope ({uncertainty_km}km radius). "
                    "Run Monte Carlo with position samples from entire "
                    "uncertainty region."
                ),
                "for_search": (
                    f"Search area must account for {uncertainty_km}km position "
                    "uncertainty compounded by drift uncertainty."
                ),
            },
            "comparable_cases": [],
        }

    # --- Statistics ---------------------------------------------------------

    async def get_statistics(
        self,
        archive: str | None = None,
        date_range: str | None = None,
        group_by: str | None = None,
    ) -> dict:
        """Get aggregate statistics across archives."""
        wrecks = await self.search_wrecks(max_results=1000)

        if date_range:
            wrecks = self._filter_by_date_range(wrecks, date_range, "loss_date")

        losses_by_region: dict[str, int] = {}
        losses_by_cause: dict[str, int] = {}
        losses_by_status: dict[str, int] = {}
        losses_by_decade: dict[str, int] = {}
        total_lives_lost = 0
        total_cargo_value = 0

        for w in wrecks:
            region = w.get("region", "other")
            losses_by_region[region] = losses_by_region.get(region, 0) + 1

            cause = w.get("loss_cause", "unknown")
            losses_by_cause[cause] = losses_by_cause.get(cause, 0) + 1

            status = w.get("status", "unknown")
            losses_by_status[status] = losses_by_status.get(status, 0) + 1

            loss_date = w.get("loss_date", "")
            if loss_date and len(loss_date) >= 4:
                decade = f"{loss_date[:3]}0s"
                losses_by_decade[decade] = losses_by_decade.get(decade, 0) + 1

            total_lives_lost += w.get("lives_lost", 0) or 0
            total_cargo_value += w.get("cargo_value_guilders", 0) or 0

        return {
            "archives_included": [archive] if archive else list(self._wreck_clients.keys()),
            "date_range": date_range or "all",
            "summary": {
                "total_losses": len(wrecks),
                "lives_lost_total": total_lives_lost,
                "cargo_value_guilders_total": total_cargo_value,
            },
            "losses_by_region": losses_by_region,
            "losses_by_cause": losses_by_cause,
            "losses_by_status": losses_by_status,
            "losses_by_decade": dict(sorted(losses_by_decade.items())),
        }

    # --- GeoJSON Export -----------------------------------------------------

    async def export_geojson(
        self,
        wreck_ids: list[str] | None = None,
        region: str | None = None,
        status: str | None = None,
        archive: str | None = None,
        include_uncertainty: bool = True,
        include_voyage_data: bool = True,
    ) -> dict:
        """Export wreck positions as GeoJSON FeatureCollection."""
        if wreck_ids:
            wrecks = []
            for wid in wreck_ids:
                w = await self.get_wreck(wid)
                if w:
                    wrecks.append(w)
        else:
            wrecks = await self.search_wrecks(
                region=region, status=status, archive=archive, max_results=1000
            )

        features = []
        for w in wrecks:
            pos = w.get("position", {})
            lat = pos.get("lat") if pos else None
            lon = pos.get("lon") if pos else None
            has_position = lat is not None and lon is not None

            properties: dict[str, Any] = {
                "wreck_id": w.get("wreck_id"),
                "ship_name": w.get("ship_name"),
                "loss_date": w.get("loss_date"),
                "loss_location": w.get("loss_location"),
                "region": w.get("region"),
                "status": w.get("status"),
            }

            if include_uncertainty and has_position:
                properties["uncertainty_km"] = pos.get("uncertainty_km", 50)

            if include_voyage_data:
                properties["ship_type"] = w.get("ship_type")
                properties["tonnage"] = w.get("tonnage")
                properties["loss_cause"] = w.get("loss_cause")
                properties["lives_lost"] = w.get("lives_lost")
                properties["depth_m"] = w.get("depth_estimate_m")

            # Use null geometry for wrecks without known coordinates
            geometry: dict[str, Any] | None = (
                {"type": "Point", "coordinates": [lon, lat]} if has_position else None
            )

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": properties,
                }
            )

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    # --- Private Helpers ----------------------------------------------------

    def _get_navigation_era(self, year: int | None) -> dict | None:
        """Look up navigation technology for a given year."""
        if year is None:
            return None
        for era_range, era_data in NAVIGATION_ERAS.items():
            start, end = era_range.split("-")
            if int(start) <= year <= int(end):
                return era_data
        return None

    def _filter_by_date_range(
        self, records: list[dict], date_range: str, date_field: str
    ) -> list[dict]:
        """Filter records by date range (YYYY/YYYY or YYYY-MM-DD/YYYY-MM-DD)."""
        parts = date_range.split("/")
        if len(parts) != 2:
            return records

        start_str, end_str = parts
        start_year = int(start_str[:4]) if len(start_str) >= 4 else 0
        end_year = int(end_str[:4]) if len(end_str) >= 4 else 9999

        filtered = []
        for r in records:
            date_val = r.get(date_field, "")
            if date_val and len(date_val) >= 4:
                try:
                    record_year = int(date_val[:4])
                except ValueError:
                    continue
                if start_year <= record_year <= end_year:
                    filtered.append(r)
        return filtered
