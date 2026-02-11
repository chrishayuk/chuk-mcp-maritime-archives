"""
BGB (Boekhouder-Generaal Batavia) cargo client.

Reads locally stored JSON data from ``data/cargo.json``, produced by
``scripts/download_cargo.py`` (Zenodo RDF) or ``scripts/generate_cargo.py``
(curated fallback). Contains ~200 curated cargo records covering VOC trade
goods shipped between Asia and the Netherlands, 1700-1795.

Source: https://bgb.huygens.knaw.nl/
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CargoClient(BaseArchiveClient):
    """
    Client for the Boekhouder-Generaal Batavia (BGB) cargo database.

    Searches and retrieves records from locally cached JSON files
    containing curated VOC cargo manifests, 1700-1795.
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
        """Search cargo records from local data."""
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
