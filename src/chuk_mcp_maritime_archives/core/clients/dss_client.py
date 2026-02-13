"""
Dutch Ships and Sailors (DSS) Linked Data client.

Reads locally stored JSON data produced by scripts/generate_dss.py.
Covers two datasets from the CLARIN IV DSS project:

- GZMVOC (Generale Zeemonsterrollen VOC): Ship-level crew composition
  and muster records from Asian waters, 1691-1791.
- MDB (Noordelijke Monsterrollen): Individual crew records from four
  northern Dutch provinces, 1803-1837.

Source data:
    Bruijn, J.R. et al. Dutch-Asiatic Shipping in the 17th and 18th
    Centuries. The Hague, 1979-1987.
    CLARIN-IV DSS Linked Data Cloud (doi:10.17026/dans-zeu-be9b).
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class DSSClient(BaseArchiveClient):
    """
    Client for the Dutch Ships and Sailors Linked Data Cloud.

    Handles two data files: GZMVOC ship-level muster records and MDB
    individual crew records from northern Dutch provinces.
    """

    MUSTERS_FILE = "dss_musters.json"
    CREWS_FILE = "dss_crews.json"

    def __init__(self, data_dir: Path | None = None) -> None:
        super().__init__(data_dir)
        self._muster_index: dict[str, dict] | None = None
        self._crew_index: dict[str, dict] | None = None
        self._voyage_muster_index: dict[str, list[dict]] | None = None

    # --- Lazy indexes -------------------------------------------------------

    def _get_musters(self) -> list[dict]:
        return self._load_json(self.MUSTERS_FILE)

    def _get_muster_index(self) -> dict[str, dict]:
        if self._muster_index is None:
            self._muster_index = {m["muster_id"]: m for m in self._get_musters()}
        return self._muster_index

    def _get_voyage_muster_index(self) -> dict[str, list[dict]]:
        if self._voyage_muster_index is None:
            idx: dict[str, list[dict]] = defaultdict(list)
            for m in self._get_musters():
                vid = m.get("das_voyage_id")
                if vid:
                    idx[vid].append(m)
            self._voyage_muster_index = dict(idx)
        return self._voyage_muster_index

    def _get_crews(self) -> list[dict]:
        return self._load_json(self.CREWS_FILE)

    def _get_crew_index(self) -> dict[str, dict]:
        if self._crew_index is None:
            self._crew_index = {c["crew_id"]: c for c in self._get_crews()}
        return self._crew_index

    # --- Abstract method implementations (delegate to crew search) ----------

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
        """Search MDB individual crew records (delegates to search_crews)."""
        return await self.search_crews(
            name=name,
            rank=rank,
            ship_name=ship_name,
            origin=origin,
            date_range=date_range,
            max_results=max_results,
            **kwargs,
        )

    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single crew record by ID (delegates to get_crew_by_id)."""
        return await self.get_crew_by_id(record_id)

    # --- Muster operations (GZMVOC) ----------------------------------------

    async def search_musters(
        self,
        *,
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        location: str | None = None,
        das_voyage_id: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        max_results: int = 50,
        **kwargs: Any,
    ) -> list[dict]:
        """Search GZMVOC ship-level muster records."""
        results = list(self._get_musters())

        if ship_name:
            results = [m for m in results if self._contains(m.get("ship_name"), ship_name)]
        if captain:
            results = [m for m in results if self._contains(m.get("captain"), captain)]
        if location:
            results = [m for m in results if self._contains(m.get("muster_location"), location)]
        if das_voyage_id:
            results = [m for m in results if m.get("das_voyage_id") == das_voyage_id]
        if year_start is not None:
            results = [
                m
                for m in results
                if m.get("muster_date") and int(m["muster_date"][:4]) >= year_start
            ]
        if year_end is not None:
            results = [
                m for m in results if m.get("muster_date") and int(m["muster_date"][:4]) <= year_end
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "muster_date")

        return results[:max_results]

    async def get_muster_by_id(self, muster_id: str) -> dict | None:
        """Retrieve a single muster record by ID."""
        index = self._get_muster_index()
        if muster_id in index:
            return index[muster_id]
        prefixed = (
            f"dss_muster:{muster_id}" if not muster_id.startswith("dss_muster:") else muster_id
        )
        return index.get(prefixed)

    async def get_musters_for_voyage(self, das_voyage_id: str) -> list[dict]:
        """Find muster records linked to a specific DAS voyage."""
        idx = self._get_voyage_muster_index()
        return idx.get(das_voyage_id, [])

    # --- Crew operations (MDB individual records) ---------------------------

    async def search_crews(
        self,
        *,
        name: str | None = None,
        rank: str | None = None,
        ship_name: str | None = None,
        origin: str | None = None,
        date_range: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        destination: str | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> list[dict]:
        """Search MDB individual crew records from northern Dutch provinces."""
        results = list(self._get_crews())

        if name:
            results = [c for c in results if self._contains(c.get("name"), name)]
        if rank:
            results = [
                c
                for c in results
                if self._contains(c.get("rank"), rank)
                or self._contains(c.get("rank_english"), rank)
            ]
        if ship_name:
            results = [c for c in results if self._contains(c.get("ship_name"), ship_name)]
        if origin:
            results = [c for c in results if self._contains(c.get("origin"), origin)]
        if destination:
            results = [c for c in results if self._contains(c.get("destination"), destination)]
        if age_min is not None:
            results = [c for c in results if (c.get("age") or 0) >= age_min]
        if age_max is not None:
            results = [c for c in results if c.get("age") is not None and c["age"] <= age_max]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "muster_date")

        return results[:max_results]

    async def get_crew_by_id(self, crew_id: str) -> dict | None:
        """Retrieve a single MDB crew record by ID."""
        index = self._get_crew_index()
        if crew_id in index:
            return index[crew_id]
        prefixed = f"dss:{crew_id}" if not crew_id.startswith("dss:") else crew_id
        return index.get(prefixed)
