"""
VOC Crew client stub.

The VOC Opvarenden crew database at the Nationaal Archief requires
a separate download script. This stub returns empty results until
the crew data download is implemented.

Future: https://www.nationaalarchief.nl/onderzoeken/index/nt00444
"""

import logging
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CrewClient(BaseArchiveClient):
    """
    Stub client for the VOC Opvarenden (crew) database.

    Returns empty results until crew data download is implemented.
    """

    CREW_FILE = "crew.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)

    async def search(
        self,
        *,
        name: str | None = None,
        rank: str | None = None,
        ship_name: str | None = None,
        voyage_id: str | None = None,
        origin: str | None = None,
        date_range: str | None = None,
        fate: str | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Search crew records. Returns empty until crew download is implemented."""
        records = self._load_json(self.CREW_FILE)
        if not records:
            return []

        if name:
            records = [c for c in records if self._contains(c.get("name"), name)]
        if rank:
            records = [c for c in records if self._contains(c.get("rank"), rank)]
        if ship_name:
            records = [c for c in records if self._contains(c.get("ship_name"), ship_name)]
        if voyage_id:
            records = [c for c in records if c.get("voyage_id") == voyage_id]
        if origin:
            records = [c for c in records if self._contains(c.get("origin"), origin)]
        if fate:
            records = [c for c in records if c.get("service_end_reason") == fate]
        if date_range:
            records = self._filter_by_date_range(records, date_range, "embarkation_date")

        return records[:max_results]

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single crew record by ID."""
        records = self._load_json(self.CREW_FILE)
        for c in records:
            if c.get("crew_id") == record_id:
                return c
        return None
