"""
Archive Manager — central orchestrator for maritime archive data.

Manages:
- Archive registry and metadata
- Data source clients for each archive (DAS, VOC Crew, Cargo, Wrecks)
- Hull profile lookups
- Position uncertainty assessment
- GeoJSON export
- Aggregate statistics
"""

import logging
from pathlib import Path
from typing import Any

from ..constants import (
    ARCHIVE_METADATA,
    NAVIGATION_ERAS,
)
from .clients import CargoClient, CrewClient, DASClient, WreckClient
from .hull_profiles import HULL_PROFILES

logger = logging.getLogger(__name__)

# Default data directory relative to the project root
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


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
        """Search for voyages from local DAS data."""
        results = await self._das_client.search(
            ship_name=ship_name,
            captain=captain,
            date_range=date_range,
            departure_port=departure_port,
            destination_port=destination_port,
            route=route,
            fate=fate,
            max_results=max_results,
        )

        if archive:
            results = [v for v in results if v.get("archive") == archive]

        return results[:max_results]

    async def get_voyage(self, voyage_id: str) -> dict | None:
        """Get full voyage details."""
        return await self._das_client.get_by_id(voyage_id)

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
        """Search wreck records from local data."""
        results = await self._wreck_client.search(
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

        if archive:
            results = [w for w in results if w.get("archive", "maarer") == archive]

        return results[:max_results]

    async def get_wreck(self, wreck_id: str) -> dict | None:
        """Get full wreck record."""
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
            "archives_included": ["das", "maarer"] if not archive else [archive],
            "date_range": date_range or "1595-1795",
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
