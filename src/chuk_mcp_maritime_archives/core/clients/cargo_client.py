"""
BGB (Boekhouder-Generaal Batavia) client for cargo manifests.

Queries the Bookkeeper-General Batavia database hosted by the
Huygens Institute:
    https://bgb.huygens.knaw.nl/

Contains cargo records for goods shipped between Asia and the
Netherlands, 1700-1795.
"""

import logging
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CargoClient(BaseArchiveClient):
    """
    HTTP client for the Boekhouder-Generaal Batavia (BGB) cargo database.

    Provides search and detail retrieval for VOC cargo manifests.
    """

    BASE_URL: str = "https://bgb.huygens.knaw.nl"
    TIMEOUT: int = 30

    # --------------------------------------------------------------------- #
    # Cargo search
    # --------------------------------------------------------------------- #

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
        """
        Search BGB cargo manifest records.

        Attempts the remote API first; falls back to sample data on failure.
        Client-side filters are applied to whichever dataset is returned.
        """
        # Build API query parameters
        params: dict[str, str] = {}
        if voyage_id:
            params["voyage"] = voyage_id
        if commodity:
            params["commodity"] = commodity
        if origin:
            params["origin"] = origin
        if destination:
            params["destination"] = destination

        api_results = await self._http_get_with_params(
            f"{self.BASE_URL}/api/search", params
        )

        if isinstance(api_results, list) and api_results:
            results = api_results
            logger.info("BGB API returned %d cargo results", len(results))
        elif isinstance(api_results, dict) and api_results:
            results = api_results.get("results", api_results.get("records", []))
            if results:
                logger.info(
                    "BGB API returned %d cargo results (unwrapped)", len(results)
                )
            else:
                logger.warning(
                    "BGB API unavailable or returned empty results; "
                    "using sample data"
                )
                results = self.get_sample_data()
        else:
            logger.warning(
                "BGB API unavailable or returned empty results; using sample data"
            )
            results = self.get_sample_data()

        # Client-side filtering
        results = self._apply_cargo_filters(
            results,
            voyage_id=voyage_id,
            commodity=commodity,
            origin=origin,
            destination=destination,
            date_range=date_range,
            min_value=min_value,
        )

        return results[:max_results]

    # --------------------------------------------------------------------- #
    # Cargo detail
    # --------------------------------------------------------------------- #

    async def get_by_id(self, record_id: str) -> dict | None:
        """
        Retrieve a single cargo record by ID.

        ``record_id`` may be a bare number (``"23456"``) or prefixed
        (``"voc_cargo:23456"``).
        """
        cargo_number = record_id.replace("voc_cargo:", "")
        url = f"{self.BASE_URL}/api/detail/{cargo_number}"

        result = await self._http_get(url)

        if result and isinstance(result, dict):
            logger.info("BGB API returned cargo detail for %s", cargo_number)
            return result

        # Fallback to sample data
        logger.warning(
            "BGB API unavailable for cargo %s; searching sample data",
            cargo_number,
        )
        full_id = f"voc_cargo:{cargo_number}"
        for cargo in self.get_sample_data():
            if cargo.get("cargo_id") == full_id:
                return cargo
        return None

    # --------------------------------------------------------------------- #
    # Cargo manifest by voyage
    # --------------------------------------------------------------------- #

    async def get_manifest(self, voyage_id: str) -> list[dict]:
        """
        Retrieve the full cargo manifest for a single voyage.

        Convenience wrapper around :meth:`search` filtered to one voyage.
        """
        return await self.search(voyage_id=voyage_id)

    # --------------------------------------------------------------------- #
    # Sample / fallback data
    # --------------------------------------------------------------------- #

    def get_sample_data(self) -> list[dict]:
        """Return curated sample cargo records for fallback."""
        return [
            {
                "cargo_id": "voc_cargo:23456",
                "voyage_id": "das:8123",
                "ship_name": "Blijdorp",
                "commodity": "pepper",
                "commodity_dutch": "peper",
                "quantity": 125000,
                "unit": "pounds",
                "weight_kg": 56700,
                "origin": "Malabar",
                "destination": "Amsterdam",
                "value_guilders": 187500,
                "date": "1705-06-12",
            },
            {
                "cargo_id": "voc_cargo:23457",
                "voyage_id": "das:8123",
                "ship_name": "Blijdorp",
                "commodity": "cinnamon",
                "commodity_dutch": "kaneel",
                "quantity": 45000,
                "unit": "pounds",
                "weight_kg": 20400,
                "origin": "Ceylon",
                "destination": "Amsterdam",
                "value_guilders": 112500,
                "date": "1705-06-12",
            },
            {
                "cargo_id": "voc_cargo:23458",
                "voyage_id": "das:8123",
                "ship_name": "Blijdorp",
                "commodity": "textiles",
                "commodity_dutch": "lijnwaden",
                "quantity": 500,
                "unit": "bales",
                "weight_kg": 15000,
                "origin": "Coromandel",
                "destination": "Amsterdam",
                "value_guilders": 75000,
                "date": "1705-06-12",
            },
            {
                "cargo_id": "voc_cargo:10001",
                "voyage_id": "das:5102",
                "ship_name": "Slot ter Hooge",
                "commodity": "silver",
                "commodity_dutch": "zilver",
                "quantity": 20000,
                "unit": "marks",
                "weight_kg": 4900,
                "origin": "Netherlands",
                "destination": "Batavia",
                "value_guilders": 3000000,
                "date": "1724-11-20",
            },
        ]

    # --------------------------------------------------------------------- #
    # Client-side filters
    # --------------------------------------------------------------------- #

    def _apply_cargo_filters(
        self,
        results: list[dict],
        *,
        voyage_id: str | None = None,
        commodity: str | None = None,
        origin: str | None = None,
        destination: str | None = None,
        date_range: str | None = None,
        min_value: float | None = None,
    ) -> list[dict]:
        """Apply client-side keyword filters to cargo results."""
        if voyage_id:
            results = [c for c in results if c.get("voyage_id") == voyage_id]
        if commodity:
            com_lower = commodity.lower()
            results = [
                c for c in results if com_lower in c.get("commodity", "").lower()
            ]
        if origin:
            orig_lower = origin.lower()
            results = [
                c for c in results if orig_lower in c.get("origin", "").lower()
            ]
        if destination:
            dest_lower = destination.lower()
            results = [
                c
                for c in results
                if dest_lower in c.get("destination", "").lower()
            ]
        if min_value is not None:
            results = [
                c for c in results if (c.get("value_guilders") or 0) >= min_value
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "date")

        return results
