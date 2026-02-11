"""
Portuguese Carreira da India client for voyages and wrecks.

Reads locally stored JSON data produced by scripts/generate_carreira.py.
Covers the Portuguese India Run, 1497-1835.

Source data compiled from:
    Guinote, Paulo, Eduardo Frutuoso, and Antonio Lopes.
    As Armadas da India 1497-1835. Lisbon, 2002.
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CarreiraClient(BaseArchiveClient):
    """
    Client for the Portuguese Carreira da India voyage database.

    Searches and retrieves records from locally cached JSON files
    containing curated Portuguese India Run voyages, 1497-1835.
    """

    VOYAGES_FILE = "carreira_voyages.json"
    WRECKS_FILE = "carreira_wrecks.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._voyage_index: dict[str, dict] | None = None
        self._wreck_index: dict[str, dict] | None = None

    def _get_voyages(self) -> list[dict]:
        return self._load_json(self.VOYAGES_FILE)

    def _get_voyage_index(self) -> dict[str, dict]:
        if self._voyage_index is None:
            self._voyage_index = {v["voyage_id"]: v for v in self._get_voyages()}
        return self._voyage_index

    def _get_wrecks(self) -> list[dict]:
        return self._load_json(self.WRECKS_FILE)

    def _get_wreck_index(self) -> dict[str, dict]:
        if self._wreck_index is None:
            self._wreck_index = {w["wreck_id"]: w for w in self._get_wrecks()}
        return self._wreck_index

    async def search(
        self,
        *,
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        route: str | None = None,
        fate: str | None = None,
        armada_year: int | None = None,
        fleet_commander: str | None = None,
        max_results: int = 50,
        **kwargs: Any,
    ) -> list[dict]:
        """Search Carreira da India voyage records from local data."""
        results = list(self._get_voyages())

        if ship_name:
            results = [v for v in results if self._contains(v.get("ship_name"), ship_name)]
        if captain:
            results = [v for v in results if self._contains(v.get("captain"), captain)]
        if fate:
            results = [v for v in results if v.get("fate") == fate]
        if departure_port:
            results = [
                v for v in results if self._contains(v.get("departure_port"), departure_port)
            ]
        if destination_port:
            results = [
                v for v in results if self._contains(v.get("destination_port"), destination_port)
            ]
        if route:
            route_lower = route.lower()
            results = [
                v
                for v in results
                if route_lower in (v.get("departure_port") or "").lower()
                or route_lower in (v.get("destination_port") or "").lower()
                or route_lower in (v.get("particulars") or "").lower()
            ]
        if armada_year is not None:
            results = [v for v in results if v.get("armada_year") == armada_year]
        if fleet_commander:
            results = [
                v
                for v in results
                if self._contains(v.get("fleet_commander"), fleet_commander)
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "departure_date")

        return results[:max_results]

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single voyage by its Carreira voyage ID."""
        index = self._get_voyage_index()
        if record_id in index:
            return index[record_id]
        prefixed = (
            f"carreira:{record_id}" if not record_id.startswith("carreira:") else record_id
        )
        return index.get(prefixed)

    async def search_wrecks(
        self,
        *,
        ship_name: str | None = None,
        date_range: str | None = None,
        region: str | None = None,
        cause: str | None = None,
        status: str | None = None,
        min_depth_m: float | None = None,
        max_depth_m: float | None = None,
        min_cargo_value: float | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Search Carreira wreck records from local data."""
        results = list(self._get_wrecks())

        if ship_name:
            results = [w for w in results if self._contains(w.get("ship_name"), ship_name)]
        if cause:
            results = [w for w in results if w.get("loss_cause") == cause]
        if status:
            results = [w for w in results if w.get("status") == status]
        if region:
            results = [w for w in results if w.get("region") == region]
        if min_depth_m is not None:
            results = [w for w in results if (w.get("depth_estimate_m") or 0) >= min_depth_m]
        if max_depth_m is not None:
            results = [
                w
                for w in results
                if w.get("depth_estimate_m") is not None and w["depth_estimate_m"] <= max_depth_m
            ]
        if min_cargo_value is not None:
            results = [
                w for w in results if (w.get("cargo_value_guilders") or 0) >= min_cargo_value
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "loss_date")

        return results[:max_results]

    async def get_wreck_by_id(self, wreck_id: str) -> dict | None:
        """Retrieve a single wreck record by ID."""
        index = self._get_wreck_index()
        if wreck_id in index:
            return index[wreck_id]
        prefixed = (
            f"carreira_wreck:{wreck_id}"
            if not wreck_id.startswith("carreira_wreck:")
            else wreck_id
        )
        return index.get(prefixed)

    async def get_wreck_by_voyage_id(self, voyage_id: str) -> dict | None:
        """Find wreck record linked to a specific voyage."""
        for w in self._get_wrecks():
            if w.get("voyage_id") == voyage_id:
                return w
        return None
