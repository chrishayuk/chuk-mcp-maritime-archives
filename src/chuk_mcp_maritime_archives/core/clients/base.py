"""
Base class for archive data source clients.

All archive clients share:
- async search() with keyword filters
- async get_by_id() for detail retrieval
- HTTP helper using urllib.request (no external deps)
- Graceful degradation when API is unavailable
"""

import asyncio
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseArchiveClient(ABC):
    """
    Abstract base for archive data source HTTP clients.

    Subclasses implement search and get_by_id against specific archive APIs.
    HTTP calls are run in threads via asyncio.to_thread to stay non-blocking.
    """

    BASE_URL: str = ""
    TIMEOUT: int = 30

    async def _http_get(self, url: str) -> dict | list | None:
        """Make a GET request and return parsed JSON, or None on failure."""

        def _fetch() -> dict | list | None:
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "chuk-mcp-maritime-archives/0.1.0",
                    },
                )
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                    return json.loads(resp.read().decode())
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                OSError,
            ) as e:
                logger.warning("HTTP request failed for %s: %s", url, e)
                return None
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON from %s: %s", url, e)
                return None

        return await asyncio.to_thread(_fetch)

    async def _http_get_with_params(
        self, base_url: str, params: dict[str, str]
    ) -> dict | list | None:
        """Make a GET request with query parameters."""
        query = urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )
        url = f"{base_url}?{query}" if query else base_url
        return await self._http_get(url)

    @abstractmethod
    async def search(self, **kwargs: Any) -> list[dict]:
        """Search records with keyword filters. Returns list of record dicts."""
        ...

    @abstractmethod
    async def get_by_id(self, record_id: str) -> dict | None:
        """Retrieve a single record by ID. Returns record dict or None."""
        ...

    @abstractmethod
    def get_sample_data(self) -> list[dict]:
        """Return sample/fallback data for when API is unavailable."""
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
                record_year = int(date_val[:4])
                if start_year <= record_year <= end_year:
                    filtered.append(rec)
        return filtered
