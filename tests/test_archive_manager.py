"""Tests for ArchiveManager."""

import pytest

from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager


@pytest.fixture
def manager() -> ArchiveManager:
    return ArchiveManager()


# ---------------------------------------------------------------------------
# Archive registry (sync)
# ---------------------------------------------------------------------------


class TestArchiveRegistry:
    def test_list_archives(self, manager: ArchiveManager):
        archives = manager.list_archives()
        assert len(archives) >= 4
        ids = [a["id"] for a in archives]
        assert "das" in ids
        assert "voc_crew" in ids
        assert "voc_cargo" in ids
        assert "maarer" in ids

    def test_get_archive_exists(self, manager: ArchiveManager):
        result = manager.get_archive("das")
        assert result is not None
        assert result["archive_id"] == "das"
        assert "name" in result

    def test_get_archive_not_found(self, manager: ArchiveManager):
        result = manager.get_archive("nonexistent")
        assert result is None

    def test_get_available_archive_ids(self, manager: ArchiveManager):
        ids = manager.get_available_archive_ids()
        assert "das" in ids
        assert len(ids) >= 4


# ---------------------------------------------------------------------------
# Hull profiles (sync)
# ---------------------------------------------------------------------------


class TestHullProfiles:
    def test_list_hull_profiles(self, manager: ArchiveManager):
        types = manager.list_hull_profiles()
        assert "retourschip" in types
        assert "fluit" in types
        assert len(types) >= 6

    def test_get_hull_profile_exists(self, manager: ArchiveManager):
        profile = manager.get_hull_profile("retourschip")
        assert profile is not None
        assert profile["ship_type"] == "retourschip"
        assert "hydrodynamics" in profile
        assert "sinking_characteristics" in profile

    def test_get_hull_profile_not_found(self, manager: ArchiveManager):
        profile = manager.get_hull_profile("nonexistent")
        assert profile is None


# ---------------------------------------------------------------------------
# Voyage operations (async)
# ---------------------------------------------------------------------------


class TestVoyageOperations:
    @pytest.mark.asyncio
    async def test_search_voyages_no_filters(self, manager: ArchiveManager):
        results = await manager.search_voyages()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_voyages_by_name(self, manager: ArchiveManager):
        results = await manager.search_voyages(ship_name="Batavia")
        assert len(results) == 1
        assert results[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_voyages_by_fate(self, manager: ArchiveManager):
        results = await manager.search_voyages(fate="wrecked")
        assert all(v["fate"] == "wrecked" for v in results)

    @pytest.mark.asyncio
    async def test_get_voyage_exists(self, manager: ArchiveManager):
        voyage = await manager.get_voyage("das:3456")
        assert voyage is not None
        assert voyage["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_voyage_not_found(self, manager: ArchiveManager):
        voyage = await manager.get_voyage("das:99999")
        assert voyage is None

    @pytest.mark.asyncio
    async def test_voyage_caching(self, manager: ArchiveManager):
        """Second call should use cache."""
        voyage1 = await manager.get_voyage("das:3456")
        assert voyage1 is not None
        # Now it's in cache
        voyage2 = await manager.get_voyage("das:3456")
        assert voyage2 is not None
        assert voyage1["ship_name"] == voyage2["ship_name"]


# ---------------------------------------------------------------------------
# Wreck operations (async)
# ---------------------------------------------------------------------------


class TestWreckOperations:
    @pytest.mark.asyncio
    async def test_search_wrecks_no_filters(self, manager: ArchiveManager):
        results = await manager.search_wrecks()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self, manager: ArchiveManager):
        results = await manager.search_wrecks(status="found")
        assert all(w["status"] == "found" for w in results)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self, manager: ArchiveManager):
        results = await manager.search_wrecks(region="cape")
        assert all(w["region"] == "cape" for w in results)

    @pytest.mark.asyncio
    async def test_get_wreck_exists(self, manager: ArchiveManager):
        wreck = await manager.get_wreck("maarer:VOC-0789")
        assert wreck is not None
        assert wreck["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_wreck_not_found(self, manager: ArchiveManager):
        wreck = await manager.get_wreck("maarer:NONEXISTENT")
        assert wreck is None


# ---------------------------------------------------------------------------
# Vessel operations (async)
# ---------------------------------------------------------------------------


class TestVesselOperations:
    @pytest.mark.asyncio
    async def test_search_vessels(self, manager: ArchiveManager):
        results = await manager.search_vessels()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_vessels_by_name(self, manager: ArchiveManager):
        results = await manager.search_vessels(name="Batavia")
        assert len(results) == 1
        assert results[0]["name"] == "Batavia"


# ---------------------------------------------------------------------------
# Crew operations (async)
# ---------------------------------------------------------------------------


class TestCrewOperations:
    @pytest.mark.asyncio
    async def test_search_crew(self, manager: ArchiveManager):
        results = await manager.search_crew()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_crew_by_ship(self, manager: ArchiveManager):
        results = await manager.search_crew(ship_name="Ridderschap")
        assert len(results) >= 1
        assert all("Ridderschap" in c["ship_name"] for c in results)

    @pytest.mark.asyncio
    async def test_get_crew_member(self, manager: ArchiveManager):
        member = await manager.get_crew_member("voc_crew:445892")
        assert member is not None
        assert member["name"] == "Jan Pietersz van der Horst"


# ---------------------------------------------------------------------------
# Cargo operations (async)
# ---------------------------------------------------------------------------


class TestCargoOperations:
    @pytest.mark.asyncio
    async def test_search_cargo(self, manager: ArchiveManager):
        results = await manager.search_cargo()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_cargo_by_voyage(self, manager: ArchiveManager):
        results = await manager.search_cargo(voyage_id="das:8123")
        assert len(results) >= 1
        assert all(c["voyage_id"] == "das:8123" for c in results)

    @pytest.mark.asyncio
    async def test_get_cargo_manifest(self, manager: ArchiveManager):
        manifest = await manager.get_cargo_manifest("das:8123")
        assert len(manifest) >= 1


# ---------------------------------------------------------------------------
# Position assessment (async)
# ---------------------------------------------------------------------------


class TestPositionAssessment:
    @pytest.mark.asyncio
    async def test_assess_position_by_date(self, manager: ArchiveManager):
        result = await manager.assess_position(date="1700-01-01")
        assert "assessment" in result
        assert "quality_score" in result["assessment"]

    @pytest.mark.asyncio
    async def test_assess_position_gps_source(self, manager: ArchiveManager):
        result = await manager.assess_position(
            position={"lat": -28.49, "lon": 113.79},
            source_description="GPS surveyed wreck site",
        )
        assert result["assessment"]["quality_score"] == 0.95
        assert result["assessment"]["uncertainty_type"] == "precise"

    @pytest.mark.asyncio
    async def test_assess_position_dead_reckoning(self, manager: ArchiveManager):
        result = await manager.assess_position(
            source_description="Dead reckoning position estimate",
            date="1650-01-01",
        )
        assert result["assessment"]["uncertainty_type"] == "dead_reckoning"
        assert result["assessment"]["quality_score"] < 0.5


# ---------------------------------------------------------------------------
# Statistics (async)
# ---------------------------------------------------------------------------


class TestStatistics:
    @pytest.mark.asyncio
    async def test_get_statistics(self, manager: ArchiveManager):
        stats = await manager.get_statistics()
        assert "summary" in stats
        assert "losses_by_region" in stats
        assert "losses_by_cause" in stats


# ---------------------------------------------------------------------------
# GeoJSON export (async)
# ---------------------------------------------------------------------------


class TestGeoJSONExport:
    @pytest.mark.asyncio
    async def test_export_geojson(self, manager: ArchiveManager):
        geojson = await manager.export_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) >= 1

    @pytest.mark.asyncio
    async def test_export_geojson_by_status(self, manager: ArchiveManager):
        geojson = await manager.export_geojson(status="found")
        for feature in geojson["features"]:
            assert feature["properties"]["status"] == "found"

    @pytest.mark.asyncio
    async def test_export_geojson_structure(self, manager: ArchiveManager):
        geojson = await manager.export_geojson()
        feature = geojson["features"][0]
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 2
        assert "properties" in feature
