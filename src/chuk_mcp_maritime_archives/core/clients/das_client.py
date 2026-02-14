"""
DAS (Dutch Asiatic Shipping) client for voyages and vessels.

Reads locally stored JSON data produced by scripts/download_das.py
from the DAS database hosted by the Huygens Institute:
    https://resources.huygens.knaw.nl/das
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class DASClient(BaseArchiveClient):
    """
    Client for the Dutch Asiatic Shipping (DAS) database.

    Searches and retrieves records from locally cached JSON files
    containing all 8,000+ VOC voyages between the Netherlands and Asia,
    1595-1795.
    """

    VOYAGES_FILE = "voyages.json"
    VESSELS_FILE = "vessels.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._voyage_index: dict[str, dict] | None = None
        self._vessel_index: dict[str, dict] | None = None
        self._voyage_vessel_index: dict[str, dict] | None = None

    def _get_voyages(self) -> list[dict]:
        return self._load_json(self.VOYAGES_FILE)

    def _get_voyage_index(self) -> dict[str, dict]:
        if self._voyage_index is None:
            self._voyage_index = {v["voyage_id"]: v for v in self._get_voyages()}
        return self._voyage_index

    def _get_vessels(self) -> list[dict]:
        return self._load_json(self.VESSELS_FILE)

    def _get_vessel_index(self) -> dict[str, dict]:
        if self._vessel_index is None:
            self._vessel_index = {v["vessel_id"]: v for v in self._get_vessels()}
        return self._vessel_index

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
        max_results: int = 50,
        **kwargs: Any,
    ) -> list[dict]:
        """Search DAS voyage records from local data."""
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
        if date_range:
            results = self._filter_by_date_range(results, date_range, "departure_date")

        return results[:max_results]

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single voyage by its DAS voyage ID."""
        index = self._get_voyage_index()
        # Support both "das:0372.1" and "0372.1" formats
        if record_id in index:
            return index[record_id]
        prefixed = f"das:{record_id}" if not record_id.startswith("das:") else record_id
        return index.get(prefixed)

    async def search_vessels(
        self,
        *,
        name: str | None = None,
        ship_type: str | None = None,
        built_range: str | None = None,
        shipyard: str | None = None,
        chamber: str | None = None,
        min_tonnage: int | None = None,
        max_tonnage: int | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """Search DAS vessel records from local data."""
        results = list(self._get_vessels())

        if name:
            results = [v for v in results if self._contains(v.get("name"), name)]
        if ship_type:
            results = [v for v in results if v.get("type") == ship_type]
        if chamber:
            results = [v for v in results if self._contains(v.get("chamber"), chamber)]
        if shipyard:
            results = [v for v in results if self._contains(v.get("yard"), shipyard)]
        if min_tonnage is not None:
            results = [v for v in results if (v.get("tonnage") or 0) >= min_tonnage]
        if max_tonnage is not None:
            results = [
                v for v in results if v.get("tonnage") is not None and v["tonnage"] <= max_tonnage
            ]
        if built_range:
            results = self._filter_by_date_range(results, built_range, "built_year")

        return results[:max_results]

    def get_vessel_for_voyage(self, voyage_id: str) -> dict | None:
        """Find vessel whose voyage_ids array contains this voyage_id."""
        if self._voyage_vessel_index is None:
            self._voyage_vessel_index = {}
            for v in self._get_vessels():
                for vid in v.get("voyage_ids", []):
                    self._voyage_vessel_index[vid] = v
        result = self._voyage_vessel_index.get(voyage_id)
        if result is None and ":" not in voyage_id:
            result = self._voyage_vessel_index.get(f"das:{voyage_id}")
        return result

    async def get_vessel_by_id(self, vessel_id: str) -> dict | None:
        """Retrieve a single vessel by ID."""
        index = self._get_vessel_index()
        if vessel_id in index:
            return index[vessel_id]
        prefixed = (
            f"das_vessel:{vessel_id}" if not vessel_id.startswith("das_vessel:") else vessel_id
        )
        return index.get(prefixed)
