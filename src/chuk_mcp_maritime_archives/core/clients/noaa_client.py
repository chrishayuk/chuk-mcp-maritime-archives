"""
NOAA Wrecks & Obstructions (AWOIS) client.

Reads locally stored JSON data produced by scripts/download_noaa.py or
scripts/generate_noaa.py. Contains ~13,000 wreck records in US waters.

Source data:
    NOAA Office of Coast Survey. Automated Wreck and Obstruction
    Information System (AWOIS). US Department of Commerce.
    Public Domain (US Government work).
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class NOAAClient(BaseArchiveClient):
    """
    Client for NOAA AWOIS wreck records.

    Wrecks-only archive — no voyage data. Searches and retrieves
    records from locally cached JSON files. Supports GP quality
    (position accuracy) filtering.
    """

    WRECKS_FILE = "noaa_wrecks.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._wreck_index: dict[str, dict] | None = None

    def _get_wrecks(self) -> list[dict]:
        return self._load_json(self.WRECKS_FILE)

    def _get_wreck_index(self) -> dict[str, dict]:
        if self._wreck_index is None:
            self._wreck_index = {w["wreck_id"]: w for w in self._get_wrecks()}
            logger.info("NOAA wreck index built: %d wrecks", len(self._wreck_index))
        return self._wreck_index

    # --- BaseArchiveClient abstract methods (delegate to wreck methods) ------

    async def search(self, **kwargs: Any) -> list[dict]:
        """Delegate to search_wrecks (NOAA has no voyage data)."""
        return await self.search_wrecks(**kwargs)

    async def get_by_id(self, record_id: str) -> dict | None:
        """Delegate to get_wreck_by_id."""
        return await self.get_wreck_by_id(record_id)

    # --- Wreck operations ----------------------------------------------------

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
        flag: str | None = None,
        vessel_type: str | None = None,
        gp_quality: int | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Search NOAA wreck records from local data."""
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
        if flag:
            results = [w for w in results if self._contains(w.get("flag"), flag)]
        if vessel_type:
            results = [w for w in results if self._contains(w.get("vessel_type"), vessel_type)]
        if gp_quality is not None:
            results = [w for w in results if w.get("gp_quality") == gp_quality]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "loss_date")

        return results[:max_results]

    async def get_wreck_by_id(self, wreck_id: str) -> dict | None:
        """Retrieve a single wreck record by ID using index."""
        index = self._get_wreck_index()
        if wreck_id in index:
            return index[wreck_id]
        prefixed = f"noaa_wreck:{wreck_id}" if not wreck_id.startswith("noaa_wreck:") else wreck_id
        return index.get(prefixed)
