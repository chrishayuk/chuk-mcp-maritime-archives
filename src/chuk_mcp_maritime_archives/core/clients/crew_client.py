"""
VOC Crew client — searches the VOC Opvarenden (crew) database.

The dataset contains up to 774,200 personnel records from the Nationaal
Archief, downloaded via ``scripts/download_crew.py``.  Because the full
dataset is large, this client builds lazy indexes on first access to
keep common lookups fast (O(1) for voyage_id, O(tokens) for name).
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CrewClient(BaseArchiveClient):
    """
    Client for the VOC Opvarenden (crew) database.

    Builds in-memory indexes on first search to accelerate lookups
    across 774K+ records.
    """

    CREW_FILE = "crew.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._voyage_index: dict[str, list[dict]] | None = None
        self._id_index: dict[str, dict] | None = None

    def _ensure_indexes(self, records: list[dict]) -> None:
        """Build voyage and ID indexes lazily on first access."""
        if self._voyage_index is not None:
            return

        voyage_idx: dict[str, list[dict]] = defaultdict(list)
        id_idx: dict[str, dict] = {}

        for rec in records:
            vid = rec.get("voyage_id")
            if vid:
                voyage_idx[vid].append(rec)
            cid = rec.get("crew_id")
            if cid:
                id_idx[cid] = rec

        self._voyage_index = dict(voyage_idx)
        self._id_index = id_idx
        logger.info(
            "Crew indexes built: %d voyage keys, %d ID keys",
            len(self._voyage_index),
            len(self._id_index),
        )

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
        """Search crew records with indexed lookups for large datasets."""
        all_records = self._load_json(self.CREW_FILE)
        if not all_records:
            return []

        self._ensure_indexes(all_records)

        # Start from narrowest index available
        if voyage_id and self._voyage_index is not None:
            records = self._voyage_index.get(voyage_id, [])
        else:
            records = all_records

        if name:
            records = [c for c in records if self._contains(c.get("name"), name)]
        if rank:
            records = [c for c in records if self._contains(c.get("rank"), rank)]
        if ship_name:
            records = [c for c in records if self._contains(c.get("ship_name"), ship_name)]
        if voyage_id and self._voyage_index is None:
            records = [c for c in records if c.get("voyage_id") == voyage_id]
        if origin:
            records = [c for c in records if self._contains(c.get("origin"), origin)]
        if fate:
            records = [c for c in records if c.get("service_end_reason") == fate]
        if date_range:
            records = self._filter_by_date_range(records, date_range, "embarkation_date")

        return records[:max_results]

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single crew record by ID using the index."""
        records = self._load_json(self.CREW_FILE)
        if not records:
            return None

        self._ensure_indexes(records)

        if self._id_index is not None:
            return self._id_index.get(record_id)

        for c in records:
            if c.get("crew_id") == record_id:
                return c
        return None
