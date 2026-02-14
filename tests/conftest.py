"""Shared fixtures for chuk-mcp-maritime-archives tests."""

from pathlib import Path

import pytest

from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Mock MCP server — collects registered tools without a real MCP runtime
# ---------------------------------------------------------------------------


class MockMCPServer:
    """Minimal MCP server mock that captures tools registered via @mcp.tool."""

    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def tool(self, fn: object) -> object:
        """Decorator that registers the function and returns it unchanged."""
        self._tools[fn.__name__] = fn  # type: ignore[union-attr]
        return fn

    def get_tool(self, name: str) -> object:
        return self._tools[name]

    def get_tools(self) -> list[object]:
        return list(self._tools.values())

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())


@pytest.fixture
def mock_mcp() -> MockMCPServer:
    return MockMCPServer()


# ---------------------------------------------------------------------------
# ArchiveManager fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager() -> ArchiveManager:
    """Fresh ArchiveManager backed by test fixture data."""
    return ArchiveManager(data_dir=FIXTURES_DIR)


# ---------------------------------------------------------------------------
# Sample data for mocking the ArchiveManager in tool tests
# ---------------------------------------------------------------------------

SAMPLE_VOYAGES = [
    {
        "voyage_id": "das:3456",
        "ship_name": "Batavia",
        "captain": "Ariaen Jacobsz",
        "departure_date": "1628-10-28",
        "departure_port": "Texel",
        "destination_port": "Batavia",
        "fate": "wrecked",
        "particulars": "Wrecked on Houtman Abrolhos, Western Australia",
    },
    {
        "voyage_id": "das:1234",
        "ship_name": "Amsterdam",
        "captain": "Willem Klump",
        "departure_date": "1748-11-15",
        "departure_port": "Texel",
        "destination_port": "Batavia",
        "fate": "wrecked",
        "particulars": "Wrecked off Hastings, England",
    },
    {
        "voyage_id": "das:5678",
        "ship_name": "Ridderschap van Holland",
        "captain": "Pieter de Haze",
        "departure_date": "1694-01-03",
        "departure_port": "Texel",
        "destination_port": "Batavia",
        "fate": "arrived",
        "particulars": "Arrived safely in Batavia",
    },
]

SAMPLE_VESSELS = [
    {
        "vessel_id": "das_vessel:001",
        "name": "Batavia",
        "type": "retourschip",
        "tonnage": 600,
        "chamber": "Amsterdam",
        "voyage_ids": ["das:3456"],
    },
    {
        "vessel_id": "das_vessel:002",
        "name": "Amsterdam",
        "type": "retourschip",
        "tonnage": 700,
        "chamber": "Amsterdam",
        "voyage_ids": ["das:1234"],
    },
]

SAMPLE_CREW = [
    {
        "crew_id": "voc_crew:445892",
        "name": "Jan Pietersz van der Horst",
        "rank": "schipper",
        "ship_name": "Ridderschap van Holland",
        "voyage_id": "das:5678",
        "origin": "Amsterdam",
        "embarkation_date": "1694-01-03",
        "service_end_reason": "returned",
    },
    {
        "crew_id": "voc_crew:445893",
        "name": "Hendrik Janssen",
        "rank": "matroos",
        "ship_name": "Ridderschap van Holland",
        "voyage_id": "das:5678",
        "origin": "Rotterdam",
        "embarkation_date": "1694-01-03",
        "service_end_reason": "died",
    },
]

SAMPLE_CARGO = [
    {
        "cargo_id": "voc_cargo:23456",
        "voyage_id": "das:8123",
        "commodity": "pepper",
        "origin": "Batavia",
        "destination": "Amsterdam",
        "date": "1720-03-15",
        "value_guilders": 187500,
    },
    {
        "cargo_id": "voc_cargo:23457",
        "voyage_id": "das:8123",
        "commodity": "nutmeg",
        "origin": "Banda",
        "destination": "Amsterdam",
        "date": "1720-03-15",
        "value_guilders": 125000,
    },
]

SAMPLE_NARRATIVE_HITS = [
    {
        "record_id": "das:3456",
        "record_type": "voyage",
        "archive": "das",
        "ship_name": "Batavia",
        "date": "1628-10-28",
        "field": "particulars",
        "snippet": "Wrecked on Houtman Abrolhos, Western Australia",
        "match_count": 2,
    },
    {
        "record_id": "eic_wreck:0001",
        "record_type": "wreck",
        "archive": "eic",
        "ship_name": "Earl of Abergavenny",
        "date": "1805-02-05",
        "field": "loss_location",
        "snippet": "Portland Bill, Dorset",
        "match_count": 1,
    },
]

SAMPLE_MUSTERS = [
    {
        "muster_id": "dss_muster:0001",
        "ship_name": "Middelburg",
        "captain": "Jan Pietersz van Hoorn",
        "muster_date": "1720-03-15",
        "muster_location": "Batavia",
        "total_crew": 120,
        "das_voyage_id": "das:1234",
        "archive": "dss",
        "mean_wage_guilders": 12.1,
    },
    {
        "muster_id": "dss_muster:0002",
        "ship_name": "Zeelandia",
        "captain": "Cornelis de Wit",
        "muster_date": "1735-07-22",
        "muster_location": "Makassar",
        "total_crew": 110,
        "das_voyage_id": None,
        "archive": "dss",
        "mean_wage_guilders": 12.0,
    },
]

SAMPLE_WAGE_COMPARISON = {
    "group1_label": "1700-1730",
    "group1_n": 5,
    "group1_mean_wage": 11.5,
    "group1_median_wage": 11.2,
    "group2_label": "1731-1760",
    "group2_n": 8,
    "group2_mean_wage": 13.0,
    "group2_median_wage": 12.8,
    "difference_pct": 13.0,
}

SAMPLE_DEMOGRAPHICS = {
    "total_records": 774200,
    "total_filtered": 774200,
    "group_by": "rank",
    "group_count": 3,
    "groups": [
        {
            "group_key": "matroos",
            "count": 250000,
            "percentage": 32.3,
            "fate_distribution": {"returned": 100000, "died_voyage": 80000, "deserted": 70000},
        },
        {
            "group_key": "soldaat",
            "count": 200000,
            "percentage": 25.8,
            "fate_distribution": {"returned": 80000, "died_asia": 120000},
        },
        {
            "group_key": "schipper",
            "count": 50000,
            "percentage": 6.5,
            "fate_distribution": {"returned": 40000, "died_voyage": 10000},
        },
    ],
    "other_count": 274200,
    "filters_applied": {},
}

SAMPLE_CAREER = {
    "query_name": "Jan Pietersz",
    "query_origin": None,
    "individual_count": 1,
    "total_matches": 3,
    "individuals": [
        {
            "name": "Jan Pietersz van der Horst",
            "origin": "Amsterdam",
            "voyage_count": 3,
            "first_date": "1694-01-03",
            "last_date": "1705-06-10",
            "career_span_years": 11.5,
            "distinct_ships": ["Ridderschap van Holland", "Huis te Manpad", "Zeelandia"],
            "ranks_held": ["schipper", "stuurman"],
            "final_fate": "died_asia",
            "voyages": [
                {
                    "crew_id": "voc_crew:445892",
                    "ship_name": "Ridderschap van Holland",
                    "voyage_id": "das:5678",
                    "rank": "schipper",
                    "embarkation_date": "1694-01-03",
                    "service_end_reason": "returned",
                },
                {
                    "crew_id": "voc_crew:445896",
                    "ship_name": "Huis te Manpad",
                    "voyage_id": "das:7890",
                    "rank": "stuurman",
                    "embarkation_date": "1699-03-15",
                    "service_end_reason": "returned",
                },
            ],
        }
    ],
}

SAMPLE_SURVIVAL = {
    "total_records": 774200,
    "total_with_known_fate": 600000,
    "group_by": "rank",
    "group_count": 3,
    "groups": [
        {
            "group_key": "matroos",
            "total": 200000,
            "survived": 80000,
            "died_voyage": 60000,
            "died_asia": 30000,
            "deserted": 20000,
            "discharged": 10000,
            "survival_rate": 40.0,
            "mortality_rate": 45.0,
            "desertion_rate": 10.0,
        },
        {
            "group_key": "schipper",
            "total": 40000,
            "survived": 30000,
            "died_voyage": 5000,
            "died_asia": 2000,
            "deserted": 1000,
            "discharged": 2000,
            "survival_rate": 75.0,
            "mortality_rate": 17.5,
            "desertion_rate": 2.5,
        },
    ],
    "filters_applied": {},
}

SAMPLE_WRECKS = [
    {
        "wreck_id": "maarer:VOC-0789",
        "voyage_id": "das:3456",
        "ship_name": "Batavia",
        "loss_date": "1629-06-04",
        "loss_cause": "reef",
        "region": "western_australia",
        "status": "found",
        "depth_estimate_m": 5,
        "lives_lost": 125,
        "cargo_value_guilders": 250000,
        "ship_type": "retourschip",
        "tonnage": 600,
        "position": {"lat": -28.49, "lon": 113.79, "uncertainty_km": 0.1},
    },
    {
        "wreck_id": "maarer:VOC-0456",
        "ship_name": "Vergulde Draeck",
        "loss_date": "1656-04-28",
        "loss_cause": "reef",
        "region": "western_australia",
        "status": "found",
        "depth_estimate_m": 8,
        "lives_lost": 68,
        "cargo_value_guilders": 78600,
        "ship_type": "retourschip",
        "tonnage": 500,
        "position": {"lat": -31.01, "lon": 115.22, "uncertainty_km": 0.5},
    },
    {
        "wreck_id": "maarer:VOC-0123",
        "ship_name": "Meermin",
        "loss_date": "1766-02-20",
        "loss_cause": "mutiny",
        "region": "cape",
        "status": "found",
        "depth_estimate_m": 3,
        "lives_lost": 0,
        "cargo_value_guilders": 12000,
        "ship_type": "hoeker",
        "tonnage": 200,
        "position": {"lat": -34.62, "lon": 20.01, "uncertainty_km": 5},
    },
]
