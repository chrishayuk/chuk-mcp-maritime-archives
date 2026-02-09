"""
Wreck database client for shipwreck and loss records.

Reads locally stored JSON data produced by scripts/download_das.py
which extracts wreck/loss records from the DAS voyage Particulars field.
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class WreckClient(BaseArchiveClient):
    """
    Client for the wreck/loss database.

    Searches and retrieves wreck records extracted from DAS voyage data.
    Loss events are identified by keywords in the Particulars field
    (Wrecked, Lost, Sunk, Captured, etc.).
    """

    WRECKS_FILE = "wrecks.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._wreck_index: dict[str, dict] | None = None

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
        """Search wreck records from local data."""
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

    async def get_by_voyage_id(self, voyage_id: str) -> dict | None:
        """Find wreck record linked to a specific voyage."""
        for w in self._get_wrecks():
            if w.get("voyage_id") == voyage_id:
                return w
        return None

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single wreck record by ID."""
        index = self._get_wreck_index()
        if record_id in index:
            return index[record_id]
        prefixed = f"maarer:{record_id}" if not record_id.startswith("maarer:") else record_id
        return index.get(prefixed)
