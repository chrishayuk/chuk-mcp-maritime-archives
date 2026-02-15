"""Tests for the CLIWOC ship tracks module."""

import json

import pytest

from chuk_mcp_maritime_archives.core.cliwoc_tracks import (
    _TRACKS,
    _bootstrap_did,
    _haversine_km,
    _mann_whitney_u,
    _month_in_range,
    _parse_period,
    aggregate_track_speeds,
    compare_speed_groups,
    compute_track_speeds,
    did_speed_test,
    export_speeds,
    get_date_range,
    get_position_count,
    get_track,
    get_track_count,
    list_nationalities,
    nearby_tracks,
    search_tracks,
    wind_direction_by_year,
)
from chuk_mcp_maritime_archives.core.galleon_analysis import galleon_transit_times

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Track data integrity
# ---------------------------------------------------------------------------


class TestTrackData:
    def test_has_tracks_loaded(self):
        assert get_track_count() > 0

    def test_has_positions(self):
        assert get_position_count() > 0

    def test_has_date_range(self):
        dr = get_date_range()
        assert dr != "unknown"
        assert "1662" in dr or "166" in dr

    def test_nationalities_present(self):
        nats = list_nationalities()
        assert len(nats) >= 2
        # UK and NL should be the largest
        assert "UK" in nats or "NL" in nats

    def test_all_tracks_have_required_fields(self):
        for track in _TRACKS[:100]:  # Sample first 100
            assert "voyage_id" in track
            assert "nationality" in track
            assert "positions" in track
            assert isinstance(track["positions"], list)
            assert track.get("position_count", 0) == len(track["positions"])

    def test_positions_have_required_fields(self):
        for track in _TRACKS[:50]:
            for pos in track["positions"][:5]:
                assert "lat" in pos
                assert "lon" in pos
                assert -90 <= pos["lat"] <= 90
                assert -180 <= pos["lon"] <= 180

    def test_nationalities_are_valid_codes(self):
        valid = {"NL", "UK", "ES", "FR", "SE", "US", "DE", "DK"}
        for track in _TRACKS[:200]:
            nat = track.get("nationality")
            if nat:
                assert nat in valid, f"Invalid nationality: {nat}"


# ---------------------------------------------------------------------------
# search_tracks
# ---------------------------------------------------------------------------


class TestSearchTracks:
    def test_no_filters(self):
        results = search_tracks(max_results=10)
        assert len(results) >= 1
        assert len(results) <= 10

    def test_filter_by_nationality(self):
        results = search_tracks(nationality="NL", max_results=20)
        assert len(results) >= 1
        for r in results:
            assert r["nationality"] == "NL"

    def test_filter_by_nationality_case_insensitive(self):
        results = search_tracks(nationality="nl", max_results=5)
        assert len(results) >= 1
        for r in results:
            assert r["nationality"] == "NL"

    def test_filter_by_year_range(self):
        results = search_tracks(year_start=1800, year_end=1810, max_results=50)
        for r in results:
            assert r.get("year_start") is not None
            assert r["year_start"] >= 1800
            assert r.get("year_end", 0) <= 1810

    def test_filter_combined(self):
        results = search_tracks(nationality="UK", year_start=1790, year_end=1800)
        for r in results:
            assert r["nationality"] == "UK"
            assert r.get("year_start", 9999) >= 1790

    def test_max_results_respected(self):
        results = search_tracks(max_results=3)
        assert len(results) <= 3

    def test_no_match(self):
        results = search_tracks(nationality="XX")
        assert len(results) == 0

    def test_results_exclude_positions(self):
        results = search_tracks(max_results=5)
        for r in results:
            assert "positions" not in r

    def test_results_have_summary_fields(self):
        results = search_tracks(max_results=5)
        for r in results:
            assert "voyage_id" in r
            assert "nationality" in r
            assert "position_count" in r


# ---------------------------------------------------------------------------
# get_track
# ---------------------------------------------------------------------------


class TestGetTrack:
    def test_existing_track(self):
        # Get first known voyage_id
        results = search_tracks(max_results=1)
        assert len(results) == 1
        vid = results[0]["voyage_id"]

        track = get_track(vid)
        assert track is not None
        assert track["voyage_id"] == vid
        assert "positions" in track
        assert len(track["positions"]) > 0

    def test_nonexistent_track(self):
        track = get_track(999999)
        assert track is None

    def test_positions_are_complete(self):
        results = search_tracks(max_results=1)
        vid = results[0]["voyage_id"]
        track = get_track(vid)

        assert track["position_count"] == len(track["positions"])
        for pos in track["positions"]:
            assert "date" in pos
            assert "lat" in pos
            assert "lon" in pos


# ---------------------------------------------------------------------------
# nearby_tracks
# ---------------------------------------------------------------------------


class TestNearbyTracks:
    def _find_known_position(self):
        """Find a date/position that's actually in the data."""
        for track in _TRACKS[:100]:
            for pos in track.get("positions", []):
                if pos.get("date"):
                    return pos["lat"], pos["lon"], pos["date"], track["voyage_id"]
        return None

    def test_finds_ship_at_known_position(self):
        result = self._find_known_position()
        if result is None:
            pytest.skip("No positions with dates in data")
        lat, lon, date, expected_vid = result

        hits = nearby_tracks(lat=lat, lon=lon, date=date, radius_km=10)
        assert len(hits) >= 1
        # The ship itself should be in the results
        voyage_ids = [h["voyage_id"] for h in hits]
        assert expected_vid in voyage_ids

    def test_zero_distance_for_exact_match(self):
        result = self._find_known_position()
        if result is None:
            pytest.skip("No positions with dates in data")
        lat, lon, date, expected_vid = result

        hits = nearby_tracks(lat=lat, lon=lon, date=date, radius_km=1)
        matching = [h for h in hits if h["voyage_id"] == expected_vid]
        assert len(matching) == 1
        assert matching[0]["distance_km"] < 0.1

    def test_no_results_remote_location(self):
        # Middle of nowhere, arbitrary date
        hits = nearby_tracks(lat=0.0, lon=0.0, date="1500-01-01", radius_km=10)
        assert len(hits) == 0

    def test_results_sorted_by_distance(self):
        result = self._find_known_position()
        if result is None:
            pytest.skip("No positions with dates in data")
        lat, lon, date, _ = result

        hits = nearby_tracks(lat=lat, lon=lon, date=date, radius_km=5000)
        if len(hits) > 1:
            for i in range(len(hits) - 1):
                assert hits[i]["distance_km"] <= hits[i + 1]["distance_km"]

    def test_results_have_distance_and_position(self):
        result = self._find_known_position()
        if result is None:
            pytest.skip("No positions with dates in data")
        lat, lon, date, _ = result

        hits = nearby_tracks(lat=lat, lon=lon, date=date, radius_km=5000)
        for h in hits:
            assert "distance_km" in h
            assert "matching_position" in h
            assert "lat" in h["matching_position"]
            assert "lon" in h["matching_position"]

    def test_max_results_respected(self):
        result = self._find_known_position()
        if result is None:
            pytest.skip("No positions with dates in data")
        lat, lon, date, _ = result

        hits = nearby_tracks(lat=lat, lon=lon, date=date, radius_km=50000, max_results=2)
        assert len(hits) <= 2


# ---------------------------------------------------------------------------
# Haversine helper
# ---------------------------------------------------------------------------


class TestHaversine:
    def test_same_point(self):
        assert _haversine_km(0, 0, 0, 0) == 0.0

    def test_known_distance(self):
        # London to Paris ~343km
        dist = _haversine_km(51.5, -0.12, 48.86, 2.35)
        assert 340 < dist < 360

    def test_antipodal(self):
        # Opposite sides of earth
        dist = _haversine_km(0, 0, 0, 180)
        assert 20000 < dist < 20100

    def test_equator_one_degree(self):
        # 1 degree at equator ~111km
        dist = _haversine_km(0, 0, 0, 1)
        assert 110 < dist < 112


# ---------------------------------------------------------------------------
# list_nationalities / helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_list_nationalities(self):
        nats = list_nationalities()
        assert isinstance(nats, dict)
        assert len(nats) >= 2

    def test_get_track_count(self):
        count = get_track_count()
        assert count > 0

    def test_get_position_count(self):
        count = get_position_count()
        assert count > 0
        assert count > get_track_count()  # More positions than tracks

    def test_get_date_range(self):
        dr = get_date_range()
        assert isinstance(dr, str)
        assert dr != "unknown"


# ---------------------------------------------------------------------------
# Track MCP tools
# ---------------------------------------------------------------------------


class TestTrackTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.tracks.api import register_tracks_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_tracks_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_search_tracks_no_filters(self):
        fn = self.mcp.get_tool("maritime_search_tracks")
        result = await fn(max_results=5)
        parsed = json.loads(result)
        assert "track_count" in parsed
        assert parsed["track_count"] >= 1
        assert len(parsed["tracks"]) <= 5

    @pytest.mark.asyncio
    async def test_search_tracks_by_nationality(self):
        fn = self.mcp.get_tool("maritime_search_tracks")
        result = await fn(nationality="ES", max_results=10)
        parsed = json.loads(result)
        assert parsed["track_count"] >= 1
        for t in parsed["tracks"]:
            assert t["nationality"] == "ES"

    @pytest.mark.asyncio
    async def test_search_tracks_by_year(self):
        fn = self.mcp.get_tool("maritime_search_tracks")
        result = await fn(year_start=1800, year_end=1810, max_results=10)
        parsed = json.loads(result)
        assert parsed["track_count"] >= 1

    @pytest.mark.asyncio
    async def test_search_tracks_no_results(self):
        fn = self.mcp.get_tool("maritime_search_tracks")
        result = await fn(nationality="XX")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_tracks_text_mode(self):
        fn = self.mcp.get_tool("maritime_search_tracks")
        result = await fn(nationality="NL", max_results=3, output_mode="text")
        assert "Voyage" in result
        assert "NL" in result

    @pytest.mark.asyncio
    async def test_get_track_success(self):
        # First find a valid ID
        search_fn = self.mcp.get_tool("maritime_search_tracks")
        search_result = await search_fn(max_results=1)
        parsed_search = json.loads(search_result)
        vid = parsed_search["tracks"][0]["voyage_id"]

        fn = self.mcp.get_tool("maritime_get_track")
        result = await fn(voyage_id=vid)
        parsed = json.loads(result)
        assert "track" in parsed
        assert parsed["track"]["voyage_id"] == vid
        assert "positions" in parsed["track"]

    @pytest.mark.asyncio
    async def test_get_track_not_found(self):
        fn = self.mcp.get_tool("maritime_get_track")
        result = await fn(voyage_id=999999)
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_track_text_mode(self):
        search_fn = self.mcp.get_tool("maritime_search_tracks")
        search_result = await search_fn(max_results=1)
        parsed_search = json.loads(search_result)
        vid = parsed_search["tracks"][0]["voyage_id"]

        fn = self.mcp.get_tool("maritime_get_track")
        result = await fn(voyage_id=vid, output_mode="text")
        assert "CLIWOC Voyage" in result

    @pytest.mark.asyncio
    async def test_nearby_tracks_success(self):
        # Find a known position
        search_fn = self.mcp.get_tool("maritime_search_tracks")
        search_result = await search_fn(max_results=1)
        parsed_search = json.loads(search_result)
        vid = parsed_search["tracks"][0]["voyage_id"]

        get_fn = self.mcp.get_tool("maritime_get_track")
        track_result = await get_fn(voyage_id=vid)
        track = json.loads(track_result)["track"]
        pos = track["positions"][0]

        fn = self.mcp.get_tool("maritime_nearby_tracks")
        result = await fn(lat=pos["lat"], lon=pos["lon"], date=pos["date"], radius_km=500)
        parsed = json.loads(result)
        assert "track_count" in parsed
        assert parsed["track_count"] >= 1

    @pytest.mark.asyncio
    async def test_nearby_tracks_no_results(self):
        fn = self.mcp.get_tool("maritime_nearby_tracks")
        result = await fn(lat=0.0, lon=0.0, date="1500-01-01", radius_km=10)
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_nearby_tracks_text_mode(self):
        search_fn = self.mcp.get_tool("maritime_search_tracks")
        search_result = await search_fn(max_results=1)
        parsed_search = json.loads(search_result)
        vid = parsed_search["tracks"][0]["voyage_id"]

        get_fn = self.mcp.get_tool("maritime_get_track")
        track_result = await get_fn(voyage_id=vid)
        track = json.loads(track_result)["track"]
        pos = track["positions"][0]

        fn = self.mcp.get_tool("maritime_nearby_tracks")
        result = await fn(
            lat=pos["lat"],
            lon=pos["lon"],
            date=pos["date"],
            radius_km=500,
            output_mode="text",
        )
        assert "Voyage" in result

    @pytest.mark.asyncio
    async def test_search_tracks_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_search_tracks")
        with patch(
            "chuk_mcp_maritime_archives.tools.tracks.api.search_tracks",
            side_effect=RuntimeError("boom"),
        ):
            result = await fn()
        parsed = json.loads(result)
        assert "boom" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_track_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_get_track")
        with patch(
            "chuk_mcp_maritime_archives.tools.tracks.api.get_track",
            side_effect=RuntimeError("crash"),
        ):
            result = await fn(voyage_id=1)
        parsed = json.loads(result)
        assert "crash" in parsed["error"]

    @pytest.mark.asyncio
    async def test_nearby_tracks_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_nearby_tracks")
        with patch(
            "chuk_mcp_maritime_archives.tools.tracks.api.nearby_tracks",
            side_effect=RuntimeError("fail"),
        ):
            result = await fn(lat=0, lon=0, date="2000-01-01")
        parsed = json.loads(result)
        assert "fail" in parsed["error"]


# ---------------------------------------------------------------------------
# Geographic bounding box search
# ---------------------------------------------------------------------------


class TestSearchTracksBBox:
    def test_search_with_lat_bounds(self):
        # Southern hemisphere tracks (e.g., Roaring Forties area)
        results = search_tracks(lat_min=-60, lat_max=-20, max_results=10)
        assert len(results) >= 1
        # All returned tracks have at least one position in the bbox
        for r in results:
            track = get_track(r["voyage_id"])
            assert track is not None
            has_pos_in_range = any(-60 <= p["lat"] <= -20 for p in track.get("positions", []))
            assert has_pos_in_range

    def test_search_with_full_bbox(self):
        # Indian Ocean region
        results = search_tracks(lat_min=-50, lat_max=-30, lon_min=15, lon_max=110, max_results=10)
        assert isinstance(results, list)
        # All results must have positions in the bbox
        for r in results:
            track = get_track(r["voyage_id"])
            assert track is not None
            has_pos = any(
                -50 <= p["lat"] <= -30 and 15 <= p["lon"] <= 110 for p in track.get("positions", [])
            )
            assert has_pos

    def test_bbox_no_results(self):
        # Middle of Pacific with tight bounds — unlikely to find tracks
        results = search_tracks(lat_min=60, lat_max=70, lon_min=-170, lon_max=-160, max_results=10)
        assert isinstance(results, list)

    def test_bbox_combined_with_nationality(self):
        results = search_tracks(nationality="NL", lat_min=-50, lat_max=-30, max_results=10)
        for r in results:
            assert r["nationality"] == "NL"


# ---------------------------------------------------------------------------
# Compute track speeds
# ---------------------------------------------------------------------------


class TestComputeTrackSpeeds:
    def _get_first_voyage_id(self):
        results = search_tracks(max_results=1)
        return results[0]["voyage_id"] if results else None

    def test_compute_speeds_basic(self):
        vid = self._get_first_voyage_id()
        if vid is None:
            pytest.skip("No tracks loaded")
        result = compute_track_speeds(vid)
        assert result is not None
        assert result["voyage_id"] == vid
        assert isinstance(result["speeds"], list)
        assert result["observation_count"] == len(result["speeds"])
        assert result["mean_km_day"] >= 0

    def test_compute_speeds_not_found(self):
        result = compute_track_speeds(999999)
        assert result is None

    def test_compute_speeds_with_bbox(self):
        # Find a track with positions in Southern Ocean
        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=1)
        if not tracks:
            pytest.skip("No tracks in Roaring Forties region")
        vid = tracks[0]["voyage_id"]
        result = compute_track_speeds(vid, lat_min=-50, lat_max=-30)
        assert result is not None
        # All returned positions should have mid-lat in range
        for s in result["speeds"]:
            assert -55 <= s["lat"] <= -25  # Some tolerance for midpoint

    def test_speed_bounds_filter(self):
        vid = self._get_first_voyage_id()
        if vid is None:
            pytest.skip("No tracks loaded")
        result = compute_track_speeds(vid, min_speed=50, max_speed=200)
        assert result is not None
        for s in result["speeds"]:
            assert 50 <= s["km_day"] <= 200

    def test_speeds_have_direction(self):
        vid = self._get_first_voyage_id()
        if vid is None:
            pytest.skip("No tracks loaded")
        result = compute_track_speeds(vid)
        assert result is not None
        for s in result["speeds"]:
            assert s.get("direction") in ("eastbound", "westbound")


# ---------------------------------------------------------------------------
# Aggregate track speeds
# ---------------------------------------------------------------------------


class TestAggregateTrackSpeeds:
    def test_aggregate_by_decade(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            lon_min=15,
            lon_max=110,
        )
        assert result["total_observations"] > 0
        assert result["total_voyages"] > 0
        assert len(result["groups"]) > 0
        for g in result["groups"]:
            assert g["n"] > 0
            assert g["mean_km_day"] > 0
            assert "group_key" in g
            # Decade keys should be numeric strings
            assert g["group_key"].isdigit()

    def test_aggregate_by_month(self):
        result = aggregate_track_speeds(
            group_by="month",
            lat_min=-50,
            lat_max=-30,
        )
        assert len(result["groups"]) > 0
        for g in result["groups"]:
            month = int(g["group_key"])
            assert 1 <= month <= 12

    def test_aggregate_by_direction(self):
        result = aggregate_track_speeds(
            group_by="direction",
            lat_min=-50,
            lat_max=-30,
        )
        assert len(result["groups"]) > 0
        keys = {g["group_key"] for g in result["groups"]}
        assert keys <= {"eastbound", "westbound"}

    def test_aggregate_by_nationality(self):
        result = aggregate_track_speeds(
            group_by="nationality",
            lat_min=-50,
            lat_max=-30,
        )
        assert len(result["groups"]) > 0
        for g in result["groups"]:
            assert len(g["group_key"]) == 2  # Two-letter nationality code

    def test_aggregate_with_direction_filter(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            direction="eastbound",
        )
        assert result["direction_filter"] == "eastbound"
        assert result["total_observations"] > 0

    def test_aggregate_with_nationality_filter(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            nationality="NL",
        )
        assert result["nationality_filter"] == "NL"

    def test_aggregate_stats_structure(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        for g in result["groups"]:
            assert "n" in g
            assert "mean_km_day" in g
            assert "median_km_day" in g
            assert "std_km_day" in g
            assert "ci_lower" in g
            assert "ci_upper" in g
            assert g["ci_lower"] <= g["mean_km_day"] <= g["ci_upper"]

    def test_aggregate_by_year(self):
        result = aggregate_track_speeds(
            group_by="year",
            lat_min=-50,
            lat_max=-30,
            lon_min=15,
            lon_max=110,
        )
        assert result["total_observations"] > 0
        assert len(result["groups"]) > 0
        for g in result["groups"]:
            assert g["group_key"].isdigit()
            year = int(g["group_key"])
            assert 1662 <= year <= 1855
            assert g["n"] > 0
            assert g["mean_km_day"] > 0

    def test_aggregate_empty_region(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=85,
            lat_max=89,  # Deep Arctic — no CLIWOC tracks here
            lon_min=170,
            lon_max=180,
        )
        assert result["total_observations"] == 0
        assert len(result["groups"]) == 0

    def test_aggregate_with_month_filter(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        assert result["month_start_filter"] == 6
        assert result["month_end_filter"] == 8

    def test_aggregate_with_month_wrap_around(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            month_start=11,
            month_end=2,
        )
        assert result["month_start_filter"] == 11
        assert result["month_end_filter"] == 2

    def test_aggregate_month_filter_reduces_count(self):
        full = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        filtered = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        assert filtered["total_observations"] <= full["total_observations"]

    def test_aggregate_month_filter_in_response(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            month_start=1,
            month_end=3,
        )
        assert "month_start_filter" in result
        assert "month_end_filter" in result
        assert result["month_start_filter"] == 1
        assert result["month_end_filter"] == 3

    def test_aggregate_by_voyage(self):
        """Voyage-level aggregation should give fewer data points."""
        obs_result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        voy_result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
        )
        assert voy_result["aggregate_by"] == "voyage"
        assert obs_result["aggregate_by"] == "observation"
        # Voyage-level should have fewer data points
        assert voy_result["total_observations"] < obs_result["total_observations"]
        assert voy_result["total_observations"] > 0

    def test_aggregate_by_voyage_response_field(self):
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
        )
        assert "aggregate_by" in result
        assert result["aggregate_by"] == "voyage"

    def test_aggregate_by_observation_default(self):
        """Default behavior unchanged."""
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["aggregate_by"] == "observation"


# ---------------------------------------------------------------------------
# Compare speed groups
# ---------------------------------------------------------------------------


class TestCompareSpeedGroups:
    def test_compare_two_periods(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["period1_n"] > 0
        assert result["period2_n"] > 0
        assert result["period1_label"] == "1750/1789"
        assert result["period2_label"] == "1820/1859"
        assert isinstance(result["mann_whitney_u"], float)
        assert isinstance(result["z_score"], float)
        assert isinstance(result["p_value"], float)
        assert isinstance(result["significant"], bool)
        assert isinstance(result["effect_size"], float)

    def test_compare_with_direction_filter(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            direction="eastbound",
        )
        assert result["period1_n"] > 0
        assert result["period2_n"] > 0

    def test_compare_empty_period(self):
        result = compare_speed_groups(
            period1_years="1500/1510",
            period2_years="1520/1530",
            lat_min=-50,
            lat_max=-30,
        )
        # Should handle gracefully — no data in these periods
        assert result["period1_n"] == 0
        assert result["p_value"] == 1.0

    def test_compare_with_month_filter(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        assert result["month_start_filter"] == 6
        assert result["month_end_filter"] == 8
        assert isinstance(result["p_value"], float)

    def test_compare_with_month_wrap_around(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            month_start=11,
            month_end=2,
        )
        assert result["month_start_filter"] == 11
        assert result["month_end_filter"] == 2

    def test_compare_voyage_level(self):
        """Voyage-level comparison should give fewer data points."""
        obs_result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
        )
        voy_result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
        )
        assert voy_result["aggregate_by"] == "voyage"
        assert voy_result["period1_n"] < obs_result["period1_n"]
        assert voy_result["period1_n"] > 0

    def test_compare_include_samples(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            include_samples=True,
        )
        assert "period1_samples" in result
        assert "period2_samples" in result
        assert isinstance(result["period1_samples"], list)
        assert len(result["period1_samples"]) == result["period1_n"]

    def test_compare_include_samples_voyage(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
            include_samples=True,
        )
        assert len(result["period1_samples"]) == result["period1_n"]
        assert result["aggregate_by"] == "voyage"

    def test_compare_no_samples_by_default(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
        )
        assert "period1_samples" not in result


# ---------------------------------------------------------------------------
# Bootstrap DiD
# ---------------------------------------------------------------------------


class TestBootstrapDiD:
    def test_known_signal(self):
        """Synthetic data with a known directional signal."""
        pre_east = [100.0, 110.0, 105.0, 95.0, 108.0]
        pre_west = [90.0, 85.0, 88.0, 92.0, 87.0]
        post_east = [140.0, 135.0, 145.0, 138.0, 142.0]
        post_west = [91.0, 89.0, 93.0, 88.0, 90.0]
        did, ci_lo, ci_hi, p = _bootstrap_did(
            pre_east, pre_west, post_east, post_west, n_bootstrap=5000, seed=42
        )
        # Eastbound gained ~36, westbound gained ~2 → DiD ≈ +34
        assert did > 20
        assert p < 0.05
        assert ci_lo > 0  # CI should not contain 0

    def test_no_signal(self):
        """Equal groups → no significant DiD."""
        vals = [100.0, 105.0, 98.0, 102.0, 101.0]
        did, ci_lo, ci_hi, p = _bootstrap_did(vals, vals, vals, vals, n_bootstrap=5000, seed=42)
        assert abs(did) < 1e-10
        assert ci_lo <= 0 <= ci_hi
        assert p > 0.05

    def test_empty_cell(self):
        """Empty cell returns p=1.0."""
        did, ci_lo, ci_hi, p = _bootstrap_did([], [1.0], [1.0], [1.0])
        assert did == 0.0
        assert p == 1.0

    def test_reproducibility(self):
        """Same seed gives same result."""
        args = ([100.0, 110.0], [90.0, 95.0], [120.0, 130.0], [92.0, 98.0])
        r1 = _bootstrap_did(*args, n_bootstrap=1000, seed=123)
        r2 = _bootstrap_did(*args, n_bootstrap=1000, seed=123)
        assert r1 == r2


# ---------------------------------------------------------------------------
# DiD speed test
# ---------------------------------------------------------------------------


class TestDidSpeedTest:
    def test_basic_did_test(self):
        result = did_speed_test(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
        )
        assert "did_estimate" in result
        assert "did_ci_lower" in result
        assert "did_ci_upper" in result
        assert "did_p_value" in result
        assert "significant" in result
        assert "period1_eastbound_n" in result
        assert "period2_westbound_n" in result
        assert "eastbound_diff" in result
        assert "westbound_diff" in result
        assert result["aggregate_by"] == "voyage"

    def test_did_voyage_vs_observation(self):
        """Voyage-level should have fewer data points."""
        voy = did_speed_test(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
        )
        obs = did_speed_test(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="observation",
        )
        assert voy["period1_eastbound_n"] < obs["period1_eastbound_n"]

    def test_did_empty_period(self):
        result = did_speed_test(
            period1_years="1500/1510",
            period2_years="1520/1530",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["did_p_value"] == 1.0
        assert result["did_estimate"] == 0.0

    def test_did_with_month_filter(self):
        result = did_speed_test(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        assert result["month_start_filter"] == 6
        assert result["month_end_filter"] == 8
        assert isinstance(result["did_p_value"], float)


# ---------------------------------------------------------------------------
# Mann-Whitney U helper
# ---------------------------------------------------------------------------


class TestMannWhitneyU:
    def test_identical_groups(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        u, z, p = _mann_whitney_u(x, y)
        assert abs(z) < 0.5  # Not significant
        assert p > 0.05

    def test_different_groups(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 11.0, 12.0, 13.0, 14.0]
        u, z, p = _mann_whitney_u(x, y)
        assert abs(z) > 1.5
        assert p < 0.05

    def test_empty_group(self):
        u, z, p = _mann_whitney_u([], [1.0, 2.0, 3.0])
        assert p == 1.0

    def test_single_element(self):
        u, z, p = _mann_whitney_u([1.0], [2.0])
        assert isinstance(u, float)
        assert isinstance(z, float)
        assert isinstance(p, float)


# ---------------------------------------------------------------------------
# Month range helper
# ---------------------------------------------------------------------------


class TestMonthInRange:
    def test_no_filter(self):
        assert _month_in_range(5, None, None) is True
        assert _month_in_range(1, None, None) is True
        assert _month_in_range(12, None, None) is True

    def test_normal_range(self):
        # Jun-Aug (austral winter)
        assert _month_in_range(6, 6, 8) is True
        assert _month_in_range(7, 6, 8) is True
        assert _month_in_range(8, 6, 8) is True
        assert _month_in_range(5, 6, 8) is False
        assert _month_in_range(9, 6, 8) is False

    def test_wrap_around(self):
        # Nov-Feb (austral summer, wraps through December)
        assert _month_in_range(11, 11, 2) is True
        assert _month_in_range(12, 11, 2) is True
        assert _month_in_range(1, 11, 2) is True
        assert _month_in_range(2, 11, 2) is True
        assert _month_in_range(5, 11, 2) is False
        assert _month_in_range(10, 11, 2) is False

    def test_single_month(self):
        assert _month_in_range(6, 6, 6) is True
        assert _month_in_range(5, 6, 6) is False
        assert _month_in_range(7, 6, 6) is False

    def test_start_only(self):
        # start=6, end=None → treated as 6-12
        assert _month_in_range(6, 6, None) is True
        assert _month_in_range(12, 6, None) is True
        assert _month_in_range(5, 6, None) is False


# ---------------------------------------------------------------------------
# Analytics MCP tools
# ---------------------------------------------------------------------------


class TestAnalyticsTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_compute_track_speeds_success(self):
        # Use a known voyage ID from the loaded data
        tracks = search_tracks(max_results=1)
        if not tracks:
            pytest.skip("No tracks loaded")
        vid = tracks[0]["voyage_id"]

        fn = self.mcp.get_tool("maritime_compute_track_speeds")
        result = await fn(voyage_id=vid)
        parsed = json.loads(result)
        assert "voyage_id" in parsed
        assert "observation_count" in parsed
        assert "speeds" in parsed

    @pytest.mark.asyncio
    async def test_compute_track_speeds_not_found(self):
        fn = self.mcp.get_tool("maritime_compute_track_speeds")
        result = await fn(voyage_id=999999)
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_compute_track_speeds_text_mode(self):
        tracks = search_tracks(max_results=1)
        if not tracks:
            pytest.skip("No tracks loaded")
        vid = tracks[0]["voyage_id"]

        fn = self.mcp.get_tool("maritime_compute_track_speeds")
        result = await fn(voyage_id=vid, output_mode="text")
        assert "Voyage" in result
        assert "km/day" in result

    @pytest.mark.asyncio
    async def test_aggregate_track_speeds_success(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        parsed = json.loads(result)
        assert "total_observations" in parsed
        assert "groups" in parsed
        assert parsed["total_observations"] > 0

    @pytest.mark.asyncio
    async def test_aggregate_track_speeds_text_mode(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="direction",
            lat_min=-50,
            lat_max=-30,
            output_mode="text",
        )
        assert "km/day" in result

    @pytest.mark.asyncio
    async def test_compare_speed_groups_success(self):
        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        result = await fn(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
        )
        parsed = json.loads(result)
        assert "mann_whitney_u" in parsed
        assert "z_score" in parsed
        assert "p_value" in parsed
        assert "significant" in parsed

    @pytest.mark.asyncio
    async def test_compare_speed_groups_text_mode(self):
        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        result = await fn(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            output_mode="text",
        )
        assert "Mann-Whitney" in result

    @pytest.mark.asyncio
    async def test_compute_track_speeds_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_compute_track_speeds")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.compute_track_speeds",
            side_effect=RuntimeError("boom"),
        ):
            result = await fn(voyage_id=1)
        parsed = json.loads(result)
        assert "boom" in parsed["error"]

    @pytest.mark.asyncio
    async def test_aggregate_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.aggregate_track_speeds",
            side_effect=RuntimeError("fail"),
        ):
            result = await fn(group_by="decade")
        parsed = json.loads(result)
        assert "fail" in parsed["error"]

    @pytest.mark.asyncio
    async def test_compare_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.compare_speed_groups",
            side_effect=RuntimeError("crash"),
        ):
            result = await fn(period1_years="1750/1789", period2_years="1820/1859")
        parsed = json.loads(result)
        assert "crash" in parsed["error"]

    @pytest.mark.asyncio
    async def test_aggregate_with_month_filter(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        parsed = json.loads(result)
        assert parsed["month_start_filter"] == 6
        assert parsed["month_end_filter"] == 8

    @pytest.mark.asyncio
    async def test_compare_with_month_filter(self):
        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        result = await fn(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            month_start=6,
            month_end=8,
        )
        parsed = json.loads(result)
        assert parsed["month_start_filter"] == 6
        assert parsed["month_end_filter"] == 8

    @pytest.mark.asyncio
    async def test_aggregate_voyage_level_tool(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            aggregate_by="voyage",
        )
        parsed = json.loads(result)
        assert parsed["aggregate_by"] == "voyage"
        assert parsed["total_observations"] > 0

    @pytest.mark.asyncio
    async def test_compare_include_samples_tool(self):
        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        result = await fn(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            include_samples=True,
        )
        parsed = json.loads(result)
        assert "period1_samples" in parsed
        assert isinstance(parsed["period1_samples"], list)

    @pytest.mark.asyncio
    async def test_did_speed_test_tool(self):
        fn = self.mcp.get_tool("maritime_did_speed_test")
        result = await fn(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
        )
        parsed = json.loads(result)
        assert "did_estimate" in parsed
        assert "did_p_value" in parsed
        assert "significant" in parsed
        assert parsed["aggregate_by"] == "voyage"

    @pytest.mark.asyncio
    async def test_did_speed_test_text_mode(self):
        fn = self.mcp.get_tool("maritime_did_speed_test")
        result = await fn(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
            output_mode="text",
        )
        assert "DiD estimate" in result
        assert "km/day" in result

    @pytest.mark.asyncio
    async def test_did_speed_test_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_did_speed_test")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.did_speed_test",
            side_effect=RuntimeError("boom"),
        ):
            result = await fn(
                period1_years="1750/1783",
                period2_years="1784/1810",
            )
        parsed = json.loads(result)
        assert "boom" in parsed["error"]


# ---------------------------------------------------------------------------
# Bootstrap Mean Difference helper
# ---------------------------------------------------------------------------


class TestBootstrapMeanDiff:
    def test_known_signal(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import _bootstrap_mean_diff

        g1 = [100.0, 105.0, 98.0, 102.0, 101.0]
        g2 = [130.0, 135.0, 128.0, 132.0, 131.0]
        diff, ci_lo, ci_hi, p = _bootstrap_mean_diff(g1, g2, n_bootstrap=5000, seed=42)
        assert diff > 25  # ~30 difference
        assert p < 0.05
        assert ci_lo > 0

    def test_no_signal(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import _bootstrap_mean_diff

        vals = [100.0, 105.0, 98.0, 102.0, 101.0]
        diff, ci_lo, ci_hi, p = _bootstrap_mean_diff(vals, vals, n_bootstrap=5000, seed=42)
        assert abs(diff) < 1e-10
        assert p > 0.05

    def test_empty_group(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import _bootstrap_mean_diff

        diff, ci_lo, ci_hi, p = _bootstrap_mean_diff([], [1.0, 2.0])
        assert diff == 0.0
        assert p == 1.0

    def test_reproducibility(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import _bootstrap_mean_diff

        g1 = [100.0, 110.0]
        g2 = [130.0, 140.0]
        r1 = _bootstrap_mean_diff(g1, g2, n_bootstrap=1000, seed=123)
        r2 = _bootstrap_mean_diff(g1, g2, n_bootstrap=1000, seed=123)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Compute track tortuosity (single voyage)
# ---------------------------------------------------------------------------


class TestComputeTrackTortuosity:
    def test_basic(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=5)
        if not tracks:
            pytest.skip("No tracks in Roaring Forties")
        vid = tracks[0]["voyage_id"]
        result = compute_track_tortuosity(vid, lat_min=-50, lat_max=-30)
        if result is None:
            pytest.skip("Insufficient positions for tortuosity")
        assert "path_km" in result
        assert "net_km" in result
        assert "tortuosity_r" in result
        assert "n_in_box" in result
        assert "inferred_direction" in result

    def test_tortuosity_positive(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=20)
        for t in tracks:
            result = compute_track_tortuosity(t["voyage_id"], lat_min=-50, lat_max=-30)
            if result is not None:
                # Tortuosity is typically >= 1.0 but can be slightly below
                # when speed filtering drops intermediate positions
                assert result["tortuosity_r"] > 0.5, (
                    f"Tortuosity implausible for voyage {t['voyage_id']}: {result['tortuosity_r']}"
                )

    def test_not_found(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        result = compute_track_tortuosity(999999)
        assert result is None

    def test_few_positions(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        # Very tight bbox should have too few positions for most voyages
        result = compute_track_tortuosity(
            search_tracks(max_results=1)[0]["voyage_id"],
            lat_min=0,
            lat_max=0.01,
            lon_min=0,
            lon_max=0.01,
        )
        assert result is None

    def test_direction_inferred(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=10)
        for t in tracks:
            result = compute_track_tortuosity(t["voyage_id"], lat_min=-50, lat_max=-30)
            if result is not None:
                assert result["inferred_direction"] in ("eastbound", "westbound")
                break


# ---------------------------------------------------------------------------
# Aggregate track tortuosity
# ---------------------------------------------------------------------------


class TestAggregateTrackTortuosity:
    def test_by_decade(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["total_voyages"] > 0
        assert len(result["groups"]) > 0
        for g in result["groups"]:
            assert g["n"] > 0
            assert g["mean_tortuosity"] >= 1.0

    def test_by_direction(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="direction",
            lat_min=-50,
            lat_max=-30,
        )
        keys = {g["group_key"] for g in result["groups"]}
        assert keys <= {"eastbound", "westbound"}

    def test_min_positions_reduces_n(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        r_low = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            min_positions=3,
        )
        r_high = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            min_positions=20,
        )
        assert r_high["total_voyages"] <= r_low["total_voyages"]

    def test_period_comparison(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            period1_years="1750/1779",
            period2_years="1800/1829",
            n_bootstrap=1000,
        )
        if result.get("comparison") is not None:
            c = result["comparison"]
            assert "diff" in c
            assert "ci_lower" in c
            assert "ci_upper" in c
            assert "p_value" in c
            assert "significant" in c
            assert c["period1_n"] > 0
            assert c["period2_n"] > 0

    def test_empty_region(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=85,
            lat_max=89,
            lon_min=170,
            lon_max=180,
        )
        assert result["total_voyages"] == 0
        assert len(result["groups"]) == 0

    def test_tortuosity_in_range(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        for g in result["groups"]:
            assert g["mean_tortuosity"] >= 1.0


# ---------------------------------------------------------------------------
# Tortuosity R filtering
# ---------------------------------------------------------------------------


class TestTortuosityRFilter:
    def test_r_max_reduces_voyages(self):
        """r_max filter excludes high-tortuosity loiterers."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        unfiltered = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        filtered = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            r_max=5.0,
        )
        assert filtered["total_voyages"] <= unfiltered["total_voyages"]
        assert filtered["r_max_filter"] == 5.0
        assert unfiltered["r_max_filter"] is None

    def test_r_min_excludes_artifacts(self):
        """r_min=1.0 excludes sub-1.0 speed-filtering artifacts."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        filtered = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            r_min=1.0,
        )
        assert filtered["total_voyages"] > 0
        assert filtered["r_min_filter"] == 1.0

    def test_r_min_and_r_max_combined(self):
        """Normal transit filter: 1.0 <= R <= 5.0."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            r_min=1.0,
            r_max=5.0,
        )
        assert result["total_voyages"] > 0
        assert result["r_min_filter"] == 1.0
        assert result["r_max_filter"] == 5.0

    def test_tight_r_filter_returns_zero(self):
        """Impossibly tight R filter -> zero voyages."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_tortuosity

        result = aggregate_track_tortuosity(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            r_min=999,
            r_max=1000,
        )
        assert result["total_voyages"] == 0


# ---------------------------------------------------------------------------
# Wind force filtering on existing tools
# ---------------------------------------------------------------------------


class TestWindForceFiltering:
    def test_aggregate_with_wind_filter(self):
        """Wind force filter restricts to observations with matching Beaufort."""
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=4,
            wind_force_max=6,
        )
        assert result["wind_force_min_filter"] == 4
        assert result["wind_force_max_filter"] == 6
        # Filtered count should be less than unfiltered
        unfiltered = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["total_observations"] <= unfiltered["total_observations"]

    def test_compare_with_wind_filter(self):
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=3,
        )
        assert result["wind_force_min_filter"] == 3
        # Wind filter should restrict to observations with Beaufort >= 3
        assert result["period1_n"] >= 0
        assert result["period2_n"] >= 0

    def test_did_with_wind_filter(self):
        result = did_speed_test(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=4,
            wind_force_max=8,
        )
        assert result["wind_force_min_filter"] == 4
        assert result["wind_force_max_filter"] == 8
        # No wind data -> p=1.0
        assert result["did_p_value"] == 1.0

    def test_aggregate_by_beaufort(self):
        result = aggregate_track_speeds(
            group_by="beaufort",
            lat_min=-50,
            lat_max=-30,
        )
        # No wind data -> no groups, but the call should not fail
        assert result["group_by"] == "beaufort"
        assert isinstance(result["groups"], list)

    def test_extreme_wind_filter_graceful(self):
        """Impossible wind filter -> zero observations with no error."""
        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=12,
            wind_force_max=12,
        )
        # Very few or no hurricane-force obs in Roaring Forties
        assert result["total_observations"] >= 0
        assert result["wind_force_min_filter"] == 12


# ---------------------------------------------------------------------------
# Wind Rose
# ---------------------------------------------------------------------------


class TestWindRose:
    def test_basic(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        assert "has_wind_data" in result
        assert "total_with_wind" in result
        assert "total_without_wind" in result
        assert "beaufort_counts" in result
        assert len(result["beaufort_counts"]) == 13  # Forces 0-12

    def test_no_wind_data_graceful(self):
        """Empty region -> no wind data, graceful response."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=85, lat_max=89, lon_min=170, lon_max=180)
        # Arctic region has no CLIWOC data at all
        assert result["has_wind_data"] is False
        assert result["total_with_wind"] == 0

    def test_with_periods(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(
            lat_min=-50,
            lat_max=-30,
            period1_years="1750/1779",
            period2_years="1800/1829",
        )
        assert "period1_label" in result
        assert "period1_counts" in result
        assert "period2_label" in result
        assert "period2_counts" in result

    def test_empty_region(self):
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=85, lat_max=89, lon_min=170, lon_max=180)
        assert result["total_with_wind"] == 0
        assert result["total_without_wind"] == 0


# ---------------------------------------------------------------------------
# Tortuosity MCP tool wrappers
# ---------------------------------------------------------------------------


class TestTortuosityTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_track_tortuosity_tool(self):
        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=5)
        if not tracks:
            pytest.skip("No tracks in region")
        vid = tracks[0]["voyage_id"]

        fn = self.mcp.get_tool("maritime_track_tortuosity")
        result = await fn(voyage_id=vid, lat_min=-50, lat_max=-30)
        parsed = json.loads(result)
        # May be an error (insufficient positions) or success
        if "error" not in parsed:
            assert "tortuosity_r" in parsed
            assert parsed["tortuosity_r"] > 0.5

    @pytest.mark.asyncio
    async def test_aggregate_tortuosity_tool(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_tortuosity")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        parsed = json.loads(result)
        assert "total_voyages" in parsed
        assert "groups" in parsed

    @pytest.mark.asyncio
    async def test_aggregate_tortuosity_text(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_tortuosity")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            output_mode="text",
        )
        assert "tortuosity" in result.lower() or "Tortuosity" in result

    @pytest.mark.asyncio
    async def test_tortuosity_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_track_tortuosity")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.compute_track_tortuosity",
            side_effect=RuntimeError("tortboom"),
        ):
            result = await fn(voyage_id=1)
        parsed = json.loads(result)
        assert "tortboom" in parsed["error"]

    @pytest.mark.asyncio
    async def test_aggregate_tortuosity_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_aggregate_track_tortuosity")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.aggregate_track_tortuosity",
            side_effect=RuntimeError("aggfail"),
        ):
            result = await fn(group_by="decade")
        parsed = json.loads(result)
        assert "aggfail" in parsed["error"]


# ---------------------------------------------------------------------------
# Wind rose MCP tool wrapper
# ---------------------------------------------------------------------------


class TestWindRoseTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_wind_rose_tool(self):
        fn = self.mcp.get_tool("maritime_wind_rose")
        result = await fn(lat_min=-50, lat_max=-30)
        parsed = json.loads(result)
        assert "has_wind_data" in parsed
        assert "beaufort_counts" in parsed

    @pytest.mark.asyncio
    async def test_wind_rose_text(self):
        fn = self.mcp.get_tool("maritime_wind_rose")
        result = await fn(lat_min=-50, lat_max=-30, output_mode="text")
        assert isinstance(result, str)
        # Should contain wind-related info or no-data message
        assert "wind" in result.lower() or "Wind" in result

    @pytest.mark.asyncio
    async def test_wind_rose_error(self):
        from unittest.mock import patch

        fn = self.mcp.get_tool("maritime_wind_rose")
        with patch(
            "chuk_mcp_maritime_archives.tools.analytics.api.wind_rose",
            side_effect=RuntimeError("wrcrash"),
        ):
            result = await fn()
        parsed = json.loads(result)
        assert "wrcrash" in parsed["error"]


# ---------------------------------------------------------------------------
# Wind force filter on existing tool wrappers
# ---------------------------------------------------------------------------


class TestWindFilterTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_aggregate_with_wind_force(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=4,
            wind_force_max=6,
        )
        parsed = json.loads(result)
        assert parsed["wind_force_min_filter"] == 4
        assert parsed["wind_force_max_filter"] == 6

    @pytest.mark.asyncio
    async def test_compare_with_wind_force(self):
        fn = self.mcp.get_tool("maritime_compare_speed_groups")
        result = await fn(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=3,
        )
        parsed = json.loads(result)
        assert parsed["wind_force_min_filter"] == 3

    @pytest.mark.asyncio
    async def test_did_with_wind_force(self):
        fn = self.mcp.get_tool("maritime_did_speed_test")
        result = await fn(
            period1_years="1750/1783",
            period2_years="1784/1810",
            lat_min=-50,
            lat_max=-30,
            wind_force_min=4,
            wind_force_max=8,
        )
        parsed = json.loads(result)
        assert parsed["wind_force_min_filter"] == 4
        assert parsed["wind_force_max_filter"] == 8

    @pytest.mark.asyncio
    async def test_aggregate_beaufort_group(self):
        fn = self.mcp.get_tool("maritime_aggregate_track_speeds")
        result = await fn(
            group_by="beaufort",
            lat_min=-50,
            lat_max=-30,
        )
        parsed = json.loads(result)
        assert parsed["group_by"] == "beaufort"


# ---------------------------------------------------------------------------
# Anchor filtering
# ---------------------------------------------------------------------------


class TestAnchorFiltering:
    def test_exclude_anchored_default(self):
        """Anchored positions excluded by default (exclude_anchored=True)."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import aggregate_track_speeds

        result = aggregate_track_speeds(
            group_by="decade",
            lat_min=-50,
            lat_max=-30,
        )
        total_filtered = result["total_observations"]
        assert total_filtered > 0

    def test_include_anchored_increases_obs(self):
        """Including anchored positions may increase observation count."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import (
            _compute_daily_speeds,
            _load_tracks,
            _TRACKS,
        )

        _load_tracks()
        # Find a track with anchored positions
        for track in _TRACKS:
            has_anchored = any(p.get("anch") == 1 for p in track.get("positions", []))
            if not has_anchored:
                continue
            excluded = _compute_daily_speeds(track, exclude_anchored=True)
            included = _compute_daily_speeds(track, exclude_anchored=False)
            # Including anchored should give >= as many results
            assert len(included) >= len(excluded)
            break

    def test_tortuosity_excludes_anchored(self):
        """Tortuosity function also excludes anchored positions by default."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import compute_track_tortuosity

        tracks = search_tracks(lat_min=-50, lat_max=-30, max_results=5)
        if not tracks:
            pytest.skip("No tracks in region")
        vid = tracks[0]["voyage_id"]
        result = compute_track_tortuosity(voyage_id=vid, lat_min=-50, lat_max=-30)
        # Either returns valid result or None (insufficient positions)
        if result is not None:
            assert result["tortuosity_r"] >= 0.9


# ---------------------------------------------------------------------------
# Wind direction in wind_rose
# ---------------------------------------------------------------------------


class TestWindDirection:
    def test_direction_counts_present(self):
        """Wind rose includes direction_counts with 8 compass sectors."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        assert "direction_counts" in result
        assert "has_direction_data" in result
        assert result["has_direction_data"] is True
        assert len(result["direction_counts"]) == 8
        sectors = [dc["sector"] for dc in result["direction_counts"]]
        assert sectors == ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

    def test_direction_counts_sum(self):
        """Direction counts should sum to total_with_direction."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        total = sum(dc["count"] for dc in result["direction_counts"])
        assert total == result["total_with_direction"]

    def test_direction_with_mean_speed(self):
        """Each non-empty direction sector should have mean_speed_km_day."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        for dc in result["direction_counts"]:
            if dc["count"] > 0:
                assert dc["mean_speed_km_day"] is not None
                assert dc["mean_speed_km_day"] > 0

    def test_direction_period_comparison(self):
        """Period comparison includes direction counts per period."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(
            lat_min=-50,
            lat_max=-30,
            period1_years="1750/1779",
            period2_years="1800/1829",
        )
        assert "period1_direction_counts" in result
        assert "period2_direction_counts" in result
        assert len(result["period1_direction_counts"]) == 8
        assert len(result["period2_direction_counts"]) == 8

    def test_direction_empty_region(self):
        """Empty region returns has_direction_data=False."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=85, lat_max=89, lon_min=170, lon_max=180)
        assert result["has_direction_data"] is False
        assert result["total_with_direction"] == 0


# ---------------------------------------------------------------------------
# Distance calibration
# ---------------------------------------------------------------------------


class TestDistanceCalibration:
    def test_calibration_present(self):
        """Wind rose includes distance calibration data."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        cal = result.get("distance_calibration")
        if cal is not None:
            assert cal["n_pairs"] > 0
            assert cal["mean_logged_km_day"] > 0
            assert cal["mean_haversine_km_day"] > 0
            assert cal["logged_over_haversine"] is not None

    def test_calibration_ratio_reasonable(self):
        """Logged/haversine ratio should be roughly 0.5-2.0 (not wildly off)."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=-50, lat_max=-30)
        cal = result.get("distance_calibration")
        if cal is not None and cal.get("logged_over_haversine"):
            ratio = cal["logged_over_haversine"]
            assert 0.1 < ratio < 10.0, f"Calibration ratio {ratio} seems unreasonable"

    def test_calibration_empty_region(self):
        """Empty region returns no calibration data."""
        from chuk_mcp_maritime_archives.core.cliwoc_tracks import wind_rose

        result = wind_rose(lat_min=85, lat_max=89, lon_min=170, lon_max=180)
        assert result.get("distance_calibration") is None


# ---------------------------------------------------------------------------
# Wind direction in tool wrappers
# ---------------------------------------------------------------------------


class TestWindDirectionTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_wind_rose_tool_direction(self):
        fn = self.mcp.get_tool("maritime_wind_rose")
        result = await fn(lat_min=-50, lat_max=-30)
        parsed = json.loads(result)
        assert "direction_counts" in parsed
        assert "has_direction_data" in parsed
        if parsed["has_direction_data"]:
            assert len(parsed["direction_counts"]) == 8

    @pytest.mark.asyncio
    async def test_wind_rose_tool_calibration(self):
        fn = self.mcp.get_tool("maritime_wind_rose")
        result = await fn(lat_min=-50, lat_max=-30)
        parsed = json.loads(result)
        # distance_calibration may or may not be present
        if parsed.get("distance_calibration"):
            cal = parsed["distance_calibration"]
            assert cal["n_pairs"] > 0

    @pytest.mark.asyncio
    async def test_wind_rose_tool_period_directions(self):
        fn = self.mcp.get_tool("maritime_wind_rose")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            period1_years="1750/1779",
            period2_years="1800/1829",
        )
        parsed = json.loads(result)
        if parsed.get("has_direction_data"):
            assert "period1_direction_counts" in parsed
            assert "period2_direction_counts" in parsed


# ---------------------------------------------------------------------------
# Speed export — core function
# ---------------------------------------------------------------------------


class TestExportSpeeds:
    def test_voyage_level_basic(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="voyage",
        )
        assert result["aggregate_by"] == "voyage"
        assert result["total_matching"] > 0
        assert result["returned"] > 0
        assert result["returned"] <= result["total_matching"]
        assert "has_more" in result
        assert "offset" in result
        s = result["samples"][0]
        assert "voyage_id" in s
        assert "year" in s
        assert "speed_km_day" in s
        assert "n_observations" in s
        assert s["n_observations"] > 0

    def test_observation_level_basic(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
        )
        assert result["aggregate_by"] == "observation"
        assert result["total_matching"] > 0
        s = result["samples"][0]
        assert "lat" in s
        assert "lon" in s
        assert "wind_force" in s or s.get("wind_force") is None
        # Full date fields for temporal analyses (lunar phase, tidal, etc.)
        assert "date" in s
        assert "day" in s
        assert isinstance(s["date"], str)
        assert 1 <= s["day"] <= 31

    def test_observation_has_more_than_voyage(self):
        obs = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
        )
        voy = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="voyage",
        )
        assert obs["total_matching"] >= voy["total_matching"]

    def test_direction_filter(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            direction="eastbound",
            aggregate_by="voyage",
        )
        for s in result["samples"]:
            assert s["direction"] == "eastbound"
        assert result["direction_filter"] == "eastbound"

    def test_truncation(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            aggregate_by="observation",
            max_results=10,
        )
        assert result["returned"] <= 10
        if result["total_matching"] > 10:
            assert result["has_more"]
            assert result["next_offset"] == 10

    def test_wind_force_filter(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            aggregate_by="observation",
            wind_force_min=4,
            wind_force_max=6,
        )
        assert result["wind_force_min_filter"] == 4
        assert result["wind_force_max_filter"] == 6
        for s in result["samples"]:
            if s.get("wind_force") is not None:
                assert 4 <= s["wind_force"] <= 6

    def test_nationality_filter(self):
        result = export_speeds(nationality="NL", aggregate_by="voyage")
        for s in result["samples"]:
            assert s["nationality"] == "NL"
        assert result["nationality_filter"] == "NL"

    def test_empty_region(self):
        result = export_speeds(
            lat_min=80,
            lat_max=85,
            lon_min=170,
            lon_max=180,
            aggregate_by="voyage",
        )
        assert result["total_matching"] == 0
        assert result["returned"] == 0
        assert result["samples"] == []
        assert not result["has_more"]
        assert result["next_offset"] is None

    def test_pagination_offset(self):
        # Get all observations
        full = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
            max_results=10000,
        )
        total = full["total_matching"]
        if total < 2:
            return  # Not enough data to test pagination

        # Get first page
        page1 = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
            max_results=5,
            offset=0,
        )
        assert page1["returned"] == min(5, total)
        assert page1["total_matching"] == total
        assert page1["offset"] == 0
        if total > 5:
            assert page1["has_more"] is True
            assert page1["next_offset"] == 5

            # Get second page
            page2 = export_speeds(
                lat_min=-50,
                lat_max=-30,
                year_start=1780,
                year_end=1820,
                aggregate_by="observation",
                max_results=5,
                offset=5,
            )
            assert page2["offset"] == 5
            assert page2["returned"] == min(5, total - 5)
            # No overlap between pages
            dates1 = {(s["voyage_id"], s["date"]) for s in page1["samples"]}
            dates2 = {(s["voyage_id"], s["date"]) for s in page2["samples"]}
            assert len(dates1 & dates2) == 0

    def test_pagination_past_end(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
            max_results=5,
            offset=999999,
        )
        assert result["returned"] == 0
        assert result["samples"] == []
        assert not result["has_more"]

    def test_filter_metadata_present(self):
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            month_start=6,
            month_end=8,
            direction="westbound",
            aggregate_by="voyage",
        )
        assert result["latitude_band"] == [-50, -30]
        assert result["year_start_filter"] == 1780
        assert result["year_end_filter"] == 1820
        assert result["month_start_filter"] == 6
        assert result["month_end_filter"] == 8
        assert result["direction_filter"] == "westbound"


# ---------------------------------------------------------------------------
# Speed export — tool wrappers
# ---------------------------------------------------------------------------


class TestExportSpeedsTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_export_speeds_json(self):
        fn = self.mcp.get_tool("maritime_export_speeds")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="voyage",
        )
        parsed = json.loads(result)
        assert "total_matching" in parsed
        assert "samples" in parsed
        assert parsed["aggregate_by"] == "voyage"

    @pytest.mark.asyncio
    async def test_export_speeds_text(self):
        fn = self.mcp.get_tool("maritime_export_speeds")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="voyage",
            output_mode="text",
        )
        assert "Total matching" in result
        assert "Aggregate by: voyage" in result

    @pytest.mark.asyncio
    async def test_export_speeds_observation(self):
        fn = self.mcp.get_tool("maritime_export_speeds")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
            aggregate_by="observation",
            max_results=20,
        )
        parsed = json.loads(result)
        assert parsed["aggregate_by"] == "observation"
        assert parsed["returned"] <= 20

    @pytest.mark.asyncio
    async def test_export_speeds_with_wind_filter(self):
        fn = self.mcp.get_tool("maritime_export_speeds")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            wind_force_min=3,
            wind_force_max=7,
            aggregate_by="observation",
            max_results=50,
        )
        parsed = json.loads(result)
        assert parsed["wind_force_min_filter"] == 3
        assert parsed["wind_force_max_filter"] == 7


# ---------------------------------------------------------------------------
# Galleon transit times — core function
# ---------------------------------------------------------------------------


class TestGalleonTransitTimes:
    def test_basic(self):
        result = galleon_transit_times()
        assert result["total_matching"] > 0
        assert result["returned"] > 0
        assert result["records"]
        r = result["records"][0]
        assert "voyage_id" in r
        assert "transit_days" in r
        assert r["transit_days"] > 0

    def test_summary_stats(self):
        result = galleon_transit_times()
        assert result["summary"] is not None
        assert result["summary"]["n"] > 0
        assert result["summary"]["mean"] > 0
        assert result["eastbound_summary"] is not None
        assert result["westbound_summary"] is not None

    def test_eastbound_filter(self):
        result = galleon_transit_times(trade_direction="eastbound")
        for r in result["records"]:
            assert r["trade_direction"] == "eastbound"
        assert result["trade_direction_filter"] == "eastbound"
        # Eastbound should be faster than westbound
        assert result["summary"]["mean"] < 100

    def test_westbound_filter(self):
        result = galleon_transit_times(trade_direction="westbound")
        for r in result["records"]:
            assert r["trade_direction"] == "westbound"
        assert result["summary"]["mean"] > 100

    def test_year_filter(self):
        result = galleon_transit_times(year_start=1600, year_end=1700)
        for r in result["records"]:
            assert 1600 <= r["year"] <= 1700

    def test_fate_filter(self):
        result = galleon_transit_times(fate="completed")
        for r in result["records"]:
            assert r["fate"] == "completed"

    def test_truncation(self):
        result = galleon_transit_times(max_results=5)
        assert result["returned"] <= 5
        if result["total_matching"] > 5:
            assert result["truncated"]

    def test_empty_filter(self):
        result = galleon_transit_times(year_start=2000, year_end=2100)
        assert result["total_matching"] == 0
        assert result["records"] == []
        assert result["summary"] is None


# ---------------------------------------------------------------------------
# Wind direction by year — core function
# ---------------------------------------------------------------------------


class TestWindDirectionByYear:
    def test_basic(self):
        result = wind_direction_by_year(
            lat_min=-50,
            lat_max=-30,
            year_start=1780,
            year_end=1820,
        )
        assert result["total_observations"] > 0
        assert result["total_with_direction"] > 0
        assert result["total_years"] > 0
        assert len(result["years"]) > 0

    def test_year_structure(self):
        result = wind_direction_by_year(
            lat_min=-50,
            lat_max=-30,
            year_start=1800,
            year_end=1810,
        )
        for yg in result["years"]:
            assert "year" in yg
            assert "total_observations" in yg
            assert "sectors" in yg
            assert len(yg["sectors"]) == 8
            # Sector percentages should sum to ~100%
            total_pct = sum(s["percent"] for s in yg["sectors"])
            assert 99.0 <= total_pct <= 101.0

    def test_sectors_complete(self):
        result = wind_direction_by_year(
            lat_min=-50,
            lat_max=-30,
            year_start=1800,
            year_end=1820,
        )
        if result["years"]:
            sectors = {s["sector"] for s in result["years"][0]["sectors"]}
            assert sectors == {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}

    def test_nationality_filter(self):
        result = wind_direction_by_year(
            lat_min=-50,
            lat_max=-30,
            nationality="NL",
        )
        assert result["nationality_filter"] == "NL"

    def test_empty_region(self):
        result = wind_direction_by_year(
            lat_min=80,
            lat_max=85,
            lon_min=170,
            lon_max=180,
        )
        assert result["total_years"] == 0
        assert result["years"] == []

    def test_filter_metadata(self):
        result = wind_direction_by_year(
            lat_min=-50,
            lat_max=-30,
            direction="eastbound",
            month_start=6,
            month_end=8,
        )
        assert result["direction_filter"] == "eastbound"
        assert result["month_start_filter"] == 6
        assert result["month_end_filter"] == 8


# ---------------------------------------------------------------------------
# Galleon transit + wind direction — tool wrappers
# ---------------------------------------------------------------------------


class TestGalleonAndWindTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from unittest.mock import MagicMock

        from chuk_mcp_maritime_archives.tools.analytics.api import register_analytics_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_analytics_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_galleon_transit_json(self):
        fn = self.mcp.get_tool("maritime_galleon_transit_times")
        result = await fn(trade_direction="eastbound")
        parsed = json.loads(result)
        assert "total_matching" in parsed
        assert "records" in parsed
        assert parsed["trade_direction_filter"] == "eastbound"

    @pytest.mark.asyncio
    async def test_galleon_transit_text(self):
        fn = self.mcp.get_tool("maritime_galleon_transit_times")
        result = await fn(output_mode="text")
        assert "Eastbound" in result
        assert "Westbound" in result

    @pytest.mark.asyncio
    async def test_wind_direction_by_year_json(self):
        fn = self.mcp.get_tool("maritime_wind_direction_by_year")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            year_start=1800,
            year_end=1820,
        )
        parsed = json.loads(result)
        assert "total_years" in parsed
        assert "years" in parsed
        if parsed["years"]:
            assert len(parsed["years"][0]["sectors"]) == 8

    @pytest.mark.asyncio
    async def test_wind_direction_by_year_text(self):
        fn = self.mcp.get_tool("maritime_wind_direction_by_year")
        result = await fn(
            lat_min=-50,
            lat_max=-30,
            year_start=1800,
            year_end=1820,
            output_mode="text",
        )
        assert "Years covered" in result


# ---------------------------------------------------------------------------
# Period parsing (comma-separated year lists)
# ---------------------------------------------------------------------------


class TestParsePeriod:
    """Tests for _parse_period helper — range vs year list formats."""

    def test_range_format(self):
        result = _parse_period("1750/1789")
        assert isinstance(result, frozenset)
        assert len(result) == 40
        assert 1750 in result
        assert 1789 in result
        assert 1749 not in result
        assert 1790 not in result

    def test_comma_format(self):
        result = _parse_period("1720,1728,1747")
        assert isinstance(result, frozenset)
        assert result == frozenset({1720, 1728, 1747})

    def test_comma_format_with_spaces(self):
        result = _parse_period("1720, 1728, 1747")
        assert result == frozenset({1720, 1728, 1747})

    def test_single_year_comma(self):
        result = _parse_period("1800")
        assert result == frozenset({1800})

    def test_range_single_year(self):
        result = _parse_period("1800/1800")
        assert result == frozenset({1800})


class TestCommaYearListIntegration:
    """Test that comma-separated year lists work end-to-end in all tools."""

    def test_compare_speed_groups_comma_years(self):
        """compare_speed_groups accepts comma-separated year lists."""
        result = compare_speed_groups(
            period1_years="1780,1785,1790,1795,1800",
            period2_years="1810,1815,1820,1825,1830",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["period1_label"] == "1780,1785,1790,1795,1800"
        assert result["period2_label"] == "1810,1815,1820,1825,1830"
        assert isinstance(result["p_value"], float)

    def test_compare_speed_groups_range_still_works(self):
        """Existing range format still works."""
        result = compare_speed_groups(
            period1_years="1750/1789",
            period2_years="1820/1859",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["period1_n"] > 0
        assert result["period2_n"] > 0

    def test_did_speed_test_comma_years(self):
        """did_speed_test accepts comma-separated year lists."""
        result = did_speed_test(
            period1_years="1780,1785,1790,1795,1800",
            period2_years="1810,1815,1820,1825,1830",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["period1_label"] == "1780,1785,1790,1795,1800"
        assert isinstance(result["did_p_value"], float)

    def test_did_speed_test_empty_comma_years(self):
        """did_speed_test with years that have no data."""
        result = did_speed_test(
            period1_years="1500,1505,1510",
            period2_years="1515,1520,1525",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["did_p_value"] == 1.0
        assert result["did_estimate"] == 0.0


# ---------------------------------------------------------------------------
# CSV output & fields filtering
# ---------------------------------------------------------------------------


class TestCsvOutput:
    """Tests for CSV output mode and field selection on export_speeds."""

    def test_csv_output_has_header_and_rows(self):
        """CSV output starts with # metadata and has CSV header + rows."""
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(voyage_id=1, year=1780, speed_km_day=120.5),
            SpeedSample(voyage_id=2, year=1785, speed_km_day=130.0),
        ]
        resp = SpeedExportResponse(
            total_matching=2,
            returned=2,
            aggregate_by="voyage",
            samples=samples,
        )
        csv = format_response(resp, output_mode="csv")
        lines = csv.strip().split("\n")
        assert lines[0].startswith("# total_matching=2")
        assert "voyage_id" in lines[1]
        assert lines[1].count(",") > 0
        assert len(lines) == 4  # metadata + header + 2 rows

    def test_csv_fields_filter(self):
        """CSV with fields parameter returns only requested columns."""
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(
                voyage_id=1,
                year=1780,
                speed_km_day=120.5,
                direction="eastbound",
                nationality="NL",
            ),
        ]
        resp = SpeedExportResponse(
            total_matching=1,
            returned=1,
            aggregate_by="voyage",
            samples=samples,
        )
        csv = format_response(
            resp,
            output_mode="csv",
            fields=["voyage_id", "year", "speed_km_day"],
        )
        lines = csv.strip().split("\n")
        header = lines[1]
        assert header == "voyage_id,year,speed_km_day"
        # Data row should have exactly 2 commas (3 fields)
        assert lines[2].count(",") == 2

    def test_csv_observation_level(self):
        """CSV works for observation-level aggregate_by."""
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(
                voyage_id=1,
                date="1780-06-15",
                year=1780,
                month=6,
                day=15,
                speed_km_day=120.5,
                direction="eastbound",
                lat=-35.0,
                lon=25.0,
            ),
        ]
        resp = SpeedExportResponse(
            total_matching=1,
            returned=1,
            aggregate_by="observation",
            samples=samples,
        )
        csv = format_response(resp, output_mode="csv")
        lines = csv.strip().split("\n")
        assert "date" in lines[1]
        assert "lat" in lines[1]
        assert "1780-06-15" in lines[2]

    def test_csv_all_records_not_truncated(self):
        """CSV returns ALL records, not just first 50 like text mode."""
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(voyage_id=i, year=1780 + i, speed_km_day=100.0 + i) for i in range(80)
        ]
        resp = SpeedExportResponse(
            total_matching=80,
            returned=80,
            aggregate_by="voyage",
            samples=samples,
        )
        csv = format_response(resp, output_mode="csv")
        lines = csv.strip().split("\n")
        # metadata + header + 80 data rows
        assert len(lines) == 82

    def test_json_with_fields(self):
        """JSON output_mode with fields returns filtered samples."""
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(
                voyage_id=1,
                year=1780,
                speed_km_day=120.5,
                direction="eastbound",
                nationality="NL",
            ),
        ]
        resp = SpeedExportResponse(
            total_matching=1,
            returned=1,
            aggregate_by="voyage",
            samples=samples,
        )
        result = format_response(
            resp,
            output_mode="json",
            fields=["voyage_id", "speed_km_day"],
        )
        data = json.loads(result)
        sample = data["samples"][0]
        assert "voyage_id" in sample
        assert "speed_km_day" in sample
        # nationality should be filtered out
        assert "nationality" not in sample

    def test_csv_integration_with_export(self):
        """export_speeds data renders correctly in CSV."""
        result = export_speeds(
            lat_min=-50,
            lat_max=-30,
            lon_min=15,
            lon_max=110,
            aggregate_by="voyage",
            max_results=5,
        )
        from chuk_mcp_maritime_archives.models.responses import (
            SpeedExportResponse,
            SpeedSample,
            format_response,
        )

        samples = [
            SpeedSample(**{k: v for k, v in s.items() if v is not None}) for s in result["samples"]
        ]
        resp = SpeedExportResponse(
            total_matching=result["total_matching"],
            returned=result["returned"],
            aggregate_by=result["aggregate_by"],
            samples=samples,
        )
        csv = format_response(resp, output_mode="csv")
        lines = csv.strip().split("\n")
        assert len(lines) >= 3  # at least metadata + header + 1 row


# ---------------------------------------------------------------------------
# Exclude years
# ---------------------------------------------------------------------------


class TestExcludeYears:
    """Tests for exclude_years parameter on compare_speed_groups and did_speed_test."""

    def test_compare_exclude_reduces_samples(self):
        """Excluding years reduces the sample count in compare_speed_groups."""
        base = compare_speed_groups(
            period1_years="1750/1800",
            period2_years="1800/1850",
            lat_min=-50,
            lat_max=-30,
        )
        with_excl = compare_speed_groups(
            period1_years="1750/1800",
            period2_years="1800/1850",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1780,1783,1785,1790,1795,1800",
        )
        # Excluding years from period1 should reduce its count
        assert with_excl["period1_n"] <= base["period1_n"]

    def test_compare_exclude_range(self):
        """Excluding a range of years works."""
        result = compare_speed_groups(
            period1_years="1750/1830",
            period2_years="1750/1830",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1780/1800",
        )
        # Both periods have same years minus excluded, so stats are identical
        assert result["period1_n"] == result["period2_n"]

    def test_compare_exclude_affects_both_periods(self):
        """Excluding years removes from both periods uniformly."""
        result = compare_speed_groups(
            period1_years="1780,1785",
            period2_years="1750/1830",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1780,1785",
        )
        # period1 had only 1780 and 1785, both excluded -> zero
        assert result["period1_n"] == 0
        # period2 is a range minus excluded -> fewer samples
        base = compare_speed_groups(
            period1_years="1780,1785",
            period2_years="1750/1830",
            lat_min=-50,
            lat_max=-30,
        )
        assert result["period2_n"] <= base["period2_n"]

    def test_compare_exclude_zeroes_both(self):
        """Excluding all years from both periods gives zero samples."""
        result = compare_speed_groups(
            period1_years="1780/1785",
            period2_years="1790/1795",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1780/1795",
        )
        assert result["period1_n"] == 0
        assert result["period2_n"] == 0

    def test_did_exclude_years(self):
        """did_speed_test with exclude_years runs without error."""
        result = did_speed_test(
            period1_years="1750/1800",
            period2_years="1800/1850",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1783",
            n_bootstrap=100,
        )
        assert isinstance(result["did_p_value"], float)

    def test_did_exclude_comma_list(self):
        """did_speed_test exclude_years with comma list."""
        result = did_speed_test(
            period1_years="1750/1830",
            period2_years="1750/1830",
            lat_min=-50,
            lat_max=-30,
            exclude_years="1720,1728,1747,1761,1775,1783",
            n_bootstrap=100,
        )
        assert isinstance(result["did_estimate"], float)
