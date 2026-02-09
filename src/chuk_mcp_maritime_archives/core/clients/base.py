"""
Base class for archive data source clients.

All archive clients share:
- Lazy-loaded JSON data from the local data directory
- In-memory search with keyword filters
- Detail retrieval by record ID
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default data directory relative to the project root
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"


class BaseArchiveClient(ABC):
    """
    Abstract base for archive data source clients.

    Subclasses implement search and get_by_id against locally stored
    JSON data files produced by the download scripts.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or _DEFAULT_DATA_DIR
        self._loaded: dict[str, list[dict]] = {}

    def _load_json(self, filename: str) -> list[dict]:
        """Load a JSON data file, caching the result in memory."""
        if filename in self._loaded:
            return self._loaded[filename]

        path = Path(self._data_dir) / filename
        if not path.exists():
            logger.warning("Data file not found: %s (run scripts/download_das.py)", path)
            self._loaded[filename] = []
            return []

        with open(path) as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.warning("Expected list in %s, got %s", path, type(data).__name__)
            data = []

        self._loaded[filename] = data
        logger.info("Loaded %d records from %s", len(data), path.name)
        return data

    @abstractmethod
    async def search(self, **kwargs: Any) -> list[dict]:
        """Search records with keyword filters. Returns list of record dicts."""
        ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single record by ID. Returns record dict or None."""
        ...

    def _filter_by_date_range(
        self, records: list[dict], date_range: str, date_field: str
    ) -> list[dict]:
        """
        Filter records by date range string.

        Accepts formats: ``YYYY/YYYY`` or ``YYYY-MM-DD/YYYY-MM-DD``.
        """
        parts = date_range.split("/")
        if len(parts) != 2:
            return records

        start_str, end_str = parts
        start_year = int(start_str[:4]) if len(start_str) >= 4 else 0
        end_year = int(end_str[:4]) if len(end_str) >= 4 else 9999

        filtered = []
        for rec in records:
            date_val = rec.get(date_field, "")
            if date_val and len(date_val) >= 4:
                try:
                    record_year = int(date_val[:4])
                except ValueError:
                    continue
                if start_year <= record_year <= end_year:
                    filtered.append(rec)
        return filtered

    @staticmethod
    def _contains(haystack: str | None, needle: str) -> bool:
        """Case-insensitive substring match."""
        if not haystack:
            return False
        return needle.lower() in haystack.lower()
