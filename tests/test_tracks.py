"""Tests for the CLIWOC ship tracks module."""

import json

import pytest

from chuk_mcp_maritime_archives.core.cliwoc_tracks import (
    _TRACKS,
    _haversine_km,
    get_date_range,
    get_position_count,
    get_track,
    get_track_count,
    list_nationalities,
    nearby_tracks,
    search_tracks,
)

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
