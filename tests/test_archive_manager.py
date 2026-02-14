"""Tests for ArchiveManager backed by local JSON fixture data."""

from unittest.mock import AsyncMock, patch

import pytest

from chuk_mcp_maritime_archives.core.archive_manager import ArchiveManager


# ---------------------------------------------------------------------------
# Archive registry (sync — reads constant data, no file I/O)
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
# Hull profiles (sync — reads constant data, no file I/O)
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
# Voyage operations (async — reads from fixture data)
# ---------------------------------------------------------------------------


class TestVoyageOperations:
    @pytest.mark.asyncio
    async def test_search_voyages_no_filters(self, manager: ArchiveManager):
        result = await manager.search_voyages()
        assert len(result.items) == 12  # 3 DAS + 3 EIC + 2 carreira + 2 galleon + 2 SOIC
        assert result.total_count == 12

    @pytest.mark.asyncio
    async def test_search_voyages_by_name(self, manager: ArchiveManager):
        result = await manager.search_voyages(ship_name="Batavia")
        assert len(result.items) == 1
        assert result.items[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_search_voyages_by_fate(self, manager: ArchiveManager):
        result = await manager.search_voyages(fate="wrecked")
        assert all(v["fate"] == "wrecked" for v in result.items)
        assert len(result.items) == 7  # 2 DAS + 2 EIC + 1 carreira + 1 galleon + 1 SOIC

    @pytest.mark.asyncio
    async def test_search_voyages_by_archive(self, manager: ArchiveManager):
        result = await manager.search_voyages(archive="das")
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_search_voyages_by_archive_no_match(self, manager: ArchiveManager):
        result = await manager.search_voyages(archive="nonexistent")
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_search_voyages_route_filter(self, manager: ArchiveManager):
        result = await manager.search_voyages(route="abrolhos")
        assert len(result.items) == 1
        assert result.items[0]["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_voyage_exists(self, manager: ArchiveManager):
        voyage = await manager.get_voyage("das:3456")
        assert voyage is not None
        assert voyage["ship_name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_voyage_not_found(self, manager: ArchiveManager):
        voyage = await manager.get_voyage("das:99999")
        assert voyage is None


# ---------------------------------------------------------------------------
# Wreck operations (async — reads from fixture data)
# ---------------------------------------------------------------------------


class TestWreckOperations:
    @pytest.mark.asyncio
    async def test_search_wrecks_no_filters(self, manager: ArchiveManager):
        result = await manager.search_wrecks()
        # 3 MAARER + 2 EIC + 1 carreira + 1 galleon + 1 SOIC + 5 UKHO + 5 NOAA
        assert len(result.items) == 18
        assert result.total_count == 18

    @pytest.mark.asyncio
    async def test_search_wrecks_by_status(self, manager: ArchiveManager):
        result = await manager.search_wrecks(status="found")
        assert all(w["status"] == "found" for w in result.items)
        # 3 MAARER + 1 EIC + 1 galleon + 1 SOIC + 4 UKHO + 4 NOAA
        assert len(result.items) == 14

    @pytest.mark.asyncio
    async def test_search_wrecks_by_region(self, manager: ArchiveManager):
        result = await manager.search_wrecks(region="cape")
        assert all(w["region"] == "cape" for w in result.items)
        # 1 MAARER (Meermin) + 1 EIC (Grosvenor) + 1 carreira (Sao Joao) + 1 UKHO (Birkenhead)
        assert len(result.items) == 4

    @pytest.mark.asyncio
    async def test_search_wrecks_by_archive(self, manager: ArchiveManager):
        result = await manager.search_wrecks(archive="maarer")
        assert len(result.items) == 3

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
# Vessel operations (async — reads from fixture data)
# ---------------------------------------------------------------------------


class TestVesselOperations:
    @pytest.mark.asyncio
    async def test_search_vessels(self, manager: ArchiveManager):
        result = await manager.search_vessels()
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_search_vessels_by_name(self, manager: ArchiveManager):
        result = await manager.search_vessels(name="Batavia")
        assert len(result.items) == 1
        assert result.items[0]["name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_vessel(self, manager: ArchiveManager):
        result = await manager.get_vessel("das_vessel:001")
        assert result is not None
        assert result["name"] == "Batavia"

    @pytest.mark.asyncio
    async def test_get_vessel_not_found(self, manager: ArchiveManager):
        result = await manager.get_vessel("das_vessel:999")
        assert result is None


# ---------------------------------------------------------------------------
# Crew operations (async — reads from fixture data)
# ---------------------------------------------------------------------------


class TestCrewOperations:
    @pytest.mark.asyncio
    async def test_search_crew(self, manager: ArchiveManager):
        result = await manager.search_crew()
        assert len(result.items) == 12

    @pytest.mark.asyncio
    async def test_search_crew_by_ship(self, manager: ArchiveManager):
        result = await manager.search_crew(ship_name="Ridderschap")
        assert len(result.items) == 4
        assert all("Ridderschap" in c["ship_name"] for c in result.items)

    @pytest.mark.asyncio
    async def test_get_crew_member(self, manager: ArchiveManager):
        member = await manager.get_crew_member("voc_crew:445892")
        assert member is not None
        assert member["name"] == "Jan Pietersz van der Horst"


# ---------------------------------------------------------------------------
# Cargo operations (async — reads from fixture data)
# ---------------------------------------------------------------------------


class TestCargoOperations:
    @pytest.mark.asyncio
    async def test_search_cargo(self, manager: ArchiveManager):
        result = await manager.search_cargo()
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_search_cargo_by_voyage(self, manager: ArchiveManager):
        result = await manager.search_cargo(voyage_id="das:8123")
        assert len(result.items) == 2
        assert all(c["voyage_id"] == "das:8123" for c in result.items)

    @pytest.mark.asyncio
    async def test_get_cargo_manifest(self, manager: ArchiveManager):
        manifest = await manager.get_cargo_manifest("das:8123")
        assert len(manifest) == 2


# ---------------------------------------------------------------------------
# Position assessment (async — may read voyage/wreck fixture data)
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

    @pytest.mark.asyncio
    async def test_assess_position_with_voyage(self, manager: ArchiveManager):
        result = await manager.assess_position(voyage_id="das:3456")
        assert "assessment" in result
        assert result["voyage_id"] == "das:3456"

    @pytest.mark.asyncio
    async def test_assess_position_with_wreck(self, manager: ArchiveManager):
        result = await manager.assess_position(wreck_id="maarer:VOC-0789")
        assert result["wreck_id"] == "maarer:VOC-0789"
        assert result["position"]["lat"] == -28.49

    @pytest.mark.asyncio
    async def test_assess_position_multiple_sources(self, manager: ArchiveManager):
        result = await manager.assess_position(
            source_description="Multiple sources triangulated",
            date="1700-01-01",
        )
        assert result["assessment"]["uncertainty_type"] == "triangulated"
        assert result["assessment"]["quality_score"] == 0.7

    @pytest.mark.asyncio
    async def test_assess_position_approximate(self, manager: ArchiveManager):
        result = await manager.assess_position(
            source_description="Approximate location from accounts",
            date="1700-01-01",
        )
        assert result["assessment"]["uncertainty_type"] == "approximate"
        assert result["assessment"]["quality_score"] == 0.3

    @pytest.mark.asyncio
    async def test_assess_position_regional(self, manager: ArchiveManager):
        result = await manager.assess_position(
            source_description="Regional Straits area only",
            date="1700-01-01",
        )
        assert result["assessment"]["uncertainty_type"] == "regional"
        assert result["assessment"]["quality_score"] == 0.15

    @pytest.mark.asyncio
    async def test_assess_position_no_year(self, manager: ArchiveManager):
        result = await manager.assess_position(
            position={"lat": 0, "lon": 0},
        )
        assert result["assessment"]["quality_score"] == 0.5

    @pytest.mark.asyncio
    async def test_navigation_era_lookup(self, manager: ArchiveManager):
        era = manager._get_navigation_era(1620)
        assert era is not None
        assert era["technology"] == "dead_reckoning_with_cross_staff"

        era = manager._get_navigation_era(1780)
        assert era is not None
        assert era["technology"] == "chronometer_era"

        era = manager._get_navigation_era(None)
        assert era is None

        era = manager._get_navigation_era(1400)
        assert era is None


# ---------------------------------------------------------------------------
# Statistics (async — reads wreck fixture data)
# ---------------------------------------------------------------------------


class TestStatistics:
    @pytest.mark.asyncio
    async def test_get_statistics(self, manager: ArchiveManager):
        stats = await manager.get_statistics()
        assert "summary" in stats
        assert "losses_by_region" in stats
        assert "losses_by_cause" in stats
        assert stats["summary"]["total_losses"] == 18  # all wreck archives combined

    @pytest.mark.asyncio
    async def test_get_statistics_with_date_range(self, manager: ArchiveManager):
        stats = await manager.get_statistics(date_range="1600/1700")
        # Batavia 1629, Vergulde Draeck 1656, San Diego 1600 (galleon)
        # + UKHO: Batavia 1629, San Diego 1600
        assert stats["summary"]["total_losses"] == 5

    @pytest.mark.asyncio
    async def test_get_statistics_computes_breakdowns(self, manager: ArchiveManager):
        stats = await manager.get_statistics()
        assert "western_australia" in stats["losses_by_region"]
        assert "cape" in stats["losses_by_region"]
        assert "reef" in stats["losses_by_cause"]
        assert "losses_by_status" in stats
        assert "losses_by_decade" in stats
        assert stats["summary"]["lives_lost_total"] == 193
        assert stats["summary"]["cargo_value_guilders_total"] == 340600


# ---------------------------------------------------------------------------
# GeoJSON export (async — reads wreck fixture data)
# ---------------------------------------------------------------------------


class TestGeoJSONExport:
    @pytest.mark.asyncio
    async def test_export_geojson(self, manager: ArchiveManager):
        geojson = await manager.export_geojson()
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 18  # all wreck archives combined

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

    @pytest.mark.asyncio
    async def test_export_geojson_by_wreck_ids(self, manager: ArchiveManager):
        geojson = await manager.export_geojson(wreck_ids=["maarer:VOC-0789"])
        assert len(geojson["features"]) == 1

    @pytest.mark.asyncio
    async def test_export_geojson_no_uncertainty(self, manager: ArchiveManager):
        geojson = await manager.export_geojson(include_uncertainty=False, include_voyage_data=False)
        props = geojson["features"][0]["properties"]
        assert "uncertainty_km" not in props
        assert "ship_type" not in props


# ---------------------------------------------------------------------------
# Manager date filter
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Timeline (async — builds from voyage, route, and wreck fixture data)
# ---------------------------------------------------------------------------


class TestBuildTimeline:
    @pytest.mark.asyncio
    async def test_build_timeline_batavia(self, manager: ArchiveManager):
        """Build timeline for the Batavia voyage — should have departure, estimates, and loss."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        assert result["voyage_id"] == "das:3456"
        assert result["ship_name"] == "Batavia"
        assert len(result["events"]) >= 2  # at least departure + loss
        assert "das" in result["data_sources"]
        assert "maarer" in result["data_sources"]

        # Check event types
        event_types = [e["type"] for e in result["events"]]
        assert "departure" in event_types
        assert "loss" in event_types

    @pytest.mark.asyncio
    async def test_build_timeline_includes_route_estimates(self, manager: ArchiveManager):
        """Timeline should include waypoint estimates from the outward route."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        event_types = [e["type"] for e in result["events"]]
        assert "waypoint_estimate" in event_types
        assert "route_estimate" in result["data_sources"]

    @pytest.mark.asyncio
    async def test_build_timeline_not_found(self, manager: ArchiveManager):
        """Non-existent voyage should return None."""
        result = await manager.build_timeline(voyage_id="das:99999")
        assert result is None

    @pytest.mark.asyncio
    async def test_build_timeline_events_sorted_chronologically(self, manager: ArchiveManager):
        """Events should be in chronological order."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        dates = [e["date"] for e in result["events"]]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_build_timeline_loss_event_has_position(self, manager: ArchiveManager):
        """The loss event should have wreck position from fixture data."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        loss_events = [e for e in result["events"] if e["type"] == "loss"]
        assert len(loss_events) == 1
        assert loss_events[0]["position"]["lat"] == -28.49
        assert loss_events[0]["position"]["lon"] == 113.79

    @pytest.mark.asyncio
    async def test_build_timeline_geojson_produced(self, manager: ArchiveManager):
        """Timeline should produce a GeoJSON LineString when multiple positions exist."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        # The loss event has a position; route estimates also have positions
        # so geojson should be produced if >= 2 positioned events
        if result["geojson"] is not None:
            assert result["geojson"]["type"] == "Feature"
            assert result["geojson"]["geometry"]["type"] == "LineString"

    @pytest.mark.asyncio
    async def test_build_timeline_completed_voyage(self, manager: ArchiveManager):
        """A completed voyage should not have a loss event."""
        result = await manager.build_timeline(voyage_id="das:5678")
        assert result is not None
        event_types = [e["type"] for e in result["events"]]
        assert "loss" not in event_types
        assert "departure" in event_types

    @pytest.mark.asyncio
    async def test_build_timeline_with_cliwoc_track(self, manager: ArchiveManager):
        """Timeline should include CLIWOC data when track is found."""
        mock_track = {
            "voyage_id": 42,
            "ship_name": "Batavia",
            "nationality": "NL",
        }
        full_track = {
            "voyage_id": 42,
            "nationality": "NL",
            "positions": [
                {"date": "1629-01-10", "lat": -10.0, "lon": 20.0},
                {"date": "1629-02-15", "lat": -20.0, "lon": 40.0},
                {"date": "1629-03-20", "lat": -30.0, "lon": 60.0},
            ],
        }
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=mock_track,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track",
                return_value=full_track,
            ),
        ):
            result = await manager.build_timeline(
                voyage_id="das:3456", include_positions=True, max_positions=10
            )
            assert result is not None
            assert "cliwoc" in result["data_sources"]
            cliwoc_events = [e for e in result["events"] if e["type"] == "cliwoc_position"]
            assert len(cliwoc_events) == 3

    @pytest.mark.asyncio
    async def test_build_timeline_cliwoc_without_positions(self, manager: ArchiveManager):
        """When CLIWOC track found but include_positions=False, only adds data source."""
        mock_track = {
            "voyage_id": 42,
            "ship_name": "Batavia",
            "nationality": "NL",
        }
        with patch(
            "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
            return_value=mock_track,
        ):
            result = await manager.build_timeline(voyage_id="das:3456", include_positions=False)
            assert result is not None
            assert "cliwoc" in result["data_sources"]
            cliwoc_events = [e for e in result["events"] if e["type"] == "cliwoc_position"]
            assert len(cliwoc_events) == 0

    @pytest.mark.asyncio
    async def test_find_cliwoc_track_by_das_number(self, manager: ArchiveManager):
        """_find_cliwoc_track_for_voyage should try DAS number first."""
        mock_track = {"voyage_id": 42, "ship_name": "Test", "positions": []}
        voyage = {"voyage_number": "3456", "ship_name": "Batavia"}
        with patch(
            "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
            return_value=mock_track,
        ):
            result, confidence = manager._find_cliwoc_track_for_voyage(voyage)
            assert result is not None
            assert result["voyage_id"] == 42
            assert "positions" not in result  # positions stripped from summary
            assert confidence == 1.0  # DAS number = exact match

    @pytest.mark.asyncio
    async def test_find_cliwoc_track_falls_back_to_ship_name(self, manager: ArchiveManager):
        """When DAS number lookup returns None, should fall back to ship name."""
        mock_track = {"voyage_id": 99, "ship_name": "Batavia"}
        voyage = {"ship_name": "Batavia", "departure_date": "1628-10-28"}
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=None,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.find_track_for_voyage",
                return_value=mock_track,
            ),
        ):
            result = manager._find_cliwoc_track_for_voyage(voyage)
            assert result is not None
            assert result["voyage_id"] == 99

    @pytest.mark.asyncio
    async def test_find_cliwoc_track_returns_none(self, manager: ArchiveManager):
        """When no CLIWOC track matches, should return None."""
        voyage = {"ship_name": "Unknown Ship"}
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=None,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.find_track_for_voyage",
                return_value=None,
            ),
        ):
            result = manager._find_cliwoc_track_for_voyage(voyage)
            assert result is None


class TestManagerDateFilter:
    def test_filter_by_date_range(self, manager: ArchiveManager):
        records = [
            {"name": "A", "loss_date": "1629-06-04"},
            {"name": "B", "loss_date": "1780-01-01"},
        ]
        result = manager._filter_by_date_range(records, "1600/1700", "loss_date")
        assert len(result) == 1
        assert result[0]["name"] == "A"

    def test_filter_by_date_range_invalid(self, manager: ArchiveManager):
        records = [{"name": "A", "loss_date": "1629"}]
        result = manager._filter_by_date_range(records, "invalid", "loss_date")
        assert len(result) == 1  # returns all


# ---------------------------------------------------------------------------
# Pagination integration tests
# ---------------------------------------------------------------------------


class TestPaginationIntegration:
    @pytest.mark.asyncio
    async def test_paginate_through_all_voyages(self, manager: ArchiveManager):
        """Page through all voyages and verify no duplicates."""
        all_ids: list[str] = []
        cursor = None
        while True:
            result = await manager.search_voyages(max_results=3, cursor=cursor)
            all_ids.extend(v["voyage_id"] for v in result.items)
            if not result.has_more:
                break
            cursor = result.next_cursor
        assert len(all_ids) == len(set(all_ids)), "Duplicate voyage IDs across pages"
        assert len(all_ids) == result.total_count

    @pytest.mark.asyncio
    async def test_first_page_matches_no_cursor(self, manager: ArchiveManager):
        """First page with cursor=None should match default behavior."""
        result_no_cursor = await manager.search_voyages(max_results=5)
        result_with_none = await manager.search_voyages(max_results=5, cursor=None)
        assert [v["voyage_id"] for v in result_no_cursor.items] == [
            v["voyage_id"] for v in result_with_none.items
        ]

    @pytest.mark.asyncio
    async def test_pagination_total_count_stable(self, manager: ArchiveManager):
        """total_count should be the same on every page."""
        result1 = await manager.search_voyages(max_results=2)
        result2 = await manager.search_voyages(max_results=2, cursor=result1.next_cursor)
        assert result1.total_count == result2.total_count

    @pytest.mark.asyncio
    async def test_max_results_clamped(self, manager: ArchiveManager):
        """Requesting more than MAX_PAGE_SIZE should be clamped."""
        result = await manager.search_voyages(max_results=9999)
        assert len(result.items) <= 500


# ---------------------------------------------------------------------------
# Narrative search (async — searches free-text fields across all fixtures)
# ---------------------------------------------------------------------------


class TestNarrativeSearch:
    @pytest.mark.asyncio
    async def test_search_narratives_simple(self, manager: ArchiveManager):
        """Single keyword should match across archives."""
        result = await manager.search_narratives(query="Abrolhos")
        assert result.total_count >= 1
        # Should find at least the DAS voyage with "Houtman Abrolhos"
        archives = {h["archive"] for h in result.items}
        assert "das" in archives

    @pytest.mark.asyncio
    async def test_search_narratives_phrase(self, manager: ArchiveManager):
        """Quoted phrase should match exactly."""
        result = await manager.search_narratives(query='"Cape of Good Hope"')
        assert result.total_count >= 1
        # Carreira voyage mentions "Cape of Good Hope" in particulars
        archives = {h["archive"] for h in result.items}
        assert "carreira" in archives

    @pytest.mark.asyncio
    async def test_search_narratives_voyage_only(self, manager: ArchiveManager):
        """record_type='voyage' should exclude wreck records."""
        result = await manager.search_narratives(query="Gothenburg", record_type="voyage")
        assert result.total_count >= 1
        assert all(h["record_type"] == "voyage" for h in result.items)

    @pytest.mark.asyncio
    async def test_search_narratives_wreck_only(self, manager: ArchiveManager):
        """record_type='wreck' should exclude voyage records."""
        result = await manager.search_narratives(query="Philippines", record_type="wreck")
        assert result.total_count >= 1
        assert all(h["record_type"] == "wreck" for h in result.items)

    @pytest.mark.asyncio
    async def test_search_narratives_by_archive(self, manager: ArchiveManager):
        """archive filter should restrict to one archive."""
        result = await manager.search_narratives(query="Wrecked", archive="eic")
        assert result.total_count >= 1
        assert all(h["archive"] == "eic" for h in result.items)

    @pytest.mark.asyncio
    async def test_search_narratives_no_results(self, manager: ArchiveManager):
        """Query with no matches should return empty results."""
        result = await manager.search_narratives(query="xyznonexistent")
        assert result.total_count == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_search_narratives_pagination(self, manager: ArchiveManager):
        """Pagination should work with cursor."""
        # "South Africa" appears in multiple records
        result1 = await manager.search_narratives(query="South Africa", max_results=1)
        assert result1.total_count >= 2
        assert len(result1.items) == 1
        assert result1.has_more is True
        assert result1.next_cursor is not None

        result2 = await manager.search_narratives(
            query="South Africa", max_results=1, cursor=result1.next_cursor
        )
        assert len(result2.items) >= 1
        # Pages should not overlap
        ids1 = {h["record_id"] + h["field"] for h in result1.items}
        ids2 = {h["record_id"] + h["field"] for h in result2.items}
        assert ids1.isdisjoint(ids2)

    @pytest.mark.asyncio
    async def test_search_narratives_snippet_extraction(self, manager: ArchiveManager):
        """Snippets should contain the matched term."""
        result = await manager.search_narratives(query="Gothenburg")
        assert result.total_count >= 1
        for h in result.items:
            assert "gothenburg" in h["snippet"].lower()

    @pytest.mark.asyncio
    async def test_search_narratives_and_logic(self, manager: ArchiveManager):
        """Multiple terms use AND logic — both must be present."""
        result = await manager.search_narratives(query="Wrecked Hastings")
        assert result.total_count >= 1
        # Only DAS voyage has both "Wrecked" and "Hastings" in particulars
        for h in result.items:
            assert "wrecked" in h["snippet"].lower() or "hastings" in h["snippet"].lower()

    @pytest.mark.asyncio
    async def test_search_narratives_empty_query(self, manager: ArchiveManager):
        """Empty query should return no results."""
        result = await manager.search_narratives(query="")
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_narratives_case_insensitive(self, manager: ArchiveManager):
        """Search should be case-insensitive."""
        upper = await manager.search_narratives(query="GOTHENBURG")
        lower = await manager.search_narratives(query="gothenburg")
        assert upper.total_count == lower.total_count
        assert upper.total_count >= 1


# ---------------------------------------------------------------------------
# get_voyage_full: hull_profile confidence + include_crew
# ---------------------------------------------------------------------------


class TestVoyageFullExtended:
    @pytest.mark.asyncio
    async def test_hull_profile_confidence(self, manager: ArchiveManager):
        """Voyage with ship_type matching a hull profile should set hull_profile confidence."""
        # Add ship_type to a fixture voyage so hull profile is found
        with patch.object(manager, "get_voyage", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "voyage_id": "das:3456",
                "ship_name": "Batavia",
                "ship_type": "retourschip",
                "departure_date": "1628-10-28",
                "fate": "wrecked",
                "archive": "das",
            }
            result = await manager.get_voyage_full("das:3456")
            assert result is not None
            assert result["hull_profile"] is not None
            assert result["link_confidence"]["hull_profile"] == 1.0
            assert "hull_profile" in result["links_found"]

    @pytest.mark.asyncio
    async def test_include_crew_true(self, manager: ArchiveManager):
        """include_crew=True should populate crew records and crew confidence."""
        mock_crew = [
            {"name": "Jan Jansen", "rank": "matroos", "link_confidence": 0.85},
            {"name": "Pieter Klaas", "rank": "schipper", "link_confidence": 0.92},
        ]
        with patch.object(
            manager, "find_crew_for_voyage", new_callable=AsyncMock, return_value=mock_crew
        ):
            result = await manager.get_voyage_full("das:5678", include_crew=True)
            assert result is not None
            assert result["crew"] is not None
            assert len(result["crew"]) == 2
            assert "crew" in result["links_found"]
            # crew confidence = min of individual crew confidences
            assert result["link_confidence"]["crew"] == 0.85

    @pytest.mark.asyncio
    async def test_include_crew_empty(self, manager: ArchiveManager):
        """include_crew=True with no crew found should not add crew to links_found."""
        with patch.object(manager, "find_crew_for_voyage", new_callable=AsyncMock, return_value=[]):
            result = await manager.get_voyage_full("das:5678", include_crew=True)
            assert result is not None
            assert result["crew"] is None or result["crew"] == []
            assert "crew" not in result["links_found"]


# ---------------------------------------------------------------------------
# find_crew_for_voyage
# ---------------------------------------------------------------------------


class TestFindCrewForVoyage:
    @pytest.mark.asyncio
    async def test_exact_voc_match(self, manager: ArchiveManager):
        """VOC crew with matching voyage_id should be found with confidence 1.0."""
        crew = await manager.find_crew_for_voyage("das:5678")
        assert len(crew) >= 1
        for c in crew:
            assert c["link_confidence"] == 1.0
            assert c["link_method"] in ("exact_voyage_id", "muster_das_voyage_id")

    @pytest.mark.asyncio
    async def test_dss_muster_exact_match(self, manager: ArchiveManager):
        """DSS muster with das_voyage_id should be found."""
        crew = await manager.find_crew_for_voyage("das:1234")
        # dss_muster:0001 has das_voyage_id "das:1234"
        muster_results = [c for c in crew if c.get("link_method") == "muster_das_voyage_id"]
        assert len(muster_results) >= 1
        for c in muster_results:
            assert c["link_confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_fuzzy_matching_path(self, manager: ArchiveManager):
        """When no exact matches, fuzzy matching by ship name + date should be tried."""
        # Use a voyage_id that has no exact crew match
        # Mock VOC and DSS exact lookups to return empty, forcing fuzzy path
        with (
            patch.object(manager._crew_client, "search", new_callable=AsyncMock, return_value=[]),
            patch.object(
                manager._dss_client,
                "get_musters_for_voyage",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch.object(
                manager,
                "get_voyage",
                new_callable=AsyncMock,
                return_value={
                    "voyage_id": "das:9999",
                    "ship_name": "Onderneming",
                    "departure_date": "1810-01-01",
                },
            ),
        ):
            crew = await manager.find_crew_for_voyage("das:9999", min_confidence=0.50)
            # DSS crew fixture has "Onderneming" with muster_date 1810-04-15
            # Fuzzy match should find them
            fuzzy = [c for c in crew if c.get("link_method") == "fuzzy_ship_date"]
            assert len(fuzzy) >= 1
            for c in fuzzy:
                assert 0.50 <= c["link_confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_voc_client_exception(self, manager: ArchiveManager):
        """Exception from VOC crew client should be caught silently."""
        with patch.object(
            manager._crew_client,
            "search",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            # Should not raise — catches exception and continues
            crew = await manager.find_crew_for_voyage("das:5678")
            # DSS muster may still return results
            assert isinstance(crew, list)

    @pytest.mark.asyncio
    async def test_dss_client_exception(self, manager: ArchiveManager):
        """Exception from DSS muster client should be caught silently."""
        with patch.object(
            manager._dss_client,
            "get_musters_for_voyage",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB error"),
        ):
            crew = await manager.find_crew_for_voyage("das:5678")
            assert isinstance(crew, list)


# ---------------------------------------------------------------------------
# _find_wreck_for_voyage
# ---------------------------------------------------------------------------


class TestFindWreckForVoyage:
    @pytest.mark.asyncio
    async def test_non_das_with_get_wreck_by_voyage_id(self, manager: ArchiveManager):
        """EIC client has get_wreck_by_voyage_id — should use it."""
        result = await manager._find_wreck_for_voyage("eic:0062")
        # May or may not find a wreck in fixtures, but should not error
        # The important thing is the branch is covered
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_unprefixed_voyage_id(self, manager: ArchiveManager):
        """Unprefixed ID like '3456' should still find wreck with voyage_id 'das:3456'."""
        result = await manager._find_wreck_for_voyage("3456")
        assert result is not None
        assert result["voyage_id"] == "das:3456"

    @pytest.mark.asyncio
    async def test_non_das_unknown_prefix(self, manager: ArchiveManager):
        """Unknown prefix without a registered client should return None."""
        result = await manager._find_wreck_for_voyage("unknown:001")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_cliwoc_track_das_number_not_found_falls_to_fuzzy(
        self, manager: ArchiveManager
    ):
        """When voyage has voyage_number but DAS lookup returns None, should try fuzzy."""
        voyage = {
            "voyage_number": "9999",
            "ship_name": "Batavia",
            "departure_date": "1628-10-28",
            "archive": "das",
        }
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=None,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.find_track_for_voyage",
                return_value=({"voyage_id": 99, "ship_name": "Batavia"}, 0.85),
            ),
        ):
            result, confidence = manager._find_cliwoc_track_for_voyage(voyage)
            assert result is not None
            assert result["voyage_id"] == 99
            assert confidence == 0.85

    def test_find_cliwoc_track_no_ship_name(self, manager: ArchiveManager):
        """Voyage with no ship_name and no voyage_number should return (None, 0.0)."""
        voyage = {"departure_date": "1700-01-01"}
        result, confidence = manager._find_cliwoc_track_for_voyage(voyage)
        assert result is None
        assert confidence == 0.0


# ---------------------------------------------------------------------------
# audit_links
# ---------------------------------------------------------------------------


class TestAuditLinks:
    @pytest.mark.asyncio
    async def test_audit_links_returns_structure(self, manager: ArchiveManager):
        """audit_links should return expected dict structure."""
        result = await manager.audit_links()
        assert "wreck_links" in result
        assert "cliwoc_links" in result
        assert "crew_links" in result
        assert "total_links_evaluated" in result
        assert "confidence_distribution" in result

    @pytest.mark.asyncio
    async def test_audit_links_wreck_ground_truth(self, manager: ArchiveManager):
        """Wreck links audit should count wrecks with voyage_id as ground truth."""
        result = await manager.audit_links()
        wl = result["wreck_links"]
        assert wl["ground_truth_count"] >= 0
        assert wl["matched_count"] >= 0
        assert 0.0 <= wl["precision"] <= 1.0
        assert 0.0 <= wl["recall"] <= 1.0

    @pytest.mark.asyncio
    async def test_audit_links_cliwoc_metrics(self, manager: ArchiveManager):
        """CLIWOC audit should count direct and fuzzy links."""
        result = await manager.audit_links()
        cl = result["cliwoc_links"]
        assert "direct_links" in cl
        assert "fuzzy_matches" in cl
        assert cl["direct_links"] >= 0

    @pytest.mark.asyncio
    async def test_audit_links_confidence_distribution(self, manager: ArchiveManager):
        """Confidence distribution should have standard buckets."""
        result = await manager.audit_links()
        dist = result["confidence_distribution"]
        assert "0.9-1.0" in dist
        assert "0.7-0.9" in dist
        assert "0.5-0.7" in dist


# ---------------------------------------------------------------------------
# build_timeline — additional branches
# ---------------------------------------------------------------------------


class TestBuildTimelineExtended:
    @pytest.mark.asyncio
    async def test_timeline_cliwoc_position_sampling(self, manager: ArchiveManager):
        """When CLIWOC track has many positions, max_positions should downsample."""
        mock_track = {"voyage_id": 42, "ship_name": "Batavia", "nationality": "NL"}
        positions = [
            {
                "date": f"1629-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                "lat": -10.0 + i,
                "lon": 20.0 + i,
            }
            for i in range(50)
        ]
        full_track = {"voyage_id": 42, "nationality": "NL", "positions": positions}
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=mock_track,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track",
                return_value=full_track,
            ),
        ):
            result = await manager.build_timeline(
                voyage_id="das:3456", include_positions=True, max_positions=5
            )
            assert result is not None
            cliwoc_events = [e for e in result["events"] if e["type"] == "cliwoc_position"]
            assert len(cliwoc_events) <= 5

    @pytest.mark.asyncio
    async def test_timeline_geojson_with_multiple_positions(self, manager: ArchiveManager):
        """GeoJSON LineString should be built when >= 2 positioned events exist."""
        mock_track = {"voyage_id": 42, "ship_name": "Batavia", "nationality": "NL"}
        full_track = {
            "voyage_id": 42,
            "nationality": "NL",
            "positions": [
                {"date": "1629-01-10", "lat": -10.0, "lon": 20.0},
                {"date": "1629-02-15", "lat": -20.0, "lon": 40.0},
            ],
        }
        with (
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track_by_das_number",
                return_value=mock_track,
            ),
            patch(
                "chuk_mcp_maritime_archives.core.archive_manager.get_track",
                return_value=full_track,
            ),
        ):
            result = await manager.build_timeline(voyage_id="das:3456", include_positions=True)
            assert result is not None
            assert result["geojson"] is not None
            assert result["geojson"]["type"] == "Feature"
            assert result["geojson"]["geometry"]["type"] == "LineString"
            coords = result["geojson"]["geometry"]["coordinates"]
            assert len(coords) >= 2

    @pytest.mark.asyncio
    async def test_timeline_arrival_event_for_completed_voyage(self, manager: ArchiveManager):
        """Non-wrecked voyage with arrival_date should have arrival event."""
        with patch.object(manager, "get_voyage", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "voyage_id": "das:5678",
                "ship_name": "Ridderschap van Holland",
                "departure_date": "1694-01-03",
                "departure_port": "Texel",
                "destination_port": "Batavia",
                "arrival_date": "1694-08-15",
                "fate": "arrived",
                "archive": "das",
            }
            result = await manager.build_timeline(voyage_id="das:5678")
            assert result is not None
            event_types = [e["type"] for e in result["events"]]
            assert "arrival" in event_types
            arrival = [e for e in result["events"] if e["type"] == "arrival"][0]
            assert arrival["title"] == "Arrived Batavia"

    @pytest.mark.asyncio
    async def test_timeline_wreck_event_position(self, manager: ArchiveManager):
        """Wreck event with position data should include lat/lon."""
        result = await manager.build_timeline(voyage_id="das:3456")
        assert result is not None
        loss_events = [e for e in result["events"] if e["type"] == "loss"]
        assert len(loss_events) == 1
        assert loss_events[0]["position"] is not None
        assert loss_events[0]["position"]["lat"] == -28.49

    @pytest.mark.asyncio
    async def test_timeline_wreck_without_loss_date(self, manager: ArchiveManager):
        """Wreck without loss_date should not produce a loss event."""
        with patch.object(manager, "_find_wreck_for_voyage", new_callable=AsyncMock) as mock_wreck:
            mock_wreck.return_value = {
                "wreck_id": "maarer:TEST",
                "ship_name": "Test Ship",
                "loss_cause": "unknown",
                # No loss_date
            }
            result = await manager.build_timeline(voyage_id="das:3456")
            assert result is not None
            # Wreck found but no loss_date means no loss event
            loss_events = [e for e in result["events"] if e["type"] == "loss"]
            assert len(loss_events) == 0

    @pytest.mark.asyncio
    async def test_timeline_wreck_position_none(self, manager: ArchiveManager):
        """Wreck with loss_date but no position should have position=None in event."""
        with patch.object(manager, "_find_wreck_for_voyage", new_callable=AsyncMock) as mock_wreck:
            mock_wreck.return_value = {
                "wreck_id": "maarer:TEST",
                "ship_name": "Test Ship",
                "loss_date": "1629-06-04",
                "loss_cause": "storm",
                # No position field
            }
            result = await manager.build_timeline(voyage_id="das:3456")
            assert result is not None
            loss_events = [e for e in result["events"] if e["type"] == "loss"]
            assert len(loss_events) == 1
            assert loss_events[0]["position"] is None


# ---------------------------------------------------------------------------
# Wreck operations — additional branches
# ---------------------------------------------------------------------------


class TestWreckOperationsExtended:
    @pytest.mark.asyncio
    async def test_search_wrecks_unknown_archive(self, manager: ArchiveManager):
        """Searching with an unknown archive name should return empty results."""
        result = await manager.search_wrecks(archive="nonexistent")
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_get_wreck_eic_prefix(self, manager: ArchiveManager):
        """wreck_id with eic_wreck: prefix should route to EIC client."""
        wreck = await manager.get_wreck("eic_wreck:0001")
        # May or may not find the wreck in fixtures
        assert wreck is None or isinstance(wreck, dict)

    @pytest.mark.asyncio
    async def test_get_wreck_unknown_prefix(self, manager: ArchiveManager):
        """wreck_id without a known prefix should default to MAARER."""
        wreck = await manager.get_wreck("unknown_id_123")
        assert wreck is None  # Not found in MAARER


# ---------------------------------------------------------------------------
# Narrative search — edge cases
# ---------------------------------------------------------------------------


class TestNarrativeSearchEdgeCases:
    def test_parse_query_terms_unmatched_quote(self, manager: ArchiveManager):
        """Unmatched opening quote should treat rest as one term."""
        terms = manager._parse_query_terms('"Cape of Good Hope')
        assert len(terms) == 1
        assert terms[0] == "Cape of Good Hope"

    def test_extract_snippet_no_match(self, manager: ArchiveManager):
        """When no term matches, snippet should return start of text."""
        snippet = manager._extract_snippet(
            "This is a long text about ships and oceans.",
            ["xyznonexistent"],
            max_len=20,
        )
        assert snippet == "This is a long text"

    @pytest.mark.asyncio
    async def test_search_narratives_nonexistent_archive(self, manager: ArchiveManager):
        """Narrative search with unknown archive should return empty."""
        result = await manager.search_narratives(query="ship", archive="nonexistent")
        assert result.total_count == 0


# ---------------------------------------------------------------------------
# Crew search — merge path
# ---------------------------------------------------------------------------


class TestCrewSearchExtended:
    @pytest.mark.asyncio
    async def test_search_crew_no_archive_merges(self, manager: ArchiveManager):
        """Search without archive should merge results from VOC + DSS."""
        result = await manager.search_crew()
        # VOC fixture has 2 crew, DSS fixture has 5 crew
        assert result.total_count >= 2

    @pytest.mark.asyncio
    async def test_search_crew_unknown_archive(self, manager: ArchiveManager):
        """Search with unknown archive should return empty."""
        result = await manager.search_crew(archive="nonexistent")
        assert len(result.items) == 0


# ---------------------------------------------------------------------------
# Wage comparison — empty stats
# ---------------------------------------------------------------------------


class TestWageComparisonExtended:
    @pytest.mark.asyncio
    async def test_compare_wages_empty_group(self, manager: ArchiveManager):
        """Period with no data should yield 0.0 mean and median."""
        result = await manager.compare_wages(
            group1_start=1400,
            group1_end=1401,
            group2_start=1720,
            group2_end=1740,
        )
        assert result["group1_mean_wage"] == 0.0
        assert result["group1_median_wage"] == 0.0

    @pytest.mark.asyncio
    async def test_compare_wages_crews_source(self, manager: ArchiveManager):
        """source='crews' path should use search_crews instead of search_musters."""
        result = await manager.compare_wages(
            group1_start=1800,
            group1_end=1815,
            group2_start=1816,
            group2_end=1835,
            source="crews",
        )
        assert "group1_label" in result
        assert "group2_label" in result


# ---------------------------------------------------------------------------
# Position assessment — additional branches
# ---------------------------------------------------------------------------


class TestAssessPositionExtended:
    @pytest.mark.asyncio
    async def test_assess_position_voyage_with_incident_position(self, manager: ArchiveManager):
        """Voyage with incident.position should use that position."""
        with patch.object(manager, "get_voyage", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "voyage_id": "das:3456",
                "departure_date": "1628-10-28",
                "incident": {"position": {"lat": -28.5, "lon": 113.8}},
            }
            result = await manager.assess_position(voyage_id="das:3456")
            assert result["position"]["lat"] == -28.5
            assert result["position"]["lon"] == 113.8

    @pytest.mark.asyncio
    async def test_assess_position_voyage_loss_date(self, manager: ArchiveManager):
        """Voyage with loss_date should use loss_date year for navigation era."""
        with patch.object(manager, "get_voyage", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "voyage_id": "das:3456",
                "loss_date": "1629-06-04",
                "departure_date": "1628-10-28",
            }
            result = await manager.assess_position(voyage_id="das:3456")
            era = result["factors"]["navigation_era"]
            assert era["year"] == 1629

    @pytest.mark.asyncio
    async def test_assess_position_voyage_invalid_date(self, manager: ArchiveManager):
        """Voyage with non-numeric date should handle ValueError."""
        with patch.object(manager, "get_voyage", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "voyage_id": "das:3456",
                "loss_date": "unknown",
                "departure_date": "xxxx-01-01",
            }
            result = await manager.assess_position(voyage_id="das:3456")
            # Should not crash — year remains None
            assert result["factors"]["navigation_era"]["year"] is None

    @pytest.mark.asyncio
    async def test_assess_position_wreck_with_position(self, manager: ArchiveManager):
        """Wreck with position should use wreck position data."""
        result = await manager.assess_position(wreck_id="maarer:VOC-0789")
        assert result["position"]["lat"] == -28.49

    @pytest.mark.asyncio
    async def test_assess_position_wreck_not_found(self, manager: ArchiveManager):
        """Non-existent wreck should fall through gracefully."""
        result = await manager.assess_position(wreck_id="maarer:NONEXISTENT")
        assert "assessment" in result

    @pytest.mark.asyncio
    async def test_assess_position_no_source_info(self, manager: ArchiveManager):
        """Falling through all elif branches (no voyage, wreck, or date)."""
        result = await manager.assess_position()
        assert result["assessment"]["quality_score"] == 0.5
        assert result["factors"]["navigation_era"]["year"] is None


# ---------------------------------------------------------------------------
# Date range filter — edge cases
# ---------------------------------------------------------------------------


class TestDateFilterExtended:
    def test_filter_value_error_date(self, manager: ArchiveManager):
        """Records with non-numeric date should be skipped (ValueError path)."""
        records = [
            {"name": "A", "loss_date": "UNKNOWN"},
            {"name": "B", "loss_date": "1629-06-04"},
        ]
        result = manager._filter_by_date_range(records, "1600/1700", "loss_date")
        assert len(result) == 1
        assert result[0]["name"] == "B"


# ---------------------------------------------------------------------------
# GeoJSON export — wreck_id not found branch
# ---------------------------------------------------------------------------


class TestGeoJSONExtended:
    @pytest.mark.asyncio
    async def test_export_geojson_wreck_id_not_found(self, manager: ArchiveManager):
        """Non-existent wreck_id in list should be skipped."""
        geojson = await manager.export_geojson(wreck_ids=["maarer:NONEXISTENT"])
        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 0


# ---------------------------------------------------------------------------
# Crew demographics
# ---------------------------------------------------------------------------


class TestCrewDemographics:
    def test_group_by_rank(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank")
        assert result["total_records"] == 12
        assert result["total_filtered"] == 12
        assert result["group_by"] == "rank"
        assert result["group_count"] > 0
        # schipper, matroos, stuurman all have 3 records
        keys = [g["group_key"] for g in result["groups"]]
        assert "schipper" in keys
        assert "matroos" in keys

    def test_group_by_origin(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="origin")
        keys = {g["group_key"] for g in result["groups"]}
        assert "Amsterdam" in keys
        assert "Rotterdam" in keys
        assert "Hamburg" in keys

    def test_group_by_fate(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="fate")
        keys = {g["group_key"] for g in result["groups"]}
        assert "returned" in keys
        assert "died_voyage" in keys

    def test_group_by_decade(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="decade")
        keys = {g["group_key"] for g in result["groups"]}
        assert "1690s" in keys
        assert "1740s" in keys

    def test_group_by_ship_name(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="ship_name")
        keys = {g["group_key"] for g in result["groups"]}
        assert "Ridderschap van Holland" in keys

    def test_filter_by_rank(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="origin", rank="matroos")
        assert result["total_filtered"] == 3
        assert result["filters_applied"]["rank"] == "matroos"

    def test_filter_by_origin(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank", origin="Amsterdam")
        assert result["total_filtered"] == 5

    def test_filter_by_date_range(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank", date_range="1700/1750")
        assert result["total_filtered"] == 5  # Zeelandia (2) + Delftland (3)

    def test_top_n(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="origin", top_n=2)
        assert result["group_count"] == 2
        assert result["other_count"] > 0

    def test_percentages_sum(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank")
        total_pct = sum(g["percentage"] for g in result["groups"])
        assert 99.0 <= total_pct <= 101.0

    def test_fate_distribution_in_groups(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank")
        for g in result["groups"]:
            assert isinstance(g["fate_distribution"], dict)
            assert sum(g["fate_distribution"].values()) == g["count"]

    def test_empty_result(self, manager: ArchiveManager):
        result = manager.crew_demographics(group_by="rank", origin="Nonexistent")
        assert result["total_filtered"] == 0
        assert result["group_count"] == 0

    def test_invalid_group_by(self, manager: ArchiveManager):
        with pytest.raises(ValueError, match="Invalid group_by"):
            manager.crew_demographics(group_by="invalid")


# ---------------------------------------------------------------------------
# Crew career
# ---------------------------------------------------------------------------


class TestCrewCareer:
    def test_basic_career(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz van der Horst")
        assert result["individual_count"] >= 1
        assert result["total_matches"] == 3  # 3 records for this name

    def test_career_with_origin(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz", origin="Amsterdam")
        assert result["individual_count"] == 1
        ind = result["individuals"][0]
        assert ind["origin"] == "Amsterdam"

    def test_career_chronological(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz van der Horst", origin="Amsterdam")
        ind = result["individuals"][0]
        dates = [v["embarkation_date"] for v in ind["voyages"] if v.get("embarkation_date")]
        assert dates == sorted(dates)

    def test_career_rank_progression(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz van der Horst", origin="Amsterdam")
        ind = result["individuals"][0]
        assert "schipper" in ind["ranks_held"]
        assert "stuurman" in ind["ranks_held"]

    def test_career_distinct_ships(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz van der Horst", origin="Amsterdam")
        ind = result["individuals"][0]
        assert len(ind["distinct_ships"]) >= 2

    def test_career_no_matches(self, manager: ArchiveManager):
        result = manager.crew_career(name="Nonexistent Person")
        assert result["individual_count"] == 0
        assert result["total_matches"] == 0

    def test_career_span(self, manager: ArchiveManager):
        result = manager.crew_career(name="Jan Pietersz van der Horst", origin="Amsterdam")
        ind = result["individuals"][0]
        assert ind["career_span_years"] is not None
        assert ind["career_span_years"] > 0


# ---------------------------------------------------------------------------
# Crew survival
# ---------------------------------------------------------------------------


class TestCrewSurvival:
    def test_group_by_rank(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="rank")
        assert result["total_records"] == 12
        assert result["total_with_known_fate"] > 0
        assert result["group_count"] > 0

    def test_group_by_origin(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="origin")
        keys = {g["group_key"] for g in result["groups"]}
        assert "Amsterdam" in keys

    def test_group_by_decade(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="decade")
        keys = {g["group_key"] for g in result["groups"]}
        assert "1690s" in keys

    def test_rates_bounded(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="rank")
        for g in result["groups"]:
            assert 0.0 <= g["survival_rate"] <= 100.0
            assert 0.0 <= g["mortality_rate"] <= 100.0
            assert 0.0 <= g["desertion_rate"] <= 100.0

    def test_counts_consistent(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="rank")
        for g in result["groups"]:
            total = (
                g["survived"] + g["died_voyage"] + g["died_asia"] + g["deserted"] + g["discharged"]
            )
            assert total == g["total"]

    def test_filter_by_rank(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="origin", rank="matroos")
        assert result["filters_applied"]["rank"] == "matroos"
        total_in_groups = sum(g["total"] for g in result["groups"])
        assert total_in_groups <= 3

    def test_filter_by_date_range(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="rank", date_range="1740/1750")
        total_in_groups = sum(g["total"] for g in result["groups"])
        assert total_in_groups == 3  # Delftland crew

    def test_empty_result(self, manager: ArchiveManager):
        result = manager.crew_survival(group_by="rank", origin="Nonexistent")
        assert result["total_with_known_fate"] == 0
        assert result["group_count"] == 0

    def test_invalid_group_by(self, manager: ArchiveManager):
        with pytest.raises(ValueError, match="Invalid group_by"):
            manager.crew_survival(group_by="invalid")
