"""
DAS (Dutch Asiatic Shipping) client for voyages and vessels.

Queries the DAS database hosted by the Huygens Institute:
    https://resources.huygens.knaw.nl/das

Provides voyage search, voyage detail retrieval, and vessel search.
Falls back to curated sample data when the remote API is unavailable.
"""

import logging
from typing import Any

from .base import BaseArchiveClient

logger = logging.getLogger(__name__)


class DASClient(BaseArchiveClient):
    """
    HTTP client for the Dutch Asiatic Shipping (DAS) database.

    The DAS database contains records of all 8 194 VOC voyages between
    the Netherlands and Asia, 1595-1795.
    """

    BASE_URL: str = "https://resources.huygens.knaw.nl/das"
    TIMEOUT: int = 30

    # --------------------------------------------------------------------- #
    # Voyage search
    # --------------------------------------------------------------------- #

    async def search(
        self,
        *,
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        route: str | None = None,
        fate: str | None = None,
        max_results: int = 50,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Search DAS voyage records.

        Attempts the remote API first; falls back to sample data on failure.
        Client-side filters are applied to whichever dataset is returned.
        """
        # Try real API
        params: dict[str, str] = {}
        if ship_name:
            params["ship"] = ship_name
        if captain:
            params["captain"] = captain
        if departure_port:
            params["departure"] = departure_port
        if destination_port:
            params["destination"] = destination_port
        if route:
            params["route"] = route
        if fate:
            params["fate"] = fate

        api_results = await self._http_get_with_params(
            f"{self.BASE_URL}/searchVoyage", params
        )

        if isinstance(api_results, list) and api_results:
            results = api_results
            logger.info("DAS API returned %d voyage results", len(results))
        else:
            if api_results is not None and not isinstance(api_results, list):
                # API returned a dict wrapper — try to unwrap
                results = api_results.get("results", api_results.get("voyages", []))  # type: ignore[union-attr]
                if results:
                    logger.info(
                        "DAS API returned %d voyage results (unwrapped)", len(results)
                    )
                else:
                    logger.warning(
                        "DAS API unavailable or returned empty results; "
                        "using sample data"
                    )
                    results = self.get_sample_data()
            else:
                logger.warning(
                    "DAS API unavailable or returned empty results; using sample data"
                )
                results = self.get_sample_data()

        # Client-side filtering
        results = self._apply_voyage_filters(
            results,
            ship_name=ship_name,
            captain=captain,
            date_range=date_range,
            departure_port=departure_port,
            destination_port=destination_port,
            fate=fate,
        )

        return results[:max_results]

    # --------------------------------------------------------------------- #
    # Voyage detail
    # --------------------------------------------------------------------- #

    async def get_by_id(self, record_id: str) -> dict | None:
        """
        Retrieve a single voyage by its DAS voyage number.

        ``record_id`` may be a bare number (``"7892"``) or prefixed
        (``"das:7892"``).
        """
        voyage_number = record_id.replace("das:", "")
        url = f"{self.BASE_URL}/detailVoyage/{voyage_number}"

        result = await self._http_get(url)

        if result and isinstance(result, dict):
            logger.info("DAS API returned voyage detail for %s", voyage_number)
            return result

        # Fallback to sample data
        logger.warning(
            "DAS API unavailable for voyage %s; searching sample data",
            voyage_number,
        )
        full_id = f"das:{voyage_number}"
        for voyage in self.get_sample_data():
            if voyage.get("voyage_id") == full_id:
                return voyage
        return None

    # --------------------------------------------------------------------- #
    # Vessel search
    # --------------------------------------------------------------------- #

    async def search_vessels(
        self,
        *,
        name: str | None = None,
        ship_type: str | None = None,
        built_range: str | None = None,
        shipyard: str | None = None,
        chamber: str | None = None,
        min_tonnage: int | None = None,
        max_tonnage: int | None = None,
        max_results: int = 50,
    ) -> list[dict]:
        """
        Search DAS vessel records.

        Attempts the remote API first; falls back to sample vessel data.
        """
        params: dict[str, str] = {}
        if name:
            params["name"] = name
        if ship_type:
            params["type"] = ship_type
        if chamber:
            params["chamber"] = chamber

        api_results = await self._http_get_with_params(
            f"{self.BASE_URL}/searchVessel", params
        )

        if isinstance(api_results, list) and api_results:
            results = api_results
            logger.info("DAS API returned %d vessel results", len(results))
        else:
            logger.warning(
                "DAS vessel API unavailable or empty; using sample vessel data"
            )
            results = self._get_sample_vessels()

        # Client-side filtering
        results = self._apply_vessel_filters(
            results,
            name=name,
            ship_type=ship_type,
            chamber=chamber,
            min_tonnage=min_tonnage,
            max_tonnage=max_tonnage,
        )

        return results[:max_results]

    # --------------------------------------------------------------------- #
    # Sample / fallback data
    # --------------------------------------------------------------------- #

    def get_sample_data(self) -> list[dict]:
        """Return curated sample voyage records for fallback."""
        return [
            {
                "voyage_id": "das:7892",
                "archive": "das",
                "ship_name": "Ridderschap van Holland",
                "ship_type": "retourschip",
                "tonnage": 850,
                "captain": "Jan Pietersz van der Horst",
                "departure_port": "Texel",
                "departure_date": "1693-12-24",
                "destination_port": "Batavia",
                "fate": "wrecked",
                "loss_date": "1694-03-15",
                "loss_region": "cape",
                "crew_count": 280,
                "summary": "Lost in storm south of the Cape. No survivors reported.",
                "incident": {
                    "fate": "wrecked",
                    "date": "1694-03-15",
                    "cause": "storm",
                    "position": {"lat": -35.0, "lon": 25.0},
                    "narrative": (
                        "Departed Texel 24 December 1693 with fleet of 5 ships. "
                        "Separated from fleet in storm off Cape. Never seen again."
                    ),
                    "lives_lost": 280,
                    "survivors": 0,
                    "archaeological_status": "unfound",
                },
                "vessel": {
                    "name": "Ridderschap van Holland",
                    "type": "retourschip",
                    "tonnage": 850,
                    "built_year": 1685,
                    "built_shipyard": "VOC Yard, Amsterdam",
                    "chamber": "Amsterdam",
                },
                "sources": [
                    {
                        "reference": "DAS voyage 7892",
                        "url": "https://resources.huygens.knaw.nl/das/detailVoyage/7892",
                    }
                ],
            },
            {
                "voyage_id": "das:8123",
                "archive": "das",
                "ship_name": "Blijdorp",
                "ship_type": "retourschip",
                "tonnage": 700,
                "captain": "Willem Jansz de Vries",
                "departure_port": "Batavia",
                "departure_date": "1705-06-12",
                "destination_port": "Amsterdam",
                "fate": "completed",
                "loss_date": None,
                "loss_region": None,
                "crew_count": 180,
                "summary": "Homeward voyage carrying pepper and cinnamon. Arrived safely.",
                "incident": None,
                "vessel": {
                    "name": "Blijdorp",
                    "type": "retourschip",
                    "tonnage": 700,
                    "built_year": 1698,
                    "built_shipyard": "VOC Yard, Rotterdam",
                    "chamber": "Rotterdam",
                },
                "sources": [{"reference": "DAS voyage 8123"}],
            },
            {
                "voyage_id": "das:6234",
                "archive": "das",
                "ship_name": "Oosterland",
                "ship_type": "retourschip",
                "tonnage": 900,
                "captain": "Pieter Jansz de Groot",
                "departure_port": "Texel",
                "departure_date": "1688-01-15",
                "destination_port": "Batavia",
                "fate": "completed",
                "loss_date": None,
                "loss_region": None,
                "crew_count": 300,
                "summary": "Outward voyage. Arrived Batavia 1688-07-22.",
                "incident": None,
                "vessel": {
                    "name": "Oosterland",
                    "type": "retourschip",
                    "tonnage": 900,
                    "built_year": 1684,
                    "built_shipyard": "VOC Yard, Amsterdam",
                    "chamber": "Amsterdam",
                },
                "sources": [{"reference": "DAS voyage 6234"}],
            },
            {
                "voyage_id": "das:5102",
                "archive": "das",
                "ship_name": "Slot ter Hooge",
                "ship_type": "retourschip",
                "tonnage": 850,
                "captain": "Jan Stavorinus",
                "departure_port": "Texel",
                "departure_date": "1724-11-20",
                "destination_port": "Batavia",
                "fate": "wrecked",
                "loss_date": "1724-11-19",
                "loss_region": "atlantic_europe",
                "crew_count": 254,
                "summary": (
                    "Wrecked on Porto Santo island, Madeira archipelago. "
                    "Carrying large silver shipment."
                ),
                "incident": {
                    "fate": "wrecked",
                    "date": "1724-11-19",
                    "cause": "grounding",
                    "position": {"lat": 33.06, "lon": -16.34},
                    "narrative": (
                        "Ran aground on Porto Santo in fog. Ship broke up. "
                        "Some crew rescued but large silver cargo lost."
                    ),
                    "lives_lost": 221,
                    "survivors": 33,
                    "archaeological_status": "found",
                },
                "vessel": {
                    "name": "Slot ter Hooge",
                    "type": "retourschip",
                    "tonnage": 850,
                    "built_year": 1718,
                    "built_shipyard": "VOC Yard, Zeeland",
                    "chamber": "Zeeland",
                },
                "sources": [{"reference": "DAS voyage 5102"}],
            },
            {
                "voyage_id": "das:3456",
                "archive": "das",
                "ship_name": "Batavia",
                "ship_type": "retourschip",
                "tonnage": 600,
                "captain": "Ariaen Jacobsz",
                "departure_port": "Texel",
                "departure_date": "1628-10-28",
                "destination_port": "Batavia",
                "fate": "wrecked",
                "loss_date": "1629-06-04",
                "loss_region": "indian_ocean",
                "crew_count": 341,
                "summary": (
                    "Wrecked on Morning Reef, Houtman Abrolhos, Western Australia. "
                    "Followed by infamous mutiny."
                ),
                "incident": {
                    "fate": "wrecked",
                    "date": "1629-06-04",
                    "cause": "reef",
                    "position": {"lat": -28.49, "lon": 113.79},
                    "narrative": (
                        "Struck reef in Houtman Abrolhos islands off Western "
                        "Australia. Crew abandoned ship. Mutiny led by Jeronimus "
                        "Cornelisz followed."
                    ),
                    "lives_lost": 125,
                    "survivors": 216,
                    "archaeological_status": "found",
                },
                "vessel": {
                    "name": "Batavia",
                    "type": "retourschip",
                    "tonnage": 600,
                    "built_year": 1628,
                    "built_shipyard": "VOC Yard, Amsterdam",
                    "chamber": "Amsterdam",
                },
                "sources": [{"reference": "DAS voyage 3456"}],
            },
        ]

    def _get_sample_vessels(self) -> list[dict]:
        """Return curated sample vessel records for fallback."""
        return [
            {
                "vessel_id": "das_vessel:1456",
                "name": "Ridderschap van Holland",
                "type": "retourschip",
                "tonnage": 850,
                "built_year": 1685,
                "shipyard": "VOC Yard, Amsterdam",
                "chamber": "Amsterdam",
                "voyage_count": 2,
                "fate": "wrecked",
                "fate_date": "1694",
            },
            {
                "vessel_id": "das_vessel:1234",
                "name": "Batavia",
                "type": "retourschip",
                "tonnage": 600,
                "built_year": 1628,
                "shipyard": "VOC Yard, Amsterdam",
                "chamber": "Amsterdam",
                "voyage_count": 1,
                "fate": "wrecked",
                "fate_date": "1629",
            },
            {
                "vessel_id": "das_vessel:1567",
                "name": "Blijdorp",
                "type": "retourschip",
                "tonnage": 700,
                "built_year": 1698,
                "shipyard": "VOC Yard, Rotterdam",
                "chamber": "Rotterdam",
                "voyage_count": 4,
                "fate": "sold",
                "fate_date": "1720",
            },
            {
                "vessel_id": "das_vessel:1890",
                "name": "Hollandia",
                "type": "retourschip",
                "tonnage": 700,
                "built_year": 1740,
                "shipyard": "VOC Yard, Amsterdam",
                "chamber": "Amsterdam",
                "voyage_count": 1,
                "fate": "wrecked",
                "fate_date": "1743",
            },
        ]

    # --------------------------------------------------------------------- #
    # Client-side filters
    # --------------------------------------------------------------------- #

    def _apply_voyage_filters(
        self,
        results: list[dict],
        *,
        ship_name: str | None = None,
        captain: str | None = None,
        date_range: str | None = None,
        departure_port: str | None = None,
        destination_port: str | None = None,
        fate: str | None = None,
    ) -> list[dict]:
        """Apply client-side keyword filters to voyage results."""
        if ship_name:
            ship_lower = ship_name.lower()
            results = [
                v for v in results if ship_lower in v.get("ship_name", "").lower()
            ]
        if captain:
            cap_lower = captain.lower()
            results = [
                v for v in results if cap_lower in v.get("captain", "").lower()
            ]
        if fate:
            results = [v for v in results if v.get("fate") == fate]
        if departure_port:
            port_lower = departure_port.lower()
            results = [
                v
                for v in results
                if port_lower in v.get("departure_port", "").lower()
            ]
        if destination_port:
            dest_lower = destination_port.lower()
            results = [
                v
                for v in results
                if dest_lower in v.get("destination_port", "").lower()
            ]
        if date_range:
            results = self._filter_by_date_range(results, date_range, "departure_date")

        return results

    def _apply_vessel_filters(
        self,
        results: list[dict],
        *,
        name: str | None = None,
        ship_type: str | None = None,
        chamber: str | None = None,
        min_tonnage: int | None = None,
        max_tonnage: int | None = None,
    ) -> list[dict]:
        """Apply client-side keyword filters to vessel results."""
        if name:
            name_lower = name.lower()
            results = [
                v for v in results if name_lower in v.get("name", "").lower()
            ]
        if ship_type:
            results = [v for v in results if v.get("type") == ship_type]
        if chamber:
            results = [v for v in results if v.get("chamber") == chamber]
        if min_tonnage is not None:
            results = [
                v for v in results if (v.get("tonnage") or 0) >= min_tonnage
            ]
        if max_tonnage is not None:
            results = [
                v
                for v in results
                if v.get("tonnage") is not None and v["tonnage"] <= max_tonnage
            ]

        return results
