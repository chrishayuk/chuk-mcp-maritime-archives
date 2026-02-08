"""
MAARER wreck database client for shipwreck and loss records.

The MAARER (Maritime Archaeological Research) database is a compiled
dataset combining wreck position data from DAS, archaeological surveys,
and historical sources covering VOC losses 1595-1795.

Because MAARER is a compiled database (not a live API), this client
attempts a data endpoint and gracefully falls back to curated sample
records.
"""

import logging
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class WreckClient(BaseArchiveClient):
    """
    Client for the MAARER VOC wreck database.

    Provides search and detail retrieval for shipwreck and loss records
    including position, depth, cause, and archaeological status.
    """

    BASE_URL: str = "https://resources.huygens.knaw.nl/das"
    TIMEOUT: int = 30

    # --------------------------------------------------------------------- #
    # Wreck search
    # --------------------------------------------------------------------- #

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
        """
        Search MAARER wreck records.

        Attempts the remote data endpoint first; falls back to sample data
        on failure.  Client-side filters are applied to whichever dataset
        is returned.
        """
        # Try remote data endpoint
        params: dict[str, str] = {}
        if ship_name:
            params["ship"] = ship_name
        if region:
            params["region"] = region
        if cause:
            params["cause"] = cause
        if status:
            params["status"] = status

        api_results = await self._http_get_with_params(
            f"{self.BASE_URL}/searchWreck", params
        )

        if isinstance(api_results, list) and api_results:
            results = api_results
            logger.info("MAARER endpoint returned %d wreck results", len(results))
        elif isinstance(api_results, dict) and api_results:
            results = api_results.get("results", api_results.get("wrecks", []))
            if results:
                logger.info(
                    "MAARER endpoint returned %d wreck results (unwrapped)",
                    len(results),
                )
            else:
                logger.warning(
                    "MAARER endpoint unavailable or returned empty results; "
                    "using sample data"
                )
                results = self.get_sample_data()
        else:
            logger.warning(
                "MAARER endpoint unavailable or returned empty results; "
                "using sample data"
            )
            results = self.get_sample_data()

        # Client-side filtering
        results = self._apply_wreck_filters(
            results,
            ship_name=ship_name,
            date_range=date_range,
            region=region,
            cause=cause,
            status=status,
            min_depth_m=min_depth_m,
            max_depth_m=max_depth_m,
            min_cargo_value=min_cargo_value,
        )

        return results[:max_results]

    # --------------------------------------------------------------------- #
    # Wreck detail
    # --------------------------------------------------------------------- #

    async def get_by_id(self, record_id: str) -> dict | None:
        """
        Retrieve a single wreck record by ID.

        ``record_id`` may be a bare code (``"VOC-0456"``) or prefixed
        (``"maarer:VOC-0456"``).
        """
        wreck_code = record_id.replace("maarer:", "")
        url = f"{self.BASE_URL}/detailWreck/{wreck_code}"

        result = await self._http_get(url)

        if result and isinstance(result, dict):
            logger.info("MAARER endpoint returned wreck detail for %s", wreck_code)
            return result

        # Fallback to sample data
        logger.warning(
            "MAARER endpoint unavailable for wreck %s; searching sample data",
            wreck_code,
        )
        full_id = f"maarer:{wreck_code}"
        for wreck in self.get_sample_data():
            if wreck.get("wreck_id") == full_id:
                return wreck
        return None

    # --------------------------------------------------------------------- #
    # Sample / fallback data
    # --------------------------------------------------------------------- #

    def get_sample_data(self) -> list[dict]:
        """Return curated sample wreck records for fallback."""
        return [
            {
                "wreck_id": "maarer:VOC-0456",
                "voyage_id": "das:7892",
                "archive": "maarer",
                "ship_name": "Ridderschap van Holland",
                "ship_type": "retourschip",
                "tonnage": 850,
                "loss_date": "1694-03-15",
                "loss_cause": "storm",
                "region": "cape",
                "position": {"lat": -35.0, "lon": 25.0, "uncertainty_km": 100},
                "depth_estimate_m": 3200,
                "status": "unfound",
                "cargo_value_guilders": 150000,
                "lives_lost": 280,
                "archaeological_notes": "Deep water location makes discovery unlikely.",
            },
            {
                "wreck_id": "maarer:VOC-0123",
                "voyage_id": "das:5102",
                "archive": "maarer",
                "ship_name": "Slot ter Hooge",
                "ship_type": "retourschip",
                "tonnage": 850,
                "loss_date": "1724-11-19",
                "loss_cause": "grounding",
                "region": "atlantic_europe",
                "position": {"lat": 33.06, "lon": -16.34, "uncertainty_km": 2},
                "depth_estimate_m": 15,
                "status": "found",
                "cargo_value_guilders": 3000000,
                "lives_lost": 221,
                "archaeological_notes": (
                    "Located 1970s. Silver cargo partially recovered."
                ),
            },
            {
                "wreck_id": "maarer:VOC-0789",
                "voyage_id": "das:3456",
                "archive": "maarer",
                "ship_name": "Batavia",
                "ship_type": "retourschip",
                "tonnage": 600,
                "loss_date": "1629-06-04",
                "loss_cause": "reef",
                "region": "indian_ocean",
                "position": {"lat": -28.49, "lon": 113.79, "uncertainty_km": 0.1},
                "depth_estimate_m": 5,
                "status": "found",
                "cargo_value_guilders": 250000,
                "lives_lost": 125,
                "archaeological_notes": (
                    "Found 1963. Extensively excavated. Hull sections in "
                    "Western Australian Museum."
                ),
            },
            {
                "wreck_id": "maarer:VOC-0234",
                "voyage_id": None,
                "archive": "maarer",
                "ship_name": "Bennebroek",
                "ship_type": "retourschip",
                "tonnage": 750,
                "loss_date": "1694-03-16",
                "loss_cause": "storm",
                "region": "cape",
                "position": {"lat": -34.5, "lon": 24.0, "uncertainty_km": 150},
                "depth_estimate_m": 2800,
                "status": "unfound",
                "cargo_value_guilders": None,
                "lives_lost": 0,
                "archaeological_notes": (
                    "Same fleet as Ridderschap, survived storm but damaged."
                ),
            },
            {
                "wreck_id": "maarer:VOC-0567",
                "voyage_id": None,
                "archive": "maarer",
                "ship_name": "Hollandia",
                "ship_type": "retourschip",
                "tonnage": 700,
                "loss_date": "1743-07-13",
                "loss_cause": "reef",
                "region": "atlantic_europe",
                "position": {"lat": 49.87, "lon": -6.43, "uncertainty_km": 0.5},
                "depth_estimate_m": 30,
                "status": "found",
                "cargo_value_guilders": 1500000,
                "lives_lost": 276,
                "archaeological_notes": (
                    "Found 1971 off Isles of Scilly. Silver cargo recovered. "
                    "Lower hull well preserved."
                ),
            },
        ]

    # --------------------------------------------------------------------- #
    # Client-side filters
    # --------------------------------------------------------------------- #

    def _apply_wreck_filters(
        self,
        results: list[dict],
        *,
        ship_name: str | None = None,
        date_range: str | None = None,
        region: str | None = None,
        cause: str | None = None,
        status: str | None = None,
        min_depth_m: float | None = None,
        max_depth_m: float | None = None,
        min_cargo_value: float | None = None,
    ) -> list[dict]:
        """Apply client-side keyword filters to wreck results."""
        if ship_name:
            name_lower = ship_name.lower()
            results = [
                w for w in results if name_lower in w.get("ship_name", "").lower()
            ]
        if region:
            results = [w for w in results if w.get("region") == region]
        if cause:
            results = [w for w in results if w.get("loss_cause") == cause]
        if status:
            results = [w for w in results if w.get("status") == status]
        if min_depth_m is not None:
            results = [
                w for w in results if (w.get("depth_estimate_m") or 0) >= min_depth_m
            ]
        if max_depth_m is not None:
            results = [
                w
                for w in results
                if w.get("depth_estimate_m") is not None
                and w["depth_estimate_m"] <= max_depth_m
            ]
        if min_cargo_value is not None:
            results = [
                w
                for w in results
                if (w.get("cargo_value_guilders") or 0) >= min_cargo_value
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "loss_date")

        return results
