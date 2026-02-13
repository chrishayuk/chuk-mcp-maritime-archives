"""Tests for ArchiveManager backed by local JSON fixture data."""

from unittest.mock import patch

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
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_search_crew_by_ship(self, manager: ArchiveManager):
        result = await manager.search_crew(ship_name="Ridderschap")
        assert len(result.items) == 2
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
            result = manager._find_cliwoc_track_for_voyage(voyage)
            assert result is not None
            assert result["voyage_id"] == 42
            assert "positions" not in result  # positions stripped from summary

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
