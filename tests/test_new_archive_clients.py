"""Tests for the four new archive clients: EIC, Carreira, Galleon, SOIC."""

from pathlib import Path

import pytest

from chuk_mcp_maritime_archives.core.clients.eic_client import EICClient
from chuk_mcp_maritime_archives.core.clients.carreira_client import CarreiraClient
from chuk_mcp_maritime_archives.core.clients.galleon_client import GalleonClient
from chuk_mcp_maritime_archives.core.clients.soic_client import SOICClient

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
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_wrecks_by_name(self):
        results = await self.client.search_wrecks(ship_name="Grosvenor")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="cape")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("eic_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "Earl of Abergavenny"

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("eic:0001")
        assert result is not None
        assert result["wreck_id"] == "eic_wreck:0001"

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
    async def test_search_by_fate(self):
        results = await self.client.search(fate="wrecked")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        result = await self.client.get_by_id("carreira:0001")
        assert result is not None
        assert result["captain"] == "Vasco da Gama"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        result = await self.client.get_by_id("carreira:9999")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["ship_name"] == "Sao Joao"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("carreira_wreck:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("carreira:0002")
        assert result is not None
        assert result["ship_name"] == "Sao Joao"

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
    async def test_search_by_trade_direction(self):
        results = await self.client.search(trade_direction="westbound")
        assert len(results) == 2

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
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["loss_cause"] == "battle"

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self):
        results = await self.client.search_wrecks(region="philippine_sea")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("galleon_wreck:0001")
        assert result is not None
        assert result["ship_name"] == "San Diego"

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("galleon:0002")
        assert result is not None

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
    async def test_search_by_destination(self):
        results = await self.client.search(destination_port="Canton")
        assert len(results) == 2

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
    async def test_search_wrecks(self):
        results = await self.client.search_wrecks()
        assert len(results) == 1
        assert results[0]["ship_name"] == "Gotheborg"

    @pytest.mark.asyncio
    async def test_get_wreck_by_id(self):
        result = await self.client.get_wreck_by_id("soic_wreck:0001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_wreck_by_voyage_id(self):
        result = await self.client.get_wreck_by_voyage_id("soic:0002")
        assert result is not None
        assert result["wreck_id"] == "soic_wreck:0001"

    @pytest.mark.asyncio
    async def test_all_records_have_archive_tag(self):
        voyages = await self.client.search()
        for v in voyages:
            assert v["archive"] == "soic"
        wrecks = await self.client.search_wrecks()
        for w in wrecks:
            assert w["archive"] == "soic"


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
        assert len(ids) == 8

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
