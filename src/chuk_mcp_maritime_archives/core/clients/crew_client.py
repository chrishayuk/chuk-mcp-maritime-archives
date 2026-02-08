"""
VOC Crew (Nationaal Archief) client for crew muster records.

Queries the VOC Opvarenden database at the Nationaal Archief:
    https://www.nationaalarchief.nl/onderzoeken/index/nt00444

Contains personnel records for 774 200 individuals who served on
VOC vessels between 1633 and 1794.
"""

import logging
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class CrewClient(BaseArchiveClient):
    """
    HTTP client for the VOC Opvarenden (crew) database.

    Searches crew muster rolls for personnel records including name,
    origin, rank, pay, and fate.
    """

    BASE_URL: str = "https://www.nationaalarchief.nl/onderzoeken/index/nt00444"
    TIMEOUT: int = 30

    # --------------------------------------------------------------------- #
    # Crew search
    # --------------------------------------------------------------------- #

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
        """
        Search VOC crew muster records.

        Attempts the remote API first; falls back to sample data on failure.
        Client-side filters are applied to whichever dataset is returned.
        """
        # Build API query parameters
        params: dict[str, str] = {}
        if name:
            params["naam"] = name
        if rank:
            params["rang"] = rank
        if ship_name:
            params["schip"] = ship_name
        if origin:
            params["herkomst"] = origin

        api_results = await self._http_get_with_params(
            f"{self.BASE_URL}/zoek", params
        )

        if isinstance(api_results, list) and api_results:
            results = api_results
            logger.info("Crew API returned %d results", len(results))
        elif isinstance(api_results, dict) and api_results:
            results = api_results.get("results", api_results.get("records", []))
            if results:
                logger.info("Crew API returned %d results (unwrapped)", len(results))
            else:
                logger.warning(
                    "Crew API unavailable or returned empty results; "
                    "using sample data"
                )
                results = self.get_sample_data()
        else:
            logger.warning(
                "Crew API unavailable or returned empty results; using sample data"
            )
            results = self.get_sample_data()

        # Client-side filtering
        results = self._apply_crew_filters(
            results,
            name=name,
            rank=rank,
            ship_name=ship_name,
            voyage_id=voyage_id,
            origin=origin,
            date_range=date_range,
            fate=fate,
        )

        return results[:max_results]

    # --------------------------------------------------------------------- #
    # Crew detail
    # --------------------------------------------------------------------- #

    async def get_by_id(self, record_id: str) -> dict | None:
        """
        Retrieve a single crew record by ID.

        ``record_id`` may be a bare number (``"445892"``) or prefixed
        (``"voc_crew:445892"``).
        """
        crew_number = record_id.replace("voc_crew:", "")
        url = f"{self.BASE_URL}/detail/{crew_number}"

        result = await self._http_get(url)

        if result and isinstance(result, dict):
            logger.info("Crew API returned detail for %s", crew_number)
            return result

        # Fallback to sample data
        logger.warning(
            "Crew API unavailable for record %s; searching sample data",
            crew_number,
        )
        full_id = f"voc_crew:{crew_number}"
        for crew in self.get_sample_data():
            if crew.get("crew_id") == full_id:
                return crew
        return None

    # --------------------------------------------------------------------- #
    # Sample / fallback data
    # --------------------------------------------------------------------- #

    def get_sample_data(self) -> list[dict]:
        """Return curated sample crew records for fallback."""
        return [
            {
                "crew_id": "voc_crew:445892",
                "name": "Jan Pietersz van der Horst",
                "rank": "schipper",
                "rank_english": "captain",
                "origin": "Amsterdam",
                "age_at_embarkation": 42,
                "monthly_pay_guilders": 80,
                "embarkation_date": "1693-12-24",
                "service_end_date": "1694-03-15",
                "service_end_reason": "died_voyage",
                "ship_name": "Ridderschap van Holland",
                "voyage_id": "das:7892",
                "notes": "Lost with ship",
            },
            {
                "crew_id": "voc_crew:445893",
                "name": "Hendrick Jansz",
                "rank": "stuurman",
                "rank_english": "first mate",
                "origin": "Enkhuizen",
                "age_at_embarkation": 35,
                "monthly_pay_guilders": 60,
                "embarkation_date": "1693-12-24",
                "service_end_date": "1694-03-15",
                "service_end_reason": "died_voyage",
                "ship_name": "Ridderschap van Holland",
                "voyage_id": "das:7892",
                "notes": "Lost with ship",
            },
            {
                "crew_id": "voc_crew:445894",
                "name": "Pieter de Groot",
                "rank": "bootsman",
                "rank_english": "boatswain",
                "origin": "Rotterdam",
                "age_at_embarkation": 28,
                "monthly_pay_guilders": 36,
                "embarkation_date": "1693-12-24",
                "service_end_date": "1694-03-15",
                "service_end_reason": "died_voyage",
                "ship_name": "Ridderschap van Holland",
                "voyage_id": "das:7892",
                "notes": "Lost with ship",
            },
            {
                "crew_id": "voc_crew:112233",
                "name": "Willem Jansz de Vries",
                "rank": "schipper",
                "rank_english": "captain",
                "origin": "Delft",
                "age_at_embarkation": 45,
                "monthly_pay_guilders": 80,
                "embarkation_date": "1705-06-12",
                "service_end_date": "1706-01-15",
                "service_end_reason": "survived",
                "ship_name": "Blijdorp",
                "voyage_id": "das:8123",
                "notes": "Completed homeward voyage safely",
            },
        ]

    # --------------------------------------------------------------------- #
    # Client-side filters
    # --------------------------------------------------------------------- #

    def _apply_crew_filters(
        self,
        results: list[dict],
        *,
        name: str | None = None,
        rank: str | None = None,
        ship_name: str | None = None,
        voyage_id: str | None = None,
        origin: str | None = None,
        date_range: str | None = None,
        fate: str | None = None,
    ) -> list[dict]:
        """Apply client-side keyword filters to crew results."""
        if name:
            name_lower = name.lower()
            results = [
                c for c in results if name_lower in c.get("name", "").lower()
            ]
        if rank:
            rank_lower = rank.lower()
            results = [
                c for c in results if rank_lower in c.get("rank", "").lower()
            ]
        if ship_name:
            ship_lower = ship_name.lower()
            results = [
                c for c in results if ship_lower in c.get("ship_name", "").lower()
            ]
        if voyage_id:
            results = [c for c in results if c.get("voyage_id") == voyage_id]
        if origin:
            origin_lower = origin.lower()
            results = [
                c for c in results if origin_lower in c.get("origin", "").lower()
            ]
        if fate:
            results = [c for c in results if c.get("service_end_reason") == fate]
        if date_range:
            results = self._filter_by_date_range(
                results, date_range, "embarkation_date"
            )

        return results
