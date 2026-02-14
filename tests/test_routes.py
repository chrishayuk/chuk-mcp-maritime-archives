"""Tests for VOC routes module and MCP tools."""

import json
from unittest.mock import MagicMock, patch

import pytest

from chuk_mcp_maritime_archives.core.voc_routes import (
    VOC_ROUTES,
    estimate_position,
    get_route,
    get_route_ids,
    list_routes,
    suggest_route,
)

from .conftest import MockMCPServer


# ---------------------------------------------------------------------------
# Route data integrity
# ---------------------------------------------------------------------------


class TestRouteData:
    def test_has_minimum_routes(self):
        assert len(VOC_ROUTES) >= 15

    def test_all_routes_have_required_fields(self):
        for route_id, route in VOC_ROUTES.items():
            assert "name" in route, f"{route_id} missing name"
            assert "direction" in route, f"{route_id} missing direction"
            assert "typical_duration_days" in route, f"{route_id} missing duration"
            assert "waypoints" in route, f"{route_id} missing waypoints"
            assert len(route["waypoints"]) >= 3, f"{route_id} has too few waypoints"

    def test_all_directions_are_valid(self):
        valid = {"outward", "return", "intra_asian", "pacific_westbound", "pacific_eastbound"}
        for route_id, route in VOC_ROUTES.items():
            assert route["direction"] in valid, (
                f"{route_id} invalid direction: {route['direction']}"
            )

    def test_waypoints_have_required_fields(self):
        for route_id, route in VOC_ROUTES.items():
            for i, wp in enumerate(route["waypoints"]):
                assert "name" in wp, f"{route_id} wp[{i}] missing name"
                assert "lat" in wp, f"{route_id} wp[{i}] missing lat"
                assert "lon" in wp, f"{route_id} wp[{i}] missing lon"
                assert "region" in wp, f"{route_id} wp[{i}] missing region"
                assert "cumulative_days" in wp, f"{route_id} wp[{i}] missing cumulative_days"

    def test_waypoints_days_are_monotonic(self):
        for route_id, route in VOC_ROUTES.items():
            days = [wp["cumulative_days"] for wp in route["waypoints"]]
            assert days == sorted(days), f"{route_id} waypoint days not monotonic: {days}"

    def test_first_waypoint_starts_at_zero(self):
        for route_id, route in VOC_ROUTES.items():
            assert route["waypoints"][0]["cumulative_days"] == 0, (
                f"{route_id} first waypoint doesn't start at day 0"
            )

    def test_all_regions_are_valid(self):
        from chuk_mcp_maritime_archives.constants import REGIONS

        valid_regions = set(REGIONS.keys())
        for route_id, route in VOC_ROUTES.items():
            for wp in route["waypoints"]:
                assert wp["region"] in valid_regions, (
                    f"{route_id} waypoint '{wp['name']}' has invalid region: {wp['region']}"
                )

    def test_key_routes_present(self):
        assert "outward_outer" in VOC_ROUTES
        assert "outward_inner" in VOC_ROUTES
        assert "return" in VOC_ROUTES
        assert "japan" in VOC_ROUTES
        assert "spice_islands" in VOC_ROUTES
        assert "eic_outward" in VOC_ROUTES
        assert "eic_china" in VOC_ROUTES
        assert "eic_return" in VOC_ROUTES
        assert "carreira_outward" in VOC_ROUTES
        assert "carreira_return" in VOC_ROUTES
        assert "galleon_westbound" in VOC_ROUTES
        assert "galleon_eastbound" in VOC_ROUTES
        assert "soic_outward" in VOC_ROUTES
        assert "soic_return" in VOC_ROUTES
        assert "eic_country" in VOC_ROUTES


# ---------------------------------------------------------------------------
# list_routes / get_route / get_route_ids
# ---------------------------------------------------------------------------


class TestListRoutes:
    def test_returns_all_routes(self):
        routes = list_routes()
        assert len(routes) == len(VOC_ROUTES)

    def test_route_summary_has_required_fields(self):
        routes = list_routes()
        for r in routes:
            assert "route_id" in r
            assert "name" in r
            assert "direction" in r
            assert "typical_duration_days" in r
            assert "waypoint_count" in r


class TestGetRoute:
    def test_get_existing_route(self):
        route = get_route("outward_outer")
        assert route is not None
        assert route["route_id"] == "outward_outer"
        assert route["name"] == "Outward Voyage — Outer Route"
        assert len(route["waypoints"]) >= 5

    def test_get_nonexistent_route(self):
        assert get_route("nonexistent") is None


class TestGetRouteIds:
    def test_returns_all_ids(self):
        ids = get_route_ids()
        assert "outward_outer" in ids
        assert "return" in ids
        assert len(ids) == len(VOC_ROUTES)


# ---------------------------------------------------------------------------
# suggest_route
# ---------------------------------------------------------------------------


class TestSuggestRoute:
    def test_by_direction_outward(self):
        results = suggest_route(direction="outward")
        assert len(results) >= 2
        assert all(r["direction"] == "outward" for r in results)

    def test_by_direction_intra_asian(self):
        results = suggest_route(direction="intra_asian")
        assert len(results) >= 3

    def test_by_departure_port(self):
        results = suggest_route(departure_port="Texel")
        assert len(results) >= 2
        # outward_outer and outward_inner both start at Texel

    def test_by_destination_port(self):
        results = suggest_route(destination_port="Deshima")
        assert len(results) >= 1
        assert any(r["route_id"] == "japan" for r in results)

    def test_by_both_ports(self):
        results = suggest_route(departure_port="Batavia", destination_port="Banda")
        assert len(results) >= 1
        assert any(r["route_id"] == "spice_islands" for r in results)

    def test_no_match(self):
        results = suggest_route(destination_port="Nonexistent")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# estimate_position
# ---------------------------------------------------------------------------


class TestEstimatePosition:
    def test_at_departure(self):
        result = estimate_position("outward_outer", "1628-10-28", "1628-10-28")
        assert result is not None
        assert result["elapsed_days"] == 0
        assert result["confidence"] == "high"
        pos = result["estimated_position"]
        assert abs(pos["lat"] - 53.05) < 0.1  # Texel

    def test_midway(self):
        # ~60 days into outward_outer should be past equator
        result = estimate_position("outward_outer", "1628-10-28", "1628-12-27")
        assert result is not None
        assert result["elapsed_days"] == 60
        assert result["confidence"] == "moderate"

    def test_at_cape(self):
        # ~110 days should be at the Cape
        result = estimate_position("outward_outer", "1628-10-28", "1629-02-15")
        assert result is not None
        assert result["elapsed_days"] == 110
        pos = result["estimated_position"]
        assert pos["region"] == "cape"

    def test_during_stop(self):
        # 115 days = 5 days into Cape stop (stop_days=21 starting at day 110)
        result = estimate_position("outward_outer", "1628-10-28", "1629-02-20")
        assert result is not None
        assert result["confidence"] == "high"
        assert "port" in result["notes"].lower() or "Cape" in result["notes"]

    def test_past_arrival(self):
        # 250 days = well past the ~190 day journey
        result = estimate_position("outward_outer", "1628-10-28", "1629-07-06")
        assert result is not None
        pos = result["estimated_position"]
        assert abs(pos["lat"] - (-6.13)) < 0.1  # Batavia
        assert result["confidence"] in ("low", "moderate")

    def test_before_departure(self):
        result = estimate_position("outward_outer", "1628-10-28", "1628-10-01")
        assert result is not None
        assert "error" in result

    def test_invalid_route(self):
        result = estimate_position("nonexistent", "1628-10-28", "1628-12-28")
        assert result is None

    def test_invalid_dates(self):
        result = estimate_position("outward_outer", "bad-date", "1628-12-28")
        assert result is None

    def test_return_route(self):
        result = estimate_position("return", "1720-11-01", "1720-12-11")
        assert result is not None
        assert result["elapsed_days"] == 40
        assert result["estimated_position"]["region"] == "indian_ocean"

    def test_japan_route(self):
        result = estimate_position("japan", "1700-07-01", "1700-07-25")
        assert result is not None
        pos = result["estimated_position"]
        assert pos["region"] in ("south_china_sea", "japan")

    def test_voyage_progress(self):
        result = estimate_position("outward_outer", "1628-10-28", "1629-02-15")
        assert result is not None
        assert 0.0 < result["voyage_progress"] <= 1.0

    def test_has_caveats(self):
        result = estimate_position("outward_outer", "1628-10-28", "1628-12-27")
        assert result is not None
        assert "caveats" in result
        assert len(result["caveats"]) >= 1


# ---------------------------------------------------------------------------
# estimate_position with speed profiles
# ---------------------------------------------------------------------------


class TestEstimatePositionWithSpeedProfiles:
    def test_midway_with_speed_profiles(self):
        result = estimate_position(
            "outward_outer", "1628-10-28", "1628-12-27", use_speed_profiles=True
        )
        assert result is not None
        # May or may not have speed_profile depending on data availability
        if "speed_profile" in result:
            sp = result["speed_profile"]
            assert "mean_km_day" in sp
            assert "std_dev_km_day" in sp
            assert "sample_count" in sp
            assert sp["mean_km_day"] > 0

    def test_at_departure_no_speed_profile(self):
        # At departure point, no interpolation happens
        result = estimate_position(
            "outward_outer", "1628-10-28", "1628-10-28", use_speed_profiles=True
        )
        assert result is not None
        assert "speed_profile" not in result

    def test_past_arrival_no_speed_profile(self):
        result = estimate_position(
            "outward_outer", "1628-10-28", "1629-07-06", use_speed_profiles=True
        )
        assert result is not None
        assert "speed_profile" not in result

    def test_nonexistent_route_with_speed_profiles(self):
        result = estimate_position(
            "nonexistent", "1628-10-28", "1628-12-27", use_speed_profiles=True
        )
        assert result is None

    def test_without_speed_profiles_no_extra_field(self):
        result = estimate_position(
            "outward_outer", "1628-10-28", "1628-12-27", use_speed_profiles=False
        )
        assert result is not None
        assert "speed_profile" not in result


# ---------------------------------------------------------------------------
# Route MCP tools
# ---------------------------------------------------------------------------


class TestRouteTools:
    @pytest.fixture(autouse=True)
    def _register(self):
        from chuk_mcp_maritime_archives.tools.routes.api import register_route_tools

        self.mcp = MockMCPServer()
        self.mgr = MagicMock()
        register_route_tools(self.mcp, self.mgr)

    @pytest.mark.asyncio
    async def test_list_routes_success(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        result = await fn()
        parsed = json.loads(result)
        assert parsed["route_count"] >= 5
        assert len(parsed["routes"]) >= 5

    @pytest.mark.asyncio
    async def test_list_routes_by_direction(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        result = await fn(direction="outward")
        parsed = json.loads(result)
        assert parsed["route_count"] >= 2
        for r in parsed["routes"]:
            assert r["direction"] == "outward"

    @pytest.mark.asyncio
    async def test_list_routes_by_port(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        result = await fn(destination_port="Deshima")
        parsed = json.loads(result)
        assert parsed["route_count"] >= 1

    @pytest.mark.asyncio
    async def test_list_routes_no_match(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        result = await fn(destination_port="Nonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_list_routes_text_mode(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        result = await fn(output_mode="text")
        assert "outward_outer" in result

    @pytest.mark.asyncio
    async def test_list_routes_error(self):
        fn = self.mcp.get_tool("maritime_list_routes")
        with patch(
            "chuk_mcp_maritime_archives.tools.routes.api.list_routes",
            side_effect=RuntimeError("boom"),
        ):
            result = await fn()
        parsed = json.loads(result)
        assert "boom" in parsed["error"]

    @pytest.mark.asyncio
    async def test_get_route_success(self):
        fn = self.mcp.get_tool("maritime_get_route")
        result = await fn(route_id="outward_outer")
        parsed = json.loads(result)
        assert "route" in parsed
        assert parsed["route"]["route_id"] == "outward_outer"
        assert len(parsed["route"]["waypoints"]) >= 5

    @pytest.mark.asyncio
    async def test_get_route_not_found(self):
        fn = self.mcp.get_tool("maritime_get_route")
        result = await fn(route_id="nonexistent")
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_get_route_text_mode(self):
        fn = self.mcp.get_tool("maritime_get_route")
        result = await fn(route_id="outward_outer", output_mode="text")
        assert "Outer Route" in result
        assert "Texel" in result
        assert "Batavia" in result

    @pytest.mark.asyncio
    async def test_get_route_error(self):
        fn = self.mcp.get_tool("maritime_get_route")
        with patch(
            "chuk_mcp_maritime_archives.tools.routes.api.get_route",
            side_effect=RuntimeError("crash"),
        ):
            result = await fn(route_id="outward_outer")
        parsed = json.loads(result)
        assert "crash" in parsed["error"]

    @pytest.mark.asyncio
    async def test_estimate_position_success(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        result = await fn(
            route_id="outward_outer",
            departure_date="1628-10-28",
            target_date="1629-02-15",
        )
        parsed = json.loads(result)
        assert "estimate" in parsed
        assert "estimated_position" in parsed["estimate"]

    @pytest.mark.asyncio
    async def test_estimate_position_not_found(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        result = await fn(
            route_id="nonexistent",
            departure_date="1628-10-28",
            target_date="1629-02-15",
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_estimate_position_before_departure(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        result = await fn(
            route_id="outward_outer",
            departure_date="1628-10-28",
            target_date="1628-10-01",
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_estimate_position_text_mode(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        result = await fn(
            route_id="outward_outer",
            departure_date="1628-10-28",
            target_date="1629-02-15",
            output_mode="text",
        )
        assert "Estimated position" in result or "Route" in result

    @pytest.mark.asyncio
    async def test_estimate_position_with_speed_profiles(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        result = await fn(
            route_id="outward_outer",
            departure_date="1628-10-28",
            target_date="1629-02-15",
            use_speed_profiles=True,
        )
        parsed = json.loads(result)
        assert "estimate" in parsed

    @pytest.mark.asyncio
    async def test_estimate_position_error(self):
        fn = self.mcp.get_tool("maritime_estimate_position")
        with patch(
            "chuk_mcp_maritime_archives.tools.routes.api.estimate_position",
            side_effect=RuntimeError("fail"),
        ):
            result = await fn(
                route_id="outward_outer",
                departure_date="1628-10-28",
                target_date="1629-02-15",
            )
        parsed = json.loads(result)
        assert "fail" in parsed["error"]


# ---------------------------------------------------------------------------
# Response model to_text
# ---------------------------------------------------------------------------


class TestRouteResponseModels:
    def test_route_list_to_text(self):
        from chuk_mcp_maritime_archives.models.responses import RouteInfo, RouteListResponse

        r = RouteInfo(
            route_id="outward_outer",
            name="Outward Outer",
            direction="outward",
            typical_duration_days=200,
            waypoint_count=10,
        )
        resp = RouteListResponse(route_count=1, routes=[r], message="1 route")
        text = resp.to_text()
        assert "outward_outer" in text
        assert "200 days" in text

    def test_route_detail_to_text(self):
        from chuk_mcp_maritime_archives.models.responses import RouteDetailResponse

        resp = RouteDetailResponse(
            route={
                "route_id": "test",
                "name": "Test Route",
                "direction": "outward",
                "typical_duration_days": 100,
                "description": "A test route",
                "waypoints": [
                    {"name": "Start", "cumulative_days": 0, "stop_days": 0, "notes": "Begin"},
                    {"name": "End", "cumulative_days": 100, "stop_days": 0, "notes": "Finish"},
                ],
                "hazards": ["Storms"],
                "season_notes": "Best in summer",
            },
            message="test",
        )
        text = resp.to_text()
        assert "Test Route" in text
        assert "Start" in text
        assert "End" in text
        assert "Storms" in text
        assert "summer" in text

    def test_route_detail_no_hazards(self):
        from chuk_mcp_maritime_archives.models.responses import RouteDetailResponse

        resp = RouteDetailResponse(
            route={
                "route_id": "t",
                "name": "T",
                "direction": "outward",
                "typical_duration_days": 10,
                "waypoints": [],
            },
            message="test",
        )
        text = resp.to_text()
        assert "Hazards" not in text

    def test_position_estimate_to_text(self):
        from chuk_mcp_maritime_archives.models.responses import PositionEstimateResponse

        resp = PositionEstimateResponse(
            estimate={
                "route_name": "Outward Outer",
                "departure_date": "1628-10-28",
                "target_date": "1629-02-15",
                "elapsed_days": 110,
                "total_route_days": 190,
                "voyage_progress": 0.58,
                "estimated_position": {"lat": -33.93, "lon": 18.42, "region": "cape"},
                "segment": {
                    "from": "Cape of Good Hope",
                    "to": "Cape of Good Hope",
                    "progress": 0.0,
                },
                "confidence": "high",
                "notes": "At port: Cape of Good Hope",
            },
            message="test",
        )
        text = resp.to_text()
        assert "Outward Outer" in text
        assert "-33.93" in text
        assert "cape" in text
        assert "58%" in text


# ---------------------------------------------------------------------------
# EIC route data
# ---------------------------------------------------------------------------


class TestEICRouteData:
    def test_eic_outward_starts_at_downs(self):
        route = get_route("eic_outward")
        assert route["waypoints"][0]["name"] == "The Downs"

    def test_eic_outward_ends_at_madras(self):
        route = get_route("eic_outward")
        assert route["waypoints"][-1]["name"] == "Madras"

    def test_eic_outward_passes_cape(self):
        route = get_route("eic_outward")
        wp_names = [wp["name"] for wp in route["waypoints"]]
        assert "Cape of Good Hope" in wp_names

    def test_eic_china_ends_at_canton(self):
        route = get_route("eic_china")
        assert route["waypoints"][-1]["name"] == "Canton"

    def test_eic_return_starts_at_madras(self):
        route = get_route("eic_return")
        assert route["waypoints"][0]["name"] == "Madras"

    def test_eic_return_ends_at_downs(self):
        route = get_route("eic_return")
        assert route["waypoints"][-1]["name"] == "The Downs"

    def test_eic_country_is_intra_asian(self):
        route = get_route("eic_country")
        assert route["direction"] == "intra_asian"

    def test_eic_routes_have_valid_durations(self):
        for rid in ("eic_outward", "eic_china", "eic_return", "eic_country"):
            route = get_route(rid)
            assert 25 <= route["typical_duration_days"] <= 250


# ---------------------------------------------------------------------------
# Carreira da India route data
# ---------------------------------------------------------------------------


class TestCarreiraRouteData:
    def test_carreira_outward_starts_at_lisbon(self):
        route = get_route("carreira_outward")
        assert route["waypoints"][0]["name"] == "Lisbon"

    def test_carreira_outward_ends_at_goa(self):
        route = get_route("carreira_outward")
        assert route["waypoints"][-1]["name"] == "Goa"

    def test_carreira_outward_passes_mozambique(self):
        route = get_route("carreira_outward")
        wp_names = [wp["name"] for wp in route["waypoints"]]
        assert "Mozambique Island" in wp_names

    def test_carreira_return_starts_at_goa(self):
        route = get_route("carreira_return")
        assert route["waypoints"][0]["name"] == "Goa"

    def test_carreira_return_ends_at_lisbon(self):
        route = get_route("carreira_return")
        assert route["waypoints"][-1]["name"] == "Lisbon"

    def test_carreira_return_passes_azores(self):
        route = get_route("carreira_return")
        wp_names = [wp["name"] for wp in route["waypoints"]]
        assert "Azores" in wp_names


# ---------------------------------------------------------------------------
# Manila Galleon route data
# ---------------------------------------------------------------------------


class TestGalleonRouteData:
    def test_galleon_westbound_starts_at_acapulco(self):
        route = get_route("galleon_westbound")
        assert route["waypoints"][0]["name"] == "Acapulco"

    def test_galleon_westbound_ends_at_manila(self):
        route = get_route("galleon_westbound")
        assert route["waypoints"][-1]["name"] == "Manila"

    def test_galleon_westbound_passes_guam(self):
        route = get_route("galleon_westbound")
        wp_names = [wp["name"] for wp in route["waypoints"]]
        assert "Guam" in wp_names

    def test_galleon_eastbound_starts_at_manila(self):
        route = get_route("galleon_eastbound")
        assert route["waypoints"][0]["name"] == "Manila"

    def test_galleon_eastbound_ends_at_acapulco(self):
        route = get_route("galleon_eastbound")
        assert route["waypoints"][-1]["name"] == "Acapulco"

    def test_galleon_directions_are_pacific(self):
        wb = get_route("galleon_westbound")
        eb = get_route("galleon_eastbound")
        assert wb["direction"] == "pacific_westbound"
        assert eb["direction"] == "pacific_eastbound"


# ---------------------------------------------------------------------------
# SOIC route data
# ---------------------------------------------------------------------------


class TestSOICRouteData:
    def test_soic_outward_starts_at_gothenburg(self):
        route = get_route("soic_outward")
        assert route["waypoints"][0]["name"] == "Gothenburg"

    def test_soic_outward_ends_at_canton(self):
        route = get_route("soic_outward")
        assert route["waypoints"][-1]["name"] == "Canton"

    def test_soic_outward_passes_cape(self):
        route = get_route("soic_outward")
        wp_names = [wp["name"] for wp in route["waypoints"]]
        assert "Cape of Good Hope" in wp_names

    def test_soic_return_starts_at_canton(self):
        route = get_route("soic_return")
        assert route["waypoints"][0]["name"] == "Canton"

    def test_soic_return_ends_at_gothenburg(self):
        route = get_route("soic_return")
        assert route["waypoints"][-1]["name"] == "Gothenburg"


# ---------------------------------------------------------------------------
# Multi-nation position estimation
# ---------------------------------------------------------------------------


class TestMultiNationPositionEstimation:
    def test_eic_outward_at_departure(self):
        result = estimate_position("eic_outward", "1750-01-15", "1750-01-15")
        assert result is not None
        assert result["elapsed_days"] == 0
        assert abs(result["estimated_position"]["lat"] - 51.21) < 0.1

    def test_eic_outward_midway(self):
        result = estimate_position("eic_outward", "1750-01-15", "1750-03-16")
        assert result is not None
        assert result["elapsed_days"] == 60

    def test_eic_outward_at_cape(self):
        result = estimate_position("eic_outward", "1750-01-15", "1750-04-25")
        assert result is not None
        assert result["estimated_position"]["region"] == "cape"

    def test_eic_china_at_canton(self):
        result = estimate_position("eic_china", "1750-01-15", "1750-09-01")
        assert result is not None
        assert abs(result["estimated_position"]["lat"] - 23.13) < 0.1

    def test_carreira_outward_at_mozambique(self):
        result = estimate_position("carreira_outward", "1550-03-15", "1550-07-13")
        assert result is not None
        assert result["estimated_position"]["region"] == "mozambique_channel"

    def test_galleon_westbound_at_guam(self):
        result = estimate_position("galleon_westbound", "1600-03-01", "1600-05-05")
        assert result is not None
        assert result["estimated_position"]["region"] == "pacific"

    def test_galleon_eastbound_at_mendocino(self):
        result = estimate_position("galleon_eastbound", "1600-07-01", "1600-10-09")
        assert result is not None
        assert result["estimated_position"]["lat"] > 30.0  # Northern Pacific/California

    def test_soic_outward_at_cape(self):
        result = estimate_position("soic_outward", "1740-01-01", "1740-04-26")
        assert result is not None
        assert result["estimated_position"]["region"] == "cape"

    def test_soic_return_at_st_helena(self):
        result = estimate_position("soic_return", "1741-01-01", "1741-04-26")
        assert result is not None
        assert result["estimated_position"]["region"] == "atlantic_crossing"

    def test_eic_country_at_masulipatnam(self):
        result = estimate_position("eic_country", "1760-06-01", "1760-06-09")
        assert result is not None
        pos = result["estimated_position"]
        assert pos["region"] == "coromandel"


# ---------------------------------------------------------------------------
# Multi-nation suggest_route
# ---------------------------------------------------------------------------


class TestMultiNationSuggestRoute:
    def test_suggest_by_downs_departure(self):
        results = suggest_route(departure_port="Downs")
        route_ids = {r["route_id"] for r in results}
        assert "eic_outward" in route_ids
        assert "eic_china" in route_ids

    def test_suggest_by_lisbon_departure(self):
        results = suggest_route(departure_port="Lisbon")
        route_ids = {r["route_id"] for r in results}
        assert "carreira_outward" in route_ids

    def test_suggest_by_gothenburg_departure(self):
        results = suggest_route(departure_port="Gothenburg")
        route_ids = {r["route_id"] for r in results}
        assert "soic_outward" in route_ids

    def test_suggest_by_acapulco_departure(self):
        results = suggest_route(departure_port="Acapulco")
        route_ids = {r["route_id"] for r in results}
        assert "galleon_westbound" in route_ids

    def test_suggest_by_manila_destination(self):
        results = suggest_route(destination_port="Manila")
        route_ids = {r["route_id"] for r in results}
        assert "galleon_westbound" in route_ids

    def test_suggest_by_canton_destination(self):
        results = suggest_route(destination_port="Canton")
        route_ids = {r["route_id"] for r in results}
        assert "eic_china" in route_ids
        assert "soic_outward" in route_ids

    def test_suggest_pacific_westbound_direction(self):
        results = suggest_route(direction="pacific_westbound")
        assert len(results) >= 1
        assert all(r["direction"] == "pacific_westbound" for r in results)

    def test_suggest_pacific_eastbound_direction(self):
        results = suggest_route(direction="pacific_eastbound")
        assert len(results) >= 1
        assert all(r["direction"] == "pacific_eastbound" for r in results)

    def test_suggest_outward_includes_multi_nation(self):
        results = suggest_route(direction="outward")
        route_ids = {r["route_id"] for r in results}
        assert "outward_outer" in route_ids
        assert "eic_outward" in route_ids
        assert "carreira_outward" in route_ids
        assert "soic_outward" in route_ids

    def test_suggest_return_includes_multi_nation(self):
        results = suggest_route(direction="return")
        route_ids = {r["route_id"] for r in results}
        assert "return" in route_ids
        assert "eic_return" in route_ids
        assert "carreira_return" in route_ids
        assert "soic_return" in route_ids
