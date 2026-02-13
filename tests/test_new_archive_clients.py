"""Tests for archive clients: EIC, Carreira, Galleon, SOIC, UKHO, NOAA, DSS."""

from pathlib import Path

import pytest

from chuk_mcp_maritime_archives.core.clients.dss_client import DSSClient
from chuk_mcp_maritime_archives.core.clients.eic_client import EICClient
from chuk_mcp_maritime_archives.core.clients.carreira_client import CarreiraClient
from chuk_mcp_maritime_archives.core.clients.galleon_client import GalleonClient
from chuk_mcp_maritime_archives.core.clients.noaa_client import NOAAClient
from chuk_mcp_maritime_archives.core.clients.soic_client import SOICClient
from chuk_mcp_maritime_archives.core.clients.ukho_client import UKHOClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# EIC Client
# ---------------------------------------------------------------------------


class TestEICClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = EICClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search()
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search(ship_name="Abergavenny")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_search_by_captain(self):
        results = await self.client.search(captain="Wordsworth")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_fate(self):
        results = await self.client.search(fate="wrecked")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_company_division(self):
        results = await self.client.search(company_division="East India Trade")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search(date_range="1800/1810")
        assert len(results) == 2  # Abergavenny 1805 + Hindostan 1803
        ids = {r["voyage_id"] for r in results}
        assert "eic:0001" in ids
        assert "eic:0002" in ids

    @pytest.mark.asyncio
    async def test_search_by_departure_port(self):
        results = await self.client.search(departure_port="Portsmouth")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_destination_port(self):
        results = await self.client.search(destination_port="Bengal")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_search_by_route(self):
        results = await self.client.search(route="portland")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_search_max_results(self):
        results = await self.client.search(max_results=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        result = await self.client.get_by_id("eic:0001")
        assert result is not None
        assert result["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("eic:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_cached_index(self):
        """Second call uses cached index."""
        result1 = await self.client.get_by_id("eic:0001")
        result2 = await self.client.get_by_id("eic:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_wrecks_by_name(self):
        results = await self.client.search_wrecks(ship_name="Grosvenor")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_cause(self):
        results = await self.client.search_wrecks(cause="grounding")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self):
        results = await self.client.search_wrecks(status="found")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="cape")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_depth(self):
        results = await self.client.search_wrecks(min_depth_m=10)
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_max_depth(self):
        results = await self.client.search_wrecks(max_depth_m=8)
        assert len(results) == 1
        assert results[0]["ship_name"] == "Grosvenor"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_cargo_value(self):
        results = await self.client.search_wrecks(min_cargo_value=999999)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_wrecks_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1800/1810")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("eic_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_cached_index(self):
        """Second call uses cached wreck index."""
        result1 = await self.client.get_wreck_by_id("eic_wreck:0001")
        result2 = await self.client.get_wreck_by_id("eic_wreck:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("eic:0001")
        assert result is not None
        assert result["wreck_id"] == "eic_wreck:0001"

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id_not_found(self):
        result = await self.client.get_wreck_by_voyage_id("eic:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        voyages = await self.client.search()
        for v in voyages:
            assert v["archive"] == "eic"
        wrecks = await self.client.search_wrecks()
        for w in wrecks:
            assert w["archive"] == "eic"


# ---------------------------------------------------------------------------
# Carreira Client
# ---------------------------------------------------------------------------


class TestCarreiraClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = CarreiraClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search(ship_name="Gabriel")
        assert len(results) == 1
        assert results[0]["captain"] == "Vasco da Gama"

    @pytest.mark.asyncio
    async def test_search_by_armada_year(self):
        results = await self.client.search(armada_year=1497)
        assert len(results) == 1
        assert results[0]["voyage_id"] == "carreira:0001"

    @pytest.mark.asyncio
    async def test_search_by_fleet_commander(self):
        results = await self.client.search(fleet_commander="Gama")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_captain(self):
        results = await self.client.search(captain="Vasco da Gama")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_departure_port(self):
        results = await self.client.search(departure_port="Lisbon")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_destination_port(self):
        results = await self.client.search(destination_port="Calicut")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_route(self):
        results = await self.client.search(route="cape")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Sao Gabriel"

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search(date_range="1490/1500")
        assert len(results) == 1
        assert results[0]["voyage_id"] == "carreira:0001"

    @pytest.mark.asyncio
    async def test_search_by_fate(self):
        results = await self.client.search(fate="wrecked")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        result = await self.client.get_by_id("carreira:0001")
        assert result is not None
        assert result["captain"] == "Vasco da Gama"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("carreira:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_cached_index(self):
        result1 = await self.client.get_by_id("carreira:0001")
        result2 = await self.client.get_by_id("carreira:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["ship_name"] == "Sao Joao"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_name(self):
        results = await self.client.search_wrecks(ship_name="Sao Joao")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_cause(self):
        results = await self.client.search_wrecks(cause="storm")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self):
        results = await self.client.search_wrecks(status="unfound")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="cape")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_depth(self):
        results = await self.client.search_wrecks(min_depth_m=10)
        assert len(results) == 0  # depth is null

    @pytest.mark.asyncio
    async def test_search_wrecks_by_max_depth(self):
        results = await self.client.search_wrecks(max_depth_m=100)
        assert len(results) == 0  # depth is null

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_cargo_value(self):
        results = await self.client.search_wrecks(min_cargo_value=999999)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_wrecks_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1550/1560")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("carreira_wreck:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_cached_index(self):
        result1 = await self.client.get_wreck_by_id("carreira_wreck:0001")
        result2 = await self.client.get_wreck_by_id("carreira_wreck:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("carreira:0002")
        assert result is not None
        assert result["ship_name"] == "Sao Joao"

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id_not_found(self):
        result = await self.client.get_wreck_by_voyage_id("carreira:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        voyages = await self.client.search()
        for v in voyages:
            assert v["archive"] == "carreira"


# ---------------------------------------------------------------------------
# Galleon Client
# ---------------------------------------------------------------------------


class TestGalleonClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = GalleonClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search(ship_name="San Diego")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_captain(self):
        results = await self.client.search(captain="Morga")
        assert len(results) == 1
        assert results[0]["ship_name"] == "San Diego"

    @pytest.mark.asyncio
    async def test_search_by_departure_port(self):
        results = await self.client.search(departure_port="Manila")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_destination_port(self):
        results = await self.client.search(destination_port="Acapulco")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_route(self):
        results = await self.client.search(route="cebu")
        assert len(results) == 1
        assert results[0]["ship_name"] == "San Pablo"

    @pytest.mark.asyncio
    async def test_search_by_trade_direction(self):
        results = await self.client.search(trade_direction="westbound")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search(date_range="1560/1570")
        assert len(results) == 1
        assert results[0]["ship_name"] == "San Pablo"

    @pytest.mark.asyncio
    async def test_search_by_fate(self):
        results = await self.client.search(fate="completed")
        assert len(results) == 1
        assert results[0]["ship_name"] == "San Pablo"

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        result = await self.client.get_by_id("galleon:0001")
        assert result is not None
        assert result["ship_name"] == "San Pablo"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("galleon:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_cached_index(self):
        result1 = await self.client.get_by_id("galleon:0001")
        result2 = await self.client.get_by_id("galleon:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["loss_cause"] == "battle"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_name(self):
        results = await self.client.search_wrecks(ship_name="San Diego")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_cause(self):
        results = await self.client.search_wrecks(cause="battle")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self):
        results = await self.client.search_wrecks(status="found")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="philippine_sea")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_depth(self):
        results = await self.client.search_wrecks(min_depth_m=50)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_max_depth(self):
        results = await self.client.search_wrecks(max_depth_m=60)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_cargo_value(self):
        results = await self.client.search_wrecks(min_cargo_value=999999)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_wrecks_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1600/1610")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("galleon_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "San Diego"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_not_found(self):
        result = await self.client.get_wreck_by_id("galleon_wreck:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_cached_index(self):
        result1 = await self.client.get_wreck_by_id("galleon_wreck:0001")
        result2 = await self.client.get_wreck_by_id("galleon_wreck:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("galleon:0002")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id_not_found(self):
        result = await self.client.get_wreck_by_voyage_id("galleon:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        voyages = await self.client.search()
        for v in voyages:
            assert v["archive"] == "galleon"


# ---------------------------------------------------------------------------
# SOIC Client
# ---------------------------------------------------------------------------


class TestSOICClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = SOICClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search(ship_name="Gotheborg")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_captain(self):
        results = await self.client.search(captain="Anckarhielm")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_fate(self):
        results = await self.client.search(fate="wrecked")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_departure_port(self):
        results = await self.client.search(departure_port="Gothenburg")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_destination(self):
        results = await self.client.search(destination_port="Canton")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_route(self):
        results = await self.client.search(route="gothenburg")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search(date_range="1730/1735")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Fredericus Rex Sueciae"

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        result = await self.client.get_by_id("soic:0001")
        assert result is not None
        assert result["ship_name"] == "Fredericus Rex Sueciae"

    @pytest.mark.asyncio
    async def test_get_by_id_without_prefix(self):
        result = await self.client.get_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("soic:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_cached_index(self):
        result1 = await self.client.get_by_id("soic:0001")
        result2 = await self.client.get_by_id("soic:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["ship_name"] == "Gotheborg"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_name(self):
        results = await self.client.search_wrecks(ship_name="Gotheborg")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_cause(self):
        results = await self.client.search_wrecks(cause="grounding")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self):
        results = await self.client.search_wrecks(status="found")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="north_sea")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_depth(self):
        results = await self.client.search_wrecks(min_depth_m=5)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_max_depth(self):
        results = await self.client.search_wrecks(max_depth_m=10)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_min_cargo_value(self):
        results = await self.client.search_wrecks(min_cargo_value=999999)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_wrecks_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1740/1750")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("soic_wreck:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_not_found(self):
        result = await self.client.get_wreck_by_id("soic_wreck:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_cached_index(self):
        result1 = await self.client.get_wreck_by_id("soic_wreck:0001")
        result2 = await self.client.get_wreck_by_id("soic_wreck:0001")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("soic:0002")
        assert result is not None
        assert result["wreck_id"] == "soic_wreck:0001"

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id_not_found(self):
        result = await self.client.get_wreck_by_voyage_id("soic:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        voyages = await self.client.search()
        for v in voyages:
            assert v["archive"] == "soic"
        wrecks = await self.client.search_wrecks()
        for w in wrecks:
            assert w["archive"] == "soic"


# ---------------------------------------------------------------------------
# UKHO Client (Wrecks Only)
# ---------------------------------------------------------------------------


class TestUKHOClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = UKHOClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search_wrecks()
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search_wrecks(ship_name="Birkenhead")
        assert len(results) == 1
        assert results[0]["ship_name"] == "HMS Birkenhead"

    @pytest.mark.asyncio
    async def test_search_by_region(self):
        results = await self.client.search_wrecks(region="cape")
        assert len(results) == 1
        assert results[0]["wreck_id"] == "ukho_wreck:00001"

    @pytest.mark.asyncio
    async def test_search_by_cause(self):
        results = await self.client.search_wrecks(cause="collision")
        assert len(results) == 1
        assert results[0]["ship_name"] == "SS Mendi"

    @pytest.mark.asyncio
    async def test_search_by_depth_min(self):
        results = await self.client.search_wrecks(min_depth_m=30)
        assert len(results) == 2  # Birkenhead (30) + San Diego (52)

    @pytest.mark.asyncio
    async def test_search_by_depth_max(self):
        results = await self.client.search_wrecks(max_depth_m=10)
        assert len(results) == 1  # Batavia (5)

    @pytest.mark.asyncio
    async def test_search_by_flag(self):
        results = await self.client.search_wrecks(flag="UK")
        assert len(results) == 2  # Birkenhead + Mendi

    @pytest.mark.asyncio
    async def test_search_by_vessel_type(self):
        results = await self.client.search_wrecks(vessel_type="galleon")
        assert len(results) == 1
        assert results[0]["ship_name"] == "San Diego"

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1900/1920")
        assert len(results) == 1
        assert results[0]["ship_name"] == "SS Mendi"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("ukho_wreck:00001")
        assert result is not None
        assert result["ship_name"] == "HMS Birkenhead"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("00001")
        assert result is not None
        assert result["ship_name"] == "HMS Birkenhead"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_not_found(self):
        result = await self.client.get_wreck_by_id("ukho_wreck:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_delegates_to_search_wrecks(self):
        """search() should return same results as search_wrecks()."""
        via_search = await self.client.search()
        via_wrecks = await self.client.search_wrecks()
        assert len(via_search) == len(via_wrecks)

    @pytest.mark.asyncio
    async def test_get_by_id_delegates_to_get_wreck_by_id(self):
        """get_by_id() should return same result as get_wreck_by_id()."""
        via_get = await self.client.get_by_id("ukho_wreck:00001")
        via_wreck = await self.client.get_wreck_by_id("ukho_wreck:00001")
        assert via_get == via_wreck

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        wrecks = await self.client.search_wrecks()
        for w in wrecks:
            assert w["archive"] == "ukho"

    @pytest.mark.asyncio
    async def test_max_results(self):
        results = await self.client.search_wrecks(max_results=2)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# NOAA Client
# ---------------------------------------------------------------------------


class TestNOAAClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = NOAAClient(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_all(self):
        results = await self.client.search_wrecks()
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_by_ship_name(self):
        results = await self.client.search_wrecks(ship_name="Monitor")
        assert len(results) == 1
        assert results[0]["ship_name"] == "USS Monitor"

    @pytest.mark.asyncio
    async def test_search_by_region(self):
        results = await self.client.search_wrecks(region="gulf_of_mexico")
        assert len(results) == 1
        assert results[0]["ship_name"] == "SS Selma"

    @pytest.mark.asyncio
    async def test_search_by_cause(self):
        results = await self.client.search_wrecks(cause="scuttled")
        assert len(results) == 1
        assert results[0]["ship_name"] == "SS Selma"

    @pytest.mark.asyncio
    async def test_search_by_depth_range(self):
        results = await self.client.search_wrecks(min_depth_m=50, max_depth_m=200)
        assert len(results) == 2  # USS Monitor (73) + Edmund Fitzgerald (160)

    @pytest.mark.asyncio
    async def test_search_by_flag(self):
        results = await self.client.search_wrecks(flag="US")
        assert len(results) == 4  # All except "Unknown barge" which has null flag

    @pytest.mark.asyncio
    async def test_search_by_vessel_type(self):
        results = await self.client.search_wrecks(vessel_type="bulk carrier")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Edmund Fitzgerald"

    @pytest.mark.asyncio
    async def test_search_by_gp_quality(self):
        results = await self.client.search_wrecks(gp_quality=1)
        assert len(results) == 2  # Monitor (1) + Fitzgerald (1)

    @pytest.mark.asyncio
    async def test_search_by_gp_quality_poor(self):
        results = await self.client.search_wrecks(gp_quality=4)
        assert len(results) == 1
        assert results[0]["ship_name"] == "Unknown barge"

    @pytest.mark.asyncio
    async def test_search_by_date_range(self):
        results = await self.client.search_wrecks(date_range="1970/1980")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Edmund Fitzgerald"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("noaa_wreck:00001")
        assert result is not None
        assert result["ship_name"] == "USS Monitor"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_without_prefix(self):
        result = await self.client.get_wreck_by_id("00001")
        assert result is not None
        assert result["ship_name"] == "USS Monitor"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id_not_found(self):
        result = await self.client.get_wreck_by_id("noaa_wreck:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_delegates_to_search_wrecks(self):
        """search() should return same results as search_wrecks()."""
        via_search = await self.client.search()
        via_wrecks = await self.client.search_wrecks()
        assert len(via_search) == len(via_wrecks)

    @pytest.mark.asyncio
    async def test_get_by_id_delegates_to_get_wreck_by_id(self):
        """get_by_id() should return same result as get_wreck_by_id()."""
        via_get = await self.client.get_by_id("noaa_wreck:00001")
        via_wreck = await self.client.get_wreck_by_id("noaa_wreck:00001")
        assert via_get == via_wreck

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        wrecks = await self.client.search_wrecks()
        for w in wrecks:
            assert w["archive"] == "noaa"

    @pytest.mark.asyncio
    async def test_max_results(self):
        results = await self.client.search_wrecks(max_results=2)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Multi-archive Manager Integration
# ---------------------------------------------------------------------------


class TestMultiArchiveManager:
    """Test the ArchiveManager with multi-archive dispatch."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager

        self.manager = ArchiveManager(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_list_archives_includes_new(self):
        archives = self.manager.list_archives()
        ids = [a["id"] for a in archives]
        assert "eic" in ids
        assert "carreira" in ids
        assert "galleon" in ids
        assert "soic" in ids
        assert "dss" in ids
        assert len(ids) == 11

    @pytest.mark.asyncio
    async def test_search_voyages_all_archives(self):
        """Search with no archive filter returns results from all archives."""
        result = await self.manager.search_voyages(max_results=100)
        archives = {v.get("archive") for v in result.items}
        # Should include DAS + the 4 new archives
        assert "das" in archives
        assert "eic" in archives
        assert "carreira" in archives
        assert "galleon" in archives
        assert "soic" in archives

    @pytest.mark.asyncio
    async def test_search_voyages_single_archive(self):
        result = await self.manager.search_voyages(archive="eic")
        assert len(result.items) == 3
        for v in result.items:
            assert v["archive"] == "eic"

    @pytest.mark.asyncio
    async def test_search_voyages_unknown_archive(self):
        result = await self.manager.search_voyages(archive="nonexistent")
        assert result.items == []

    @pytest.mark.asyncio
    async def test_get_voyage_eic(self):
        result = await self.manager.get_voyage("eic:0001")
        assert result is not None
        assert result["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_voyage_carreira(self):
        result = await self.manager.get_voyage("carreira:0001")
        assert result is not None
        assert result["captain"] == "Vasco da Gama"

    @pytest.mark.asyncio
    async def test_get_voyage_galleon(self):
        result = await self.manager.get_voyage("galleon:0001")
        assert result is not None
        assert result["ship_name"] == "San Pablo"

    @pytest.mark.asyncio
    async def test_get_voyage_soic(self):
        result = await self.manager.get_voyage("soic:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_voyage_das_still_works(self):
        result = await self.manager.get_voyage("das:3456")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_wrecks_all_archives(self):
        result = await self.manager.search_wrecks(max_results=100)
        archives = {w.get("archive") for w in result.items}
        assert len(archives) >= 2  # at least MAARER + some new

    @pytest.mark.asyncio
    async def test_search_wrecks_single_archive(self):
        result = await self.manager.search_wrecks(archive="eic")
        for w in result.items:
            assert w["archive"] == "eic"

    @pytest.mark.asyncio
    async def test_get_wreck_eic(self):
        result = await self.manager.get_wreck("eic_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_wreck_galleon(self):
        result = await self.manager.get_wreck("galleon_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "San Diego"

    @pytest.mark.asyncio
    async def test_get_wreck_soic(self):
        result = await self.manager.get_wreck("soic_wreck:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_maarer_still_works(self):
        result = await self.manager.get_wreck("maarer:VOC-0789")
        assert result is not None
        assert result["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_voyages_by_name_across_archives(self):
        result = await self.manager.search_voyages(ship_name="Gotheborg")
        assert len(result.items) >= 1
        assert result.items[0]["archive"] == "soic"

    @pytest.mark.asyncio
    async def test_voyage_full_eic(self):
        result = await self.manager.get_voyage_full("eic:0001")
        assert result is not None
        assert result["voyage"]["archive"] == "eic"
        # Wreck should be found via _find_wreck_for_voyage
        assert result["wreck"] is not None
        assert result["wreck"]["wreck_id"] == "eic_wreck:0001"

    @pytest.mark.asyncio
    async def test_search_wrecks_ukho_archive(self):
        result = await self.manager.search_wrecks(archive="ukho")
        assert len(result.items) == 5
        for w in result.items:
            assert w["archive"] == "ukho"

    @pytest.mark.asyncio
    async def test_get_wreck_ukho_routing(self):
        result = await self.manager.get_wreck("ukho_wreck:00001")
        assert result is not None
        assert result["ship_name"] == "HMS Birkenhead"

    @pytest.mark.asyncio
    async def test_search_wrecks_all_includes_ukho(self):
        result = await self.manager.search_wrecks(max_results=500)
        archives = {w.get("archive") for w in result.items}
        assert "ukho" in archives

    @pytest.mark.asyncio
    async def test_search_wrecks_noaa_archive(self):
        result = await self.manager.search_wrecks(archive="noaa")
        assert len(result.items) == 5
        for w in result.items:
            assert w["archive"] == "noaa"

    @pytest.mark.asyncio
    async def test_get_wreck_noaa_routing(self):
        result = await self.manager.get_wreck("noaa_wreck:00001")
        assert result is not None
        assert result["ship_name"] == "USS Monitor"

    @pytest.mark.asyncio
    async def test_search_wrecks_all_includes_noaa(self):
        result = await self.manager.search_wrecks(max_results=500)
        archives = {w.get("archive") for w in result.items}
        assert "noaa" in archives


# ---------------------------------------------------------------------------
# DSS Client (Dutch Ships and Sailors)
# ---------------------------------------------------------------------------


class TestDSSClient:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = DSSClient(data_dir=FIXTURES_DIR)

    # --- Muster search tests ---

    @pytest.mark.asyncio
    async def test_search_musters_all(self):
        results = await self.client.search_musters()
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_search_musters_by_ship_name(self):
        results = await self.client.search_musters(ship_name="Middelburg")
        assert len(results) == 2
        assert all(r["ship_name"] == "Middelburg" for r in results)

    @pytest.mark.asyncio
    async def test_search_musters_by_captain(self):
        results = await self.client.search_musters(captain="Pietersz")
        assert len(results) == 1
        assert results[0]["captain"] == "Jan Pietersz van Hoorn"

    @pytest.mark.asyncio
    async def test_search_musters_by_location(self):
        results = await self.client.search_musters(location="Batavia")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_musters_by_date_range(self):
        results = await self.client.search_musters(date_range="1740/1760")
        assert len(results) == 2  # 1750 + 1760

    @pytest.mark.asyncio
    async def test_search_musters_by_year_start(self):
        results = await self.client.search_musters(year_start=1740)
        assert len(results) == 2  # 1750 + 1760

    @pytest.mark.asyncio
    async def test_search_musters_by_year_end(self):
        results = await self.client.search_musters(year_end=1730)
        assert len(results) == 1  # 1720 only

    @pytest.mark.asyncio
    async def test_search_musters_by_das_voyage(self):
        results = await self.client.search_musters(das_voyage_id="das:1234")
        assert len(results) == 1
        assert results[0]["muster_id"] == "dss_muster:0001"

    @pytest.mark.asyncio
    async def test_search_musters_max_results(self):
        results = await self.client.search_musters(max_results=2)
        assert len(results) == 2

    # --- Muster get tests ---

    @pytest.mark.asyncio
    async def test_get_muster_by_id(self):
        result = await self.client.get_muster_by_id("dss_muster:0001")
        assert result is not None
        assert result["ship_name"] == "Middelburg"

    @pytest.mark.asyncio
    async def test_get_muster_by_id_without_prefix(self):
        result = await self.client.get_muster_by_id("0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_muster_by_id_not_found(self):
        result = await self.client.get_muster_by_id("dss_muster:9999")
        assert result is None

    # --- Muster-voyage cross-link tests ---

    @pytest.mark.asyncio
    async def test_musters_for_voyage(self):
        results = await self.client.get_musters_for_voyage("das:5678")
        assert len(results) == 1
        assert results[0]["muster_id"] == "dss_muster:0004"

    @pytest.mark.asyncio
    async def test_musters_for_voyage_no_match(self):
        results = await self.client.get_musters_for_voyage("das:9999")
        assert len(results) == 0

    # --- Crew search tests ---

    @pytest.mark.asyncio
    async def test_search_crews_all(self):
        results = await self.client.search_crews()
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_crews_by_name(self):
        results = await self.client.search_crews(name="Fokkema")
        assert len(results) == 1
        assert results[0]["name"] == "Lammert Fokkema"

    @pytest.mark.asyncio
    async def test_search_crews_by_rank(self):
        results = await self.client.search_crews(rank="matroos")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_crews_by_rank_english(self):
        results = await self.client.search_crews(rank="sailor")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_crews_by_origin(self):
        results = await self.client.search_crews(origin="Groningen")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_crews_by_destination(self):
        results = await self.client.search_crews(destination="Batavia")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_crews_by_age_min(self):
        results = await self.client.search_crews(age_min=30)
        assert len(results) == 2  # age 35 + age 40

    @pytest.mark.asyncio
    async def test_search_crews_by_age_max(self):
        results = await self.client.search_crews(age_max=25)
        assert len(results) == 2  # age 22 + age 19

    @pytest.mark.asyncio
    async def test_search_crews_by_date_range(self):
        results = await self.client.search_crews(date_range="1815/1825")
        assert len(results) == 2  # 1815 + 1820

    @pytest.mark.asyncio
    async def test_search_crews_by_ship_name(self):
        results = await self.client.search_crews(ship_name="Onderneming")
        assert len(results) == 2

    # --- Crew get tests ---

    @pytest.mark.asyncio
    async def test_get_crew_by_id(self):
        result = await self.client.get_crew_by_id("dss:00001")
        assert result is not None
        assert result["name"] == "Lammert Fokkema"

    @pytest.mark.asyncio
    async def test_get_crew_by_id_without_prefix(self):
        result = await self.client.get_crew_by_id("00001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_crew_by_id_not_found(self):
        result = await self.client.get_crew_by_id("dss:99999")
        assert result is None

    # --- Abstract method delegation ---

    @pytest.mark.asyncio
    async def test_search_delegates_to_crews(self):
        """The abstract search() method delegates to search_crews()."""
        results = await self.client.search(name="Fokkema")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_delegates_to_crew(self):
        """The abstract get_by_id() delegates to get_crew_by_id()."""
        result = await self.client.get_by_id("dss:00001")
        assert result is not None

    # --- Archive tag consistency ---

    @pytest.mark.asyncio
    async def test_all_musters_have_archive_tag(self):
        results = await self.client.search_musters()
        for m in results:
            assert m["archive"] == "dss"

    @pytest.mark.asyncio
    async def test_all_crews_have_archive_tag(self):
        results = await self.client.search_crews()
        for c in results:
            assert c["archive"] == "dss"


# ---------------------------------------------------------------------------
# DSS integration via ArchiveManager
# ---------------------------------------------------------------------------


class TestDSSArchiveManagerIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager

        self.manager = ArchiveManager(data_dir=FIXTURES_DIR)

    @pytest.mark.asyncio
    async def test_search_musters(self):
        result = await self.manager.search_musters()
        assert result.total_count == 4

    @pytest.mark.asyncio
    async def test_get_muster(self):
        result = await self.manager.get_muster("dss_muster:0001")
        assert result is not None
        assert result["ship_name"] == "Middelburg"

    @pytest.mark.asyncio
    async def test_search_crew_dss_archive(self):
        result = await self.manager.search_crew(archive="dss")
        assert result.total_count == 5
        for c in result.items:
            assert c["archive"] == "dss"

    @pytest.mark.asyncio
    async def test_get_crew_member_dss_routing(self):
        result = await self.manager.get_crew_member("dss:00001")
        assert result is not None
        assert result["name"] == "Lammert Fokkema"

    @pytest.mark.asyncio
    async def test_compare_wages_musters(self):
        result = await self.manager.compare_wages(
            group1_start=1700,
            group1_end=1740,
            group2_start=1741,
            group2_end=1780,
        )
        assert result["group1_n"] >= 1
        assert result["group2_n"] >= 1
        assert "difference_pct" in result

    @pytest.mark.asyncio
    async def test_compare_wages_crews(self):
        result = await self.manager.compare_wages(
            group1_start=1805,
            group1_end=1820,
            group2_start=1821,
            group2_end=1837,
            source="crews",
        )
        assert result["group1_n"] >= 1
        assert "group2_mean_wage" in result
