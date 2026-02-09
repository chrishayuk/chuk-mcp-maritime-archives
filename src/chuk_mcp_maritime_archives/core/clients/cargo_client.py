"""
BGB (Boekhouder-Generaal Batavia) cargo client stub.

The BGB cargo database requires a separate download script.
This stub returns empty results until the cargo data download
is implemented.

Future: https://bgb.huygens.knaw.nl/
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CargoClient(BaseArchiveClient):
    """
    Stub client for the Boekhouder-Generaal Batavia (BGB) cargo database.

    Returns empty results until cargo data download is implemented.
    """

    CARGO_FILE = "cargo.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)

    async def search(
        self,
        *,
        voyage_id: str | None = None,
        commodity: str | None = None,
        origin: str | None = None,
        destination: str | None = None,
        date_range: str | None = None,
        min_value: float | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Search cargo records. Returns empty until cargo download is implemented."""
        records = self._load_json(self.CARGO_FILE)
        if not records:
            return []

        if voyage_id:
            records = [c for c in records if c.get("voyage_id") == voyage_id]
        if commodity:
            records = [c for c in records if self._contains(c.get("commodity"), commodity)]
        if origin:
            records = [c for c in records if self._contains(c.get("origin"), origin)]
        if destination:
            records = [c for c in records if self._contains(c.get("destination"), destination)]
        if min_value is not None:
            records = [c for c in records if (c.get("value_guilders") or 0) >= min_value]
        if date_range:
            records = self._filter_by_date_range(records, date_range, "date")

        return records[:max_results]

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single cargo record by ID."""
        records = self._load_json(self.CARGO_FILE)
        for c in records:
            if c.get("cargo_id") == record_id:
                return c
        return None

    async def get_manifest(self, voyage_id: str) -> list[dict]:
        """Retrieve the full cargo manifest for a single voyage."""
        return await self.search(voyage_id=voyage_id)
