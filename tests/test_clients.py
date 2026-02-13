"""Tests for archive client classes using local JSON fixture data."""

from pathlib import Path

import pytest

from chuk_mcp_maritime_archives.core.clients.base import BaseArchiveClient
from chuk_mcp_maritime_archives.core.clients.cargo_client import CargoClient
from chuk_mcp_maritime_archives.core.clients.crew_client import CrewClient
from chuk_mcp_maritime_archives.core.clients.das_client import DASClient
from chuk_mcp_maritime_archives.core.clients.wreck_client import WreckClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# BaseArchiveClient helpers
# ---------------------------------------------------------------------------


class TestContains:
    def test_match(self):
        assert BaseArchiveClient._contains("Batavia", "batavia") is True

    def test_no_match(self):
        assert BaseArchiveClient._contains("Batavia", "Amsterdam") is False

    def test_none_haystack(self):
        assert BaseArchiveClient._contains(None, "test") is False

    def test_empty_haystack(self):
        assert BaseArchiveClient._contains("", "test") is False

    def test_partial_match(self):
        assert BaseArchiveClient._contains("Ridderschap van Holland", "Holland") is True


class TestFilterByDateRange:
    def setup_method(self):
        self.client = DASClient(data_dir=FIXTURES_DIR)
        self.records = [
            {"name": "A", "date": "1620-05-01"},
            {"name": "B", "date": "1700-03-15"},
            {"name": "C", "date": "1780-11-20"},
        ]

    def test_filter_year_range(self):
        result = self.client._filter_by_date_range(self.records, "1650/1750", "date")
        assert len(result) == 1
        assert result[0]["name"] == "B"

    def test_filter_full_date_range(self):
        result = self.client._filter_by_date_range(self.records, "1600-01-01/1700-12-31", "date")
        assert len(result) == 2

    def test_filter_invalid_format(self):
        result = self.client._filter_by_date_range(self.records, "invalid", "date")
        assert len(result) == 3  # returns all

    def test_filter_missing_date_field(self):
        records = [{"name": "A"}, {"name": "B", "date": "1700-01-01"}]
        result = self.client._filter_by_date_range(records, "1600/1800", "date")
        assert len(result) == 1

    def test_filter_empty_date(self):
        records = [{"name": "A", "date": ""}, {"name": "B", "date": "1700-01-01"}]
        result = self.client._filter_by_date_range(records, "1600/1800", "date")
        assert len(result) == 1

    def test_filter_short_date(self):
        records = [{"name": "A", "date": "17"}, {"name": "B", "date": "1700-01-01"}]
        result = self.client._filter_by_date_range(records, "1600/1800", "date")
        assert len(result) == 1


class TestLoadJson:
    def test_load_existing_file(self):
        client = DASClient(data_dir=FIXTURES_DIR)
        data = client._load_json("voyages.json")
        assert len(data) == 3
        assert data[0]["ship_name"] == "Batavia"

    def test_load_missing_file(self):
        client = DASClient(data_dir=FIXTURES_DIR)
        data = client._load_json("nonexistent.json")
        assert data == []

    def test_caching(self):
        client = DASClient(data_dir=FIXTURES_DIR)
        data1 = client._load_json("voyages.json")
        data2 = client._load_json("voyages.json")
        assert data1 is data2  # same object, loaded once

    def test_load_from_nonexistent_dir(self):
        client = DASClient(data_dir=Path("/tmp/nonexistent_dir_12345"))
        data = client._load_json("voyages.json")
        assert data == []


# ---------------------------------------------------------------------------
# DASClient
# ---------------------------------------------------------------------------


class TestDASClient:
    def setup_method(self):
        self.client = DASClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_no_filters(self):
        results = await self.client.search()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_filters_by_name(self):
        results = await self.client.search(ship_name="Batavia")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_filters_by_captain(self):
        results = await self.client.search(captain="Jacobsz")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_fate(self):
        results = await self.client.search(fate="wrecked")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_departure_port(self):
        results = await self.client.search(departure_port="Texel")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_filters_by_destination_port(self):
        results = await self.client.search(destination_port="Batavia")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_filters_by_route(self):
        results = await self.client.search(route="abrolhos")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_filters_by_date_range(self):
        results = await self.client.search(date_range="1700/1800")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Amsterdam"

    @pytest.mark.asyncio
    async def test_search_max_results(self):
        results = await self.client.search(max_results=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        result = await self.client.get_by_id("das:3456")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("3456")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("das:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_vessels_no_filters(self):
        results = await self.client.search_vessels()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_vessels_filters_by_name(self):
        results = await self.client.search_vessels(name="Batavia")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_vessels_filters_by_type(self):
        results = await self.client.search_vessels(ship_type="retourschip")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_vessels_filters_by_chamber(self):
        results = await self.client.search_vessels(chamber="Amsterdam")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_vessels_filters_by_tonnage(self):
        results = await self.client.search_vessels(min_tonnage=650, max_tonnage=800)
        assert len(results) == 1
        assert results[0]["name"] == "Amsterdam"

    @pytest.mark.asyncio
    async def test_search_vessels_min_tonnage_excludes_none(self):
        results = await self.client.search_vessels(min_tonnage=1)
        assert all(v.get("tonnage") is not None for v in results)

    @pytest.mark.asyncio
    async def test_search_vessels_max_tonnage_excludes_none(self):
        results = await self.client.search_vessels(max_tonnage=1000)
        assert all(v.get("tonnage") is not None and v["tonnage"] <= 1000 for v in results)

    @pytest.mark.asyncio
    async def test_get_vessel_by_id(self):
        result = await self.client.get_vessel_by_id("das_vessel:001")
        assert result is not None
        assert result["name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_vessel_by_id_without_prefix(self):
        result = await self.client.get_vessel_by_id("001")
        assert result is not None
        assert result["name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_vessel_by_id_not_found(self):
        result = await self.client.get_vessel_by_id("das_vessel:999")
        assert result is None


# ---------------------------------------------------------------------------
# CrewClient
# ---------------------------------------------------------------------------


class TestCrewClient:
    def setup_method(self):
        self.client = CrewClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_no_filters(self):
        results = await self.client.search()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_name(self):
        results = await self.client.search(name="Pietersz")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_rank(self):
        results = await self.client.search(rank="matroos")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_ship_name(self):
        results = await self.client.search(ship_name="Ridderschap")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_voyage_id(self):
        results = await self.client.search(voyage_id="das:5678")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_origin(self):
        results = await self.client.search(origin="Amsterdam")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_fate(self):
        results = await self.client.search(fate="died")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_date_range(self):
        results = await self.client.search(date_range="1690/1700")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_no_match(self):
        results = await self.client.search(name="Nonexistent")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_max_results(self):
        results = await self.client.search(max_results=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_indexes_cached(self):
        """Second search uses cached indexes (early return in _ensure_indexes)."""
        await self.client.search()
        # Index is now built; second call triggers the early return
        results = await self.client.search(name="Pietersz")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        result = await self.client.get_by_id("voc_crew:445892")
        assert result is not None
        assert result["name"] == "Jan Pietersz van der Horst"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("voc_crew:999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_empty_file(self):
        """get_by_id returns None when crew file is empty."""
        client = CrewClient(data_dir=Path("/tmp/nonexistent_crew_dir_12345"))
        result = await client.get_by_id("voc_crew:445892")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_empty_file(self):
        """search returns [] when crew file is empty."""
        client = CrewClient(data_dir=Path("/tmp/nonexistent_crew_dir_12345"))
        results = await client.search()
        assert results == []

    @pytest.mark.asyncio
    async def test_ensure_indexes_handles_missing_fields(self):
        """_ensure_indexes skips records missing voyage_id or crew_id."""
        client = CrewClient(data_dir=FIXTURES_DIR)
        records = [
            {"name": "No IDs at all"},
            {"crew_id": "c1", "name": "Has crew_id only"},
            {"voyage_id": "v1", "name": "Has voyage_id only"},
        ]
        client._ensure_indexes(records)
        assert client._id_index is not None
        assert "c1" in client._id_index
        assert client._voyage_index is not None
        assert "v1" in client._voyage_index

    @pytest.mark.asyncio
    async def test_get_by_id_fallback_scan(self):
        """get_by_id falls back to linear scan when _id_index is None."""
        client = CrewClient(data_dir=FIXTURES_DIR)
        # Load records and build indexes, then force _id_index to None
        await client.search()
        client._id_index = None
        result = await client.get_by_id("voc_crew:445892")
        assert result is not None
        assert result["name"] == "Jan Pietersz van der Horst"

    @pytest.mark.asyncio
    async def test_get_by_id_fallback_scan_not_found(self):
        """get_by_id fallback scan returns None if not found."""
        client = CrewClient(data_dir=FIXTURES_DIR)
        await client.search()
        client._id_index = None
        result = await client.get_by_id("voc_crew:nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_voyage_id_without_index(self):
        """voyage_id filter falls back to linear scan without index."""
        client = CrewClient(data_dir=FIXTURES_DIR)
        # Preload records & build indexes, then null out voyage index
        await client.search()
        client._voyage_index = None
        results = await client.search(voyage_id="das:5678")
        assert len(results) == 2


# ---------------------------------------------------------------------------
# CargoClient
# ---------------------------------------------------------------------------


class TestCargoClient:
    def setup_method(self):
        self.client = CargoClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_no_filters(self):
        results = await self.client.search()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_voyage_id(self):
        results = await self.client.search(voyage_id="das:8123")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_commodity(self):
        results = await self.client.search(commodity="pepper")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_origin(self):
        results = await self.client.search(origin="Batavia")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_destination(self):
        results = await self.client.search(destination="Amsterdam")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_min_value(self):
        results = await self.client.search(min_value=150000)
        assert len(results) == 1
        assert results[0]["commodity"] == "pepper"

    @pytest.mark.asyncio
    async def test_search_filters_by_date_range(self):
        results = await self.client.search(date_range="1720/1720")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_no_match(self):
        results = await self.client.search(voyage_id="das:9999")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        result = await self.client.get_by_id("voc_cargo:23456")
        assert result is not None
        assert result["commodity"] == "pepper"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("voc_cargo:999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_manifest(self):
        results = await self.client.get_manifest("das:8123")
        assert len(results) == 2


# ---------------------------------------------------------------------------
# WreckClient
# ---------------------------------------------------------------------------


class TestWreckClient:
    def setup_method(self):
        self.client = WreckClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_no_filters(self):
        results = await self.client.search()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_filters_by_ship_name(self):
        results = await self.client.search(ship_name="Batavia")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_cause(self):
        results = await self.client.search(cause="reef")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_filters_by_status(self):
        results = await self.client.search(status="found")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_filters_by_region(self):
        results = await self.client.search(region="cape")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_filters_by_depth(self):
        results = await self.client.search(min_depth_m=3, max_depth_m=6)
        assert len(results) == 2  # Batavia (5m) and Meermin (3m)

    @pytest.mark.asyncio
    async def test_search_filters_by_cargo_value(self):
        results = await self.client.search(min_cargo_value=100000)
        assert len(results) == 1
        assert results[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_filters_by_date_range(self):
        results = await self.client.search(date_range="1600/1650")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_max_results(self):
        results = await self.client.search(max_results=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        result = await self.client.get_by_id("maarer:VOC-0789")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("VOC-0789")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("maarer:NONE")
        assert result is None
