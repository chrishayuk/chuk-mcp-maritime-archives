"""Tests for speed profiles module and MCP tool."""

import json
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from chuk_mcp_maritime_archives.core.speed_profiles import (
    _PROFILES,
    get_segment_speed,
    get_speed_profile,
    list_profiled_routes,
)

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Speed profile data integrity
# ---------------------------------------------------------------------------


class TestSpeedProfileData:
    def test_has_minimum_profiles(self):
        assert len(_PROFILES) > 100

    def test_all_profiles_have_required_fields(self):
        required = {
            "route_id",
            "segment_from",
            "segment_to",
            "departure_month",
            "sample_count",
            "mean_km_day",
            "median_km_day",
            "std_dev_km_day",
        }
        for i, p in enumerate(_PROFILES):
            for field in required:
                assert field in p, f"profile[{i}] missing {field}"

    def test_speed_values_are_realistic(self):
        for i, p in enumerate(_PROFILES):
            assert 20.0 <= p["mean_km_day"] <= 400.0, (
                f"profile[{i}] mean_km_day={p['mean_km_day']} out of range"
            )

    def test_std_dev_is_non_negative(self):
        for i, p in enumerate(_PROFILES):
            assert p["std_dev_km_day"] >= 0, (
                f"profile[{i}] std_dev_km_day={p['std_dev_km_day']} is negative"
            )

    def test_sample_count_at_least_one(self):
        for i, p in enumerate(_PROFILES):
            assert p["sample_count"] >= 1, f"profile[{i}] sample_count={p['sample_count']} < 1"


# ---------------------------------------------------------------------------
# get_speed_profile
# ---------------------------------------------------------------------------


class TestGetSpeedProfile:
    def test_returns_profiles_for_existing_route(self):
        profiles = get_speed_profile("outward_outer")
        assert len(profiles) >= 1
        for p in profiles:
            assert p["route_id"] == "outward_outer"
            assert p.get("departure_month") is None  # all-months aggregates

    def test_returns_empty_for_nonexistent_route(self):
        assert get_speed_profile("nonexistent") == []

    def test_with_departure_month_returns_month_specific_or_fallback(self):
        profiles = get_speed_profile("outward_outer", departure_month=1)
        assert len(profiles) >= 1
        # Should get month-specific where available, fallback to all-months
        for p in profiles:
            assert p["route_id"] == "outward_outer"

    def test_list_profiled_routes_returns_known_routes(self):
        routes = list_profiled_routes()
        assert isinstance(routes, list)
        assert len(routes) >= 6
        assert "outward_outer" in routes
        assert "return" in routes
        assert "ceylon" in routes


# ---------------------------------------------------------------------------
# get_segment_speed
# ---------------------------------------------------------------------------


class TestGetSegmentSpeed:
    def test_returns_data_for_known_segment(self):
        result = get_segment_speed("outward_outer", "Cape Verde", "Equator crossing")
        assert result is not None
        assert result["route_id"] == "outward_outer"
        assert result["segment_from"] == "Cape Verde"
        assert result["segment_to"] == "Equator crossing"
        assert result["mean_km_day"] > 0

    def test_returns_none_for_unknown_segment(self):
        result = get_segment_speed("outward_outer", "Atlantis", "El Dorado")
        assert result is None

    def test_month_fallback_to_all_months(self):
        # Request a month that may not exist; should still return all-months
        result = get_segment_speed(
            "outward_outer", "Cape Verde", "Equator crossing", departure_month=99
        )
        assert result is not None
        assert result.get("departure_month") is None  # fell back to all-months


# ---------------------------------------------------------------------------
# Speed profile MCP tool
# ---------------------------------------------------------------------------


class TestSpeedProfileTool:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.speed.api import register_speed_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_speed_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_success(self):
        fn = self.mcp.get_tool("maritime_get_speed_profile")
        result = await fn(route_id="outward_outer")
        parsed = json.loads(result)
        assert parsed["route_id"] == "outward_outer"
        assert parsed["segment_count"] >= 1
        assert len(parsed["segments"]) >= 1

    @pytest.mark.asyncio
    async def test_not_found(self):
        fn = self.mcp.get_tool("maritime_get_speed_profile")
        result = await fn(route_id="nonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_with_departure_month(self):
        fn = self.mcp.get_tool("maritime_get_speed_profile")
        result = await fn(route_id="outward_outer", departure_month=1)
        parsed = json.loads(result)
        assert parsed["route_id"] == "outward_outer"
        assert parsed["segment_count"] >= 1

    @pytest.mark.asyncio
    async def test_text_mode_output(self):
        fn = self.mcp.get_tool("maritime_get_speed_profile")
        result = await fn(route_id="outward_outer", output_mode="text")
        assert "outward_outer" in result
        assert "km/day" in result


# ---------------------------------------------------------------------------
# Response model tests
# ---------------------------------------------------------------------------


class TestSpeedProfileModels:
    def test_segment_speed_info_creation(self):
        from chuk_mcp_maritime_archives.models.responses import SegmentSpeedInfo

        info = SegmentSpeedInfo(
            segment_from="Cape Verde",
            segment_to="Equator crossing",
            departure_month=None,
            sample_count=100,
            mean_km_day=185.8,
            median_km_day=185.4,
            std_dev_km_day=93.5,
        )
        assert info.segment_from == "Cape Verde"
        assert info.mean_km_day == 185.8
        assert info.min_km_day is None  # optional, not provided

    def test_speed_profile_response_to_text(self):
        from chuk_mcp_maritime_archives.models.responses import (
            SegmentSpeedInfo,
            SpeedProfileResponse,
        )

        seg = SegmentSpeedInfo(
            segment_from="Cape Verde",
            segment_to="Equator crossing",
            sample_count=100,
            mean_km_day=185.8,
            median_km_day=185.4,
            std_dev_km_day=93.5,
        )
        resp = SpeedProfileResponse(
            route_id="outward_outer",
            segment_count=1,
            segments=[seg],
            notes="Test notes",
            message="Speed profile for outward_outer: 1 segments",
        )
        text = resp.to_text()
        assert "outward_outer" in text
        assert "Cape Verde" in text
        assert "Equator crossing" in text
        assert "186 km/day" in text  # mean formatted as integer
        assert "Test notes" in text

    def test_extra_fields_are_forbidden(self):
        from chuk_mcp_maritime_archives.models.responses import SegmentSpeedInfo

        with pytest.raises(ValidationError):
            SegmentSpeedInfo(
                segment_from="A",
                segment_to="B",
                sample_count=10,
                mean_km_day=100.0,
                median_km_day=100.0,
                std_dev_km_day=10.0,
                bogus_field="should fail",
            )
